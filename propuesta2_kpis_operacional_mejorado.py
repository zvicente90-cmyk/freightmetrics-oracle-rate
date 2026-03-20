"""
DASHBOARD OPERACIONAL MEJORADO: Análisis técnico y control detallado
Control diario con predicciones y análisis avanzado
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy import stats
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Simular datos históricos
def generar_datos_historicos():
    """Genera dataset simulado de tarifas spot últimos 6 meses"""
    zonas = ["Norte", "Centro", "Sur"]
    equipos = ["Caja Seca", "Plataforma", "Refrigerado", "Full"]
    
    datos = []
    fecha_inicio = datetime.now() - timedelta(days=180)
    
    np.random.seed(42)
    
    for i in range(180):
        fecha = fecha_inicio + timedelta(days=i)
        for zona in zonas:
            for equipo in equipos:
                base = {"Norte": 0.45, "Centro": 0.42, "Sur": 0.38}[zona]
                factor_equipo = {"Caja Seca": 1.0, "Plataforma": 1.15, "Refrigerado": 1.35, "Full": 1.25}[equipo]
                
                tendencia = (i / 180) * 0.05
                noise = np.random.normal(0, 0.02)
                tarifa = base * factor_equipo * (1 + tendencia) + noise
                
                datos.append({
                    'fecha': fecha,
                    'dia_semana': fecha.strftime('%A'),
                    'semana': fecha.isocalendar()[1],
                    'mes': fecha.strftime('%Y-%m'),
                    'zona': zona,
                    'equipo': equipo,
                    'tarifa': max(tarifa, 0.2),
                    'demanda': np.random.randint(3, 10),
                    'disponibilidad': np.random.uniform(0.4, 0.95),
                    'volatilidad': abs(np.random.normal(0, 1.5))
                })
    
    return pd.DataFrame(datos)

def calcular_volatilidad(datos):
    """Calcula coeficiente de variación"""
    return (datos.std() / datos.mean() * 100) if datos.mean() > 0 else 0

def calcular_tendencia(df_zona_equipo):
    """Proyecta tendencia usando regresión lineal"""
    df_zona_equipo = df_zona_equipo.sort_values('fecha').reset_index(drop=True)
    
    if len(df_zona_equipo) < 2:
        return None, None
    
    X = np.arange(len(df_zona_equipo)).reshape(-1, 1)
    y = df_zona_equipo['tarifa'].values
    
    # Regresión lineal
    slope = (np.mean(X.flatten() * y) - np.mean(X.flatten()) * np.mean(y)) / (np.var(X.flatten()) + 1e-10)
    intercept = np.mean(y) - slope * np.mean(X.flatten())
    
    # Proyección 14 días
    X_future = np.arange(len(df_zona_equipo), len(df_zona_equipo) + 14).reshape(-1, 1)
    y_pred = slope * X_future.flatten() + intercept
    
    return y_pred, slope

def main():
    st.set_page_config(page_title="📊 Dashboard Operacional - Tarifas Spot", layout="wide")
    
    # Estilos
    st.markdown("""
    <style>
        .alert-danger { background: #FFE5E5; border-left: 4px solid #FF6B6B; padding: 10px; border-radius: 6px; }
        .alert-warning { background: #FFF5E5; border-left: 4px solid #FFA500; padding: 10px; border-radius: 6px; }
        .alert-info { background: #E5F2FF; border-left: 4px solid #4A90E2; padding: 10px; border-radius: 6px; }
        .alert-success { background: #E5FFE5; border-left: 4px solid #51CF66; padding: 10px; border-radius: 6px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Encabezado
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A365D 0%, #4A90E2 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h1>📊 Dashboard Operacional</h1>
        <p>Tarifas Spot México - Control Técnico Diario</p>
        <small>Análisis detallado para operadores | Predicciones a 14 días</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    df = generar_datos_historicos()
    df_actual = df[df['fecha'] == df['fecha'].max()]
    df_ultimos_7d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=7)]
    df_ultimos_30d = df[df['fecha'] >= df['fecha'].max() - timedelta(days=30)]
    
    # CONTROLES LATERALES
    st.sidebar.markdown("## 🔧 Filtros")
    zona_sel = st.sidebar.selectbox("Zona", ["Todas"] + list(df['zona'].unique()))
    equipo_sel = st.sidebar.selectbox("Equipo", ["Todos"] + list(df['equipo'].unique()))
    
    # Filtrar datos según selección
    df_filtrado = df_ultimos_30d.copy()
    
    if zona_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['zona'] == zona_sel]
    if equipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_sel]
    
    # ========================================================================
    # SECCIÓN 1: STATUS ACTUAL
    # ========================================================================
    st.markdown("## ⚡ Status Actual")
    
    df_actual_filtrado = df_actual.copy()
    if zona_sel != "Todas":
        df_actual_filtrado = df_actual_filtrado[df_actual_filtrado['zona'] == zona_sel]
    if equipo_sel != "Todos":
        df_actual_filtrado = df_actual_filtrado[df_actual_filtrado['equipo'] == equipo_sel]
    
    if not df_actual_filtrado.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        tarifa_actual = df_actual_filtrado['tarifa'].mean()
        tarifa_7d_ant = df_ultimos_7d[df_ultimos_7d['fecha'] < df_ultimos_7d['fecha'].max() - timedelta(days=1)]['tarifa'].mean()
        cambio_7d = ((tarifa_actual - tarifa_7d_ant) / tarifa_7d_ant * 100) if tarifa_7d_ant > 0 else 0
        
        with col1:
            st.metric(
                "💵 Tarifa HOY",
                f"${tarifa_actual:.4f}/km",
                f"{cambio_7d:+.2f}% vs 7 días",
                delta_color="inverse"
            )
        
        demanda_actual = df_actual_filtrado['demanda'].mean()
        disponibilidad = df_actual_filtrado['disponibilidad'].mean() * 100
        volatilidad = calcular_volatilidad(df_ultimos_7d['tarifa'])
        
        with col2:
            st.metric(
                "🚚 Demanda",
                f"{demanda_actual:.1f}",
                "Alta" if demanda_actual > 6 else "Moderada" if demanda_actual > 4 else "Baja"
            )
        
        with col3:
            st.metric(
                "📦 Disponibilidad",
                f"{disponibilidad:.1f}%",
                "Activa" if disponibilidad > 70 else "Limitada"
            )
        
        with col4:
            st.metric(
                "📊 Volatilidad",
                f"{volatilidad:.2f}%",
                "Alta" if volatilidad > 10 else "Moderada" if volatilidad > 5 else "Baja"
            )
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 2: ALERTAS OPERACIONALES
    # ========================================================================
    st.markdown("## ⚠️ Alertas Operacionales")
    
    alertas = []
    
    # Analizar volatilidad
    volatilidad_actual = calcular_volatilidad(df_ultimos_7d['tarifa'])
    if volatilidad_actual > 12:
        alertas.append(("danger", f"🔴 VOLATILIDAD ALTA: {volatilidad_actual:.1f}% - Considerar estrategia de cobertura"))
    elif volatilidad_actual > 8:
        alertas.append(("warning", f"🟠 Volatilidad moderada-alta: {volatilidad_actual:.1f}% - Monitorear cambios"))
    
    # Analizar demanda
    demanda_promedio_7d = df_ultimos_7d['demanda'].mean()
    if demanda_promedio_7d > 7:
        alertas.append(("warning", "🟠 DEMANDA ELEVADA - Oportunidad de ajuste de precios"))
    
    # Analizar disponibilidad
    disponibilidad_promedio = df_ultimos_7d['disponibilidad'].mean()
    if disponibilidad_promedio < 0.5:
        alertas.append(("danger", f"🔴 DISPONIBILIDAD CRÍTICA: {disponibilidad_promedio*100:.0f}% - Problemas de flujo"))
    
    if alertas:
        for tipo_alerta, mensaje in alertas:
            st.markdown(f'<div class="alert-{tipo_alerta}">{mensaje}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ Sin alertas críticas - Sistema operativo</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 3: ANÁLISIS TÉCNICO DETALLADO
    # ========================================================================
    st.markdown("## 📈 Análisis Técnico")
    
    col_linea, col_predictivo = st.columns(2)
    
    with col_linea:
        # Gráfica con bandas de volatilidad
        df_resumen = df_filtrado.groupby(pd.Grouper(key='fecha', freq='D')).agg({
            'tarifa': ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        df_resumen.columns = ['fecha', 'promedio', 'std', 'min', 'max']
        df_resumen['banda_sup'] = df_resumen['promedio'] + (df_resumen['std'] * 1.5)
        df_resumen['banda_inf'] = df_resumen['promedio'] - (df_resumen['std'] * 1.5)
        
        fig_bandas = go.Figure()
        
        # Bandas de Bollinger
        fig_bandas.add_trace(go.Scatter(
            x=df_resumen['fecha'],
            y=df_resumen['banda_sup'],
            fill=None,
            mode='lines',
            name='Banda Superior',
            line=dict(color='rgba(74,144,226,0)', width=0),
            showlegend=False
        ))
        
        fig_bandas.add_trace(go.Scatter(
            x=df_resumen['fecha'],
            y=df_resumen['banda_inf'],
            fill='tonexty',
            mode='lines',
            name='Banda Inferior',
            line=dict(color='rgba(74,144,226,0)', width=0),
            fillcolor='rgba(74,144,226,0.2)',
            showlegend=False
        ))
        
        # Línea promedio
        fig_bandas.add_trace(go.Scatter(
            x=df_resumen['fecha'],
            y=df_resumen['promedio'],
            mode='lines+markers',
            name='Promedio',
            line=dict(color='#4A90E2', width=3),
            marker=dict(size=5)
        ))
        
        fig_bandas.update_layout(
            title="📊 Bandas de Bollinger (Últimos 30 días)",
            height=400,
            hovermode='x unified',
            template='plotly_white',
            xaxis_title="Fecha",
            yaxis_title="Tarifa (USD/km)"
        )
        
        st.plotly_chart(fig_bandas, use_container_width=True)
    
    with col_predictivo:
        # Proyección de tendencia
        if not df_filtrado.empty:
            df_filtrado_sort = df_filtrado.sort_values('fecha')
            y_pred, slope = calcular_tendencia(df_filtrado_sort)
            
            if y_pred is not None:
                # Crear figura
                fecha_actual = df_filtrado_sort['fecha'].max()
                fechas_futuras = [fecha_actual + timedelta(days=x) for x in range(14)]
                
                fig_pred = go.Figure()
                
                # Datos históricos (últimos 7 días)
                df_hist = df_filtrado_sort.tail(7).groupby('fecha')['tarifa'].mean().reset_index()
                
                fig_pred.add_trace(go.Scatter(
                    x=df_hist['fecha'],
                    y=df_hist['tarifa'],
                    mode='lines+markers',
                    name='Histórico',
                    line=dict(color='#4A90E2', width=2),
                    marker=dict(size=8)
                ))
                
                # Proyección
                fig_pred.add_trace(go.Scatter(
                    x=fechas_futuras,
                    y=y_pred,
                    mode='lines+markers',
                    name='Proyección (14 días)',
                    line=dict(color='#FF6B6B', width=2, dash='dash'),
                    marker=dict(size=6)
                ))
                
                # Anotación de tendencia
                tendencia_texto = f"Tendencia: {'+' if slope > 0 else ''}{slope*100:.2f}% por día"
                color_tendencia = '#FF6B6B' if slope > 0 else '#51CF66'
                
                fig_pred.update_layout(
                    title="🔮 Proyección de Precios (14 días)",
                    height=400,
                    hovermode='x unified',
                    template='plotly_white',
                    xaxis_title="Fecha",
                    yaxis_title="Tarifa Proyectada (USD/km)",
                    annotations=[dict(
                        text=tendencia_texto,
                        x=0.5, y=1.08,
                        xref='paper', yref='paper',
                        showarrow=False,
                        font=dict(size=12, color=color_tendencia)
                    )]
                )
                
                st.plotly_chart(fig_pred, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 6: ANÁLISIS DE DIESEL EN TIEMPO REAL
    # ========================================================================
    st.markdown("## ⛽ Costo de Diesel en Tiempo Real")
    
    if DieselPricesAPI:
        try:
            # Obtener precios actuales
            precios_diesel, fuente = get_cached_diesel_prices()
            df_historico_diesel = get_cached_historical_prices(30)
            
            # Fila 1: KPIs de Diesel
            col_diesel1, col_diesel2, col_diesel3, col_diesel4 = st.columns(4)
            
            with col_diesel1:
                precio_promedio = precios_diesel.get("promedio_nacional", 0)
                st.metric(
                    "⛽ Precio Nacional",
                    f"${precio_promedio:.2f}/L",
                    f"Fuente: {fuente}"
                )
            
            # Precio por zona
            precio_norte = precios_diesel.get("norte", 0)
            precio_centro = precios_diesel.get("centro", 0)
            precio_sur = precios_diesel.get("sur", 0)
            
            with col_diesel2:
                st.metric(
                    "🌍 Norte",
                    f"${precio_norte:.2f}/L",
                    f"vs Nacional: {((precio_norte/precio_promedio-1)*100):+.1f}%"
                )
            
            with col_diesel3:
                st.metric(
                    "🌍 Centro",
                    f"${precio_centro:.2f}/L",
                    f"vs Nacional: {((precio_centro/precio_promedio-1)*100):+.1f}%"
                )
            
            with col_diesel4:
                st.metric(
                    "🌍 Sur",
                    f"${precio_sur:.2f}/L",
                    f"vs Nacional: {((precio_sur/precio_promedio-1)*100):+.1f}%"
                )
            
            st.markdown("---")
            
            # Fila 2: Gráficas
            col_grafica_diesel, col_comparativa_diesel = st.columns(2)
            
            with col_grafica_diesel:
                # Gráfica lineal de precios históricos por zona
                fig_diesel_linea = px.line(
                    df_historico_diesel,
                    x='dia',
                    y='precio',
                    color='zona',
                    title="📈 Tendencia de Diesel (Últimos 30 días)",
                    labels={'precio': 'Precio (MXN/L)', 'dia': 'Fecha'},
                    template='plotly_white',
                    markers=True
                )
                
                fig_diesel_linea.update_traces(line=dict(width=2), marker=dict(size=5))
                fig_diesel_linea.update_layout(hovermode='x unified', height=400)
                
                st.plotly_chart(fig_diesel_linea, use_container_width=True)
            
            with col_comparativa_diesel:
                # Gráfica de barras: Precio actual vs Promedio 30 días
                zonas_datos = []
                
                for zona in ["norte", "centro", "sur"]:
                    precio_actual = precios_diesel.get(zona, 0)
                    df_zona = df_historico_diesel[df_historico_diesel["zona"] == zona.capitalize()]
                    promedio_30d = df_zona["precio"].mean()
                    
                    zonas_datos.append({
                        "zona": zona.capitalize(),
                        "Precio Actual": precio_actual,
                        "Promedio 30d": promedio_30d
                    })
                
                df_comparativa = pd.DataFrame(zonas_datos)
                
                fig_comparativa = go.Figure(data=[
                    go.Bar(name='Precio Actual', x=df_comparativa["zona"], y=df_comparativa["Precio Actual"], marker_color='#FF6B6B'),
                    go.Bar(name='Promedio 30d', x=df_comparativa["zona"], y=df_comparativa["Promedio 30d"], marker_color='#4ECDC4')
                ])
                
                fig_comparativa.update_layout(
                    title="💰 Precio Actual vs Promedio 30 Días",
                    height=400,
                    barmode='group',
                    template='plotly_white',
                    xaxis_title="Zona",
                    yaxis_title="Precio (MXN/L)"
                )
                
                st.plotly_chart(fig_comparativa, use_container_width=True)
            
            st.markdown("---")
            
            # Impacto en Costos de Operación
            st.markdown("## 💳 Impacto en Costos de Operación")
            
            col_impacto1, col_impacto2, col_impacto3 = st.columns(3)
            
            # Estimaciones de costo para rutas típicas
            distancia_norte = 1000  # km
            distancia_centro = 500
            distancia_sur = 800
            consumo = 0.25  # L/km
            
            calculo_norte = DieselPricesAPI.estimate_fuel_cost(distancia_norte, consumo)
            calculo_centro = DieselPricesAPI.estimate_fuel_cost(distancia_centro, consumo)
            calculo_sur = DieselPricesAPI.estimate_fuel_cost(distancia_sur, consumo)
            
            with col_impacto1:
                st.markdown(f"""
                <div style="background: #E5F2FF; border-left: 4px solid #4A90E2; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta Tipo Norte</strong><br>
                    Distancia: {distancia_norte} km<br>
                    <code>Consumo: {calculo_norte['litros_necesarios']:.1f}L</code><br>
                    <strong style="color: #FF6B6B; font-size: 1.3em;">${calculo_norte['costo_total_mxn']:.2f} MXN</strong><br>
                    <small>Por km: ${calculo_norte['costo_por_km']:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_impacto2:
                st.markdown(f"""
                <div style="background: #E5F2FF; border-left: 4px solid #4ECDC4; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta Tipo Centro</strong><br>
                    Distancia: {distancia_centro} km<br>
                    <code>Consumo: {calculo_centro['litros_necesarios']:.1f}L</code><br>
                    <strong style="color: #4ECDC4; font-size: 1.3em;">${calculo_centro['costo_total_mxn']:.2f} MXN</strong><br>
                    <small>Por km: ${calculo_centro['costo_por_km']:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_impacto3:
                st.markdown(f"""
                <div style="background: #E5F2FF; border-left: 4px solid #45B7D1; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta Tipo Sur</strong><br>
                    Distancia: {distancia_sur} km<br>
                    <code>Consumo: {calculo_sur['litros_necesarios']:.1f}L</code><br>
                    <strong style="color: #45B7D1; font-size: 1.3em;">${calculo_sur['costo_total_mxn']:.2f} MXN</strong><br>
                    <small>Por km: ${calculo_sur['costo_por_km']:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Insights de Diesel
            st.markdown("---")
            st.markdown("## 📌 Insights de Diesel")
            
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                # Comparativa actual vs promedio
                promedio_nacional_30d = df_historico_diesel.groupby('zona')['precio'].mean().mean()
                cambio_nacional = ((precio_promedio - promedio_nacional_30d) / promedio_nacional_30d * 100) if promedio_nacional_30d > 0 else 0
                
                if cambio_nacional > 3:
                    st.markdown(f'<div class="alert-warning">🔴 DIESEL CARO: +{cambio_nacional:.1f}% vs promedio 30d<br>Considera estrategia de combustible</div>', unsafe_allow_html=True)
                elif cambio_nacional < -3:
                    st.markdown(f'<div class="alert-success">🟢 OPORTUNIDAD: {cambio_nacional:.1f}% vs promedio 30d<br>Buen momento para abastecer</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-info">→ ESTABLE: {cambio_nacional:+.1f}% vs promedio 30d<br>Precios dentro de rango normal</div>', unsafe_allow_html=True)
            
            with col_insight2:
                # Diferencia entre zonas
                diferencia_zonas = precio_norte - precio_sur
                zona_mas_cara = "Norte" if precio_norte > precio_sur else "Sur"
                zona_mas_barata = "Sur" if precio_norte > precio_sur else "Norte"
                
                st.markdown(f"""
                <div class="alert-info">
                    <strong>📍 Diferencia Regional</strong><br>
                    {zona_mas_cara} es ${abs(diferencia_zonas):.2f}/L más caro que {zona_mas_barata}<br>
                    <em>Impacto en viajes de {distancia_norte}km: ${abs(diferencia_zonas) * consumo * distancia_norte:.2f}</em>
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error en módulo de Diesel: {e}")
    else:
        st.info("⚠️ Módulo de Diesel no disponible. Instala diesel_prices.py")
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 4: MATRIZ COMPARATIVA DETALLADA
    # ========================================================================
    st.markdown("## 🔥 Matriz Comparativa (Últimos 7 días vs 30 días)")
    
    col_m7, col_m30 = st.columns(2)
    
    for col, datos, titulo in [(col_m7, df_ultimos_7d, "7 DÍAS"), (col_m30, df_ultimos_30d, "30 DÍAS")]:
        with col:
            pivot = datos.pivot_table(
                values='tarifa',
                index='zona',
                columns='equipo',
                aggfunc='mean'
            )
            
            fig_hm = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='RdYlGn_r',
                text=[[f"${pivot.iloc[i,j]:.3f}" for j in range(len(pivot.columns))] 
                      for i in range(len(pivot.index))],
                texttemplate='%{text}',
                textfont={"size": 11},
                colorbar=dict(title="USD/km")
            ))
            
            fig_hm.update_layout(
                title=f"Matriz Tarifaria - Últimos {titulo}",
                height=300,
                template='plotly_white'
            )
            
            st.plotly_chart(fig_hm, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 5: RANKING Y ANÁLISIS
    # ========================================================================
    st.markdown("## 🏆 Rankings y Análisis")
    
    col_rank1, col_rank2, col_rank3 = st.columns(3)
    
    with col_rank1:
        st.markdown("### 💰 Equipos Más Caros")
        equipo_prices = df_ultimos_7d.groupby('equipo')['tarifa'].mean().sort_values(ascending=False)
        for idx, (equipo, tarifa) in enumerate(equipo_prices.items(), 1):
            st.markdown(f"**{idx}. {equipo}** - ${tarifa:.4f}/km")
    
    with col_rank2:
        st.markdown("### 🔄 Mayor Volatilidad")
        equipo_vol = df_ultimos_7d.groupby('equipo')['tarifa'].apply(
            lambda x: (x.std() / x.mean() * 100) if x.mean() > 0 else 0
        ).sort_values(ascending=False)
        for idx, (equipo, vol) in enumerate(equipo_vol.items(), 1):
            st.markdown(f"**{idx}. {equipo}** - {vol:.2f}%")
    
    with col_rank3:
        st.markdown("### 📊 Mayor Demanda")
        demanda_rank = df_ultimos_7d.groupby('equipo')['demanda'].mean().sort_values(ascending=False)
        for idx, (equipo, dem) in enumerate(demanda_rank.items(), 1):
            st.markdown(f"**{idx}. {equipo}** - {dem:.1f} promedio")
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.85em;">
        <p>FreightMetrics MVP | Dashboard Operacional</p>
        <p>Última actualización: {} | Período análisis: 6 meses</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
