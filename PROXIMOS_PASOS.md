## 🎯 INSTRUCCIONES RÁPIDAS - PRÓXIMOS PASOS

### 1️⃣ Verificar Instalación de Dependencias

Las gráficas utilizan **Plotly**, que ya debería estar en `requirements.txt`.  
Verifica que tengas instalado:

```bash
pip install plotly>=5.0.0
pip install streamlit>=1.0.0
pip install pandas>=1.0.0
pip install numpy>=1.0.0
```

### 2️⃣ Cuál Dashboard Usar Según Tu Necesidad

| Necesidad | Dashboard | Comando |
|-----------|-----------|---------|
| 👔 Decisiones estratégicas | **Ejecutivo** | `streamlit run propuesta1_kpis_ejecutivo_mejorado.py` |
| ⚙️ Monitoreo operativo | **Operacional** | `streamlit run propuesta2_kpis_operacional_mejorado.py` |
| 📊 Consultar tarifas | **Matriz** | `streamlit run indice_tarifas_spot_mejorado.py` |

### 3️⃣ Características Principales por Dashboard

#### 📊 Dashboard Ejecutivo
- **Ideal para**: Gerentes, directivos
- **Tiempo de uso**: 5-10 minutos
- **Función**: Visión general del mercado
- **Acciones**: Decisiones estratégicas

**Main Features:**
- 4 KPIs principales
- 3+ insights automáticos
- Gráficas de tendencia
- Matriz tarifaria interactiva
- Análisis de distribución

#### ⚙️ Dashboard Operacional  
- **Ideal para**: Operadores, supervisores
- **Tiempo de uso**: Diario para monitoreo
- **Función**: Control técnico operativo
- **Acciones**: Ajustes operacionales

**Main Features:**
- Alertas automáticas
- Bandas de Bollinger
- Proyecciones (14 días)
- Comparativas 7 vs 30 días
- Rankings de equipos

#### 📊 Matriz Tarifaria
- **Ideal para**: Todos (referencia rápida)
- **Tiempo de uso**: 2-3 minutos
- **Función**: Consultar tarifas
- **Acciones**: Decisiones de precios

**Main Features:**
- Filtros por período y equipo
- Tarjetas de zonas
- Heatmap interactivo
- Tabla detallada
- Estadísticas

### 4️⃣ Entender los Insights

#### ✅ Insight sobre Precios
```
📍 Norte es 15.2% más caro que Sur
```
**Significa**: La zona Norte tiene tarifas más elevadas  
**Acción**: Evaluar competitividad vs costo operativo

#### ⚠️ Insight de Volatilidad
```
🔴 VOLATILIDAD ALTA: 12.3%
```
**Significa**: Los precios fluctúan mucho  
**Acción**: Considerar coberturas o forward contracts

#### 🚚 Insight de Demanda
```
🚚 Centro: Mayor demanda (+8.5%)
```
**Significa**: Más carga en Centro  
**Acción**: Potencial para subirprecios o focus en esa zona

#### ✨ Insight de Estabilidad
```
✅ Caja Seca: Más predecible
```
**Significa**: Precios consistentes  
**Acción**: Mejor para planificación

### 5️⃣ Cómo Interpretar las Gráficas

#### Heatmap (Colores)
- 🔴 **Rojo** = Precios altos (caro)
- 🟠 **Naranja** = Precios moderados  
- 🟡 **Amarillo** = Precios bajos
- 🟢 **Verde** = Precios muy bajos

#### Gráfica de Línea (Tendencias)
- ⬆️ **Línea sube** = Precios al alza
- ⬇️ **Línea baja** = Precios a la baja
- ➡️ **Línea recta** = Precios estables

#### Bandas de Bollinger
```
─── Banda Superior (límite alto esperado)
───•──────────• Promedio (centro)
─── Banda Inferior (límite bajo esperado)
```
Cuando el precio **toca banda superior** → Caro  
Cuando el precio **toca banda inferior** → Barato

