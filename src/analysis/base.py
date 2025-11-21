"""Módulo base para análisis de grafos - Principio de Segregación de Interfaces (ISP)."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import networkx as nx


class GraphAnalyzer(ABC):
    """Clase base abstracta para analizadores de grafos (SRP, OCP, ISP)."""
    
    @abstractmethod
    def analyze(self, graph: nx.Graph, **kwargs) -> Dict[str, Any]:
        """Realiza análisis y devuelve resultados en formato serializable."""
        pass
    
    @abstractmethod
    def get_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae métricas esenciales para APIs/backend."""
        pass
    
    def print_results(self, results: Dict[str, Any]):
        """Imprime resultados del análisis (opcional - para CLI)."""
        pass
