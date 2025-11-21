"""Módulo de carga y validación de datos con principios SOLID."""
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict
from abc import ABC, abstractmethod


class DataValidator(ABC):
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


class EstudiantesValidator(DataValidator):
     
    REQUIRED_COLS = ['id_estudiante', 'carrera', 'anio_ingreso'] # Columnas obligatorias
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = set(self.REQUIRED_COLS) - set(df.columns)
        if missing:
            raise ValueError(f"Columnas faltantes en estudiantes: {missing}")
        
        if df['id_estudiante'].duplicated().any():
            raise ValueError("IDs de estudiantes duplicados encontrados")
        
        return df


class ClasesValidator(DataValidator):

    REQUIRED_COLS = ['id_clase', 'nombre_clase', 'salon', 'dia_semana', #Columnas obligatorias
                     'horario_inicio', 'horario_fin', 'max_estudiantes'] 
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = set(self.REQUIRED_COLS) - set(df.columns)
        if missing:
            raise ValueError(f"Columnas faltantes en clases: {missing}")
        return df


class AsistenciasValidator(DataValidator):
  
    REQUIRED_COLS = ['id_estudiante', 'id_clase', 'pos_x', 'pos_y'] # Columnas obligatorias
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = set(self.REQUIRED_COLS) - set(df.columns)
        if missing:
            raise ValueError(f"Columnas faltantes en asistencias: {missing}")
        
        if df[['pos_x', 'pos_y']].isnull().any().any():
            raise ValueError("Posiciones de asientos incompletas")
        
        return df


class DataLoader:

    def __init__(self, 
                 estudiantes_path: Path,
                 clases_path: Path,
                 asistencias_path: Path,
                 validators: Dict[str, DataValidator] = None):
        self.estudiantes_path = estudiantes_path
        self.clases_path = clases_path
        self.asistencias_path = asistencias_path
        
        # Validadores por defecto si no se proporcionan
        self.validators = validators or {
            'estudiantes': EstudiantesValidator(),
            'clases': ClasesValidator(),
            'asistencias': AsistenciasValidator()
        }
    
    def load_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        estudiantes = self._load_and_validate(
            self.estudiantes_path, 
            self.validators['estudiantes']
        )
        clases = self._load_and_validate(
            self.clases_path,
            self.validators['clases']
        )
        asistencias = self._load_and_validate(
            self.asistencias_path,
            self.validators['asistencias']
        )
        
        return estudiantes, clases, asistencias
    
    def _load_and_validate(self, path: Path, validator: DataValidator) -> pd.DataFrame:
        try:
            df = pd.read_csv(path)
            return validator.validate(df)
        except FileNotFoundError:
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        except Exception as e:
            raise ValueError(f"Error cargando {path}: {str(e)}")
