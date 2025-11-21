"""Módulo de construcción de grafos con algoritmos optimizados."""
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from src.core.sparse_network import SparseContactNetwork


class ContactGraphBuilder:
    """Construye redes de contacto basadas en proximidad (SRP)."""
    
    MAX_PROXIMITY = 1  # Vecindad 3x3
    
    def build_class_graph(self, df_clase: pd.DataFrame) -> nx.Graph:

        G = nx.Graph()
        
        if len(df_clase) == 0:
            return G
        
        personas = df_clase[['persona_id', 'fila_asiento', 'columna_asiento']].values
        duracion = df_clase['duracion_horas'].iloc[0] if len(df_clase) > 0 else 2.0
        
        # Cálculo optimizado de aristas
        edges = self._calculate_edges_vectorized(personas, duracion)
        G.add_weighted_edges_from(edges, weight='peso')
        
        return G
    
    def _calculate_edges_vectorized(self, 
                                    personas: np.ndarray, 
                                    duracion: float) -> List[Tuple]:
        """Cálculo COMPLETAMENTE vectorizado sin loops Python."""
        n = len(personas)
        if n < 2:
            return []
        
        # Broadcasting: calcular TODAS las distancias de una vez [n, n, 2]
        coords = personas[:, 1:3].astype(float)  # [n, 2] (fila, columna)
        coord_diff = coords[:, None, :] - coords[None, :, :]  # Broadcasting
        
        # Distancia Chebyshev (vecindad 3x3): max(|Δfila|, |Δcol|)
        max_dist = np.max(np.abs(coord_diff), axis=2)  # [n, n]
        
        # Máscara: vecindad 3x3 Y triangular superior (evitar duplicados)
        mask = (max_dist <= self.MAX_PROXIMITY) & np.triu(np.ones((n, n), dtype=bool), k=1)
        
        # Extraer índices de aristas válidas
        i_indices, j_indices = np.where(mask)
        
        if len(i_indices) == 0:
            return []
        
        # Calcular pesos vectorizadamente
        dist_euclidean = np.sqrt(np.sum(coord_diff[i_indices, j_indices]**2, axis=1))
        pesos = (1.0 / (1.0 + dist_euclidean)) * min(duracion, 1.5)
        
        # Construir lista de aristas (IDs pueden ser strings)
        edges = [(personas[i, 0], personas[j, 0], float(w)) 
                 for i, j, w in zip(i_indices, j_indices, pesos)]
        
        return edges
    
    def build_daily_graph(self, df_dia: pd.DataFrame) -> nx.Graph:
        """Construye grafo diario fusionando todas las sesiones de clase."""
        G_dia = nx.Graph()
        
        for seccion, df_clase in df_dia.groupby('seccion_id'):
            G_clase = self.build_class_graph(df_clase)
            
            # Fusionar grafos, manteniendo peso máximo
            for u, v, data in G_clase.edges(data=True):
                if G_dia.has_edge(u, v):
                    G_dia[u][v]['peso'] = max(G_dia[u][v]['peso'], data['peso'])
                else:
                    G_dia.add_edge(u, v, peso=data['peso'])
        
        return G_dia
    
    def build_sparse_daily_network(self, df_dia: pd.DataFrame) -> SparseContactNetwork:
        """Construye red sparse directamente desde datos (optimizado)."""
        all_edges = []
        
        # Recolectar aristas de todas las clases
        for seccion, df_clase in df_dia.groupby('seccion_id'):
            if len(df_clase) == 0:
                continue
            
            personas = df_clase[['persona_id', 'fila_asiento', 'columna_asiento']].values
            duracion = df_clase['duracion_horas'].iloc[0] if len(df_clase) > 0 else 2.0
            
            # Reutilizar cálculo vectorizado existente
            class_edges = self._calculate_edges_vectorized(personas, duracion)
            all_edges.extend(class_edges)
        
        # Fusionar aristas duplicadas (mantener peso máximo)
        edge_dict = {}
        for u, v, w in all_edges:
            # Normalizar orden para grafo no dirigido
            key = (min(u, v), max(u, v))
            edge_dict[key] = max(edge_dict.get(key, 0), w)
        
        # Convertir a lista de aristas únicas
        unique_edges = [(u, v, w) for (u, v), w in edge_dict.items()]
        
        # Construir red sparse
        network = SparseContactNetwork()
        network.build_from_edges(unique_edges)
        
        return network


class GraphAnalyzer:
    """Analiza estadísticas de grafos (SRP)."""
    
    @staticmethod
    def get_statistics(G: nx.Graph) -> Dict:
        """Calcula estadísticas comprehensivas del grafo."""
        if G.number_of_nodes() == 0:
            return {
                'nodos': 0,
                'aristas': 0,
                'densidad': 0,
                'componentes': 0,
                'componente_mayor': 0
            }
        
        componentes = list(nx.connected_components(G))
        
        return {
            'nodos': G.number_of_nodes(),
            'aristas': G.number_of_edges(),
            'densidad': nx.density(G),
            'componentes': len(componentes),
            'componente_mayor': len(max(componentes, key=len)) if componentes else 0
        }
