"""Módulo de red de contacto usando matrices sparse CSR para optimización."""
import numpy as np
import scipy.sparse as sp
from typing import List, Tuple, Dict


class SparseContactNetwork:
    """
    Red de contacto usando matriz sparse CSR (Compressed Sparse Row).
    """
    
    def __init__(self, num_nodes: int = 0):
        self.num_nodes = num_nodes
        self.node_to_idx: Dict[int, int] = {}  # Mapeo ID → índice
        self.idx_to_node: Dict[int, int] = {}  # Mapeo índice → ID
        self.matrix: sp.csr_matrix = None      # Matriz CSR de pesos
    
    def build_from_edges(self, edges: List[Tuple[int, int, float]]):
        """
        Construye matriz CSR desde lista de aristas.
        
        Args:
            edges: Lista de (source, target, weight)
        """
        if not edges:
            self.num_nodes = 0
            self.matrix = sp.csr_matrix((0, 0), dtype=np.float32)
            return
        
        # Extraer nodos únicos
        unique_nodes = set()
        for u, v, _ in edges:
            unique_nodes.add(u)
            unique_nodes.add(v)
        
        # Crear mapeos bidireccionales
        sorted_nodes = sorted(unique_nodes)
        self.num_nodes = len(sorted_nodes)
        
        for idx, node_id in enumerate(sorted_nodes):
            self.node_to_idx[node_id] = idx
            self.idx_to_node[idx] = node_id
        
        # Construir listas para formato COO (Coordinate)
        row, col, data = [], [], []
        
        for u, v, weight in edges:
            i = self.node_to_idx[u]
            j = self.node_to_idx[v]
            
            # Grafo no dirigido: añadir ambas direcciones
            row.extend([i, j])
            col.extend([j, i])
            data.extend([weight, weight])
        
        # Crear matriz sparse en formato CSR
        self.matrix = sp.csr_matrix(
            (data, (row, col)),
            shape=(self.num_nodes, self.num_nodes),
            dtype=np.float32
        )
        
        # Eliminar duplicados sumando (por si acaso)
        self.matrix.sum_duplicates()
    
    def get_matrix(self) -> sp.csr_matrix:
        """Devuelve la matriz CSR."""
        return self.matrix
    
    def get_node_count(self) -> int:
        """Número de nodos en la red."""
        return self.num_nodes
    
    def get_edge_count(self) -> int:
        """Número de aristas (contando cada arista una vez)."""
        return self.matrix.nnz // 2  # Dividir por 2 porque es simétrica
    
    def map_ids_to_indices(self, node_ids: List[int]) -> np.ndarray:
        """Convierte IDs de nodos a índices de matriz."""
        return np.array([self.node_to_idx[nid] for nid in node_ids if nid in self.node_to_idx])
    
    def map_indices_to_ids(self, indices: np.ndarray) -> List[int]:
        """Convierte índices de matriz a IDs de nodos."""
        return [self.idx_to_node[int(idx)] for idx in indices]
    
    def get_memory_usage(self) -> int:
        """Retorna uso de memoria en bytes."""
        if self.matrix is None:
            return 0
        
        return (
            self.matrix.data.nbytes +
            self.matrix.indices.nbytes +
            self.matrix.indptr.nbytes
        )
    
    def __repr__(self) -> str:
        return (
            f"SparseContactNetwork(nodes={self.num_nodes}, "
            f"edges={self.get_edge_count()}, "
            f"memory={self.get_memory_usage() / 1024:.1f}KB)"
        )
