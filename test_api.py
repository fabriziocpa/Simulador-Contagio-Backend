"""
Script de prueba para verificar que la API funciona correctamente.

Uso: python test_api.py
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from app import app

def test_routes():
    """Verifica que todas las rutas estén registradas."""
    print("="*70)
    print("TEST: Rutas de la API")
    print("="*70)
    
    routes = [route for route in app.routes if hasattr(route, 'path')]
    
    print(f"\nTotal de rutas: {len(routes)}\n")
    
    for route in routes:
        if hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"{methods:10} {route.path}")
    
    print("\n" + "="*70)
    print("✓ API cargada correctamente")
    print("="*70)
    print("\nPara iniciar el servidor:")
    print("  uvicorn app:app --reload")
    print("\nDocumentación Swagger:")
    print("  http://localhost:8000/docs")
    print("\n" + "="*70)


if __name__ == "__main__":
    test_routes()
