# 📊 Guía de Mejoras - Gráficas y Dashboards Dinámicos

## 🎯 Resumen de Mejoras

Se han creado versiones mejoradas de todos los dashboards con gráficas más dinámicas, insights automáticos y mejor visualización de datos.

### Archivos Creados

#### 1. **graphics_utils.py** - Librería Reutilizable
Módulo con utilidades para gráficas dinámicas e insights automáticos.

**Clases principales:**

- **`InsightGenerator`**: Genera insights automáticos cortos y precisos
  - `generate_price_insights()`: Análisis de cambios de precio
  - `generate_volatility_insights()`: Análisis de volatilidad
  - `generate_demand_insights()`: Análisis de demanda

- **`GraphicsLibrary`**: Librería de gráficas profesionales
  - `create_heatmap_tarifas()`: Heatmap interactivo
  - `create_trend_chart()`: Gráficas de tendencia
  - `create_comparison_bars()`: Gráficas comparativas
  - `create_zone_comparison_radar()`: Radar chart de zonas
  - `create_box_plot()`: Análisis de distribución
  - `create_scatter_demand()`: Relación demanda vs tarifa
  - `create_kpi_metric_card()`: Tarjetas de métricas

#### 2. **propuesta1_kpis_ejecutivo_mejorado.py** - Dashboard Ejecutivo
Dashboard estratégico con enfoque en decisiones de alto nivel.

**Características:**

✅ **KPIs Principales (4 cards)**
- Tarifa promedio general
- Zona más cara
- Equipo más demandado
- Volatilidad general

✅ **Insights Automáticos**
- Cambios de precio significativos
- Análisis de volatilidad
- Patrones de demanda

✅ **Visualizaciones Dinámicas**
- Tendencia tarifaria (línea)
- Comparativa por zona (barras)
- Matriz tarifaria (heatmap)
- Distribución por equipo (box plot)
- Relación demanda vs tarifa (scatter)

✅ **Tabla Detallada**
- Datos completos filtrados por zona y equipo

#### 3. **propuesta2_kpis_operacional_mejorado.py** - Dashboard Operacional
Dashboard técnico para operadores con énfasis en monitoreo diario.

**Características:**

✅ **Status Actual (4 métricas)**
- Tarifa del día con cambio vs 7 días
- Demanda actual
- Disponibilidad de equipos
- Volatilidad actual

✅ **Alertas Operacionales**
- Volatilidad alta
- Demanda elevada
- Disponibilidad crítica
- Sistema automático de alertas

✅ **Análisis Técnico Avanzado**
- Bandas de Bollinger
- Proyección de tendencias (14 días)
- Regresión lineal automática
- Señales de compra/venta

✅ **Matriz Comparativa**
- Últimos 7 días vs 30 días
- Heatmaps lado a lado

✅ **Rankings**
- Equipos más caros
- Mayor volatilidad
- Mayor demanda

#### 4. **indice_tarifas_spot_mejorado.py** - Matriz Tarifaria
Interfaz completa para consulta de tarifas con análisis interactivo.

**Características:**

✅ **Filtros Intuitivos**
- Selector de año
- Selector de mes
- Selector de tipo de equipo

✅ **Comparativa por Zonas**
- Tarjetas de tarifas (Norte, Centro, Sur)
- Gráfica de barras comparativa
- Insights rápidos (zona cara, barata, diferencia)

✅ **Matriz Completa**
- Heatmap de todas las combinaciones
- Tabla detallada con estadísticas
- Ranking de equipos

✅ **Estadísticas**
- Promedio general
- Mediana
- Máximo y mínimo
- Rangos por zona

---

## 🚀 Cómo Usar los Nuevos Dashboards

### Opción 1: Ejecutar Dashboard Ejecutivo
```bash
streamlit run propuesta1_kpis_ejecutivo_mejorado.py
```
**Ideal para:** Directivos, gerentes, decisiones estratégicas

### Opción 2: Ejecutar Dashboard Operacional
```bash
streamlit run propuesta2_kpis_operacional_mejorado.py
```
**Ideal para:** Operadores, supervisores, monitoreo diario

### Opción 3: Ejecutar Matriz Tarifaria
```bash
streamlit run indice_tarifas_spot_mejorado.py
```
**Ideal para:** Consulta de tarifas actuales, análisis de precios

---

## 📈 Características Principales por Dashboard

### Dashboard Ejecutivo 🎯

| Elemento | Descripción |
|----------|------------|
| **KPIs** | 4 métricas principales de negocio |
| **Insights** | 3 insights automáticos del mercado |
| **Tendencia** | Gráfica de línea últimos 30 días |
| **Comparativa** | Tarifa promedio por zona |
| **Matriz** | Heatmap interactivo zonas × equipos |
| **Análisis** | Box plot y scatter demanda vs tarifa |

### Dashboard Operacional ⚙️

