"""Analizador de centralidad para identificar nodos clave."""
import networkx as nx
from typing import Dict, Any
from .base import GraphAnalyzer


class CentralityAnalyzer(GraphAnalyzer):
    """Analiza métricas de centralidad para identificar propagadores clave."""
    
    def analyze(self, graph: nx.DiGraph, **kwargs) -> Dict[str, Any]:
        """Analiza métricas de centralidad."""
        if graph.number_of_edges() == 0:
            return {'top_spreaders': [], 'max_spread': 0}
        
        out_degrees = dict(graph.out_degree())
        top_spreaders = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {'top_spreaders': top_spreaders, 'max_spread': top_spreaders[0][1] if top_spreaders else 0}
    
    def get_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae métricas esenciales para backend/API."""
        return {
            'max_spread': results['max_spread'],
            'top_5_spreaders': [
                {'node_id': node_id, 'contagios': count}
                for node_id, count in results['top_spreaders'][:5]
            ]
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Imprime resultados del análisis de centralidad."""
        print(f"\n{'='*60}")
        print("TOP 10 SUPER-PROPAGADORES")
        print(f"{'='*60}")
        
        for i, (pid, count) in enumerate(results['top_spreaders'], 1):
            if count > 0:
                print(f"{i:2d}. ID {pid}: {count} contagios directos")
