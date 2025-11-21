"""Módulo de visualización usando patrones Template Method y Strategy."""
import matplotlib.pyplot as plt
import networkx as nx
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Set
from ..core.config import VIZ_CONFIG


class GraphVisualizer(ABC):
    """Clase base para visualización de grafos (Patrón Template Method)."""
    
    def __init__(self, config=VIZ_CONFIG):
        self.config = config
    
    def visualize(self, G: nx.Graph, output_path: Path, title: str):
        """Método plantilla para pipeline de visualización."""
        if G.number_of_nodes() == 0:
            return
        
        pos = self._calculate_layout(G)
        fig = plt.figure(figsize=self.config.figsize)
        
        self._draw_edges(G, pos)
        self._draw_nodes(G, pos)
        self._add_decorations(title)
        
        self._save_figure(output_path)
    
    def _calculate_layout(self, G: nx.Graph) -> Dict:
        """Calcula posiciones de nodos (puede ser sobrescrito)."""
        # Usa layout aleatorio en lugar de spring para evitar dependencia scipy
        return nx.random_layout(G, seed=42)
    
    @abstractmethod
    def _draw_edges(self, G: nx.Graph, pos: Dict):
        """Dibuja aristas (debe ser implementado por subclases)."""
        pass
    
    @abstractmethod
    def _draw_nodes(self, G: nx.Graph, pos: Dict):
        """Dibuja nodos (debe ser implementado por subclases)."""
        pass
    
    def _add_decorations(self, title: str):
        """Agrega título y formato."""
        plt.title(title, fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
    
    def _save_figure(self, output_path: Path):
        """Guarda figura en archivo."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=self.config.dpi, bbox_inches='tight')
        plt.close()


class BasicGraphVisualizer(GraphVisualizer):
    """Visualiza grafo básico de contacto."""
    
    def _draw_edges(self, G: nx.Graph, pos: Dict):
        nx.draw_networkx_edges(
            G, pos, 
            alpha=self.config.edge_alpha,
            width=self.config.edge_width,
            edge_color=self.config.color_edge
        )
    
    def _draw_nodes(self, G: nx.Graph, pos: Dict):
        nx.draw_networkx_nodes(
            G, pos,
            node_size=self.config.node_size,
            node_color=self.config.color_student,
            alpha=0.7
        )


class WeightedGraphVisualizer(GraphVisualizer):
    """Visualiza grafo con aristas ponderadas."""
    
    def _draw_edges(self, G: nx.Graph, pos: Dict):
        weights = [G[u][v]['peso'] for u, v in G.edges()]
        max_w = max(weights) if weights else 1
        widths = [3 * (w / max_w) for w in weights]
        
        nx.draw_networkx_edges(
            G, pos,
            width=widths,
            alpha=0.4,
            edge_color='#888888'
        )
    
    def _draw_nodes(self, G: nx.Graph, pos: Dict):
        nx.draw_networkx_nodes(
            G, pos,
            node_size=self.config.node_size,
            node_color=self.config.color_student,
            alpha=0.7
        )


class EpidemicGraphVisualizer(GraphVisualizer):
    """Visualiza grafo con estados epidémicos."""
    
    def __init__(self, estados: Dict[int, int], nuevos: Set[int], config=VIZ_CONFIG):
        super().__init__(config)
        self.estados = estados
        self.nuevos = nuevos
    
    def _draw_edges(self, G: nx.Graph, pos: Dict):
        nx.draw_networkx_edges(
            G, pos,
            alpha=0.2,
            width=0.5,
            edge_color=self.config.color_edge
        )
    
    def _draw_nodes(self, G: nx.Graph, pos: Dict):
        # Clasificar nodos
        susceptibles = [n for n in G.nodes() if self.estados.get(n, 0) == 0]
        infectados_previos = [
            n for n in G.nodes() 
            if self.estados.get(n, 0) == 1 and n not in self.nuevos
        ]
        nuevos_list = [n for n in G.nodes() if n in self.nuevos]
        
        # Dibujar susceptibles
        if susceptibles:
            nx.draw_networkx_nodes(
                G, pos, nodelist=susceptibles,
                node_size=self.config.node_size,
                node_color=self.config.color_student,
                alpha=0.6, label='Susceptibles'
            )
        
        # Dibujar infectados previos
        if infectados_previos:
            nx.draw_networkx_nodes(
                G, pos, nodelist=infectados_previos,
                node_size=self.config.node_size * 1.5,
                node_color=self.config.color_infected,
                alpha=0.8, label='Infectados previos'
            )
        
        # Dibujar nuevos infectados
        if nuevos_list:
            nx.draw_networkx_nodes(
                G, pos, nodelist=nuevos_list,
                node_size=self.config.node_size * 2,
                node_color=self.config.color_new_infected,
                edgecolors='#000000', linewidths=2,
                alpha=1.0, label='Nuevos infectados'
            )
        
        plt.legend(loc='upper right', fontsize=10)


class PropagationTreeVisualizer(GraphVisualizer):
    """Visualiza árbol de propagación."""
    
    def _draw_edges(self, G: nx.DiGraph, pos: Dict):
        nx.draw_networkx_edges(
            G, pos,
            alpha=0.3, width=0.8,
            edge_color='#888888',
            arrows=True,
            arrowsize=10,
            arrowstyle='->'
        )
    
    def _draw_nodes(self, G: nx.DiGraph, pos: Dict):
        # Colorear por grado saliente (super-propagadores)
        out_degrees = dict(G.out_degree())
        max_degree = max(out_degrees.values()) if out_degrees else 1
        node_colors = [out_degrees.get(n, 0) for n in G.nodes()]
        
        nx.draw_networkx_nodes(
            G, pos,
            node_size=100,
            node_color=node_colors,
            cmap=plt.cm.Reds,
            vmin=0, vmax=max_degree,
            alpha=0.9,
            edgecolors='#000000',
            linewidths=1
        )


class MSTGraphVisualizer(GraphVisualizer):
    """Visualiza Minimum Spanning Tree con aristas destacadas."""
    
    def _draw_edges(self, G: nx.Graph, pos: Dict):
        # Dibujar aristas del MST con grosor proporcional al peso
        if G.number_of_edges() == 0:
            return
        
        weights = [G[u][v].get('peso', 1.0) for u, v in G.edges()]
        max_w = max(weights) if weights else 1
        min_w = min(weights) if weights else 0
        
        # Normalizar anchos entre 1 y 4
        if max_w > min_w:
            widths = [1 + 3 * ((w - min_w) / (max_w - min_w)) for w in weights]
        else:
            widths = [2.5] * len(weights)
        
        # Colores según peso (verde = fuerte, amarillo = débil)
        edge_colors = []
        for w in weights:
            if max_w > min_w:
                intensity = (w - min_w) / (max_w - min_w)
            else:
                intensity = 0.5
            # Verde para contactos fuertes, amarillo para débiles
            color = plt.cm.YlGn(0.3 + 0.7 * intensity)
            edge_colors.append(color)
        
        nx.draw_networkx_edges(
            G, pos,
            width=widths,
            edge_color=edge_colors,
            alpha=0.7
        )
    
    def _draw_nodes(self, G: nx.Graph, pos: Dict):
        # Colorear nodos por grado (nodos hub)
        degrees = dict(G.degree())
        max_degree = max(degrees.values()) if degrees else 1
        node_colors = [degrees.get(n, 0) for n in G.nodes()]
        
        nx.draw_networkx_nodes(
            G, pos,
            node_size=self.config.node_size * 1.5,
            node_color=node_colors,
            cmap=plt.cm.Blues,
            vmin=0,
            vmax=max_degree,
            alpha=0.8,
            edgecolors='#000000',
            linewidths=1.5
        )


class VisualizationFacade:
    """Fachada para todas las operaciones de visualización (Patrón Fachada)."""
    
    def __init__(self, config=VIZ_CONFIG):
        self.config = config
    
    def visualize_daily_graph(self, G: nx.Graph, dia: str, output_dir: Path):
        """Visualiza grafo básico diario de contacto."""
        visualizer = BasicGraphVisualizer(self.config)
        stats = f"{G.number_of_nodes()} estudiantes, {G.number_of_edges()} contactos"
        title = f"{dia}\n{stats}"
        output_path = output_dir / f"{dia.lower()}.png"
        visualizer.visualize(G, output_path, title)
    
    def visualize_weighted_graph(self, G: nx.Graph, dia: str, output_dir: Path):
        """Visualiza grafo con pesos."""
        visualizer = WeightedGraphVisualizer(self.config)
        title = f"{dia} - Pesos"
        output_path = output_dir / f"{dia.lower()}_pesos.png"
        visualizer.visualize(G, output_path, title)
    
    def visualize_epidemic_state(self, 
                                 G: nx.Graph,
                                 estados: Dict[int, int],
                                 nuevos: Set[int],
                                 dia: str,
                                 output_dir: Path):
        """Visualiza estado epidémico."""
        visualizer = EpidemicGraphVisualizer(estados, nuevos, self.config)
        total_inf = sum(1 for s in estados.values() if s == 1)
        stats = f"{total_inf} infectados ({len(nuevos)} nuevos)"
        title = f"{dia}\n{stats}"
        output_path = output_dir / f"{dia.lower()}_epidemia.png"
        visualizer.visualize(G, output_path, title)
    
    def visualize_infected_subgraph(self,
                                   G_infectados: nx.Graph,
                                   dia: str,
                                   output_dir: Path):
        """Visualiza subgrafo de estudiantes infectados."""
        visualizer = BasicGraphVisualizer(self.config)
        stats = f"{G_infectados.number_of_nodes()} infectados, {G_infectados.number_of_edges()} conexiones"
        title = f"{dia} - Subgrafo de Infectados\n{stats}"
        output_path = output_dir / f"{dia.lower()}_infectados.png"
        visualizer.visualize(G_infectados, output_path, title)
    
    def visualize_propagation_tree(self, tree: nx.DiGraph, output_path: Path):
        """Visualiza árbol de propagación."""
        visualizer = PropagationTreeVisualizer(self.config)
        title = f"Árbol de Propagación\n{tree.number_of_nodes()} infectados, {tree.number_of_edges()} transmisiones"
        visualizer.visualize(tree, output_path, title)
    
    def visualize_mst(self, mst: nx.Graph, dia: str, output_dir: Path):
        """Visualiza Minimum Spanning Tree del grafo diario."""
        visualizer = MSTGraphVisualizer(self.config)
        stats = f"{mst.number_of_nodes()} nodos, {mst.number_of_edges()} aristas críticas"
        title = f"{dia} - MST\n{stats}"
        output_path = output_dir / f"{dia.lower()}_mst.png"
        visualizer.visualize(mst, output_path, title)

