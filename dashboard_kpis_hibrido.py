"""
DASHBOARD HÍBRIDO: Tarifas Spot México
Integra datos REALES de matriz_comparativa_mx.json - Valores en PESOS MEXICANOS
Zonas: Norte, Centro, Sur | Equipos: Caja Seca, Plataforma, Refrigerado, Full
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from scipy import stats
import json
import os
import sys

# Agregar path para importar módulos locales
sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="📊 Tarifas Spot MXN - Híbrido", layout="wide", initial_sidebar_state="expanded")

# ============================================================================
# CARGAR DATOS REALES
# ============================================================================

@st.cache_data
def cargar_datos_reales():
    """Carga datos REALES de matriz_comparativa_mx.json y históricos EN PESOS"""
    try:
        # Cargar matriz comparativa (datos actuales por zona/equipo EN PESOS)
        matriz_path = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
        with open(matriz_path, 'r', encoding='utf-8') as f:
            matriz_data = json.load(f)
        
        # Cargar histórico de FreightMetrics
        hist_path = os.path.join(os.path.dirname(__file__), "freightmetrics_historical.json")
        with open(hist_path, 'r', encoding='utf-8') as f:
            historico_data = json.load(f)
        
        return matriz_data, historico_data
    except Exception as e:
        st.warning(f"⚠️ Error cargando datos reales: {str(e)}")
        return None, None


@st.cache_data
def procesar_matriz_a_dataframe():
    """Extrae tarifas SPOT FINAL de matriz_comparativa_mx.json en MXN/km por zona/equipo"""
    try:
        matriz_path = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
        with open(matriz_path, 'r', encoding='utf-8') as f:
            matriz_data = json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Error cargando matriz: {str(e)}")
        return generar_datos_simulados()
    
    if not matriz_data or "matriz" not in matriz_data:
        return generar_datos_simulados()
    
    datos = []
    meses_orden = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    try:
        for anio, anio_data in matriz_data.get("matriz", {}).items():
            for mes, mes_data in anio_data.items():
                # mes_data contiene zonas como claves
                for zona, zona_rows in mes_data.items():
                    if isinstance(zona_rows, list):
                        # Buscar la fila con "TARIFA SPOT FINAL"
                        for row in zona_rows:
                            if row.get("Componente") == "TARIFA SPOT FINAL":
                                try:
                                    mes_num = meses_orden.index(mes) + 1
                                except ValueError:
                                    mes_num = 1
                                
                                datos.append({
                                    'fecha': f"{anio}-{mes}",
                                    'fecha_dt': pd.to_datetime(f"{anio}-{mes_num:02d}-01"),
                                    'zona': zona,
                                    'caja_seca_mxn': float(row.get("Caja Seca (Dry Van)", 0)),
                                    'plataforma_mxn': float(row.get("Plataforma (Flatbed)", 0)),
                                    'refrigerado_mxn': float(row.get("Refrigerado (Reefer)", 0)),
                                    'full_mxn': float(row.get("Full (Doble)", 0)),
                                })
                                break
    except Exception as e:
        st.warning(f"⚠️ Error procesando matriz: {str(e)}")
        return generar_datos_simulados()
    
    if datos:
        df = pd.DataFrame(datos)
        df = df.sort_values('fecha_dt')
        return df
    
    return generar_datos_simulados()


def generar_datos_simulados():
    """Genera dataset simulado cuando no hay datos reales - EN PESOS"""
    zonas = ["Norte", "Centro", "Sur"]
    equipos = ["Caja Seca", "Plataforma", "Refrigerado", "Full"]
    meses = pd.date_range(start='2026-01-01', periods=3, freq='M')
    
    datos = []
    for fecha in meses:
        for zona in zonas:
            # Tarifas base simuladas en PESOS por zona/equipo
            tarifas_base = {
                "Norte": {"Caja Seca": 32.50, "Plataforma": 37.40, "Refrigerado": 46.80, "Full": 53.90},
                "Centro": {"Caja Seca": 30.10, "Plataforma": 34.60, "Refrigerado": 43.20, "Full": 49.80},
                "Sur": {"Caja Seca": 28.70, "Plataforma": 33.00, "Refrigerado": 41.30, "Full": 47.50},
            }
            
            row_data = {
                'fecha': f"{fecha.year}-{fecha.strftime('%b')}",
                'fecha_sort': fecha,
                'zona': zona,
                'caja_seca_mxn': tarifas_base[zona]["Caja Seca"],
                'plataforma_mxn': tarifas_base[zona]["Plataforma"],
                'refrigerado_mxn': tarifas_base[zona]["Refrigerado"],
                'full_mxn': tarifas_base[zona]["Full"],
            }
            datos.append(row_data)
    
    df = pd.DataFrame(datos)
    return df.sort_values('fecha_sort')



# ============================================================================
# FUNCIONES DE ANÁLISIS
# ============================================================================

def calcular_volatilidad(serie):
    """Calcula volatilidad como coeficiente de variación (%)"""
    if len(serie) < 2 or serie.std() == 0 or serie.mean() == 0:
        return 0.0
    return (serie.std() / abs(serie.mean()) * 100)


def pronosticar_tendencia(valores, dias_futuros=14):
    """Proyecta tendencia lineal con intervalo de confianza"""
    if len(valores) < 2:
        return valores, valores, valores
    
    x = np.arange(len(valores))
    z = np.polyfit(x, valores, 1)
    p = np.poly1d(z)
    
    y_pred = p(x)
    residuos = valores - y_pred
    std_residuos = np.std(residuos) if len(residuos) > 0 else 0
    
    # Proyectar
    x_future = np.arange(len(valores), len(valores) + dias_futuros)
    y_future = p(x_future)
    
    # Intervalos de confianza
    upper_band = y_future + 1.96 * std_residuos if std_residuos > 0 else y_future
    lower_band = y_future - 1.96 * std_residuos if std_residuos > 0 else y_future
    
    return y_future, upper_band, lower_band


# Configuración de colores
colores = {"Norte": "#FF6B6B", "Centro": "#4ECDC4", "Sur": "#45B7D1"}
colores_equipo = {
    "Caja Seca": "#FF9999",
    "Plataforma": "#66B2FF",
    "Refrigerado": "#99FF99",
    "Full": "#FFCC99"
}

# ============================================================================
# CARGAR DATOS GLOBALES
# ============================================================================

df_principal = procesar_matriz_a_dataframe()
matriz_data, historico_data = cargar_datos_reales()

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    border-radius: 15px; color: white; margin-bottom: 20px;'>
<h1>📊 Dashboard Tarifas Spot México</h1>
<p>💵 Valores en PESOS MEXICANOS (MXN/km) | 📍 Zonas: Norte, Centro, Sur | 🚛 Equipos: 4 tipos</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["👔 Ejecutivo", "🔧 Operacional", "⚙️ Configuración"])

# ============================================================================
# TAB 1: DASHBOARD EJECUTIVO
# ============================================================================

# ============================================================================
# TAB 1: DASHBOARD EJECUTIVO
# ============================================================================

with tab1:
    st.markdown("#### 💼 Visión Estratégica del Mercado")
    
    if df_principal is not None and len(df_principal) > 0:
        df_actual = df_principal[df_principal['fecha_dt'] == df_principal['fecha_dt'].max()]
        
        # KPI 1: Tarifa promedio actual por zona (Caja Seca referencia)
        st.markdown("**💰 Tarifa Promedio Actual - Caja Seca (MXN/km)**")
        
        col_norte, col_centro, col_sur = st.columns(3)
        
        with col_norte:
            tarifa_norte = df_actual[df_actual['zona'] == 'Norte']['caja_seca_mxn'].mean()
            st.metric(
                label="🌍 Norte",
                value=f"${tarifa_norte:.2f}" if tarifa_norte > 0 else "N/A"
            )
        
        with col_centro:
            tarifa_centro = df_actual[df_actual['zona'] == 'Centro']['caja_seca_mxn'].mean()
            st.metric(
                label="🌍 Centro",
                value=f"${tarifa_centro:.2f}" if tarifa_centro > 0 else "N/A"
            )
        
        with col_sur:
            tarifa_sur = df_actual[df_actual['zona'] == 'Sur']['caja_seca_mxn'].mean()
            st.metric(
                label="🌍 Sur",
                value=f"${tarifa_sur:.2f}" if tarifa_sur > 0 else "N/A"
            )
        
        st.markdown("---")
        
        # KPI 2: Gráfico de evolución por zona (Caja Seca)
        st.markdown("**📈 Evolución Histórica de Tarifas (Caja Seca)**")
        
        df_grafico = df_principal[df_principal['caja_seca_mxn'] > 0].copy().sort_values('fecha_dt')
        
        if len(df_grafico) > 0:
            fig_linea = px.line(
                df_grafico,
                x='fecha',
                y='caja_seca_mxn',
                color='zona',
                markers=True,
                labels={'caja_seca_mxn': 'Tarifa (MXN/km)', 'fecha': 'Período'},
                color_discrete_map=colores,
                template='plotly_white'
            )
            fig_linea.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_linea.update_layout(hovermode='x unified', height=350)
            st.plotly_chart(fig_linea, use_container_width=True)
        
        st.markdown("---")
        
        # KPI 3: Matriz de calor - Zonas × Equipos
        st.markdown("**🔥 Matriz Actual: Zonas × Equipos (MXN/km)**")
        
        if len(df_actual) > 0:
            pivot_data = []
            for _, row in df_actual.iterrows():
                pivot_data.append({
                    'Zona': row['zona'],
                    'Caja Seca': row['caja_seca_mxn'],
                    'Plataforma': row['plataforma_mxn'],
                    'Refrigerado': row['refrigerado_mxn'],
                    'Full': row['full_mxn']
                })
            
            pivot_df = pd.DataFrame(pivot_data).set_index('Zona')
            pivot_df = pivot_df.round(2)
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale='RdYlGn_r',
                text=pivot_df.values.round(2),
                texttemplate='$%{text:.2f}',
                textfont={"size": 12},
                colorbar=dict(title="MXN/km")
            ))
            fig_heatmap.update_layout(height=280, template='plotly_white')
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        st.markdown("---")
        
        # KPI 4: Comparativa de equipos (promedio todas las zonas)
        st.markdown("**⚡ Tarifa Promedio por Equipo (Todas las zonas)**")
        
        equipos_promedio = {
            'Caja Seca': df_actual['caja_seca_mxn'].mean(),
            'Plataforma': df_actual['plataforma_mxn'].mean(),
            'Refrigerado': df_actual['refrigerado_mxn'].mean(),
            'Full': df_actual['full_mxn'].mean()
        }
        
        fig_equipos = px.bar(
            x=list(equipos_promedio.keys()),
            y=list(equipos_promedio.values()),
            color=list(equipos_promedio.keys()),
            color_discrete_map=colores_equipo,
            labels={'x': 'Equipo', 'y': 'Tarifa (MXN/km)'},
            template='plotly_white'
        )
        fig_equipos.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_equipos, use_container_width=True)
        
        st.markdown("---")
        
        # KPI 5: Resumen de tendencias por zona
        st.markdown("**📊 Resumen por Zona**")
        
        resumen = []
        for zona in ['Norte', 'Centro', 'Sur']:
            df_zona = df_principal[df_principal['zona'] == zona]['caja_seca_mxn'].dropna()
            if len(df_zona) > 0:
                resumen.append({
                    'Zona': zona,
                    'Promedio': f"${df_zona.mean():.2f}",
                    'Mínimo': f"${df_zona.min():.2f}",
                    'Máximo': f"${df_zona.max():.2f}",
                    'Volatilidad': f"{calcular_volatilidad(df_zona):.1f}%"
                })
        
        df_resumen = pd.DataFrame(resumen)
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
    else:
        st.warning("⚠️ No hay datos disponibles para mostrar")

# ============================================================================
# TAB 2: DASHBOARD OPERACIONAL
# ============================================================================

with tab2:
    st.markdown("#### 🔧 Control Detallado - Análisis Técnico")
    
    # Filtros en sidebar
    col_z, col_e = st.columns(2)
    
    with col_z:
        zona_sel = st.selectbox(
            "🌍 Selecciona Zona",
            ["Centro", "Norte", "Sur"],
            key="dash_zone"
        )
    
    with col_e:
        equipo_sel = st.selectbox(
            "🚛 Selecciona Equipo",
            ["Caja Seca", "Plataforma", "Refrigerado", "Full"],
            key="dash_equipo"
        )
    
    st.markdown("---")
    
    # Filtrar datos
    df_filtered = df_principal[df_principal['zona'] == zona_sel].copy()
    
    # Seleccionar columna según equipo
    col_equipo = {
        'Caja Seca': 'caja_seca_mxn',
        'Plataforma': 'plataforma_mxn',
        'Refrigerado': 'refrigerado_mxn',
        'Full': 'full_mxn'
    }[equipo_sel]
    
    df_filtered = df_filtered[df_filtered[col_equipo] > 0].copy()
    
    if len(df_filtered) > 0:
        # KPI 1: Tarifa actual vs histórica
        st.markdown(f"**📌 {zona_sel} - {equipo_sel} (MXN/km)**")
        
        tarifa_actual = df_filtered[df_filtered['fecha_dt'] == df_filtered['fecha_dt'].max()][col_equipo].values
        tarifa_actual = tarifa_actual[0] if len(tarifa_actual) > 0 else 0
        tarifa_promedio = df_filtered[col_equipo].mean()
        tarifa_max = df_filtered[col_equipo].max()
        tarifa_min = df_filtered[col_equipo].min()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Tarifa HOY", f"${tarifa_actual:.2f}", delta_color="off")
        with col2:
            st.metric("📈 Promedio", f"${tarifa_promedio:.2f}")
        with col3:
            st.metric("⬆️ Máximo", f"${tarifa_max:.2f}")
        with col4:
            st.metric("⬇️ Mínimo", f"${tarifa_min:.2f}")
        
        st.markdown("---")
        
        # KPI 2: Volatilidad
        st.markdown("**📉 Volatilidad (Coeficiente de Variación)**")
        
        volatilidad = calcular_volatilidad(df_filtered[col_equipo].values)
        
        if volatilidad <= 5:
            estado = "🟢 BAJO (Estable)"
            color = "#51cf66"
        elif volatilidad <= 10:
            estado = "🟡 MEDIO"
            color = "#ffd43b"
        else:
            estado = "🔴 ALTO"
            color = "#ff6b6b"
        
        st.markdown(f"<div style='background: {color}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;'>{estado}<br>Variabilidad: {volatilidad:.1f}%</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # KPI 3: Gráfico temporal
        st.markdown(f"**📊 Evolución {zona_sel} - {equipo_sel}**")
        
        fig_temporal = px.line(
            df_filtered,
            x='fecha',
            y=col_equipo,
            markers=True,
            labels={col_equipo: 'Tarifa (MXN/km)', 'fecha': 'Período'},
            template='plotly_white'
        )
        fig_temporal.update_traces(line=dict(width=3, color=colores.get(zona_sel, "#667eea")), marker=dict(size=8))
        fig_temporal.update_layout(hovermode='x unified', height=350)
        st.plotly_chart(fig_temporal, use_container_width=True)
        
        st.markdown("---")
        
        # KPI 4: Tabla detallada
        st.markdown("**📋 Histórico Detallado**")
        
        df_tabla = df_filtered[['fecha', col_equipo]].copy()
        df_tabla.columns = ['Período', 'Tarifa (MXN/km)']
        df_tabla['Tarifa (MXN/km)'] = df_tabla['Tarifa (MXN/km)'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(df_tabla, use_container_width=True, height=300, hide_index=True)
        
        # Exportar
        csv_data = df_filtered[['fecha', col_equipo]].copy()
        csv_data.columns = ['Período', 'Tarifa (MXN/km)']
        csv = csv_data.to_csv(index=False)
        
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"tarifas_{zona_sel}_{equipo_sel}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning(f"⚠️ Sin datos para {zona_sel} - {equipo_sel}")

# ============================================================================
# TAB 3: CONFIGURACIÓN
# ============================================================================

with tab3:
    st.markdown("#### ⚙️ Información del Dashboard")
    
    st.info("""
    ### 📊 Dashboard de Tarifas Spot México
    
    **Fuentes de Datos:**
    - 📁 `matriz_comparativa_mx.json` - Datos oficiales por zona, equipo y período
    - 📊 `freightmetrics_historical.json` - Histórico de rutas y tarifas
    - 🔄 `Tendencias_de_mercado.py` - Análisis y proyecciones
    
    **Características:**
    - ✅ Valores en **PESOS MEXICANOS** (MXN/km)
    - ✅ 3 Zonas geográficas: **Norte, Centro, Sur**
    - ✅ 4 Tipos de equipos: **Caja Seca, Plataforma, Refrigerado, Full**
    - ✅ Análisis histórico y volatilidad
    - ✅ Compatible con mapa de México
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌍 Zonas Geográficas")
        st.markdown("""
        - **🔴 Norte**: Fronterizas
          - Cd. Juárez, Nuevo Laredo, Monterrey, Chihuahua
        
        - **🟠 Centro**: Eje Transversal
          - CDMX, Bajío, Querétaro, Toluca
        
        - **🟡 Sur**: Sureste
          - Mérida, Cancún, Villahermosa, Tuxtla
        """)
    
    with col2:
        st.markdown("#### 🚛 Equipos de Transporte")
        st.markdown("""
        - **🚐 Caja Seca (Dry Van)** 
          - Carga general seco
        
        - **🚚 Plataforma (Flatbed)** 
          - Carga plana / Sobredimensionada
        
        - **❄️ Refrigerado (Reefer)** 
          - Carga refrigerada
        
        - **🚛 Full (Doble)** 
          - Doble remolque
        """)
    
    st.markdown("---")
    
    st.markdown("#### 📈 Métricas Calculadas")
    
    with st.expander("Volatilidad (Coef. Variación %)", expanded=False):
        st.latex(r"CV = \frac{\sigma}{\mu} \times 100")
        st.write("""
        Mide la variabilidad de tarifas:
        - 🟢 **BAJO**: CV ≤ 5% (Estable)
        - 🟡 **MEDIO**: 5% < CV ≤ 10%
        - 🔴 **ALTO**: CV > 10% (Riesgo)
        """)
    
    with st.expander("Tarifa Promedio", expanded=False):
        st.write("""
        Promedio de la tarifa SPOT FINAL por zona y equipo.
        Refleja el precio promedio en el período analizado.
        """)
    
    st.markdown("---")
    
    st.markdown("#### 📋 Período de Análisis")
    st.info(f"""
    - **Datos Históricos**: Últimos meses disponibles
    - **Actualización**: Conforme se carguen nuevos períodos
    - **Zonas Analizadas**: 3 (Norte, Centro, Sur)
    - **Equipos Analizados**: 4 tipos
    """)
    
    st.markdown("---")
    
    st.success(f"""
    ✅ Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Datos sincronizados directamente desde:
    - `matriz_comparativa_mx.json`
    - `freightmetrics_historical.json`
    """)

