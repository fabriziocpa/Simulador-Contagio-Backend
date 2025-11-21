"""Módulo coordinador de análisis - Patrón Fachada."""
import networkx as nx
import pandas as pd
from typing import Dict, Any

from .wcc_analyzer import WCCAnalyzer
from .mst_analyzer import MSTAnalyzer, MSTComparator
from .centrality_analyzer import CentralityAnalyzer


class AnalysisCoordinator:
    """Coordina múltiples análisis de propagación (SRP, DIP)."""
    
    def __init__(self):
        self.analyzers = {'wcc': WCCAnalyzer(), 'centrality': CentralityAnalyzer()}
    
    def run_all_analyses(self, propagation_tree: nx.DiGraph,
                        estudiantes: pd.DataFrame = None) -> Dict[str, Dict]:
        """Ejecuta todos los análisis de propagación y devuelve resultados."""
        results = {}
        
        for name, analyzer in self.analyzers.items():
            results[name] = analyzer.analyze(propagation_tree, estudiantes=estudiantes)
            analyzer.print_results(results[name])
        
        return results
    
    def get_all_metrics(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Extrae métricas esenciales de todos los análisis (para backend).
        
        Args:
            results: Resultados de run_all_analyses()
            
        Returns:
            Diccionario con métricas esenciales de todos los analyzers
        """
        metrics = {}
        
        for name, analyzer in self.analyzers.items():
            if name in results:
                metrics[name] = analyzer.get_metrics(results[name])
        
        return metrics


class DailyGraphAnalysisCoordinator:
    """Coordinador de análisis MST para grafos diarios."""
    
    def __init__(self, weight_mode: str = 'inverse'):
        self.analyzers = {'mst': MSTAnalyzer(weight_mode=weight_mode)}
    
    def run_all_analyses(self, daily_graph: nx.Graph) -> Dict[str, Dict]:
        """Ejecuta análisis MST y devuelve resultados."""
        results = {}
        
        for name, analyzer in self.analyzers.items():
            results[name] = analyzer.analyze(daily_graph)
            analyzer.print_results(results[name])
        
        return results
    
    def get_all_metrics(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Extrae métricas esenciales del análisis MST (para backend)."""
        metrics = {}
        
        for name, analyzer in self.analyzers.items():
            if name in results:
                metrics[name] = analyzer.get_metrics(results[name])
        
        return metrics


# Funciones helper (mantener retrocompatibilidad)

def create_infected_subgraph(G: nx.Graph, estados: Dict[int, int]) -> nx.Graph:
    """Crea subgrafo con solo nodos infectados."""
    infectados = [n for n, s in estados.items() if s == 1 and n in G]
    return G.subgraph(infectados).copy()
