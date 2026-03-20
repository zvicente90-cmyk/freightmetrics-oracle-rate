# 📊 Dashboard Híbrido - Tarifas Spot México

## 🚀 Inicio Rápido

```bash
# Ejecutar dashboard completo
streamlit run dashboard_kpis_hibrido.py
```

Se abrirá automáticamente en: **http://localhost:8501**

---

## 📑 Estructura del Dashboard

### **Tab 1: 👔 Ejecutivo**
Visión estratégica para gerentes y decisores

**KPIs:**
- 💰 **Tarifa Promedio Actual** (por zona)
  - Cards con valores y cambio % respecto mes anterior
  - Colores: Rojo (subida) / Verde (bajada)

- 📈 **Gráfico de Evolución** (6 meses)
  - Líneas por zona (Norte, Centro, Sur)
  - Identifica tendencias vs competencia

- 🔥 **Matriz de Calor** (Zonas × Equipos)
  - Visor rápido de donde están los precios más altos
  - Colores Verde → Rojo (barato → caro)

- ⚡ **Top 3 Cambios** (últimos 7 días)
  - Identifica movimientos más significativos
  - Ayuda a reaccionar a cambios de mercado

- 💡 **Brecha vs DAT USA**
  - Compara nuestras tarifas vs DAT (referencia USA)
  - Indicador de competitividad

**Tiempo de lectura:** < 2 minutos ✓

---

### **Tab 2: 🔧 Operacional**
Control técnico para operadores y analistas

**Filtros Disponibles:**
- 🌍 Zona (Todas / Norte / Centro / Sur)
- 🚛 Equipo (Todos / Caja Seca / Plataforma / Refrigerado / Full)
- 📅 Período (7-180 días)

**KPIs:**

- 📌 **Tarifa Actual vs Histórica**
  - Tarifa de HOY
  - Promedio del período seleccionado
  - Máximo y Mínimo en período

- 📊 **Barras Agrupadas** (Zona × Equipo)
  - Comparativa visual de precios
  - Identifica equipo más caro/barato por zona

- 📉 **Volatilidad (Riesgo)**
  - Coeficiente de variación por zona
  - 🟢 Bajo (<10%) / 🟡 Medio (10-15%) / 🔴 Alto (>15%)
  - Ayuda a medir estabilidad del mercado

- 🔮 **Proyección de Tendencia** (14 días)
  - Regresión lineal de últimos 60 datos
  - Intervalo de confianza ±1σ
  - Indica si mercado sube, baja o se estabiliza

- 📋 **Tabla Detallada** (últimos 30 días)
  - Vista granular de todos los datos
  - **Descargable en CSV** 📥

**Tiempo de análisis:** 5-10 minutos

---

### **Tab 3: ⚙️ Configuración**
Documentación de cálculos y fórmulas

- Sobre el dashboard
- Explicación de KPIs
- Fórmulas matemáticas
- Metodología de cálculos

---

## 📊 Datos y Zonas

**Zonas cubitas:**
- 🔴 **Norte**: Monterrey, Chihuahua, Nuevo Laredo
- 🔵 **Centro**: México City, Querétaro, San Luis Potosí
- 🟢 **Sur**: Mérida, Cancún, Felipe Carrillo Puerto

**Tipos de Equipo:**
- 🚛 **Caja Seca**: Carga general (base: USD $0.45/km)
- 🎯 **Plataforma**: Carga sin techo (base: USD $0.52/km)
- ❄️ **Refrigerado**: Carga refrigerada (base: USD $0.61/km)
- ⚡ **Full**: Doble remolque (base: USD $0.56/km)

---

## 🔧 Personalización

### Cambiar período de datos
En **Tab 2**, usa el slider "Días históricos" (7-180)

### Filtrar por zona
Dropdown en **Tab 2** - Selecciona: Todas / Norte / Centro / Sur

### Filtrar por equipo
Dropdown en **Tab 2** - Selecciona: Todos / Equipo específico

### Descargar datos
Botón **📥 Descargar CSV** en **Tab 2**
Exporta tabla completa en formato CSV

---

## 📈 Interpretación de Gráficos

### Gráfico de Línea (Tab 1)
- **Línea sube** → Mercado al alza (presión de precios)
- **Línea baja** → Mercado a la baja (presión competitiva)
- **Línea plana** → Mercado estable

### Matriz de Calor (Tab 1)
- **Verde oscuro** → Precio barato (oportunidad)
- **Rojo oscuro** → Precio caro (advertencia)
- **Amarillo** → Precio medio

### Volatilidad (Tab 2)
- **<10%** → Mercado predecible ✓
- **10-15%** → Mercado variable ⚠️
- **>15%** → Mercado volátil 🚨

### Proyección (Tab 2)
- **Línea punteada sube** → Tendencia alcista (precios subirán)
- **Línea punteada baja** → Tendencia bajista (precios bajarán)
- **Banda gris** → Margen de error (±1 desviación estándar)

---

## ⚡ Casos de Uso

### Para Gerentes
```
→ Ir a Tab Ejecutivo
→ Ver cards de tarifa promedio por zona
→ Revisar top 3 cambios
→ Decidir estrategia de precios
Tiempo: 2 min
```

### Para Operadores
```
→ Ir a Tab Operacional
→ Seleccionar zona de interés
→ Revisar volatilidad (riesgo)
→ Revisar proyección (próximas 2 semanas)
→ Ajustar cotizaciones según tendencia
Tiempo: 5 min
```

### Para Análisis Profundo
```
→ Tab Operacional
→ Aplicar filtros (zona + equipo + período)
→ Analizar volatilidad
→ Revisar proyección
→ Descargar CSV para análisis adicional
→ Generar reportes
Tiempo: 15-20 min
```

---

## 🔄 Actualización de Datos

**Incluye simulación de:** 180 días históricos
**Frecuencia esperada:** Diaria (integrar con BD real)
**Última actualización (formato):** 2026-03-16 14:30:00

---

## 📱 Responsive Design

Dashboard optimizado para:
- ✓ Desktop (recomendado)
- ✓ Tablet
- ⚠️ Mobile (algunos gráficos pueden requerir scroll)

---

## 🎯 Próximos Pasos

1. **Conectar Base de Datos Real**
   - Cambiar `generar_datos_historicos()` por query a BD

2. **Agregar Actualizaciones Automáticas**
   - Scheduler para refrescar datos diariamente

3. **Historiales Personalizados**
   - Guardar preferencias de filtros por usuario

4. **Alertas**
   - Notificaciones cuando volatilidad > 20%
   - Alerta si precio sube > 5% en 24h

5. **Roles y Permisos**
   - Limitar acceso a zonas/equipos por usuario

---

## 📞 Soporte

Para dudas sobre cálculos o interpretación:
Ver **Tab 3 - Configuración** para documentación técnica

