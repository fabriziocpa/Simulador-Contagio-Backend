# Simulador de Epidemias - Backend API

API REST para simulación epidemiológica en redes de contacto estudiantil mediante modelos SIR vectorizados y análisis de grafos.

## Stack Tecnológico

| Tecnología | Propósito |
|------------|-----------|
| FastAPI | Framework API REST |
| NumPy/SciPy | Computación matricial |
| NetworkX | Algoritmos de grafos |
| Pandas | Procesamiento de datos |
| Uvicorn | Servidor ASGI |

## Instalación

```bash
pip install -r requerimientos.txt
cd Backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Documentación: http://localhost:8000/docs

## Arquitectura

```
Backend/
├── app.py                    # FastAPI principal
├── api/routers/
│   ├── mtc.py                # Endpoints MST/MTC
│   ├── nodes.py              # Endpoints de nodos
│   └── simulation.py         # Endpoints simulación
├── src/
│   ├── core/
│   │   ├── epidemic.py       # Modelo SIR vectorizado
│   │   ├── graph.py          # Construcción de grafos
│   │   ├── network_cache.py  # Cache LRU
│   │   └── sparse_network.py # Matrices CSR
│   ├── data/
│   │   ├── loader.py         # Carga CSV
│   │   └── processor.py      # Procesamiento
│   └── analysis/
│       ├── mst_analyzer.py   # Minimum Spanning Tree
│       ├── wcc_analyzer.py   # Componentes conexas
│       └── centrality_analyzer.py
└── data/                     # Archivos CSV
```

## Modelo Epidemiológico

### Estados SIR
- S: Susceptible (no infectado)
- I: Infectado (transmisor activo)

### Ecuación de Transmisión
```
Exposición:    E(t) = C @ I(t)
Probabilidad:  P(t) = 1 - exp(-beta * E(t))
Infección:     I(t+1) = I(t) OR (S(t) AND random() < P(t))
```

### Parámetros
- beta: Tasa de transmisión [0, 1]
- C: Matriz de contactos sparse (CSR)

## Endpoints API

### Nodos
```
GET /api/nodes
```
Retorna posición 3D y estado de cada estudiante.

### Simulación
```
POST /api/simulation/start
Body: { "beta": 0.3, "num_pacientes_cero": 5, "weight_mode": "inverse" }

GET /api/simulation/{id}/infected
GET /api/simulation/{id}/wcc
```

### Análisis MST
```
GET /api/mtc/analyze?weight_mode=inverse&day=Lunes
```

## Algoritmos

### Construcción de Red
- Regla: Dos estudiantes conectan si comparten clase y asistieron el mismo día
- Pesos: uniform, duration, inverse
- Formato: Matriz sparse CSR (96% compresión)

### MST (Minimum Spanning Tree)
- Algoritmo: Kruskal con Union-Find
- Identifica conexiones críticas de transmisión
- Detecta nodos puente de alto contacto

### WCC (Componentes Conexas)
- Algoritmo: DFS/BFS
- Identifica subgrupos aislados
- Priorización para cuarentena

## Rendimiento

| Métrica | Valor |
|---------|-------|
| Nodos | 3000+ |
| Aristas/día | 45,000 |
| Tick simulación | <10ms |
| Análisis MST | 50-100ms |
| Compresión sparse | 96% |

## Datos de Entrada

| Archivo | Contenido |
|---------|-----------|
| estudiantes.csv | ID, datos demográficos |
| clases.csv | ID, duración, horario |
| asistencias.csv | Estudiante, clase, día, presente |
