"""Inmutabilidad y seguridad de tipos."""
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

@dataclass(frozen=True)
class Paths:

    DATA_DIR: Path = Path('data')
    OUTPUT_DIR: Path = Path('output')
    
    @property
    def estudiantes(self) -> Path:
        return self.DATA_DIR / 'estudiantes.csv'
    
    @property
    def clases(self) -> Path:
        return self.DATA_DIR / 'clases.csv'
    
    @property
    def asistencias(self) -> Path:
        return self.DATA_DIR / 'asistencias.csv'
    
    @property
    def grafos_diarios(self) -> Path:
        return self.OUTPUT_DIR / 'grafos_diarios'
    
    @property
    def epidemia(self) -> Path:
        return self.OUTPUT_DIR / 'epidemia'


@dataclass(frozen=True)
class GridConfig:

    SMALL: Tuple[int, int] = (5, 6)  # 30 estudiantes máximo
    LARGE: Tuple[int, int] = (5, 8)  # 40 estudiantes máximo
    
    def get_grid(self, max_estudiantes: int) -> Tuple[int, int]:
        return self.SMALL if max_estudiantes <= 30 else self.LARGE

@dataclass(frozen=True)
class SimulationConfig:
    
    beta: float = 0.5  # Tasa de transmisión
    num_pacientes_cero: int = 5
    seed: int = 42
    dias_semana: Tuple[str, ...] = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes')


@dataclass(frozen=True)
class VisualizationConfig:
    dpi: int = 300
    node_size: int = 50
    figsize: Tuple[int, int] = (16, 12)
    color_student: str = '#00BFFF'
    color_infected: str = '#FF4444'
    color_new_infected: str = '#FF0000'
    color_edge: str = '#CCCCCC'
    edge_alpha: float = 0.3
    edge_width: float = 0.5


# Singleton instances
PATHS = Paths()
GRID_CONFIG = GridConfig()
SIM_CONFIG = SimulationConfig()
VIZ_CONFIG = VisualizationConfig()
