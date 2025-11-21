# Backend - Simulador de Epidemias API

API REST para simulación de epidemias en redes de contacto estudiantil construida con FastAPI.

## Descripción

Este backend expone la lógica de simulación epidémica existente a través de una API REST eficiente. Utiliza algoritmos vectorizados y matrices sparse para optimizar el rendimiento en redes de miles de estudiantes.

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos con tipado estático
- **NumPy/SciPy**: Computación científica vectorizada
- **NetworkX**: Análisis de grafos y redes
- **Pandas**: Manipulación de datos CSV

## Instalación

1. Instalar dependencias:
```bash
pip install -r requerimientos.txt
```

2. Ejecutar servidor:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints Principales

### Visualización
- `GET /api/nodes` - Obtiene todos los nodos (estudiantes) para visualización 3D

### Análisis MST/MTC
- `GET /api/mtc/analyze?weight_mode=inverse` - Análisis de Minimum Spanning Tree
  - Identifica contactos críticos y nodos puente
  - Proporciona recomendaciones epidemiológicas

### Simulación Epidémica
- `POST /api/simulation/start` - Inicia simulación SIR
  - Parámetros: `beta` (tasa transmisión), `num_pacientes_cero`
- `GET /api/simulation/{id}/infected` - Obtiene infectados por día
- `GET /api/simulation/{id}/wcc` - Análisis de componentes conexas

## Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura

```
Backend/
├── app.py              # Aplicación FastAPI principal
├── api/routers/        # Endpoints organizados por módulos
├── src/                # Lógica de simulación (reutilizada)
├── data/               # Archivos CSV de entrada
└── requerimientos.txt  # Dependencias Python
```

## Características

- **Alto rendimiento**: Simulaciones vectorizadas con NumPy
- **Escalable**: Maneja redes de 3000+ estudiantes eficientemente  
- **CORS habilitado**: Permite conexión desde frontend local
- **Logging completo**: Trazabilidad de operaciones
- **Tipado estático**: Validación automática con Pydantic