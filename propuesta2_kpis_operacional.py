"""
PROPUESTA 2: KPIs Dashboard Operacional
Control diario y análisis técnico de tarifas spot México
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy import stats

# Simular datos históricos
def generar_datos_historicos():
    """Genera dataset simulado de tarifas spot últimos 6 meses"""
    zonas = ["Norte", "Centro", "Sur"]
    equipos = ["Caja Seca", "Plataforma", "Refrigerado", "Full"]
    
    datos = []
    fecha_inicio = datetime.now() - timedelta(days=180)
    
    for i in range(180):
        fecha = fecha_inicio + timedelta(days=i)
        for zona in zonas:
            for equipo in equipos:
                base = {"Norte": 0.45, "Centro": 0.42, "Sur": 0.38}[zona]
                factor_equipo = {"Caja Seca": 1.0, "Plataforma": 1.15, "Refrigerado": 1.35, "Full": 1.25}[equipo]
                noise = np.random.normal(0, 0.02)
                tarifa = base * factor_equipo + noise
                
                datos.append({
                    'fecha': fecha,
                    'semana': fecha.isocalendar()[1],
                    'mes': fecha.strftime('%Y-%m'),
                    'zona': zona,
                    'equipo': equipo,
                    'tarifa_usd_km': max(tarifa, 0.2),
                    'demanda': np.random.randint(3, 10),
                    'variacion_dia': np.random.normal(0, 1.5)
                })
    
    return pd.DataFrame(datos)

def calcular_volatilidad(datos):
    """Calcula coeficiente de variación (volatilidad)"""
    return (datos.std() / datos.mean() * 100) if datos.mean() > 0 else 0

def pronosticar_tendencia(df_zona_equipo):
    """Proyecta tendencia usando regresión lineal"""
    df_zona_equipo = df_zona_equipo.sort_values('fecha')
    X = np.arange(len(df_zona_equipo)).reshape(-1, 1)
    y = df_zona_equipo['tarifa_usd_km'].values
    
    # Regresión lineal simple
    slope = (np.mean(X.flatten() * y) - np.mean(X.flatten()) * np.mean(y)) / np.var(X.flatten())
    intercept = np.mean(y) - slope * np.mean(X.flatten())
    
    # Generar proyección para próximos 14 días
    X_future = np.arange(len(df_zona_equipo), len(df_zona_equipo) + 14).reshape(-1, 1)
    y_pred = slope * X_future.flatten() + intercept
    
    return y_pred, slope

def main():
    st.set_page_config(page_title="📊 Tarifas Spot MXN - Operacional", layout="wide")
    
    st.markdown("# 📊 Dashboard Operacional: Tarifas Spot México")
    st.markdown("*Control detallado y análisis técnico para operadores*")
    st.markdown("---")
    
    df = generar_datos_historicos()
    df_actual = df[df['fecha'] == df['fecha'].max()]
    df_ultimos_30 = df[df['fecha'] >= df['fecha'].max() - timedelta(days=30)]
    
    # FILTROS
    st.sidebar.markdown("### 🔧 Controles")
    zona_sel = st.sidebar.selectbox("Zona", ["Todas"] + list(df['zona'].unique()))
    equipo_sel = st.sidebar.selectbox("Equipo", ["Todos"] + list(df['equipo'].unique()))
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if zona_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['zona'] == zona_sel]
    if equipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_sel]
    
    # ============================================================================
    # KPI 1: TARIFA ACTUAL vs HISTÓRICA
    # ============================================================================
    st.markdown("### 📌 Tarifa Actual vs Histórica")
    
    tarifa_hoy = df_filtrado[df_filtrado['fecha'] == df['fecha'].max()]['tarifa_usd_km'].mean()
    tarifa_promedio_30 = df_filtrado[df_filtrado['fecha'] >= df['fecha'].max() - timedelta(days=30)]['tarifa_usd_km'].mean()
    tarifa_max_30 = df_filtrado[df_filtrado['fecha'] >= df['fecha'].max() - timedelta(days=30)]['tarifa_usd_km'].max()
    tarifa_min_30 = df_filtrado[df_filtrado['fecha'] >= df['fecha'].max() - timedelta(days=30)]['tarifa_usd_km'].min()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Tarifa HOY", f"${tarifa_hoy:.3f}/km", "USD/km", delta_color="off")
    with col2:
        st.metric("📈 Promedio 30d", f"${tarifa_promedio_30:.3f}/km")
    with col3:
        st.metric("⬆️ Máximo 30d", f"${tarifa_max_30:.3f}/km")
    with col4:
        st.metric("⬇️ Mínimo 30d", f"${tarifa_min_30:.3f}/km")
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 2: GRÁFICOS DE BARRAS AGRUPADAS (Zona × Equipo)
    # ============================================================================
    st.markdown("### 📊 Comparativa de Tarifas: Zona × Equipo")
    
    df_comparativa = df_actual.copy()
    
    fig_barras = px.bar(
        df_comparativa,
        x='zona',
        y='tarifa_usd_km',
        color='equipo',
        barmode='group',
        title='Tarifas por Zona y Tipo de Equipo',
        labels={'tarifa_usd_km': 'Tarifa (USD/km)', 'zona': 'Zona'},
        template='plotly_white',
        color_discrete_map={
            'Caja Seca': '#FF6B6B',
            'Plataforma': '#4ECDC4',
            'Refrigerado': '#45B7D1',
            'Full': '#FFA07A'
        }
    )
    fig_barras.update_traces(
        hovertemplate='<b>%{x}</b><br>%{fullData.name}<br>Tarifa: $%{y:.3f}/km<extra></extra>'
    )
    fig_barras.update_layout(height=400, hovermode='x unified')
    
    st.plotly_chart(fig_barras, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 3: VOLATILIDAD Y RIESGO
    # ============================================================================
    st.markdown("### 📉 Volatilidad por Zona (Últimos 30 días)")
    
    volatilidad_data = []
    for zona in df['zona'].unique():
        df_zona = df_ultimos_30[df_ultimos_30['zona'] == zona]['tarifa_usd_km']
        vol = calcular_volatilidad(df_zona)
        volatilidad_data.append({'zona': zona, 'volatilidad': vol})
    
    vol_df = pd.DataFrame(volatilidad_data).sort_values('volatilidad', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    colores_vol = {'Norte': '#FF6B6B', 'Centro': '#4ECDC4', 'Sur': '#45B7D1'}
    
    for idx, (_, row) in enumerate(vol_df.iterrows()):
        with [col1, col2, col3][idx]:
            riesgo = "🔴 ALTO" if row['volatilidad'] > 15 else "🟡 MEDIO" if row['volatilidad'] > 10 else "🟢 BAJO"
            color_riesgo = "#ff6b6b" if row['volatilidad'] > 15 else "#ffd43b" if row['volatilidad'] > 10 else "#51cf66"
            
            st.markdown(f"""
            <div style='background: {color_riesgo}; color: white; padding: 15px; border-radius: 10px; text-align: center;'>
            <b>{row['zona']}</b><br>
            Coef. Variación: <span style='font-size: 20px;'>{row['volatilidad']:.1f}%</span><br>
            {riesgo}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 4: PROYECCIÓN DE TENDENCIA
    # ============================================================================
    st.markdown("### 🔮 Proyección de Tendencia (Próximas 2 semanas)")
    
    df_proyeccion = df_filtrado.tail(60).copy()
    y_pred, slope = pronosticar_tendencia(df_proyeccion)
    
    # Datos históricos
    df_hist = df_proyeccion.sort_values('fecha')
    fechas_hist = pd.date_range(start=df_hist['fecha'].min(), periods=len(df_hist), freq='D')
    
    # Datos proyectados
    fechas_fut = pd.date_range(start=df_hist['fecha'].max() + timedelta(days=1), periods=14, freq='D')
    
    # Crear figura
    fig_proyeccion = go.Figure()
    
    # Línea histórica
    fig_proyeccion.add_trace(go.Scatter(
        x=fechas_hist,
        y=df_hist['tarifa_usd_km'].values,
        mode='lines',
        name='Histórico',
        line=dict(color='#4ECDC4', width=3),
        hovertemplate='Fecha: %{x|%d-%m}<br>Tarifa: $%{y:.3f}/km<extra></extra>'
    ))
    
    # Línea proyectada
    fig_proyeccion.add_trace(go.Scatter(
        x=fechas_fut,
        y=y_pred,
        mode='lines',
        name='Proyección',
        line=dict(color='#FF6B6B', width=2, dash='dash'),
        hovertemplate='Proyección: $%{y:.3f}/km<extra></extra>'
    ))
    
    # Banda de confianza
    intervalo = np.std(df_hist['tarifa_usd_km'].values) * 0.5
    fig_proyeccion.add_trace(go.Scatter(
        x=list(fechas_fut) + list(fechas_fut)[::-1],
        y=list(y_pred + intervalo) + list(y_pred - intervalo)[::-1],
        fill='toself',
        name='Intervalo ±1σ',
        fillcolor='rgba(255,107,107,0.2)',
        line_color='rgba(255,255,255,0)',
        hoverinfo='skip'
    ))
    
    fig_proyeccion.update_layout(
        title='Histórico + Proyección (60 días pasados + 14 días futuros)',
        hovermode='x unified',
        height=400,
        template='plotly_white',
        xaxis_title='Fecha',
        yaxis_title='Tarifa (USD/km)',
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_proyeccion, use_container_width=True)
    
    # Interpretación
    tendencia_str = "📈 ALCISTA" if slope > 0.0001 else "📉 BAJISTA" if slope < -0.0001 else "➡️ ESTABLE"
    color_tendencia = "#ff6b6b" if slope > 0.0001 else "#51cf66" if slope < -0.0001 else "#6B7280"
    
    st.markdown(f"""
    <div style='background: {color_tendencia}; color: white; padding: 10px; border-radius: 8px; text-align: center;'>
    <b>Tendencia proyectada: {tendencia_str}</b> | Pendiente: {slope:.6f} USD/km/día
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 5: TABLA INTERACTIVA FILTRADA
    # ============================================================================
    st.markdown("### 📋 Datos Detallados (Últimos 30 días)")
    
    df_tabla = df_ultimos_30.copy()
    df_tabla['fecha_formatted'] = df_tabla['fecha'].dt.strftime('%Y-%m-%d')
    df_tabla['tarifa_formatted'] = df_tabla['tarifa_usd_km'].apply(lambda x: f"${x:.3f}")
    
    # Ordenar por fecha descendente
    df_tabla = df_tabla.sort_values('fecha', ascending=False)
    
    # Seleccionar columnas para mostrar
    cols_display = ['fecha_formatted', 'zona', 'equipo', 'tarifa_formatted', 'demanda', 'variacion_dia']
    cols_names = ['Fecha', 'Zona', 'Equipo', 'Tarifa', 'Demanda (1-10)', 'Variación Día (%)']
    
    # DataEditor interactivo
    st.dataframe(
        df_tabla[cols_display].rename(columns=dict(zip(cols_display, cols_names))),
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Botón descargar
    csv = df_tabla[cols_display].to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"tarifas_spot_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.markdown("*Datos actualizados a las: {}*".format(datetime.now().strftime('%Y-%m-%d %H:%M')))

if __name__ == "__main__":
    main()
