"""Simulador principal de grafos - genera redes diarias de contacto."""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import PATHS, SIM_CONFIG, VIZ_CONFIG
from src.data.loader import DataLoader
from src.data.processor import DataProcessor
from src.core.graph import ContactGraphBuilder, GraphAnalyzer
from src.visualization.visualizers import VisualizationFacade
from src.analysis import DailyGraphAnalysisCoordinator
from src.utils.helpers import DirectoryManager


class GraphSimulatorApp:
    """Aplicación principal para generación de grafos (Patrón Fachada)."""
    
    def __init__(self):
        self.paths = PATHS
        self.sim_config = SIM_CONFIG
        self.viz_config = VIZ_CONFIG
        
        self.loader = DataLoader(
            self.paths.estudiantes,
            self.paths.clases,
            self.paths.asistencias
        )
        self.processor = DataProcessor()
        self.graph_builder = ContactGraphBuilder()
        self.graph_analyzer = GraphAnalyzer()
        self.visualizer = VisualizationFacade(self.viz_config)
        
        self.mst_coordinator = DailyGraphAnalysisCoordinator(weight_mode='inverse')
    
    def run(self):
        """Ejecuta la simulación."""
        DirectoryManager.clean_and_create(self.paths.OUTPUT_DIR)
        
        estudiantes, clases, asistencias = self.loader.load_all()
        df_unificado = self.processor.create_unified_dataframe(
            estudiantes, clases, asistencias
        )
        
        print(f"\n{'Día':<12} {'Nodos':>6} {'Aristas':>8} {'Densidad':>10} {'MST Edges':>10}")
        print("=" * 60)
        
        output_dir = self.paths.grafos_diarios
        
        for dia_nombre in self.sim_config.dias_semana:
            df_dia = self.processor.filter_by_day(df_unificado, dia_nombre)
            
            if len(df_dia) == 0:
                continue
            
            G_dia = self.graph_builder.build_daily_graph(df_dia)
            stats = self.graph_analyzer.get_statistics(G_dia)
            
            mst_results = self.mst_coordinator.run_all_analyses(G_dia)
            mst_graph = mst_results['mst']['mst']
            
            print(f"{dia_nombre:<12} {stats['nodos']:>6} {stats['aristas']:>8} "
                  f"{stats['densidad']:>10.4f} {mst_graph.number_of_edges():>10}")
            
            self.visualizer.visualize_daily_graph(G_dia, dia_nombre, output_dir)
            self.visualizer.visualize_weighted_graph(G_dia, dia_nombre, output_dir)
            
            self.visualizer.visualize_mst(mst_graph, dia_nombre, output_dir)
        
        print("=" * 60)
        print(f"Resultados: {output_dir}")
        print(f"  - Grafos completos: *_pesos.png")
        print(f"  - MST: *_mst.png\n")


def main():
    """Punto de entrada."""
    app = GraphSimulatorApp()
    app.run()


if __name__ == '__main__':
    main()
