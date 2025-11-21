"""
Router de Simulación - Epidemia

Endpoints para iniciar simulaciones y obtener resultados.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path
import uuid
import time
import numpy as np

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import PATHS, SIM_CONFIG
from src.data.loader import DataLoader
from src.data.processor import DataProcessor
from src.core.graph import ContactGraphBuilder
from src.core.sparse_network import SparseContactNetwork
from src.core.epidemic import VectorizedSIRSimulator, VectorizedPropagationTree
from src.core.network_cache import NetworkCacheManager
from src.analysis.analyzers import AnalysisCoordinator, create_infected_subgraph
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Modelos Pydantic
# ============================================================================

class SimulationRequest(BaseModel):
    """Request para iniciar simulación."""
    beta: float = Field(default=0.3, ge=0.0, le=1.0, description="Tasa de transmisión (0-1)")
    num_pacientes_cero: int = Field(default=5, ge=1, le=100, description="Número de pacientes cero")


class SimulationResponse(BaseModel):
    """Respuesta al iniciar simulación."""
    simulation_id: str
    message: str
    beta: float
    num_pacientes_cero: int
    pacientes_cero: List[str]


class InfectedByDay(BaseModel):
    """Infectados por día."""
    dia: str
    dia_numero: int
    nuevos_infectados: int
    total_infectados: int
    infectados_ids: List[str]


class InfectedResponse(BaseModel):
    """Respuesta con infectados por día."""
    simulation_id: str
    dias: List[InfectedByDay]
    total_final: int
    tasa_ataque: float


class WCCComponent(BaseModel):
    """Componente WCC."""
    tamano: int
    super_spreaders: List[Dict[str, Any]]


class WCCResponse(BaseModel):
    """Respuesta con análisis WCC."""
    simulation_id: str
    num_componentes: int
    componente_gigante_size: int
    top_components: List[WCCComponent]
    fragmentacion_index: float


# ============================================================================
# Almacenamiento en memoria de simulaciones
# ============================================================================

_simulations: Dict[str, Dict[str, Any]] = {}
_loader = None
_processor = None
_graph_builder = None
_network_cache = None


def get_dependencies():
    """Inicializa y retorna dependencias globales."""
    global _loader, _processor, _graph_builder, _network_cache
    
    if _loader is None:
        _loader = DataLoader(PATHS.estudiantes, PATHS.clases, PATHS.asistencias)
        _processor = DataProcessor()
        _graph_builder = ContactGraphBuilder()
        _network_cache = NetworkCacheManager(_graph_builder)
        logger.info("Dependencias de simulación inicializadas")
    
    return _loader, _processor, _graph_builder, _network_cache


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/simulation/start", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest):
    """
    Inicia una nueva simulación epidémica.
    
    Parámetros:
    - beta: Tasa de transmisión (0-1)
    - num_pacientes_cero: Cantidad de pacientes iniciales
    
    Returns:
        SimulationResponse con ID de simulación y pacientes cero seleccionados
    """
    try:
        # Generar ID único
        simulation_id = str(uuid.uuid4())
        
        # Obtener dependencias
        loader, processor, graph_builder, network_cache = get_dependencies()
        
        # Cargar datos
        estudiantes, clases, asistencias = loader.load_all()
        df_unificado = processor.create_unified_dataframe(estudiantes, clases, asistencias)
        
        # Seleccionar pacientes cero aleatorios
        np.random.seed(int(time.time() * 1000000) % 2**32)
        pacientes_cero = np.random.choice(
            estudiantes['id_estudiante'].tolist(),
            size=request.num_pacientes_cero,
            replace=False
        ).tolist()
        # Asegurar que son strings
        pacientes_cero = [str(pid) for pid in pacientes_cero]
        
        logger.info(f"Simulación {simulation_id} iniciada con beta={request.beta}, pacientes_cero={pacientes_cero}")
        
        # Ejecutar simulación
        infected_by_day = []
        propagation_tree = VectorizedPropagationTree()
        
        # Estados globales (asegurar que todas las claves son strings)
        global_states = {str(sid): 0 for sid in estudiantes['id_estudiante']}
        for pid in pacientes_cero:
            global_states[str(pid)] = 1
        
        dia_numero = 0
        for dia_nombre in SIM_CONFIG.dias_semana:
            df_dia = processor.filter_by_day(df_unificado, dia_nombre)
            
            if len(df_dia) == 0:
                continue
            
            # Construir red sparse
            sparse_network = network_cache.get_or_build(dia_nombre, df_dia)
            
            if sparse_network.get_node_count() == 0:
                continue
            
            # Simulador vectorizado
            simulator = VectorizedSIRSimulator(request.beta, sparse_network.get_node_count())
            simulator.set_contact_matrix(sparse_network.get_matrix())
            
            # Mapear infectados
            infectados_globales = [sid for sid, s in global_states.items() if s == 1]
            patient_zero_indices = sparse_network.map_ids_to_indices(infectados_globales)
            simulator.initialize_infections(patient_zero_indices)
            
            # Simular tick
            num_nuevos, new_indices = simulator.simulate_tick()
            
            # Actualizar estados
            if num_nuevos > 0:
                new_ids = sparse_network.map_indices_to_ids(new_indices)
                for nid in new_ids:
                    global_states[str(nid)] = 1
                
                # Registrar transmisiones
                infected_indices = simulator.get_infected_indices()
                propagation_tree.record_transmissions(
                    infected_indices,
                    new_indices,
                    sparse_network.get_matrix(),
                    dia_nombre,
                    sparse_network.idx_to_node
                )
            
            total_infectados = sum(global_states.values())
            infectados_ids = [str(sid) for sid, s in global_states.items() if s == 1]
            
            infected_by_day.append(InfectedByDay(
                dia=dia_nombre,
                dia_numero=dia_numero,
                nuevos_infectados=num_nuevos,
                total_infectados=total_infectados,
                infectados_ids=infectados_ids
            ))
            
            dia_numero += 1
        
        # Calcular WCC
        arbol_nx = propagation_tree.to_networkx()
        analyzer = AnalysisCoordinator()
        all_results = analyzer.run_all_analyses(arbol_nx, estudiantes)
        wcc_results = all_results.get('wcc', {})
        
        # Almacenar resultados
        _simulations[simulation_id] = {
            'beta': request.beta,
            'num_pacientes_cero': request.num_pacientes_cero,
            'pacientes_cero': pacientes_cero,
            'infected_by_day': infected_by_day,
            'global_states': global_states,
            'wcc_results': wcc_results,
            'estudiantes': estudiantes,
            'timestamp': time.time()
        }
        
        logger.info(f"Simulación {simulation_id} completada. Total infectados: {sum(global_states.values())}")
        
        return SimulationResponse(
            simulation_id=simulation_id,
            message="Simulación completada exitosamente",
            beta=request.beta,
            num_pacientes_cero=request.num_pacientes_cero,
            pacientes_cero=pacientes_cero
        )
    
    except Exception as e:
        logger.error(f"Error en simulación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")


@router.get("/simulation/{simulation_id}/infected", response_model=InfectedResponse)
async def get_infected(simulation_id: str):
    """
    Obtiene los infectados por día de una simulación.
    
    Returns:
        InfectedResponse con infectados por día
    """
    if simulation_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    sim = _simulations[simulation_id]
    total_final = sum(sim['global_states'].values())
    num_estudiantes = len(sim['estudiantes'])
    tasa_ataque = (total_final / num_estudiantes) * 100 if num_estudiantes > 0 else 0
    
    logger.info(f"Retornando infectados de simulación {simulation_id}")
    
    return InfectedResponse(
        simulation_id=simulation_id,
        dias=sim['infected_by_day'],
        total_final=total_final,
        tasa_ataque=tasa_ataque
    )


@router.get("/simulation/{simulation_id}/wcc", response_model=WCCResponse)
async def get_wcc(simulation_id: str):
    """
    Obtiene análisis WCC de una simulación.
    
    Solo disponible después de completar la simulación.
    
    Returns:
        WCCResponse con análisis de componentes
    """
    if simulation_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    sim = _simulations[simulation_id]
    wcc = sim['wcc_results']
    
    # Extraer componentes principales
    top_components = []
    if 'analisis_componentes' in wcc and wcc['analisis_componentes']:
        for comp in wcc['analisis_componentes'][:3]:
            top_components.append(WCCComponent(
                tamano=comp['tamano'],
                super_spreaders=comp['super_spreaders']
            ))
    
    logger.info(f"Retornando WCC de simulación {simulation_id}")
    
    return WCCResponse(
        simulation_id=simulation_id,
        num_componentes=wcc['num_componentes'],
        componente_gigante_size=wcc['componente_gigante'],
        top_components=top_components,
        fragmentacion_index=1.0 - (wcc['componente_gigante'] / sum(wcc['tamanos'])) if sum(wcc['tamanos']) > 0 else 0.0
    )
