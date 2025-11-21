"""
Router de MTC (Minimum Spanning Tree)

Endpoints para análisis MTC de la red de contactos.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sys
from pathlib import Path
import uuid

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import PATHS, SIM_CONFIG
from src.data.loader import DataLoader
from src.data.processor import DataProcessor
from src.core.graph import ContactGraphBuilder
from src.analysis import DailyGraphAnalysisCoordinator
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Modelos Pydantic
# ============================================================================

class MTCRequest(BaseModel):
    """Request para iniciar análisis MTC."""
    weight_mode: str = "inverse"  # inverse o direct


class MTCResponse(BaseModel):
    """Respuesta al iniciar análisis MTC."""
    mtc_id: str
    message: str


class CriticalEdge(BaseModel):
    """Arista crítica en el MST."""
    estudiante_a: str
    estudiante_b: str
    peso: float
    interpretacion: str


class BridgeNode(BaseModel):
    """Nodo puente crítico en el MST."""
    estudiante_id: str
    grado: int
    betweenness: float
    interpretacion: str


class MTCInfo(BaseModel):
    """Información detallada del análisis MTC."""
    mtc_id: str
    
    # Estadísticas básicas
    num_nodos: int
    num_aristas_originales: int
    num_aristas_mst: int
    peso_total_mst: float
    peso_promedio: float
    ratio_reduccion: float
    num_componentes: int
    
    # Información crítica para epidemiología
    aristas_criticas: List[CriticalEdge]
    nodos_puente: List[BridgeNode]
    
    # Interpretación contextual
    interpretacion: str
    recomendaciones: List[str]


# ============================================================================
# Almacenamiento en memoria
# ============================================================================

_mtc_results: Dict[str, Dict[str, Any]] = {}
_loader = None
_processor = None
_graph_builder = None


def get_dependencies():
    """Inicializa y retorna dependencias globales."""
    global _loader, _processor, _graph_builder
    
    if _loader is None:
        _loader = DataLoader(PATHS.estudiantes, PATHS.clases, PATHS.asistencias)
        _processor = DataProcessor()
        _graph_builder = ContactGraphBuilder()
        logger.info("Dependencias de MTC inicializadas")
    
    return _loader, _processor, _graph_builder


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/mtc/analyze", response_model=MTCInfo)
async def analyze_mtc(weight_mode: str = "inverse"):
    """
    Analiza la red de contactos y retorna información del MST directamente.
    
    Este endpoint es independiente de las simulaciones y puede ejecutarse
    en cualquier momento para obtener análisis de la estructura de la red.
    
    Args:
        weight_mode: 'inverse' (default) o 'direct' para pesos del MST
    
    Returns:
        MTCInfo con métricas del MST
    """
    try:
        # Obtener dependencias
        loader, processor, graph_builder = get_dependencies()
        
        # Cargar datos
        estudiantes, clases, asistencias = loader.load_all()
        df_unificado = processor.create_unified_dataframe(estudiantes, clases, asistencias)
        
        # Crear coordinador de análisis
        coordinator = DailyGraphAnalysisCoordinator(weight_mode=weight_mode)
        
        # Analizar el primer día con datos (o agregar todos los días)
        for dia_nombre in SIM_CONFIG.dias_semana:
            df_dia = processor.filter_by_day(df_unificado, dia_nombre)
            
            if len(df_dia) == 0:
                continue
            
            # Construir grafo del día
            G_dia = graph_builder.build_daily_graph(df_dia)
            
            # Analizar MST
            results = coordinator.run_all_analyses(G_dia)
            mst_data = results['mst']
            mst_graph = mst_data['mst']
            
            # Generar ID único para este análisis
            mtc_id = str(uuid.uuid4())
            
            # Extraer top 10 aristas críticas (contactos más fuertes)
            critical_edges = []
            for u, v, peso in mst_data['critical_edges'][:10]:
                interpretacion = "Contacto muy frecuente" if peso > 5 else "Contacto frecuente" if peso > 2 else "Contacto moderado"
                critical_edges.append(CriticalEdge(
                    estudiante_a=str(u),
                    estudiante_b=str(v),
                    peso=round(peso, 2),
                    interpretacion=interpretacion
                ))
            
            # Identificar nodos puente (clave para conectividad)
            import networkx as nx
            betweenness = nx.betweenness_centrality(mst_graph)
            degree = dict(mst_graph.degree())
            
            # Top 10 nodos puente
            bridge_nodes = []
            sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
            for node_id, bc in sorted_nodes:
                deg = degree.get(node_id, 0)
                if bc > 0:
                    interpretacion = "Super-conector crítico" if bc > 0.1 else "Conector importante" if bc > 0.05 else "Conector"
                    bridge_nodes.append(BridgeNode(
                        estudiante_id=str(node_id),
                        grado=deg,
                        betweenness=round(bc, 4),
                        interpretacion=interpretacion
                    ))
            
            # Generar interpretación contextual
            num_nodos = mst_graph.number_of_nodes()
            num_aristas = mst_graph.number_of_edges()
            ratio = mst_data['reduction_ratio']
            
            interpretacion = (
                f"El MST identifica {num_aristas} contactos esenciales entre {num_nodos} estudiantes, "
                f"reduciendo la red en {ratio*100:.1f}%. Estos contactos representan los caminos de "
                f"transmisión más probables en caso de epidemia."
            )
            
            # Generar recomendaciones
            recomendaciones = []
            if len(bridge_nodes) > 0:
                recomendaciones.append(
                    f"Priorizar vigilancia epidemiológica en los {len(bridge_nodes)} nodos puente identificados, "
                    f"ya que conectan múltiples grupos."
                )
            
            if mst_data['num_componentes'] > 1:
                recomendaciones.append(
                    f"La red tiene {mst_data['num_componentes']} componentes aislados. "
                    f"Las intervenciones pueden ser más efectivas si se enfocan por componente."
                )
            else:
                recomendaciones.append(
                    "La red está completamente conectada. Una epidemia podría propagarse a toda la población "
                    "si no se implementan medidas de control."
                )
            
            if len(critical_edges) > 0:
                avg_critical = sum(e.peso for e in critical_edges[:3]) / min(3, len(critical_edges))
                if avg_critical > 5:
                    recomendaciones.append(
                        "Se detectaron contactos muy frecuentes. Considerar distanciamiento físico o "
                        "reducción de tamaño de grupos en clases más concurridas."
                    )
            
            logger.info(f"Análisis MTC completado: {mtc_id}")
            
            return MTCInfo(
                mtc_id=mtc_id,
                num_nodos=num_nodos,
                num_aristas_originales=G_dia.number_of_edges(),
                num_aristas_mst=num_aristas,
                peso_total_mst=mst_data['total_weight'],
                peso_promedio=mst_data['avg_weight'],
                ratio_reduccion=mst_data['reduction_ratio'],
                num_componentes=mst_data['num_componentes'],
                aristas_criticas=critical_edges,
                nodos_puente=bridge_nodes,
                interpretacion=interpretacion,
                recomendaciones=recomendaciones
            )
        
        # Si no hay datos
        raise HTTPException(status_code=404, detail="No se encontraron datos para analizar")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en análisis MTC: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en análisis MTC: {str(e)}")
