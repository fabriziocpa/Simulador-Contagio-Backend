"""
Router de Nodos - Visualización

Endpoints para obtener información de nodos (estudiantes) para visualización 3D.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.loader import DataLoader
from src.core.config import PATHS
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class StudentNode(BaseModel):
    """Modelo de nodo de estudiante para visualización."""
    id: str
    nombre: str
    carrera: str
    anio_ingreso: int


class NodesResponse(BaseModel):
    """Respuesta con lista de nodos."""
    total: int
    nodes: List[StudentNode]


# Instancia global del loader (singleton para eficiencia)
_loader = None


def get_loader() -> DataLoader:
    """Obtiene o crea instancia del DataLoader."""
    global _loader
    if _loader is None:
        _loader = DataLoader(
            PATHS.estudiantes,
            PATHS.clases,
            PATHS.asistencias
        )
        logger.info("DataLoader inicializado")
    return _loader


@router.get("/nodes", response_model=NodesResponse)
async def get_all_nodes():
    """
    Obtiene todos los nodos (estudiantes) para visualización.
    
    Retorna información básica de cada estudiante sin aristas.
    Los nodos se visualizarán en una esfera 3D en el frontend.
    
    Returns:
        NodesResponse con lista de estudiantes
    """
    try:
        loader = get_loader()
        estudiantes, _, _ = loader.load_all()
        
        nodes = [
            StudentNode(
                id=str(row['id_estudiante']),
                nombre=row['nombre'],
                carrera=row['carrera'],
                anio_ingreso=int(row['anio_ingreso'])
            )
            for _, row in estudiantes.iterrows()
        ]
        
        logger.info(f"Retornando {len(nodes)} nodos para visualización")
        
        return NodesResponse(
            total=len(nodes),
            nodes=nodes
        )
    
    except Exception as e:
        logger.error(f"Error al obtener nodos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al cargar nodos: {str(e)}")
