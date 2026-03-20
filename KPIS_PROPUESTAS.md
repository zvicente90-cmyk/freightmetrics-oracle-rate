# Propuestas de KPIs - Historial Tarifas Spot México

## 📊 PROPUESTA 1: Dashboard EJECUTIVO
### (Visión Global + Decisiones Estratégicas)

**Enfoque:** Alerta temprana de cambios de mercado, rentabilidad general

### KPIs Principales:

1. **📈 Tarifa Promedio Actual (por Zona)**
   - Métrica: $ USD/km
   - Muestra: Caja Seca vs Full vs Refrigerado vs Plataforma
   - Visualización: 4 cards grandes con números destacados
   - Ejemplo: [NORTE: $0.45/km] [CENTRO: $0.42/km] [SUR: $0.38/km]

2. **📊 Gráfico de Línea: Evolución Histórica (Últimos 6 meses)**
   - X: Semanas
   - Y: Tarifa promedio (USD/km)
   - Líneas: Zona Norte, Centro, Sur
   - Colores: Naranja (N), Azul (C), Verde (S)
   - Interactivo: Hover muestra fecha + valor exacto

3. **🔄 Matriz de Calor: Zonas × Equipos**
   - Filas: Zona (Norte, Centro, Sur)
   - Columnas: Equipo (Caja Seca, Plataforma, Refrigerado, Full)
   - Colores: Verde (barato) → Rojo (caro)
   - Muestra tarifa actual + variación % respecto hace 1 mes

4. **⚡ Cambios Destacados (Top 3)**
   - Ranking de cambios más significativos últimos 7 días
   - Ejemplo: 
     * 🔴 Plataforma Norte: +8.5% (por demanda)
     * 🟢 Caja Seca Sur: -3.2% (oferta normalizada)
     * 🔴 Refrigerado Centro: +2.1% (combustible)

5. **💡 Indicador: Brecha vs DAT USA**
   - Muestra diferencia: Tarifas MXN convertidas vs DAT USD
   - Insight: Si MXN se devalúa, nuestras tarifas bajan vs competencia
   - Gauge: Rojo (desventaja >20%), Amarillo (10-20%), Verde (<10%)

---

## 📊 PROPUESTA 2: Dashboard OPERACIONAL
### (Detalle Técnico + Control de Precios)

**Enfoque:** Monitoreo diario, control de márgenes, volatilidad

### KPIs Principales:

1. **📌 Tarifa Actual vs. Histórica**
   - Card 1: Tarifa HOY (grande)
   - Card 2: Promedio últimas 4 semanas
   - Card 3: Min/Max últimos 30 días
   - Visualización: 3 columnas de cards

2. **📊 Gráficos de Barras Agrupadas**
   - Zona × Equipo (matriz visual)
   - 3 gráficos laterales: Norte, Centro, Sur
   - Cada uno con 4 barras (Caja Seca, Plataforma, Refrig, Full)
   - Código de color por equipo (consistente)

3. **📉 Volatilidad y Riesgo (Desviación Estándar)**
   - KPI: coeficiente de variación por zona
   - Indicador: % de volatilidad
   - Interpretación: >15% = ALTO RIESGO (color rojo)
   - Card con semáforo visual

4. **🔮 Proyección de Tendencia (Línea con área)**
   - Histórico (línea sólida) + Proyección (línea punteada)
   - Machine Learning: Regresión simple/tendencia
   - Intervalo: Últimos 3 meses + predicción 2 semanas
   - Muestra banda de confianza (sombreado)

5. **📋 Tabla Interactiva Filtrada**
   - Columnas: Fecha, Zona, Equipo, Tarifa, Cambio%, Índice
   - Filtros: Zona, Equipo, Rango Fecha
   - Sortable: Click en columnas
   - Exportable: CSV/Excel

---

## 🎯 Comparativa

| Aspecto | Propuesta 1 (Ejecutivo) | Propuesta 2 (Operacional) |
|---------|------------------------|---------------------------|
| **Público** | Gerencia/Decisores | Operadores/Analistas |
| **Granularidad** | Agregado/Zonal | Detallado/Por equipo |
| **# de gráficos** | 4-5 (simples) | 6-7 (complejos) |
| **Interactividad** | Media (filtros básicos) | Alta (muchos filtros) |
| **Tiempo lectura** | <2 min | 5-10 min |
| **Acción frecuente** | Mensual | Diaria |
| **Forecast** | No | Sí |
| **Volatilidad** | No | Sí |

---

## 💾 Estructura de Datos Necesaria

```json
{
  "fecha": "2026-03-16",
  "semana": 11,
  "mes": "2026-03",
  "zona": "Norte",
  "equipo": "Caja Seca",
  "tarifa_usd_km": 0.45,
  "tarifa_mxn": 8100,
  "tipo_cambio": 18.0,
  "demanda": 7,
  "oferta": 5,
  "indice_combustible": 1.05,
  "variacion_semana_anterior": +2.1,
  "notas": "Demanda alta por temporada"
}
```

---

## 🚀 Próximos Pasos

1. **Seleccionar propuesta** (o híbrido)
2. **Crear tabla base** con datos históricos
3. **Implementar gráficos** con Plotly (dinámicos)
4. **Agregar filtros** Streamlit (zona, equipo, rango)
5. **Testing** con datos reales