| Elemento | Descripción |
|----------|------------|
| **Status** | 4 métricas operacionales actuales |
| **Alertas** | Sistema de alertas automáticas |
| **Bandas** | Bandas de Bollinger para volatilidad |
| **Proyección** | Predicción 14 días con tendencia |
| **Matriz 7/30** | Comparativa de períodos |
| **Rankings** | Top 3 equipos por diferentes criterios |

### Matriz Tarifaria 📊

| Elemento | Descripción |
|----------|------------|
| **Filtros** | Año, mes, tipo de equipo |
| **Tarjetas** | Tarifas por zona en tarjetas |
| **Heatmap** | Matriz completa interactiva |
| **Tabla** | Datos detallados con estadísticas |
| **Rankings** | Equipos ordenados por precio |

---

## 🎨 Mejoras Visuales

✨ **Gráficas Dinámicas**
- Plotly interactivo (zoom, hover, exportar)
- Colores corporativos coherentes
- Animaciones suaves
- Responsive design

✨ **Insights Inteligentes**
- Análisis automático de tendencias
- Comparativas significativas
- Alertas basadas en umbrales
- Recomendaciones cortas y precisas

✨ **Interfaz Mejorada**
- Headers con gradientes
- Tarjetas con sombras
- Métricas destacadas
- Mejor organización del espacio

---

## 📊 Fórmulas y Cálculos

### Volatilidad
```
Volatilidad = (Desviación Estándar / Promedio) × 100
```

### Cambio Porcentual
```
Cambio % = ((Valor Actual - Valor Anterior) / Valor Anterior) × 100
```

### Bandas de Bollinger
```
Banda Superior = Promedio + (Desv. Estándar × 1.5)
Banda Inferior = Promedio - (Desv. Estándar × 1.5)
```

### Tendencia (Regresión Lineal)
```
Slope = (Σ(X·Y) - n·X̄·Ȳ) / (Σ(X²) - n·X̄²)
```

---

## 🔄 Integración con Backend

Los dashboards pueden conectarse fácilmente con el backend (`main.py`):

```python
import requests

# Obtener predicción del backend
response = requests.post('http://localhost:8000/predict', json={
    'route': {
        'distancia_km': 800,
        'tipo_carga': 0,
        'riesgo_pais': 0.3,
        'precio_diesel': 22,
        'tiempo_cruce': 6,
        'inflacion_mxn': 5.5,
        'tipo_cambio': 18,
        'demanda_mercado': 0.7,
        'capacidad_disponible': 0.6
    },
    'prediction_days': 14
})

prediccion = response.json()
```

---

## 💡 Tips de Uso

### Para Ejecutivos
1. Enfócate en los KPIs principales
2. Lee los insights automáticos
3. Observa la tendencia general
4. Usa la matriz para decisiones estratégicas

### Para Operadores
1. Monitorea las alertas diariamente
2. Revisa las bandas de volatilidad
3. Analiza las proyecciones
4. Compara períodos 7/30 días

### Para Consultores
1. Usa la matriz tarifaria como referencia
2. Exporta gráficas para reportes
3. Analiza rankings por equipo
4. Documenta tendencias

---

## 🔧 Personalización

### Cambiar Colores
En `graphics_utils.py`, modifica los diccionarios de color:
```python
colores_zona = {
    "Norte": "#FF6B6B",
    "Centro": "#4ECDC4",
    "Sur": "#45B7D1"
}
```

### Agregar Nuevas Métricas
Usa la clase `InsightGenerator` para agregar más análisis:
```python
insights = []
insights.extend(insight_gen.generate_price_insights(df_actual, df_prev))
# Agregar más...
```

### Cambiar Período de Análisis
En los dashboards, modifica el timedelta:
```python
df_ultimos_30d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=30)]
# Cambiar a 60 días:
df_ultimos_60d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=60)]
```

---

## 📝 Estructura de Datos

### DataFrame Esperado
```
fecha      | zona   | equipo       | tarifa | demanda | disponibilidad
-----------|--------|--------------|--------|---------|---------------
2026-03-19 | Norte  | Caja Seca    | 0.45   | 8       | 0.85
2026-03-19 | Centro | Plataforma   | 0.48   | 6       | 0.72
...
```

### JSON de Matriz
```json
{
  "matriz": {
    "2026": {
      "Mar": {
        "Norte": [
          {"Componente": "TARIFA SPOT FINAL", "Caja Seca (Dry Van)": 25.50, ...}
        ]
      }
    }
  }
}
```

---

## 🐛 Troubleshooting

**Problema:** Las gráficas no cargan
- Solución: Verifica que pandas, plotly y streamlit estén instalados

**Problema:** Los datos aparecen en blanco
- Solución: Verifica que el JSON esté bien formado

**Problema:** Las alertas no funcionan
- Solución: Asegúrate de que los datos tengan las columnas esperadas

---

## 📞 Contacto y Soporte

Para realizar cambios o agregar nuevas funcionalidades, contacta al equipo de desarrollo.

---

**Versión:** 1.0 | **Fecha:** Marzo 2026 | **Estado:** Actualizado
