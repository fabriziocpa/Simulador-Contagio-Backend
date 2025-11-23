# Simulador de Epidemias - Backend API

API REST para simulación epidemiológica en redes de contacto estudiantil utilizando modelos SIR vectorizados y análisis de grafos.

## Arquitectura e Implementación

### Gestión de Datos

**DataLoader** (`src/data/loader.py`):
- Carga archivos CSV: estudiantes, clases, asistencias
- Validación de integridad y detección de duplicados
- Mapeo bidireccional ID ↔ índice para optimización

**DataProcessor** (`src/data/processor.py`):
- Procesamiento unificado de datos mediante merge de DataFrames
- Filtro temporal por días válidos
- Output: DataFrame con columnas [estudiante_id, clase_id, día, presente]

### Construcción de Redes y Aristas

**Regla de Contacto**: Dos estudiantes contactan si pertenecen a la misma clase y ambos asistieron el mismo día.

**Proceso de Construcción**:
1. **Agrupación por día**: Para cada día ∈ {Lunes, Martes, ..., Viernes}
2. **Agrupación por clase**: Dentro de cada día, agrupar estudiantes por clase
3. **Generación de aristas**: Para cada clase con n ≥ 2 estudiantes, crear aristas entre todas las parejas

**Algoritmo de Aristas Vectorizado**:
```
Para cada día d ∈ D:
  Para cada clase c ∈ clases_día:
    estudiantes_c = {s₁, s₂, ..., sₙ} donde n = |estudiantes_c|
    Si n ≥ 2:
      Para cada par (i,j) donde 1 ≤ i < j ≤ n:
        arista = (sᵢ, sⱼ)
        peso = f(duración_c, modo_peso)
        grafo.agregar_arista(arista, peso)
```

**Complejidad**: O(∑_{c∈C} C(n_c, 2)) donde C(n,2) = n(n-1)/2

**Fórmulas de Peso**:
- `uniform`: w = 1.0
- `duration`: w = duración_c / duración_máxima
- `inverse`: w = 1 / duración_c (contactos largos = mayor riesgo)

**Mapeo Índice-ID**: Conversión bidireccional para matrices:
- φ: ID_estudiante → índice_matriz ∈ [0, N-1]
- φ⁻¹: índice_matriz → ID_estudiante

**SparseContactNetwork** (CSR Format):
- **Matriz densa**: N×N elementos (N ≈ 3000)
- **Matriz sparse**: 3 arrays: data[K], indices[K], indptr[N+1]
- **Compresión**: 96% reducción memoria
- **Operaciones**: multiplicación matricial O(K) vs O(N²)

### Modelo Epidemiológico SIR

**Estados**:
- S: Susceptible (no infectado, estado inicial)
- I: Infectado (transmisor activo)

**Ecuación de Transmisión por Tick**:
```
Estado inicial: Sᵢ(t), Iᵢ(t) ∈ {0,1} para i ∈ [1,N]

Exposición: Eᵢ(t) = ∑_{j=1}^N Cᵢⱼ × Iⱼ(t)
         donde Cᵢⱼ = peso arista (i,j) si existe, 0 otherwise

Probabilidad: Pᵢ(t) = 1 - exp(-β × Eᵢ(t))

Transmisión: Iᵢ(t+1) = Iᵢ(t) ∨ (Sᵢ(t) ∧ (random() < Pᵢ(t)))
```

**Parámetros**:
- β ∈ [0,1]: tasa de transmisión
- Eᵢ(t): exposición acumulada del nodo i en tiempo t
- Pᵢ(t): probabilidad de infección condicional

**Optimizaciones Vectorizadas**:
- **Pre-asignación buffers**: NumPy arrays fijos
- **Máscara susceptibles**: actualización incremental S_maskᵢ
- **Multiplicación sparse**: SciPy BLAS (Cᵢⱼ @ Iⱼ)
- **SIMD**: operaciones vectorizadas en CPU

**Complejidad**: O(K) por tick, K = aristas grafo (10⁴-10⁵)

### Análisis de Algoritmos

