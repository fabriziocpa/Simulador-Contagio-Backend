"""Analizador de Componentes Conexas Débilmente (WCC)."""
import networkx as nx
import pandas as pd
from typing import Dict, Any
from .base import GraphAnalyzer


class WCCAnalyzer(GraphAnalyzer):
    """Analiza componentes conexas débiles para identificar clusters de infectados."""
    
    def analyze(self, graph: nx.DiGraph, estudiantes: pd.DataFrame = None) -> Dict[str, Any]:
        """Analiza WCC en árbol de transmisión."""
        if graph.number_of_nodes() == 0:
            return {'num_componentes': 0, 'tamanos': [], 'componente_gigante': 0, 'componentes': []}
        
        # Convertir a no dirigido para WCC
        G_undirected = graph.to_undirected()
        componentes = list(nx.connected_components(G_undirected))
        
        results = {
            'num_componentes': len(componentes),
            'tamanos': sorted([len(c) for c in componentes], reverse=True),
            'componente_gigante': len(max(componentes, key=len)) if componentes else 0,
            'componentes': sorted(componentes, key=len, reverse=True)  # All components
        }
        
        if estudiantes is not None:
            results['analisis_componentes'] = [
                self._analyze_component(comp, estudiantes, graph)
                for comp in results['componentes']
            ]
        
        return results
    
    def get_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae métricas esenciales para backend/API."""
        metrics = {
            'num_componentes': results['num_componentes'],
            'componente_gigante_size': results['componente_gigante'],
            'top_3_sizes': results['tamanos'][:3],
            'fragmentacion_index': self._calculate_fragmentation(results)
        }
        
        if 'analisis_componentes' in results and results['analisis_componentes']:
            top_spreaders = []
            for comp in results['analisis_componentes'][:3]:
                if comp['super_spreaders']:
                    top_spreaders.extend(comp['super_spreaders'][:2])
            metrics['super_spreaders'] = top_spreaders[:5]
        
        return metrics
    
    def _calculate_fragmentation(self, results: Dict[str, Any]) -> float:
        """Calcula índice de fragmentación (1 = muy fragmentado, 0 = conectado)."""
        if results['num_componentes'] == 0:
            return 0.0
        
        total_nodos = sum(results['tamanos'])
        if total_nodos == 0:
            return 0.0
            
        return 1.0 - (results['componente_gigante'] / total_nodos)
    
    def _analyze_component(self, 
                          nodos: set, 
                          estudiantes: pd.DataFrame,
                          graph: nx.DiGraph) -> Dict:
        """Analiza un componente individual."""
        df_comp = estudiantes[estudiantes['id_estudiante'].isin(nodos)]
        
        # Obtener distribuciones
        carreras = df_comp['carrera'].value_counts().head(3).to_dict()
        anios = df_comp['anio_ingreso'].value_counts().head(3).to_dict()
        
        # Encontrar super-propagadores
        subgrafo = graph.subgraph(nodos)
        out_degrees = dict(subgrafo.out_degree())
        super_spreaders = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'tamano': len(nodos),
            'carreras': carreras,
            'anios': anios,
            'miembros': [str(nid) for nid in nodos],  # NEW: All member IDs as strings
            'super_spreaders': [
                {
                    'id': pid,
                    'contagios': count,
                    'carrera': estudiantes[estudiantes['id_estudiante'] == pid]['carrera'].iloc[0]
                    if len(estudiantes[estudiantes['id_estudiante'] == pid]) > 0 else 'N/A'
                }
                for pid, count in super_spreaders if count > 0
            ]
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Imprime resultados del análisis WCC."""
        print(f"\n{'='*60}")
        print("ANÁLISIS DE COMPONENTES CONEXAS (WCC)")
        print(f"{'='*60}")
        print(f"Número de componentes: {results['num_componentes']}")
        print(f"Tamaño componente gigante: {results['componente_gigante']}")
        print(f"Distribución de tamaños: {results['tamanos'][:10]}")
        print(f"Índice de fragmentación: {self.get_metrics(results)['fragmentacion_index']:.3f}")
        
        if 'analisis_componentes' in results:
            for i, comp_analysis in enumerate(results['analisis_componentes'], 1):
                print(f"\nComponente {i} ({comp_analysis['tamano']} estudiantes):")
                print(f"  Carreras: {comp_analysis['carreras']}")
                print(f"  Años: {comp_analysis['anios']}")
                
                if comp_analysis['super_spreaders']:
                    print(f"  Super-propagadores:")
                    for sp in comp_analysis['super_spreaders']:
                        print(f"    {sp['id']}: {sp['contagios']} contagios ({sp['carrera']})")