#### Box Plot (Distribución)
```
     ─•─  Máximo
       │
       │ Cuartil superior (75%)
    ─┌─┘
    │█│  Mediana (50%)
    └─┘
       │ Cuartil inferior (25%)
       │
     ─•─  Mínimo
```

### 6️⃣ Configurar para Tu Equipo

**Si quieres acceso remoto:**

```bash
# Ejecutar en puerto diferente
streamlit run propuesta1_kpis_ejecutivo_mejorado.py --server.port 8501

# O modificar config en ~/.streamlit/config.toml:
[server]
port = 8501
```

**Si quieres agregar usuarios:**

Todos pueden acceder a `http://tu-servidor:8501`  
Solo necesitan tener acceso a la red.

### 7️⃣ Personalizar Colores (Opcional)

En `graphics_utils.py`, línea ~50:

```python
colores_zona = {
    "Norte": "#FF6B6B",   # Cambia esto
    "Centro": "#4ECDC4",  # O esto
    "Sur": "#45B7D1"      # O esto
}
```

### 8️⃣ Agregar Nuevas Métricas

**Para agregar un nuevo KPI:**

1. Abre `propuesta1_kpis_ejecutivo_mejorado.py`
2. Ve a la sección "KPIs Principales"
3. Copia un bloque `st.metric()`
4. Modifica con tu nueva métrica

**Ejemplo:**
```python
with col_nuevo:
    st.metric(
        "📍 Mi nueva métrica",
        f"${nuevo_valor:.2f}",
        "descriptivo"
    )
```

### 9️⃣ Troubleshooting

#### ❌ "No module named 'plotly'"
```bash
pip install plotly
```

#### ❌ Las gráficas están vacías
- Verifica que el dataset tienen datos
- Asegúrate de que las columnas están bien nombradas
- Comprueba que no hay valores NaN

#### ❌ Las alertas no funcionan
- Verifica que `df_ultimos_7d` no está vacío
- Comprueba los umbrales en el código
- Asegúrate de que hay datos suficientes

#### ❌ Error de conexión con backend
- Verifica: `python main.py` está ejecutándose
- Verifica: Puerto 8000 está disponible
- Comprueba: `http://localhost:8000/docs` funciona

### 🔟 Quick Reference Card

```
╔════════════════════════════════════════════╗
║  ATAJOS RÁPIDOS                            ║
╠════════════════════════════════════════════╣
║  Exec Dash:    Decisiones estratégicas    ║
║  Op Dash:      Monitoreo diario            ║
║  Matriz:       Consultar tarifas           ║
║                                            ║
║  Insights:     Automáticos en tiempo real  ║
║  Alertas:      Basadas en umbrales        ║
║  Proyecciones: 14 días predichos          ║
║                                            ║
║  Heatmap:      Zoom → Hover → Exportar    ║
║  Líneas:       Interactive zoom ready     ║
║  Tablas:       Descargable                │
╚════════════════════════════════════════════╝
```

---

## 📌 CHECKLIST FINAL

- [ ] Dependencias necesarias instaladas (`pip install ...`)
- [ ] Backend ejecutándose (`python main.py` en terminal)
- [ ] Dashboard Ejecutivo testeado
- [ ] Dashboard Operacional testeado  
- [ ] Matriz tarifaria testeada
- [ ] Insights mostrándose correctamente
- [ ] Alerts configuradas según necesidad
- [ ] Acceso remoto configurado (si aplica)
- [ ] Equipo entrenado en uso de dashboards
- [ ] Backups del JSON realizados

---

**¿Preguntas?** Consulta `GUIA_MEJORAS_GRAFICAS.md` para documentación completa.

**Listo para continuar?** Ejecuta: `streamlit run propuesta1_kpis_ejecutivo_mejorado.py`

**Estado**: ✅ COMPLETADO - Ready to use