**MSTAnalyzer - Minimum Spanning Tree**:
```
Entrada: G = (V, E, w) grafo ponderado conexo
Salida: T ⊂ E árbol con |V|-1 aristas, peso mínimo

Algoritmo: Kruskal con Union-Find
1. Ordenar aristas por peso ascendente
2. Inicializar componentes: cada vértice es componente
3. Para cada arista (u,v) en orden:
   Si componente(u) ≠ componente(v):
     Agregar (u,v) a T
     Unir componentes
4. Retornar T

Transformación pesos para MST:
- inverse: w_mst = 1/(w_original + ε)
- negative: w_mst = -w_original
- uniform: w_mst = w_original
```

**Fórmulas de Centralidad**:
```
Degree centrality: C_D(v) = deg(v) / (n-1)

Betweenness centrality: C_B(v) = ∑_{s≠v≠t} σ_st(v) / σ_st

Closeness centrality: C_C(v) = 1 / ∑_{u≠v} d(v,u)

Donde:
- σ_st: caminos mínimos entre s,t
- σ_st(v): caminos mínimos que pasan por v
- d(v,u): distancia geodésica entre v,u
```

**WCCAnalyzer - Weakly Connected Components**:
```
Entrada: Grafo G = (V, E)
Salida: Partición V = C₁ ∪ C₂ ∪ ... ∪ C_k

Algoritmo DFS/BFS:
Para cada v ∈ V no visitado:
  Iniciar componente C nueva
  DFS/BFS desde v, marcar visitados
  Agregar nodos alcanzables a C

Métricas por componente:
- Tamaño: |Cᵢ|
- Prioridad cuarentena: 1 / |Cᵢ|
```

### Gestión de Caché

**NetworkCacheManager**:
- **Política**: LRU por día
- **Hit**: O(1) recuperación
- **Miss**: O(K) construcción + cache
- **Optimización**: ~500ms construcción → <0.1ms acceso

## Endpoints API

### Visualización
```
GET /api/nodes
```
Retorna array nodos con posición 3D, estado infección.

### Análisis MTC/MST
```
GET /api/mtc/analyze?weight_mode=inverse&day=Lunes
```
Parámetros: weight_mode (inverse|duration|uniform), day (opcional)

### Simulación SIR
```
POST /api/simulation/start
Body: { "beta": 0.3, "num_pacientes_cero": 1, "weight_mode": "inverse" }
```

```
GET /api/simulation/{id}/infected
GET /api/simulation/{id}/wcc
```

## Instalación

```bash
pip install -r requerimientos.txt
cd Backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Documentación: http://localhost:8000/docs

## Stack Técnico

- **API**: FastAPI + Uvicorn
- **Computación**: NumPy + SciPy (álgebra lineal, matrices sparse)
- **Grafos**: NetworkX (MST, componentes)
- **Datos**: Pandas (procesamiento CSV)
- **Logging**: Python logging

## Rendimiento

- Nodos: 3000+
- Aristas/día: ~45,000
- Tick simulación: <10ms
- Análisis MST: 50-100ms
- Memoria: ~500MB (cache completo)

## Estructura del Proyecto

```
Backend/
├── app.py                          # FastAPI principal
├── api/routers/                    # Endpoints
├── src/core/                       # Lógica central
├── src/data/                       # Procesamiento datos
├── src/analysis/                   # Algoritmos análisis
├── src/utils/                      # Utilidades
└── data/                           # Archivos CSV
```

## Arquitectura e Implementación

### Gestión de Datos

**DataLoader** (`src/data/loader.py`):
- Carga archivos CSV: estudiantes, clases, asistencias
- Validación de integridad y detección de duplicados
- Mapeo bidireccional ID ↔ índice para optimización

**DataProcessor** (`src/data/processor.py`):
- Procesamiento unificado de datos mediante merge de DataFrames
- Filtro temporal por días válidos
- Output: DataFrame con columnas [estudiante_id, clase_id, día, presente]

### Construcción de Redes y Aristas

**Regla de Contacto**: Dos estudiantes contactan si pertenecen a la misma clase y ambos asistieron el mismo día.

**Proceso de Construcción**:
1. **Agrupación por día**: Para cada día de la semana, filtrar estudiantes presentes
2. **Agrupación por clase**: Dentro de cada día, agrupar estudiantes por clase
3. **Generación de aristas**: Para cada clase con ≥2 estudiantes, crear aristas entre todas las parejas posibles

**Algoritmo de Aristas Vectorizado** (`src/core/graph.py`):
```python
# Para cada día y clase:
estudiantes_clase = [id1, id2, id3, ..., idN]  # N estudiantes

