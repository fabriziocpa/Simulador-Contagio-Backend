"""Módulo de procesamiento y transformación de datos."""
import pandas as pd
from typing import Dict, Tuple
from ..core.config import GRID_CONFIG


class DataProcessor:
    """Procesa y unifica datos de múltiples fuentes (SRP - Responsabilidad Única)."""
    
    DIA_MAP = {
        'Lunes': 1, 'Martes': 2, 'Miércoles': 3, 
        'Jueves': 4, 'Viernes': 5, 'Sábado': 6
    }
    
    def __init__(self, grid_config=GRID_CONFIG):
        self.grid_config = grid_config
    
    def create_unified_dataframe(self, 
                                estudiantes: pd.DataFrame,
                                clases: pd.DataFrame,
                                asistencias: pd.DataFrame) -> pd.DataFrame:

        # Unir datos
        df = asistencias.merge(clases, on='id_clase', how='left')
        
        # Agregar campos calculados
        df['dia_orden'] = df['dia_semana'].map(self.DIA_MAP)
        df['duracion_horas'] = df.apply(
            lambda r: self._calcular_duracion(r['horario_inicio'], r['horario_fin']), 
            axis=1
        )
        
        # Agregar dimensiones de cuadrícula
        grids = df['max_estudiantes'].apply(self.grid_config.get_grid)
        df['filas_asientos'] = grids.apply(lambda x: x[0])
        df['columnas_asientos'] = grids.apply(lambda x: x[1])
        
        # Renombrar columnas para consistencia
        df = df.rename(columns={
            'id_estudiante': 'persona_id',
            'pos_x': 'fila_asiento',
            'pos_y': 'columna_asiento',
            'id_clase': 'seccion_id',
            'nombre_clase': 'curso',
            'salon': 'aula'
        })
        
        return df
    
    @staticmethod
    def _calcular_duracion(inicio: str, fin: str) -> float:

        try:
            h1, m1 = map(int, inicio.split(':'))
            h2, m2 = map(int, fin.split(':'))
            return (h2 * 60 + m2 - h1 * 60 - m1) / 60.0
        except (ValueError, AttributeError):
            return 2.0  # Por defecto 2 horas
    
    @staticmethod
    def filter_by_day(df: pd.DataFrame, dia_nombre: str) -> pd.DataFrame:
        return df[df['dia_semana'] == dia_nombre].copy()
