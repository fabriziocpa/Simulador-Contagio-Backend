"""Simulador SIR completamente vectorizado usando matrices sparse."""
import numpy as np
import scipy.sparse as sp
from typing import List, Tuple, Set, Dict


class VectorizedSIRSimulator:
    """Simulador SIR vectorizado de alto rendimiento.
    - Multithreading automático vía vecLib/Accelerate
    - Vectorización SIMD optimizada para ARM64 """
    
    def __init__(self, beta: float, num_nodes: int):
        self.beta = beta
        self.num_nodes = num_nodes
        
        # Estados: 0=S (susceptible), 1=I (infectado)
        self.states = np.zeros(num_nodes, dtype=np.int8)
        
        # Optimización 1: Pre-asignar buffer de números aleatorios
        self.random_buffer = np.empty(num_nodes, dtype=np.float32)
        
        # Optimización 2: Cache de máscara de susceptibles (actualización incremental)
        self.susceptible_mask = np.ones(num_nodes, dtype=bool)
        
        # Matriz de contacto (se asignará externamente)
        self.contact_matrix: sp.csr_matrix = None
    
    def initialize_infections(self, patient_zero_indices: np.ndarray):
        """Inicializa infecciones con pacientes cero."""
        self.states[:] = 0
        self.susceptible_mask[:] = True  # Resetear máscara
        if len(patient_zero_indices) > 0:
            self.states[patient_zero_indices] = 1
            self.susceptible_mask[patient_zero_indices] = False  # Marcar infectados
    
    def set_contact_matrix(self, matrix: sp.csr_matrix):
        """Asigna la matriz de contacto para este día."""
        self.contact_matrix = matrix
    
    def simulate_tick(self) -> Tuple[int, np.ndarray]:
        """Simula un tick de transmisión vectorizado."""
        if self.contact_matrix is None:
            return 0, np.array([], dtype=int)
        
        # Vector de infectados
        infected = (self.states == 1).astype(np.float32)
        
        # Exposición: producto matriz-vector sparse (optimizado por SciPy)
        exposure = self.contact_matrix @ infected
        
        # Probabilidad de transmisión: P = 1 - exp(-β * E)
        P = 1.0 - np.exp(-self.beta * exposure)
        
        # Decisión estocástica vectorizada (usando buffer pre-asignado)
        self.random_buffer[:] = np.random.rand(self.num_nodes)
       
        new_infections = (self.random_buffer < P) & self.susceptible_mask
        new_indices = np.where(new_infections)[0]
        
        if len(new_indices) > 0:
            self.states[new_indices] = 1
            self.susceptible_mask[new_indices] = False  # Actualización incremental
        
        return len(new_indices), new_indices
    
    def get_infected_count(self) -> int:
        return int(np.sum(self.states == 1))
    
    def get_infected_indices(self) -> np.ndarray:
        return np.where(self.states == 1)[0]
    
    def get_states_dict(self, idx_to_node: Dict[int, int]) -> Dict[int, int]:
        """
        Convierte estados a diccionario con IDs originales.
        
        Args:
            idx_to_node: Mapeo índice → ID de nodo
            
        Returns:
            Dict {node_id: state}
        """
        return {idx_to_node[i]: int(self.states[i]) for i in range(self.num_nodes)}


class VectorizedPropagationTree:
    """Árbol de propagación simulador vectorizado."""
    
    def __init__(self):
        # Listas para almacenar transmisiones
        self.sources: List[int] = []      # IDs de fuentes
        self.targets: List[int] = []      # IDs de objetivos
        self.weights: List[float] = []    # Pesos de contacto
        self.days: List[str] = []         # Días de transmisión
    
    def record_transmissions(self, 
                            sources: np.ndarray,
                            targets: np.ndarray,
                            contact_matrix: sp.csr_matrix,
                            day_name: str,
                            idx_to_node: Dict[int, int]):
        """Registra múltiples transmisiones de forma vectorizada."""
        for target_idx in targets:
            # Obtener vecinos infectados que podrían haber transmitido
            # Esto requiere buscar en la matriz sparse
            row = contact_matrix[target_idx]
            neighbor_indices = row.indices
            neighbor_weights = row.data
            
            # Filtrar solo vecinos infectados (aproximación: usar último infectado)
            # En realidad, múltiples infectados podrían transmitir, tomamos el primero
            # que esté en sources
            for i, neighbor_idx in enumerate(neighbor_indices):
                if neighbor_idx in sources:
                    source_id = idx_to_node[int(neighbor_idx)]
                    target_id = idx_to_node[int(target_idx)]
                    weight = float(neighbor_weights[i])
                    
                    self.sources.append(source_id)
                    self.targets.append(target_id)
                    self.weights.append(weight)
                    self.days.append(day_name)
                    break  # Solo registrar primera transmisión
    
    def get_transmission_count(self) -> int:
        """Número total de transmisiones registradas."""
        return len(self.sources)
    
    def to_networkx(self):
        """Convierte a NetworkX DiGraph para compatibilidad."""
        import networkx as nx
        
        G = nx.DiGraph()
        for i in range(len(self.sources)):
            G.add_edge(
                self.sources[i],
                self.targets[i],
                peso=self.weights[i],
                dia=self.days[i]
            )
        
        return G
    
    def get_tree(self):
        return self.to_networkx()
