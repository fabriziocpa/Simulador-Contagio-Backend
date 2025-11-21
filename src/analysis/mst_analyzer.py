"""Analizador de Minimum Spanning Tree (MST) para grafos de contacto."""
import networkx as nx
from typing import Dict, Any, List, Tuple
from .base import GraphAnalyzer


class MSTAnalyzer(GraphAnalyzer):
    """Analiza MST para extraer estructura esencial de conexiones minimizando peso total."""
    
    def __init__(self, weight_mode: str = 'inverse'):
        """Inicializa con modo de transformación de pesos: 'inverse', 'negative' o 'original'."""
        self.weight_mode = weight_mode
    
    def analyze(self, graph: nx.Graph, **kwargs) -> Dict[str, Any]:
        """Construye y analiza el MST del grafo."""
        if graph.number_of_nodes() == 0:
            return {'mst': nx.Graph(), 'num_componentes': 0, 'total_weight': 0.0,
                    'avg_weight': 0.0, 'critical_edges': [], 'reduction_ratio': 0.0}
        
        G_weighted = self._prepare_graph(graph)
        
        # Construir MST usando Kruskal
        if nx.is_connected(G_weighted):
            mst = nx.minimum_spanning_tree(G_weighted, weight='mst_weight', algorithm='kruskal')
            num_componentes = 1
        else:
            mst = nx.Graph()
            components = list(nx.connected_components(G_weighted))
            num_componentes = len(components)
            
            for component in components:
                subgraph = G_weighted.subgraph(component)
                if subgraph.number_of_nodes() > 1:
                    sub_mst = nx.minimum_spanning_tree(subgraph, weight='mst_weight', algorithm='kruskal')
                    mst.add_edges_from(sub_mst.edges(data=True))
                else:
                    mst.add_node(list(component)[0])
        
        # Restaurar pesos originales
        for u, v in mst.edges():
            mst[u][v]['peso'] = graph[u][v]['peso']
            if 'mst_weight' in mst[u][v]:
                del mst[u][v]['mst_weight']
        
        return {
            'mst': mst,
            'num_componentes': num_componentes,
            'total_weight': self._calculate_total_weight(mst),
            'avg_weight': self._calculate_avg_weight(mst),
            'critical_edges': self._find_critical_edges(mst),
            'reduction_ratio': self._calculate_reduction_ratio(graph, mst)
        }
    
    def get_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae métricas esenciales para backend/API."""
        mst = results['mst']
        
        return {
            'nodes': mst.number_of_nodes(),
            'edges': mst.number_of_edges(),
            'componentes': results['num_componentes'],
            'total_weight': round(results['total_weight'], 4),
            'avg_weight': round(results['avg_weight'], 4),
            'reduction_ratio': round(results['reduction_ratio'], 4),
            'critical_edges_count': len(results['critical_edges']),
            'top_critical_edges': [
                {'source': u, 'target': v, 'weight': round(w, 4)}
                for u, v, w in results['critical_edges'][:5]
            ]
        }
    
    def _prepare_graph(self, graph: nx.Graph) -> nx.Graph:
        """Prepara el grafo transformando los pesos según el modo."""
        G_prepared = graph.copy()
        
        for u, v, data in G_prepared.edges(data=True):
            peso_original = data.get('peso', 1.0)
            
            if self.weight_mode == 'inverse':
                data['mst_weight'] = 1.0 / (peso_original + 1e-10)
            elif self.weight_mode == 'negative':
                data['mst_weight'] = -peso_original
            else:
                data['mst_weight'] = peso_original
        
        return G_prepared
    
    def _calculate_total_weight(self, mst: nx.Graph) -> float:
        """Calcula peso total del MST."""
        if mst.number_of_edges() == 0:
            return 0.0
        return sum(data.get('peso', 0.0) for _, _, data in mst.edges(data=True))
    
    def _calculate_avg_weight(self, mst: nx.Graph) -> float:
        """Calcula peso promedio de aristas en MST."""
        if mst.number_of_edges() == 0:
            return 0.0
        return self._calculate_total_weight(mst) / mst.number_of_edges()
    
    def _find_critical_edges(self, mst: nx.Graph) -> List[Tuple[int, int, float]]:
        """Encuentra aristas críticas (todas en MST) ordenadas por peso descendente."""
        critical = [(u, v, data.get('peso', 0.0)) for u, v, data in mst.edges(data=True)]
        return sorted(critical, key=lambda x: x[2], reverse=True)
    
    def _calculate_reduction_ratio(self, original: nx.Graph, mst: nx.Graph) -> float:
        """Calcula ratio de reducción de aristas: 1 - (edges_mst / edges_original)."""
        if original.number_of_edges() == 0:
            return 0.0
        return 1.0 - (mst.number_of_edges() / original.number_of_edges())
    
    def print_results(self, results: Dict[str, Any]):
        """Imprime resultados del análisis MST."""
        mst = results['mst']
        
        print(f"\n{'='*60}")
        print("ANÁLISIS DE MINIMUM SPANNING TREE (MST)")
        print(f"{'='*60}")
        print(f"Modo de pesos: {self.weight_mode}")
        print(f"Nodos: {mst.number_of_nodes()}")
        print(f"Aristas: {mst.number_of_edges()}")
        print(f"Componentes: {results['num_componentes']}")
        print(f"Peso total: {results['total_weight']:.4f}")
        print(f"Peso promedio: {results['avg_weight']:.4f}")
        print(f"Ratio de reducción: {results['reduction_ratio']:.2%}")
        
        if results['critical_edges']:
            print(f"\nTop 5 Aristas Críticas:")
            for i, (u, v, w) in enumerate(results['critical_edges'][:5], 1):
                print(f"  {i}. {u} ↔ {v}: {w:.4f}")


class MSTComparator:
    """Compara grafo original vs MST."""
    
    @staticmethod
    def compare(original: nx.Graph, mst: nx.Graph) -> Dict[str, Any]:
        """Compara métricas entre grafo original y MST."""
        return {
            'original': {
                'nodes': original.number_of_nodes(),
                'edges': original.number_of_edges(),
                'density': nx.density(original) if original.number_of_nodes() > 0 else 0
            },
            'mst': {
                'nodes': mst.number_of_nodes(),
                'edges': mst.number_of_edges(),
                'density': nx.density(mst) if mst.number_of_nodes() > 0 else 0
            },
            'reduction': {
                'edges_removed': original.number_of_edges() - mst.number_of_edges(),
                'edge_reduction_pct': (1 - mst.number_of_edges() / original.number_of_edges() 
                                      if original.number_of_edges() > 0 else 0) * 100,
                'density_reduction_pct': (1 - (nx.density(mst) / nx.density(original))
                                         if nx.density(original) > 0 else 0) * 100
            }
        }
    
    @staticmethod
    def print_comparison(comparison: Dict[str, Any]):
        """Imprime comparación."""
        print(f"\n{'='*60}")
        print("COMPARACIÓN: GRAFO ORIGINAL vs MST")
        print(f"{'='*60}")
        
        orig = comparison['original']
        mst = comparison['mst']
        red = comparison['reduction']
        
        print(f"\nGrafo Original:")
        print(f"  Nodos: {orig['nodes']}")
        print(f"  Aristas: {orig['edges']}")
        print(f"  Densidad: {orig['density']:.6f}")
        
        print(f"\nMST:")
        print(f"  Nodos: {mst['nodes']}")
        print(f"  Aristas: {mst['edges']}")
        print(f"  Densidad: {mst['density']:.6f}")
        
        print(f"\nReducción:")
        print(f"  Aristas removidas: {red['edges_removed']}")
        print(f"  Reducción de aristas: {red['edge_reduction_pct']:.2f}%")
        print(f"  Reducción de densidad: {red['density_reduction_pct']:.2f}%")
