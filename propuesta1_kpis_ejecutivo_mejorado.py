"""
DASHBOARD EJECUTIVO MEJORADO: KPIs Tarifas Spot México
Visión estratégica con inteligencia automática de insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from graphics_utils import InsightGenerator, GraphicsLibrary
except ImportError:
    pass

# Simular datos históricos
def generar_datos_historicos():
    """Genera dataset simulado de tarifas spot últimos 6 meses"""
    zonas = ["Norte", "Centro", "Sur"]
    equipos = ["Caja Seca", "Plataforma", "Refrigerado", "Full"]
    
    datos = []
    fecha_inicio = datetime.now() - timedelta(days=180)
    
    np.random.seed(42)  # Para reproducibilidad
    
    for i in range(180):
        fecha = fecha_inicio + timedelta(days=i)
        for zona in zonas:
            for equipo in equipos:
                base = {"Norte": 0.45, "Centro": 0.42, "Sur": 0.38}[zona]
                factor_equipo = {"Caja Seca": 1.0, "Plataforma": 1.15, "Refrigerado": 1.35, "Full": 1.25}[equipo]
                
                # Agregar tendencia
                tendencia = (i / 180) * 0.05
                noise = np.random.normal(0, 0.02)
                tarifa = base * factor_equipo * (1 + tendencia) + noise
                
                datos.append({
                    'fecha': fecha,
                    'semana': fecha.isocalendar()[1],
                    'mes': fecha.strftime('%Y-%m'),
                    'zona': zona,
                    'equipo': equipo,
                    'tarifa': max(tarifa, 0.2),
                    'demanda': np.random.randint(3, 10),
                    'volatilidad': np.random.normal(0, 1.5)
                })
    
    return pd.DataFrame(datos)

def main():
    st.set_page_config(page_title="📊 Dashboard Ejecutivo - Tarifas Spot", layout="wide")
    
    # Tema
    st.markdown("""
    <style>
        .header-principal {
            background: linear-gradient(135deg, #1A365D 0%, #4A90E2 100%);
            padding: 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 30px;
        }
        .insight-box {
            background: rgba(74, 144, 226, 0.1);
            border-left: 4px solid #4A90E2;
            padding: 12px;
            border-radius: 6px;
            margin: 8px 0;
            font-size: 0.95em;
        }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Encabezado
    st.markdown("""
    <div class="header-principal">
        <h1>📊 Dashboard Ejecutivo</h1>
        <p>Tarifas Spot México - Inteligencia de Mercado</p>
        <small>Últimos 6 meses | Actualizado diariamente</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    df = generar_datos_historicos()
    df_actual = df[df['fecha'] == df['fecha'].max()]
    df_ultimos_30d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=30)]
    df_ultimos_7d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=7)]
    
    # ========================================================================
    # SECCIÓN 1: KPIs PRINCIPALES
    # ========================================================================
    st.markdown("## 💰 KPIs Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Tarifa Promedio General
    tarifa_prom_actual = df_actual['tarifa'].mean()
    tarifa_prom_30d_ant = df[df['fecha'] < df['fecha'].max() - timedelta(days=30)].groupby(pd.Grouper(key='fecha', freq='D'))['tarifa'].mean().tail(30).mean()
    delta_tarifa = ((tarifa_prom_actual - tarifa_prom_30d_ant) / tarifa_prom_30d_ant * 100) if tarifa_prom_30d_ant > 0 else 0
    
    with col1:
        st.metric(
            "💵 Tarifa Promedio",
            f"${tarifa_prom_actual:.3f}/km",
            f"{delta_tarifa:+.1f}%",
            delta_color="inverse"
        )
    
    # KPI 2: Zona más cara
    zona_mas_cara_tarifa = df_actual.groupby('zona')['tarifa'].mean().max()
    zona_mas_cara = df_actual.groupby('zona')['tarifa'].mean().idxmax()
    
    with col2:
        st.metric(
            "📍 Zona Más Cara",
            f"{zona_mas_cara}",
            f"${zona_mas_cara_tarifa:.3f}/km"
        )
    
    # KPI 3: Equipo más demandado
    equipo_demanda = df_ultimos_7d.groupby('equipo')['demanda'].mean().idxmax()
    demanda_valor = df_ultimos_7d.groupby('equipo')['demanda'].mean().max()
    
    with col3:
        st.metric(
            "🚚 Equipo Top",
            f"{equipo_demanda}",
            f"Demanda: {demanda_valor:.1f}"
        )
    
    # KPI 4: Volatilidad General
    volatilidad_general = (df_ultimos_30d['tarifa'].std() / df_ultimos_30d['tarifa'].mean() * 100)
    
    with col4:
        st.metric(
            "📊 Volatilidad",
            f"{volatilidad_general:.1f}%",
            "Estabilidad: Moderada" if volatilidad_general < 10 else "Estabilidad: Alta",
            delta_color="off"
        )
    
    # ========================================================================
    # SECCIÓN 2: INSIGHTS AUTOMÁTICOS
    # ========================================================================
    st.markdown("## 🎯 Insights del Mercado")
    
    try:
        insight_gen = InsightGenerator()
        insights = []
        insights.extend(insight_gen.generate_price_insights(df_actual, df_ultimos_30d))
        insights.extend(insight_gen.generate_volatility_insights(df_ultimos_7d))
        insights.extend(insight_gen.generate_demand_insights(df_ultimos_7d))
        
        col_insight1, col_insight2, col_insight3 = st.columns(3)
        
        for idx, insight in enumerate(insights[:3]):
            with [col_insight1, col_insight2, col_insight3][idx]:
                st.markdown(f"""
                <div class="insight-box">
                    <strong>{insight['emoji']} {insight['text']}</strong>
                </div>
                """, unsafe_allow_html=True)
    except:
        pass
    
    # ========================================================================
    # SECCIÓN 3: GRÁFICAS PRINCIPALES
    # ========================================================================
    st.markdown("## 📈 Análisis de Tendencias")
    
    # Fila 1: Tendencia + Comparativa por zona
    col_trend, col_comp = st.columns(2)
    
    with col_trend:
        # Gráfica de línea: evolución por zona
        df_semanas = df_ultimos_30d.groupby(
            [pd.Grouper(key='fecha', freq='D'), 'zona']
        )['tarifa'].mean().reset_index()
        
        fig_trend = px.line(
            df_semanas,
            x='fecha',
            y='tarifa',
            color='zona',
            title="📈 Tendencia Tarifaria (Últimos 30 días)",
            labels={'tarifa': 'Tarifa (USD/km)', 'fecha': 'Fecha'},
            template='plotly_white',
            markers=True
        )
        
        fig_trend.update_traces(line=dict(width=2), marker=dict(size=5))
        fig_trend.update_layout(
            hovermode='x unified',
            height=400,
            font=dict(size=11)
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_comp:
        # Gráfica de barras: comparativa por zona
        zonas_promedio = df_actual.groupby('zona')['tarifa'].mean().sort_values(ascending=False)
        
        fig_barras = px.bar(
            x=zonas_promedio.index,
            y=zonas_promedio.values,
            title="💰 Tarifa Promedio por Zona (HOY)",
            labels={'x': 'Zona', 'y': 'Tarifa (USD/km)'},
            template='plotly_white',
            text=[f"${v:.3f}" for v in zonas_promedio.values],
            color=['#FF6B6B', '#4ECDC4', '#45B7D1'][:len(zonas_promedio)]
        )
        
        fig_barras.update_traces(textposition='outside')
        fig_barras.update_layout(
            height=400,
            showlegend=False,
            font=dict(size=11)
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
    
    # ========================================================================
    # SECCIÓN 4: MATRIZ TARIFARIA INTERACTIVA
    # ========================================================================
    st.markdown("## 🔥 Matriz Tarifaria (Zonas × Equipos)")
    
    col_matriz, col_dist = st.columns([2, 1])
    
    with col_matriz:
        # Heatmap interactivo
        pivot_actual = df_actual.pivot_table(
            values='tarifa',
            index='zona',
            columns='equipo',
            aggfunc='mean'
        )
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot_actual.values,
            x=pivot_actual.columns,
            y=pivot_actual.index,
            colorscale='RdYlGn_r',
            text=[[f"${pivot_actual.iloc[i,j]:.3f}" for j in range(len(pivot_actual.columns))] 
                  for i in range(len(pivot_actual.index))],
            texttemplate='%{text}',
            textfont={"size": 13},
            colorbar=dict(title="USD/km"),
            hovertemplate='<b>%{y}</b> | %{x}<br>Tarifa: $%{z:.4f}/km<extra></extra>'
        ))
        
        fig_heatmap.update_layout(
            title="Tarifas Spot Actuales",
            height=400,
            template='plotly_white',
            xaxis_title="Tipo de Equipo",
            yaxis_title="Zona"
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col_dist:
        st.markdown("### 📊 Rangos de Tarifa")
        
        for zona in pivot_actual.index:
            min_tarifa = pivot_actual.loc[zona].min()
            max_tarifa = pivot_actual.loc[zona].max()
            rango = max_tarifa - min_tarifa
            
            st.markdown(f"""
            <div class="metric-card">
                <strong>{zona}</strong><br>
                Min: ${min_tarifa:.3f}<br>
                Max: ${max_tarifa:.3f}<br>
                <span style="color: #4A90E2; font-weight: bold;">Rango: ${rango:.3f}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # SECCIÓN 5: ANÁLISIS POR EQUIPO
    # ========================================================================
    st.markdown("## 🚛 Análisis por Tipo de Equipo")
    
    col_box, col_scatter = st.columns(2)
    
    with col_box:
        # Box plot: distribución de precios por equipo
        fig_box = px.box(
            df_ultimos_30d,
            x='equipo',
            y='tarifa',
            title="📦 Distribución de Precios por Equipo",
            template='plotly_white',
            points='outliers'
        )
        
        fig_box.update_layout(height=400)
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col_scatter:
        # Scatter: demanda vs tarifa
        fig_scatter = px.scatter(
            df_ultimos_7d,
            x='demanda',
            y='tarifa',
            color='zona',
            size='demanda',
            hover_data=['equipo'],
            title="📍 Demanda vs Tarifa (7 días)",
            template='plotly_white'
        )
        
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # ========================================================================
    # SECCIÓN 6: TABLA DE DATOS DETALLADA
    # ========================================================================
    st.markdown("## 📋 Datos Detallados")
    
    with st.expander("📌 Ver tabla completa de tarifas actuales", expanded=False):
        tabla_actual = df_actual.groupby(['zona', 'equipo']).agg({
            'tarifa': ['mean', 'min', 'max', 'std'],
            'demanda': 'mean'
        }).round(4)
        
        tabla_actual.columns = ['Promedio', 'Mínimo', 'Máximo', 'Desv. Est.', 'Demanda']
        
        st.dataframe(tabla_actual, use_container_width=True)
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        <p>FreightMetrics MVP | Dashboard Ejecutivo</p>
        <p>Datos actualizados: {} | Período: Últimos 6 meses</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
