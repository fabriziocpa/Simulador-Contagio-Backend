"""
Módulo de análisis de grafos - Arquitectura modular siguiendo SOLID.

Exporta:
- Analyzers especializados (WCC, MST, Centrality)
- Coordinadores (AnalysisCoordinator, DailyGraphAnalysisCoordinator)
- Funciones helper
"""

# Analyzers base
from .base import GraphAnalyzer

# Analyzers especializados
from .wcc_analyzer import WCCAnalyzer
from .mst_analyzer import MSTAnalyzer, MSTComparator
from .centrality_analyzer import CentralityAnalyzer

# Coordinadores
from .analyzers import (
    AnalysisCoordinator,
    DailyGraphAnalysisCoordinator,
    create_infected_subgraph
)

__all__ = [
    # Base
    'GraphAnalyzer',
    
    # Analyzers especializados
    'WCCAnalyzer',
    'MSTAnalyzer',
    'MSTComparator',
    'CentralityAnalyzer',
    
    # Coordinadores
    'AnalysisCoordinator',
    'DailyGraphAnalysisCoordinator',
    
    # Helpers
    'create_infected_subgraph'
]

