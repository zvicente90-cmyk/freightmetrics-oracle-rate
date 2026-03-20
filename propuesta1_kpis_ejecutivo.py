"""
PROPUESTA 1: KPIs Dashboard Ejecutivo
Visión estratégica del mercado de tarifas spot México
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Simular datos históricos (luego conectar a BD real)
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
                # Tarifas base por zona
                base = {"Norte": 0.45, "Centro": 0.42, "Sur": 0.38}[zona]
                # Factor por equipo
                factor_equipo = {"Caja Seca": 1.0, "Plataforma": 1.15, "Refrigerado": 1.35, "Full": 1.25}[equipo]
                # Variación aleatoria (tendencia)
                noise = np.random.normal(0, 0.02)
                tarifa = base * factor_equipo + noise
                
                datos.append({
                    'fecha': fecha,
                    'semana': fecha.isocalendar()[1],
                    'mes': fecha.strftime('%Y-%m'),
                    'zona': zona,
                    'equipo': equipo,
                    'tarifa_usd_km': max(tarifa, 0.2),  # Min 0.2 USD/km
                    'demanda': np.random.randint(3, 10),
                    'variacion_dia': np.random.normal(0, 1.5)
                })
    
    return pd.DataFrame(datos)

def main():
    st.set_page_config(page_title="📊 Tarifas Spot MXN - Ejecutivo", layout="wide")
    
    # Título
    st.markdown("# 📊 Dashboard Ejecutivo: Tarifas Spot México")
    st.markdown("*Inteligencia de mercado para decisiones estratégicas*")
    st.markdown("---")
    
    # Cargar datos
    df = generar_datos_historicos()
    df_actual = df[df['fecha'] == df['fecha'].max()]
    df_mes_anterior = df[df['mes'] == (datetime.now() - timedelta(days=30)).strftime('%Y-%m')]
    
    # ============================================================================
    # KPI 1: TARIFA PROMEDIO POR ZONA (4 CARDS)
    # ============================================================================
    st.markdown("### 💰 Tarifa Promedio Actual (USD/km)")
    
    zonas_data = df_actual.groupby('zona')['tarifa_usd_km'].mean().sort_values(ascending=False)
    
    cols = st.columns(4)
    colores = {"Norte": "#FF6B6B", "Centro": "#4ECDC4", "Sur": "#45B7D1"}
    
    for idx, (zona, tarifa) in enumerate(zonas_data.items()):
        with cols[idx % 4]:
            # Calcular cambio respecto mes anterior
            tarifa_mes_ant = df_mes_anterior[df_mes_anterior['zona'] == zona]['tarifa_usd_km'].mean()
            cambio_pct = ((tarifa - tarifa_mes_ant) / tarifa_mes_ant * 100) if tarifa_mes_ant > 0 else 0
            
            delta_color = "🔴" if cambio_pct > 0 else "🟢" if cambio_pct < 0 else "⚪"
            
            st.metric(
                label=f"🌍 {zona}",
                value=f"${tarifa:.3f}",
                delta=f"{delta_color} {cambio_pct:+.1f}%"
            )
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 2: GRÁFICO DE LÍNEA - EVOLUCIÓN HISTÓRICA
    # ============================================================================
    st.markdown("### 📈 Evolución por Zona (Últimos 6 meses)")
    
    # Agrupar por semana
    df_semanas = df.groupby(['semana', 'zona'])['tarifa_usd_km'].mean().reset_index()
    
    fig_linea = px.line(
        df_semanas,
        x='semana',
        y='tarifa_usd_km',
        color='zona',
        markers=True,
        title="Tendencia de Tarifas",
        labels={'tarifa_usd_km': 'Tarifa (USD/km)', 'semana': 'Semana'},
        color_discrete_map=colores,
        template='plotly_white'
    )
    fig_linea.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata[0]}</b><br>Semana %{x}<br>Tarifa: $%{y:.3f}/km<extra></extra>',
        customdata=df_semanas[['zona']].values
    )
    fig_linea.update_layout(
        hovermode='x unified',
        height=400,
        font=dict(size=12)
    )
    
    st.plotly_chart(fig_linea, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 3: MATRIZ DE CALOR - ZONAS × EQUIPOS
    # ============================================================================
    st.markdown("### 🔥 Matriz de Calor: Zonas × Equipos (Tarifa Actual)")
    
    pivot_actual = df_actual.pivot_table(
        values='tarifa_usd_km',
        index='zona',
        columns='equipo',
        aggfunc='mean'
    )
    
    # Calcular variación respecto mes anterior
    pivot_mes_ant = df_mes_anterior.pivot_table(
        values='tarifa_usd_km',
        index='zona',
        columns='equipo',
        aggfunc='mean'
    )
    
    variacion = ((pivot_actual - pivot_mes_ant) / pivot_mes_ant * 100).fillna(0)
    
    # Crear anotaciones con cambio %
    anotaciones = []
    for i, zona in enumerate(pivot_actual.index):
        for j, equipo in enumerate(pivot_actual.columns):
            valor = pivot_actual.iloc[i, j]
            cambio = variacion.iloc[i, j]
            anotaciones.append(dict(
                x=j, y=i,
                text=f"${valor:.2f}<br>({cambio:+.1f}%)",
                showarrow=False,
                font=dict(color='white', size=11)
            ))
    
    fig_calor = go.Figure(data=go.Heatmap(
        z=pivot_actual.values,
        x=pivot_actual.columns,
        y=pivot_actual.index,
        colorscale='RdYlGn_r',
        text=[[f"${pivot_actual.iloc[i,j]:.2f}" for j in range(len(pivot_actual.columns))] 
              for i in range(len(pivot_actual.index))],
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title="USD/km"),
        hovertemplate='%{y}<br>%{x}<br>Tarifa: $%{z:.3f}/km<extra></extra>'
    ))
    
    fig_calor.update_layout(
        height=300,
        template='plotly_white',
        xaxis_title="Tipo de Equipo",
        yaxis_title="Zona",
    )
    
    st.plotly_chart(fig_calor, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 4: CAMBIOS DESTACADOS (TOP 3)
    # ============================================================================
    st.markdown("### ⚡ Cambios Significativos (Últimos 7 días)")
    
    df_7dias = df[df['fecha'] >= df['fecha'].max() - timedelta(days=7)]
    cambios = df_7dias.groupby(['zona', 'equipo']).agg({
        'tarifa_usd_km': ['first', 'last'],
        'demanda': 'mean'
    }).reset_index()
    
    cambios.columns = ['zona', 'equipo', 'tarifa_ini', 'tarifa_fin', 'demanda_promedio']
    cambios['cambio_pct'] = ((cambios['tarifa_fin'] - cambios['tarifa_ini']) / cambios['tarifa_ini'] * 100)
    cambios = cambios.sort_values('cambio_pct', key=abs, ascending=False).head(3)
    
    cols = st.columns(3)
    for idx, (_, row) in enumerate(cambios.iterrows()):
        with cols[idx]:
            emoji = "🔴" if row['cambio_pct'] > 0 else "🟢"
            color = "#ff6b6b" if row['cambio_pct'] > 0 else "#51cf66"
            
            st.markdown(f"""
            <div style='background: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center;'>
            <b>{emoji} {row['zona']} - {row['equipo']}</b><br>
            ${row['tarifa_ini']:.2f} → ${row['tarifa_fin']:.2f}<br>
            <span style='font-size: 18px; font-weight: bold;'>{row['cambio_pct']:+.1f}%</span><br>
            <span style='font-size: 11px;'>Demanda: {row['demanda_promedio']:.1f}/10</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================================================
    # KPI 5: BRECHA VS DAT USA
    # ============================================================================
    st.markdown("### 💡 Posicionamiento vs DAT USA")
    
    dat_referencia = {"Caja Seca": 0.245, "Plataforma": 0.294, "Refrigerado": 0.287, "Full": 0.270}
    
    cols = st.columns(4)
    for idx, (equipo, tarifa_dat) in enumerate(dat_referencia.items()):
        with cols[idx]:
            tarifa_mxn = df_actual[df_actual['equipo'] == equipo]['tarifa_usd_km'].mean()
            brecha_pct = ((tarifa_mxn - tarifa_dat) / tarifa_dat * 100)
            
            if brecha_pct > 20:
                estatus = "🔴 CARO"
                color = "#ff6b6b"
            elif brecha_pct > 10:
                estatus = "🟡 ALTO"
                color = "#ffd43b"
            else:
                estatus = "🟢 COMP."
                color = "#51cf66"
            
            st.markdown(f"""
            <div style='background: {color}; color: white; padding: 12px; border-radius: 8px; text-align: center;'>
            <b>{equipo}</b><br>
            MXN: ${tarifa_mxn:.3f} | DAT: ${tarifa_dat:.3f}<br>
            <span style='font-size: 16px; font-weight: bold;'>{estatus}</span><br>
            {brecha_pct:+.1f}%
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("*Datos actualizados a las: {}*".format(datetime.now().strftime('%Y-%m-%d %H:%M')))

if __name__ == "__main__":
    main()