# Generar todas las combinaciones C(N,2)
for i in range(N):
    for j in range(i+1, N):
        arista = (estudiantes_clase[i], estudiantes_clase[j])
        peso = normalizar_duracion_clase(clase)  # [0,1]
        grafo.agregar_arista(arista, peso)

# Complejidad: O(∑ C(n_k,2)) donde n_k = estudiantes/clase/día
```

**Mapeo Índice-ID**: Conversión bidireccional para optimización matricial:
- ID estudiante → índice matriz (0 a N-1)
- Índice matriz → ID estudiante

**Pesos de Arista**:
- `uniform`: peso = 1.0 para todas las aristas
- `duration`: peso = duración_clase / duración_máxima
- `inverse`: peso = 1 / duración_clase (contactos largos = más riesgo)

**SparseContactNetwork** (`src/core/sparse_network.py`):
- Conversión a matriz CSR (Compressed Sparse Row)
- Optimización: 96% reducción de memoria vs matriz densa
- Operaciones eficientes: multiplicación matricial vectorizada

### Modelo Epidemiológico SIR

**Estados**:
- S: Susceptible (no infectado)
- I: Infectado (transmisor activo)

**Ecuación de Transmisión**:
```
Exposición(E) = contact_matrix @ I_vector
Probabilidad(P) = 1 - exp(-β × E)

β ∈ [0,1]: tasa de transmisión
E: contactos infectados

Decisión: random() < P ⟹ infección
```

**Optimizaciones**:
- Pre-asignación de buffers NumPy
- Vectorización SIMD
- Multiplicación sparse matrix (SciPy BLAS)
- Complejidad: O(k) por tick (k = aristas ≈ 10⁴-10⁵)

### Análisis de Algoritmos

**MSTAnalyzer** (Minimum Spanning Tree):
- Algoritmo: Kruskal con Union-Find
- Pesos: 1/duración_contacto (relación inversa)
- Output: árbol de expansión mínima (n-1 aristas)
- Interpretación: rutas críticas de transmisión

**WCCAnalyzer** (Weakly Connected Components):
- Descomposición en subgrafos desconectados
- Identificación de "islas epidémicas"
- Prioridad de cuarentena: inverso del tamaño componente

**CentralityAnalyzer**:
- Betweenness: caminos que pasan por nodo
- Closeness: distancia promedio a otros nodos
- Degree: contactos directos
- Aplicación: identificación de nodos críticos

### Gestión de Caché

**NetworkCacheManager** (`src/core/network_cache.py`):
- Evita recálculo de grafos idénticos
- Cache por día: hit < 0.1ms, miss ≈ 500ms
- Optimización de memoria y tiempo

## Endpoints API

### Visualización
```
GET /api/nodes
```
Retorna array de nodos con posición 3D, estado de infección.

### Análisis MTC/MST
```
GET /api/mtc/analyze?weight_mode=inverse&day=Lunes
```
Parámetros: weight_mode (inverse|duration|uniform), day (opcional)
Retorna: aristas MST, nodos de alto grado, recomendaciones.

### Simulación SIR
```
POST /api/simulation/start
Body: { "beta": 0.3, "num_pacientes_cero": 1, "weight_mode": "inverse" }
```
Inicia simulación, retorna timeline de infección.

```
GET /api/simulation/{id}/infected
```
Estado de infección por día.

```
GET /api/simulation/{id}/wcc
```
Componentes conexas del grafo.

## Instalación

```bash
pip install -r requerimientos.txt
cd Backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Documentación: http://localhost:8000/docs

## Stack Técnico

- **API**: FastAPI + Uvicorn
- **Computación**: NumPy + SciPy (álgebra lineal, matrices sparse)
- **Grafos**: NetworkX (MST, componentes)
- **Datos**: Pandas (procesamiento CSV)
- **Logging**: Python logging

## Rendimiento

- Nodos: 3000+
- Aristas/día: ~45,000
- Tick simulación: <10ms
- Análisis MST: 50-100ms
- Memoria: ~500MB (cache completo)

## Estructura del Proyecto

```
Backend/
├── app.py                          # FastAPI principal
├── api/routers/                    # Endpoints
├── src/core/                       # Lógica central
├── src/data/                       # Procesamiento datos
├── src/analysis/                   # Algoritmos análisis
├── src/utils/                      # Utilidades
└── data/                           # Archivos CSV
```
