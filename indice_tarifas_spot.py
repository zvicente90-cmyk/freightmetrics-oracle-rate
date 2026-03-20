import streamlit as st
import pandas as pd
from pdf_generator import dataframe_to_pdf
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de página para usar todo el ancho disponible
st.set_page_config(
    page_title="FreightMetrics - Índice Spot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.markdown("### Tendencia de Tarifas Spot Freightmetrics Mexico")
    st.caption("Somos el primer sistema en informar sobre mercado de las tarifas spot en Mexico.")
    import json, os
    matriz_file = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
    try:
        with open(matriz_file, "r", encoding="utf-8") as f:
            matriz_data = json.load(f)
        # Filtros organizados en una fila
        col1, col2, col3 = st.columns(3)
        
        with col1:
            anios = list(matriz_data["matriz"].keys())
            anio_sel = st.selectbox("Año de referencia", anios, index=anios.index("2026") if "2026" in anios else 0)
        
        with col2:
            meses = list(matriz_data["matriz"][anio_sel].keys())
            mes_sel = st.selectbox("Mes de referencia", meses, index=meses.index("Mar") if "Mar" in meses else 0)
        
        with col3:
            equipos = ["Dry Van - Carga seca general", "Flatbed - Carga plana", "Reefer - Carga refrigerada", "Doble Articulado/ Full"]
            equipo_sel = st.selectbox("Equipo", equipos, index=0)
            
            # Mapear nombres del UI a nombres del JSON
            mapeo_equipos = {
                "Dry Van - Carga seca general": "Caja Seca (Dry Van)",
                "Flatbed - Carga plana": "Plataforma (Flatbed)", 
                "Reefer - Carga refrigerada": "Refrigerado (Reefer)",
                "Doble Articulado/ Full": "Full (Doble)"
            }
            equipo_json = mapeo_equipos.get(equipo_sel, "Caja Seca (Dry Van)")
            
        zonas = list(matriz_data["matriz"][anio_sel][mes_sel].keys())
        
        # Mapa interactivo de México con tarifas spot (estilo DAT mejorado)
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Coordenadas aproximadas de las zonas de México
        zonas_coords = {
            "Norte": {"lat": 28.6353, "lon": -106.0889, "name": "Norte"},
            "Centro": {"lat": 19.4326, "lon": -99.1332, "name": "Centro"},
            "Sur": {"lat": 16.7569, "lon": -93.1292, "name": "Sur"}
        }
        
        # Obtener tarifas por zona basándose en filtros seleccionados
        tarifas_data = []
        tarifas_valores = []
        zonas_sin_datos = []
        
        for zona in zonas_coords.keys():
            try:
                # Verificar que la zona existe en los datos
                if zona not in matriz_data["matriz"][anio_sel][mes_sel]:
                    zonas_sin_datos.append(zona)
                    st.warning(f"⚠️ No hay datos para {zona} en {mes_sel} {anio_sel}")
                    continue
                    
                matriz_z = pd.DataFrame(matriz_data["matriz"][anio_sel][mes_sel][zona])
                
                # Verificar que existe la tarifa final para el equipo seleccionado
                tarifa_final_rows = matriz_z[matriz_z["Componente"] == "TARIFA SPOT FINAL"]
                if tarifa_final_rows.empty:
                    st.warning(f"⚠️ No se encontró TARIFA SPOT FINAL para {zona}")
                    continue
                    
                if equipo_json not in tarifa_final_rows.columns:
                    st.warning(f"⚠️ No hay datos para {equipo_sel} en {zona}")
                    continue
                    
                valor = tarifa_final_rows[equipo_json].values[0]
                
                # Validación más robusta de los valores
                if pd.isna(valor) or valor is None or valor <= 0:
                    st.warning(f"⚠️ Valor inválido para {zona}: {valor}")
                    continue
                
                # Asegurar que el valor sea un número válido
                try:
                    valor_float = float(valor)
                    if not pd.isna(valor_float) and valor_float > 0:
                        tarifas_data.append({
                            "zona": zona,
                            "tarifa": valor_float,
                            "lat": zonas_coords[zona]["lat"],
                            "lon": zonas_coords[zona]["lon"], 
                            "texto": f"<b>{zona}</b><br>${valor_float:.2f}/km"
                        })
                        tarifas_valores.append(valor_float)
                    else:
                        st.warning(f"⚠️ Valor NaN o inválido para {zona}: {valor}")
                except (ValueError, TypeError) as ve:
                    st.warning(f"⚠️ Error de conversión para {zona}: {valor} - {ve}")
                    continue
                
            except KeyError as e:
                st.error(f"❌ Error de estructura de datos en {zona}: {e}")
                zonas_sin_datos.append(zona)
            except Exception as e:
                st.error(f"❌ Error inesperado procesando {zona}: {e}")
                zonas_sin_datos.append(zona)
        
        # Mostrar información de depuración si no hay datos suficientes
        if not tarifas_data:
            st.error(f"❌ No se encontraron datos válidos para {equipo_sel} en {mes_sel} {anio_sel}")
            st.info("💡 Intenta seleccionar otro mes o equipo")
            return
        elif zonas_sin_datos:
            st.info(f"ℹ️ Datos no disponibles para: {', '.join(zonas_sin_datos)}")
        
        # Crear mapa con múltiples layers (estilo DAT)
        fig = go.Figure()
        
        # Layer 1: Mapa base
        fig.add_trace(go.Scattergeo(
            lon=[-102.5528],
            lat=[23.6345],
            mode='markers',
            marker=dict(size=0, opacity=0),
            showlegend=False
        ))
        
        # Layer 2: Zonas con círculos proporcionales al precio
        max_tarifa = max(tarifas_valores) if tarifas_valores else 50
        min_tarifa = min(tarifas_valores) if tarifas_valores else 30
        
        # Validar que no haya problemas con los valores
        if not tarifas_valores:
            st.error("❌ No hay valores de tarifa válidos para mostrar")
            return
            
        max_tarifa = max(tarifas_valores)
        min_tarifa = min(tarifas_valores)
        
        if max_tarifa == min_tarifa:
            # Si todas las tarifas son iguales, usar tamaño fijo
            tarifa_range = 1  # Evitar división por cero
        else:
            tarifa_range = max_tarifa - min_tarifa
        
        for data in tarifas_data:
            # Validar que la tarifa no sea NaN o None
            if data["tarifa"] is None or pd.isna(data["tarifa"]):
                continue  # Saltar este punto si la tarifa es inválida
                
            # Tamaño proporcional al precio (con validación)
            if tarifa_range == 1:  # Todas las tarifas son iguales
                size_factor = 25  # Tamaño medio fijo
            else:
                size_factor = ((data["tarifa"] - min_tarifa) / tarifa_range) * 30 + 20
            
            # Asegurar que size_factor sea válido
            if pd.isna(size_factor) or size_factor <= 0:
                size_factor = 25  # Valor por defecto
            
            # Color azul corporativo basado en precio (actualizado con rangos reales)
            if data["tarifa"] < 25:
                color = "#4A90E2"  # Azul claro corporativo - Económica
            elif data["tarifa"] < 30:
                color = "#357ABD"  # Azul medio corporativo - Moderada
            else:
                color = "#2C5F8A"  # Azul oscuro corporativo - Elevada
            
            # Círculo principal
            fig.add_trace(go.Scattergeo(
                lon=[data["lon"]],
                lat=[data["lat"]],
                mode="markers",
                marker=dict(
                    size=size_factor,
                    color=color,
                    line=dict(width=3, color='white'),
                    opacity=0.8,
                    sizemode='diameter'
                ),
                name=data["zona"],
                hovertemplate=f"<b>Zona {data['zona']}</b><br>" +
                             f"<b>Equipo:</b> {equipo_sel}<br>" +
                             f"<b>Tarifa Spot:</b> ${data['tarifa']:.2f}/km<br>" +
                             f"<b>Período:</b> {mes_sel} {anio_sel}<br>" +
                             "<extra></extra>",
                showlegend=False
            ))
            
            # Texto con tarifa
            fig.add_trace(go.Scattergeo(
                lon=[data["lon"]],
                lat=[data["lat"]],
                mode="text",
                text=[f"${data['tarifa']:.2f}"],
                textfont=dict(size=20, color="white", family="Arial Black"),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Mejorar layout estilo DAT
        fig.update_layout(
            title={
                'text': f"FreightMetrics México - Tarifas Spot {equipo_sel}<br><sub>{mes_sel} {anio_sel} | Valores en MXN/km</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#2c3e50'}
            },
            geo=dict(
                projection_type='natural earth',
                showland=True,
                landcolor="#2C5282",  # Azul ejecutivo para el fondo del mapa
                showocean=True,
                oceancolor="#1A365D",  # Azul más oscuro para océanos
                showlakes=True,
                lakecolor="#1A365D",
                showrivers=False,
                showcountries=True,
                countrycolor="#E2E8F0",  # Gris claro para fronteras país
                countrywidth=2,
                showsubunits=True,
                subunitcolor="#CBD5E0",  # Gris medio para estados
                subunitwidth=1,
                center=dict(lat=23.6345, lon=-102.5528),
                scope='north america',
                lonaxis=dict(range=[-118, -86]),
                lataxis=dict(range=[14, 33]),
                resolution=50,
                bgcolor='rgba(0,0,0,0)'
            ),
            height=700,
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=0, r=0, t=80, b=0)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Nota metodológica
        st.caption("**Nota Metodológica:** Cálculos basados en la metodología de costos de operación de la SCT, indexados con indicadores de inflación sectorial del INEGI y precios regionales de energía (CRE). FreightMetrics actúa como un agregador de datos para la toma de decisiones.")
        
        # Mostrar solo tabla resumen de tarifas spot finales con formato profesional
        st.markdown("### 💼 Tarifas Spot por Zona")
        
        # CSS para tabla profesional azul
        st.markdown("""
        <style>
        .tarifa-table {
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 8px 32px rgba(74, 144, 226, 0.2);
        }
        .tarifa-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 15px;
            margin: 8px;
            text-align: center;
            border-left: 4px solid #4A90E2;
            transition: transform 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .tarifa-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(74, 144, 226, 0.3);
        }
        .zona-titulo {
            color: #2C5F8A;
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        .tarifa-valor {
            color: #1A365D;
            font-size: 1.8em;
            font-weight: 700;
            margin: 5px 0;
        }
        .tarifa-label {
            color: #357ABD;
            font-size: 0.9em;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)
        
        resumen_tarifas = []
        for zona in ["Norte", "Centro", "Sur"]:
            try:
                # Verificar que existan datos para la zona seleccionada
                if zona not in matriz_data["matriz"][anio_sel][mes_sel]:
                    resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": "Sin datos"})
                    continue
                    
                matriz_z = pd.DataFrame(matriz_data["matriz"][anio_sel][mes_sel][zona])
                tarifa_rows = matriz_z[matriz_z["Componente"] == "TARIFA SPOT FINAL"]
                
                if tarifa_rows.empty or equipo_json not in tarifa_rows.columns:
                    resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": "N/A"})
                    continue
                    
                tarifa = tarifa_rows[equipo_json].values[0]
                if pd.isna(tarifa):
                    resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": "N/A"})
                else:
                    resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": f"${tarifa:.2f}"})
            except Exception as e:
                resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": "Error"})
        
        # Mostrar como tarjetas profesionales
        st.markdown('<div class="tarifa-table">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, tarifa in enumerate(resumen_tarifas):
            with cols[i]:
                zona = tarifa["Zona"]
                valor = tarifa["Tarifa Spot Final (MXN/km)"]
                
                # Determinar color según zona
                if zona == "Norte":
                    color_accent = "#4A90E2"
                elif zona == "Centro":
                    color_accent = "#357ABD"
                else:
                    color_accent = "#2C5F8A"
                
                st.markdown(f"""
                <div class="tarifa-card" style="border-left-color: {color_accent};">
                    <div class="zona-titulo">{zona}</div>
                    <div class="tarifa-valor">{valor}</div>
                    <div class="tarifa-label">por kilómetro</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas adicionales estilo DAT - OCULTO
        # if tarifas_valores:
        #     st.markdown("### 📈 Análisis del Mercado")
        #     
        #     # CSS para métricas profesionales
        #     st.markdown("""
        #     <style>
        #     .metric-container {
        #         background: rgba(74, 144, 226, 0.08);
        #         border-radius: 12px;
        #         padding: 15px;
        #         margin: 10px 0;
        #     }
        #     .stMetric > div {
        #         background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(226, 232, 240, 0.9) 100%);
        #         border-radius: 10px;
        #         padding: 15px;
        #         border-left: 4px solid #4A90E2;
        #         box-shadow: 0 4px 15px rgba(74, 144, 226, 0.1);
        #         transition: transform 0.2s ease;
        #     }
        #     .stMetric > div:hover {
        #         transform: translateY(-2px);
        #         box-shadow: 0 6px 20px rgba(74, 144, 226, 0.2);
        #     }
        #     .stMetric label {
        #         color: #2C5F8A !important;
        #         font-weight: 600 !important;
        #         font-size: 0.95em !important;
        #     }
        #     .stMetric [data-testid="metric-container"] > div:first-child {
        #         color: #1A365D !important;
        #         font-size: 1.8em !important;
        #         font-weight: 700 !important;
        #     }
        #     </style>
        #     """, unsafe_allow_html=True)
        #     
        #     st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        #     col1, col2, col3, col4 = st.columns(4)
        #     with col1:
        #         st.metric("💼 Tarifa Promedio", f"${sum(tarifas_valores)/len(tarifas_valores):.2f}/km")
        #     with col2:
        #         st.metric("📊 Tarifa Más Alta", f"${max(tarifas_valores):.2f}/km", f"+${max(tarifas_valores) - min(tarifas_valores):.2f}")
        #     with col3:
        #         st.metric("💰 Tarifa Más Baja", f"${min(tarifas_valores):.2f}/km")
        #     with col4:
        #         variacion = ((max(tarifas_valores) - min(tarifas_valores)) / min(tarifas_valores) * 100)
        #         st.metric("📈 Variación Nacional", f"{variacion:.1f}%")
        #     st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error cargando matriz comparativa: {e}")

    # 🆕 DASHBOARD HÍBRIDO INTEGRADO
    st.markdown("---")
    
    # Crear tabs para la página
    tabs = st.tabs(["📊 Matriz Tarifaria", "👔 Análisis Ejecutivo", "🔧 Análisis Operacional", "⛽ Costo de Diesel"])
    
    with tabs[0]:
        st.markdown("### 📊 Analisis del Mercado Spot en Mexico")
        st.info("El mercado de tarifas spot en Mexico es altamente dinamico y volatil. Las tarifas pueden variar significativamente entre zonas y tipos de carga debido a factores como la demanda, disponibilidad de equipos y condiciones del mercado. Este analisis proporciona una vision general de las tendencias actuales, permitiendo a los profesionales del autotransporte tomar decisiones informadas y estratetigas.")
        
        try:
            # Cargar datos para matriz
            matriz_path = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
            with open(matriz_path, 'r', encoding='utf-8') as f:
                matriz_data_matriz = json.load(f)
            
            # Procesar todos los datos
            df_matriz = []
            meses_orden = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            
            for anio, anio_data in matriz_data_matriz.get("matriz", {}).items():
                for mes, mes_data in anio_data.items():
                    for zona, zona_rows in mes_data.items():
                        if isinstance(zona_rows, list):
                            for row in zona_rows:
                                if row.get("Componente") == "TARIFA SPOT FINAL":
                                    try:
                                        mes_num = meses_orden.index(mes) + 1
                                    except ValueError:
                                        mes_num = 1
                                    
                                    df_matriz.append({
                                        'fecha': f"{anio}-{mes}",
                                        'fecha_dt': pd.to_datetime(f"{anio}-{mes_num:02d}-01"),
                                        'zona': zona,
                                        'caja_seca': float(row.get("Caja Seca (Dry Van)", 0)),
                                        'plataforma': float(row.get("Plataforma (Flatbed)", 0)),
                                        'refrigerado': float(row.get("Refrigerado (Reefer)", 0)),
                                        'full': float(row.get("Full (Doble)", 0)),
                                    })
                                    break
            
            if df_matriz:
                df_matriz_main = pd.DataFrame(df_matriz).sort_values('fecha_dt')
                
                # Selector de mes para matriz
                st.markdown("**Selecciona período para análisis:**")
                col_mes_sel, col_empty = st.columns([2, 8])
                with col_mes_sel:
                    fechas_unicas = df_matriz_main['fecha'].unique()
                    fecha_sel = st.selectbox("Período", fechas_unicas, index=len(fechas_unicas)-1)
                
                df_mes_sel = df_matriz_main[df_matriz_main['fecha'] == fecha_sel]
                
                if len(df_mes_sel) > 0:
                    st.markdown("---")
                    
                    # TABLA 1: Matriz de tarifas (Zonas × Equipos)
                    st.markdown(f"**📋 Matriz de Tarifas Spot - {fecha_sel} (MXN/km)**")
                    
                    matriz_pivot = df_mes_sel[['zona', 'caja_seca', 'plataforma', 'refrigerado', 'full']].copy()
                    matriz_pivot.columns = ['Zona', 'Caja Seca', 'Plataforma', 'Refrigerado', 'Full']
                    matriz_pivot = matriz_pivot.set_index('Zona')
                    
                    # Mostrar tabla con formato
                    st.dataframe(
                        matriz_pivot.round(2),
                        width='stretch',
                        height=250
                    )
                    
                    st.markdown("---")
                    
                    # GRÁFICA 1: Heatmap de matriz
                    st.markdown(f"**🔥 Mapa de Calor: Matriz Tarifaria**")
                    
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=matriz_pivot.values,
                        x=matriz_pivot.columns,
                        y=matriz_pivot.index,
                        colorscale='RdYlGn_r',
                        text=matriz_pivot.values.round(2),
                        texttemplate='$%{text:.2f}',
                        textfont={"size": 14},
                        colorbar=dict(title="MXN/km")
                    ))
                    fig_heatmap.update_layout(height=350, template='plotly_white')
                    st.plotly_chart(fig_heatmap, width='stretch')
                    
                    st.markdown("---")
                    
                    # GRÁFICA 2: Comparativa tipo de carga por zona
                    st.markdown("**📊 Comparativa por tipo de carga y por Zona**")
                    
                    df_melted = df_mes_sel[['zona', 'caja_seca', 'plataforma', 'refrigerado', 'full']].copy()
                    df_melted.columns = ['Zona', 'Caja Seca', 'Plataforma', 'Refrigerado', 'Full']
                    df_melted = df_melted.melt(id_vars=['Zona'], var_name='Equipo', value_name='Tarifa')
                    
                    fig_barras = px.bar(
                        df_melted,
                        x='Zona',
                        y='Tarifa',
                        color='Equipo',
                        barmode='group',
                        labels={'Tarifa': 'Tarifa (MXN/km)', 'Zona': 'Zona'},
                        template='plotly_white',
                        color_discrete_map={
                            'Caja Seca': '#FF9999',
                            'Plataforma': '#66B2FF',
                            'Refrigerado': '#99FF99',
                            'Full': '#FFCC99'
                        }
                    )
                    fig_barras.update_layout(height=400, hovermode='x unified')
                    st.plotly_chart(fig_barras, width='stretch')
                    
                    st.markdown("---")
                    
                    # GRÁFICA 3: Tarifa promedio por equipo
                    st.markdown("**⚡ Tarifa Promedio Nacional por Equipo**")
                    
                    promedios = {
                        'Caja Seca': df_mes_sel['caja_seca'].mean(),
                        'Plataforma': df_mes_sel['plataforma'].mean(),
                        'Refrigerado': df_mes_sel['refrigerado'].mean(),
                        'Full': df_mes_sel['full'].mean()
                    }
                    
                    fig_promedio = px.bar(
                        x=list(promedios.keys()),
                        y=list(promedios.values()),
                        labels={'x': 'Equipo', 'y': 'Tarifa (MXN/km)'},
                        text_auto='.2f',
                        template='plotly_white',
                        color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']
                    )
                    fig_promedio.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_promedio, width='stretch')
                    
                    st.markdown("---")
                    
                    # MÉTRICAS RESUMEN
                    st.markdown("**💡 Resumen de Análisis**")
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric(
                            "Tarifa Máxima",
                            f"${df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].max().max():.2f}/km",
                            "Full - Sur"
                        )
                    
                    with col_m2:
                        st.metric(
                            "Tarifa Mínima",
                            f"${df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].min().min():.2f}/km",
                            "Caja Seca - Norte"
                        )
                    
                    with col_m3:
                        variacion = ((df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].max().max() - 
                                     df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].min().min()) / 
                                    df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].min().min() * 100)
                        st.metric("Variación Total", f"{variacion:.1f}%")
                    
                    with col_m4:
                        promedio_total = df_mes_sel[['caja_seca', 'plataforma', 'refrigerado', 'full']].mean().mean()
                        st.metric("Promedio Nacional", f"${promedio_total:.2f}/km")
        
        except Exception as e:
            st.error(f"❌ Error cargando análisis de matriz: {str(e)}")
        
    with tabs[1]:
        st.markdown("#### 💼 Visión Estratégica del Mercado")
        
        try:
            # Cargar datos para ejecutivo
            matriz_path = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
            with open(matriz_path, 'r', encoding='utf-8') as f:
                matriz_data_exec = json.load(f)
            
            df_exec = []
            meses_orden = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            
            for anio, anio_data in matriz_data_exec.get("matriz", {}).items():
                for mes, mes_data in anio_data.items():
                    for zona, zona_rows in mes_data.items():
                        if isinstance(zona_rows, list):
                            for row in zona_rows:
                                if row.get("Componente") == "TARIFA SPOT FINAL":
                                    try:
                                        mes_num = meses_orden.index(mes) + 1
                                    except ValueError:
                                        mes_num = 1
                                    
                                    df_exec.append({
                                        'fecha': f"{anio}-{mes}",
                                        'fecha_dt': pd.to_datetime(f"{anio}-{mes_num:02d}-01"),
                                        'zona': zona,
                                        'caja_seca_mxn': float(row.get("Caja Seca (Dry Van)", 0)),
                                        'plataforma_mxn': float(row.get("Plataforma (Flatbed)", 0)),
                                        'refrigerado_mxn': float(row.get("Refrigerado (Reefer)", 0)),
                                        'full_mxn': float(row.get("Full (Doble)", 0)),
                                    })
                                    break
            
            if df_exec:
                df_exec_main = pd.DataFrame(df_exec).sort_values('fecha_dt')
                df_actual_exec = df_exec_main[df_exec_main['fecha_dt'] == df_exec_main['fecha_dt'].max()]
                
                # KPI 1: Tarifa promedio
                st.markdown("**💰 Tarifa Promedio Actual (MXN/km) - Caja Seca**")
                col_n, col_c, col_s = st.columns(3)
                
                colores_exec = {"Norte": "#FF6B6B", "Centro": "#4ECDC4", "Sur": "#45B7D1"}
                
                with col_n:
                    tarifa_n = df_actual_exec[df_actual_exec['zona'] == 'Norte']['caja_seca_mxn'].mean()
                    st.metric("🌍 Norte", f"${tarifa_n:.2f}" if tarifa_n > 0 else "N/A")
                with col_c:
                    tarifa_c = df_actual_exec[df_actual_exec['zona'] == 'Centro']['caja_seca_mxn'].mean()
                    st.metric("🌍 Centro", f"${tarifa_c:.2f}" if tarifa_c > 0 else "N/A")
                with col_s:
                    tarifa_s = df_actual_exec[df_actual_exec['zona'] == 'Sur']['caja_seca_mxn'].mean()
                    st.metric("🌍 Sur", f"${tarifa_s:.2f}" if tarifa_s > 0 else "N/A")
                
                st.markdown("---")
                
                # KPI 2: Evolución
                st.markdown("**📈 Evolución de Tarifas (Caja Seca)**")
                df_grafico = df_exec_main[df_exec_main['caja_seca_mxn'] > 0].copy()
                
                if len(df_grafico) > 0:
                    fig_linea = px.line(
                        df_grafico, x='fecha', y='caja_seca_mxn',
                        color='zona', markers=True,
                        labels={'caja_seca_mxn': 'Tarifa (MXN/km)', 'fecha': 'Período'},
                        color_discrete_map=colores_exec,
                        template='plotly_white'
                    )
                    fig_linea.update_traces(line=dict(width=3), marker=dict(size=8))
                    fig_linea.update_layout(hovermode='x unified', height=350)
                    st.plotly_chart(fig_linea, width='stretch')
                
                st.markdown("---")
                
                # KPI 3: Matriz de calor
                st.markdown("**🔥 Matriz Actual: Zonas × Equipos (MXN/km)**")
                if len(df_actual_exec) > 0:
                    pivot_data = []
                    for _, row in df_actual_exec.iterrows():
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
                    st.plotly_chart(fig_heatmap, width='stretch')
                
                st.markdown("---")
                
                # KPI 4: Comparativa equipos
                st.markdown("**⚡ Tarifa Promedio por Equipo**")
                equipos_prom = {
                    'Caja Seca': df_actual_exec['caja_seca_mxn'].mean(),
                    'Plataforma': df_actual_exec['plataforma_mxn'].mean(),
                    'Refrigerado': df_actual_exec['refrigerado_mxn'].mean(),
                    'Full': df_actual_exec['full_mxn'].mean()
                }
                
                colores_equipo_exec = {
                    "Caja Seca": "#FF9999",
                    "Plataforma": "#66B2FF",
                    "Refrigerado": "#99FF99",
                    "Full": "#FFCC99"
                }
                
                fig_equipos = px.bar(
                    x=list(equipos_prom.keys()),
                    y=list(equipos_prom.values()),
                    color=list(equipos_prom.keys()),
                    color_discrete_map=colores_equipo_exec,
                    labels={'x': 'Equipo', 'y': 'Tarifa (MXN/km)'},
                    template='plotly_white'
                )
                fig_equipos.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_equipos, width='stretch')
        
        except Exception as e:
            st.error(f"❌ Error cargando KPIs Ejecutivo: {str(e)}")
    
    with tabs[2]:
        st.markdown("#### 🔧 Control Operacional Detallado")
        
        try:
            # Filtros operacionales
            col_z, col_e = st.columns(2)
            
            with col_z:
                zona_sel = st.selectbox("🌍 Selecciona Zona", ["Centro", "Norte", "Sur"], key="op_zone")
            
            with col_e:
                equipo_sel = st.selectbox("🚛 Selecciona Equipo", ["Caja Seca", "Plataforma", "Refrigerado", "Full"], key="op_equipo")
            
            st.markdown("---")
            
            # Cargar datos operacionales
            matriz_path = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
            with open(matriz_path, 'r', encoding='utf-8') as f:
                matriz_data_op = json.load(f)
            
            df_op = []
            meses_orden = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            
            for anio, anio_data in matriz_data_op.get("matriz", {}).items():
                for mes, mes_data in anio_data.items():
                    for zona, zona_rows in mes_data.items():
                        if isinstance(zona_rows, list):
                            for row in zona_rows:
                                if row.get("Componente") == "TARIFA SPOT FINAL":
                                    try:
                                        mes_num = meses_orden.index(mes) + 1
                                    except ValueError:
                                        mes_num = 1
                                    
                                    df_op.append({
                                        'fecha': f"{anio}-{mes}",
                                        'fecha_dt': pd.to_datetime(f"{anio}-{mes_num:02d}-01"),
                                        'zona': zona,
                                        'caja_seca_mxn': float(row.get("Caja Seca (Dry Van)", 0)),
                                        'plataforma_mxn': float(row.get("Plataforma (Flatbed)", 0)),
                                        'refrigerado_mxn': float(row.get("Refrigerado (Reefer)", 0)),
                                        'full_mxn': float(row.get("Full (Doble)", 0)),
                                    })
                                    break
            
            df_op_main = pd.DataFrame(df_op).sort_values('fecha_dt')
            df_filtered = df_op_main[df_op_main['zona'] == zona_sel].copy()
            
            col_equipo_map = {
                'Caja Seca': 'caja_seca_mxn',
                'Plataforma': 'plataforma_mxn',
                'Refrigerado': 'refrigerado_mxn',
                'Full': 'full_mxn'
            }[equipo_sel]
            
            df_filtered = df_filtered[df_filtered[col_equipo_map] > 0].copy()
            
            if len(df_filtered) > 0:
                # KPI 1: Tarifa actual vs histórica
                st.markdown(f"**📌 {zona_sel} - {equipo_sel} (MXN/km)**")
                
                tarifa_act = df_filtered[df_filtered['fecha_dt'] == df_filtered['fecha_dt'].max()][col_equipo_map].values
                tarifa_act = tarifa_act[0] if len(tarifa_act) > 0 else 0
                tarifa_prom = df_filtered[col_equipo_map].mean()
                tarifa_max = df_filtered[col_equipo_map].max()
                tarifa_min = df_filtered[col_equipo_map].min()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Tarifa HOY", f"${tarifa_act:.2f}", delta_color="off")
                with col2:
                    st.metric("📈 Promedio", f"${tarifa_prom:.2f}")
                with col3:
                    st.metric("⬆️ Máximo", f"${tarifa_max:.2f}")
                with col4:
                    st.metric("⬇️ Mínimo", f"${tarifa_min:.2f}")
                
                st.markdown("---")
                
                # KPI 2: Volatilidad
                st.markdown("**📉 Volatilidad (Coeficiente de Variación)**")
                
                volatilidad = (df_filtered[col_equipo_map].std() / df_filtered[col_equipo_map].mean() * 100) if df_filtered[col_equipo_map].mean() > 0 else 0
                
                if volatilidad <= 5:
                    estado, color = "🟢 BAJO (Estable)", "#51cf66"
                elif volatilidad <= 10:
                    estado, color = "🟡 MEDIO", "#ffd43b"
                else:
                    estado, color = "🔴 ALTO", "#ff6b6b"
                
                st.markdown(f"<div style='background: {color}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;'>{estado}<br>Variabilidad: {volatilidad:.1f}%</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # KPI 3: Gráfico temporal
                st.markdown(f"**📊 Evolución {zona_sel} - {equipo_sel}**")
                
                fig_temporal = px.line(
                    df_filtered,
                    x='fecha',
                    y=col_equipo_map,
                    markers=True,
                    labels={col_equipo_map: 'Tarifa (MXN/km)', 'fecha': 'Período'},
                    template='plotly_white'
                )
                colores_zonas = {"Norte": "#FF6B6B", "Centro": "#4ECDC4", "Sur": "#45B7D1"}
                fig_temporal.update_traces(line=dict(width=3, color=colores_zonas.get(zona_sel, "#667eea")), marker=dict(size=8))
                fig_temporal.update_layout(hovermode='x unified', height=350)
                st.plotly_chart(fig_temporal, width='stretch')
                
                st.markdown("---")
                
                # KPI 4: Tabla detallada
                st.markdown("**📋 Histórico Detallado**")
                
                df_tabla = df_filtered[['fecha', col_equipo_map]].copy()
                df_tabla.columns = ['Período', 'Tarifa (MXN/km)']
                df_tabla['Tarifa (MXN/km)'] = df_tabla['Tarifa (MXN/km)'].apply(lambda x: f"${x:.2f}")
                
                st.dataframe(df_tabla, width='stretched', height=300, hide_index=True)
                
                # Exportar CSV
                csv_export = df_filtered[['fecha', col_equipo_map]].copy()
                csv_export.columns = ['Período', 'Tarifa (MXN/km)']
                csv_str = csv_export.to_csv(index=False)
                
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv_str,
                    file_name=f"tarifas_{zona_sel}_{equipo_sel}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"⚠️ Sin datos para {zona_sel} - {equipo_sel}")
        
        except Exception as e:
            st.error(f"❌ Error cargando KPIs Operacional: {str(e)}")
    
    with tabs[3]:
        st.markdown("#### ⛽ Análisis de Costos de Diesel")
        
        try:
            # Importar el módulo de precios reales
            from diesel_prices_real import obtener_precios_reales, obtener_historico_simulado, calcular_metricas_diesel
            
            # Crear función con caché para obtener precios (24 horas)
            @st.cache_data(ttl=86400)  # Cache por 24 horas (se actualiza diariamente)
            def get_diesel_data():
                precios, fuente = obtener_precios_reales()
                historico = obtener_historico_simulado(30)
                metricas = calcular_metricas_diesel(precios, historico)
                return precios, fuente, historico, metricas
            
            # Obtener precios en tiempo real
            precios_actuales, fuente, df_diesel_hist, metricas = get_diesel_data()
            
            # Mostrar fuente de datos con botón de actualización
            col_info, col_btn = st.columns([2, 1])
            with col_info:
                if "Tiempo Real" in fuente:
                    st.success(f"✅ {fuente} - {precios_actuales.get('fecha_actualizacion', 'N/A')}")
                else:
                    st.warning(f"⚠️ {fuente}")
            
            with col_btn:
                if st.button("🔄 Actualizar Ahora", key="diesel_refresh"):
                    # Limpiar el caché y recargar datos
                    st.cache_data.clear()
                    st.rerun()
            
            st.markdown("---")
            
            st.markdown("**💰 Precios Actuales (MXN/L)**")
            col_dn, col_dc, col_ds, col_dp = st.columns(4)
            
            with col_dn:
                st.metric("🔴 Región Norte (NL)", f"${precios_actuales['norte']:.2f}/L", "Nueva León")
            with col_dc:
                st.metric("🟠 Región Centro (Jal)", f"${precios_actuales['centro']:.2f}/L", "Jalisco")
            with col_ds:
                st.metric("🟡 Región Sur (Est)", f"${precios_actuales['sur']:.2f}/L", "Estimado")
            with col_dp:
                st.metric("📍 Nacional (Promedio)", f"${precios_actuales['promedio_nacional']:.2f}/L", "Oficial")
            
            st.markdown("---")
            
            # Gráfico: Tendencia 30 días
            st.markdown("**📈 Tendencia de Precios (Últimos 30 días)**")
            
            fig_diesel_trend = go.Figure()
            fig_diesel_trend.add_trace(go.Scatter(
                x=df_diesel_hist['fecha'], y=df_diesel_hist['norte'],
                mode='lines+markers', name='Norte',
                line=dict(color='#FF6B6B', width=2), marker=dict(size=5)
            ))
            fig_diesel_trend.add_trace(go.Scatter(
                x=df_diesel_hist['fecha'], y=df_diesel_hist['centro'],
                mode='lines+markers', name='Centro',
                line=dict(color='#4ECDC4', width=2), marker=dict(size=5)
            ))
            fig_diesel_trend.add_trace(go.Scatter(
                x=df_diesel_hist['fecha'], y=df_diesel_hist['sur'],
                mode='lines+markers', name='Sur',
                line=dict(color='#45B7D1', width=2), marker=dict(size=5)
            ))
            
            fig_diesel_trend.update_layout(
                height=350, template='plotly_white',
                hovermode='x unified', title_x=0.5
            )
            st.plotly_chart(fig_diesel_trend, width='stretch')
            
            st.markdown("---")
            
            # Comparativa: Actual vs Promedio 30 días
            st.markdown("**📊 Comparativa: Precio Actual vs Promedio 30 Días**")
            
            col_comp1, col_comp2 = st.columns(2)
            
            with col_comp1:
                promedio_30d_norte = df_diesel_hist['norte'].mean()
                promedio_30d_centro = df_diesel_hist['centro'].mean()
                promedio_30d_sur = df_diesel_hist['sur'].mean()
                
                fig_comp_diesel = go.Figure(data=[
                    go.Bar(name='Precio Actual', x=['Norte', 'Centro', 'Sur'], 
                           y=[precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']],
                           marker_color='#FF6B6B'),
                    go.Bar(name='Promedio 30d', x=['Norte', 'Centro', 'Sur'],
                           y=[promedio_30d_norte, promedio_30d_centro, promedio_30d_sur],
                           marker_color='#4ECDC4')
                ])
                fig_comp_diesel.update_layout(height=350, template='plotly_white', barmode='group')
                st.plotly_chart(fig_comp_diesel, width='stretch')
            
            with col_comp2:
                # Variación porcentual
                var_norte = ((precios_actuales['norte'] - promedio_30d_norte) / promedio_30d_norte * 100)
                var_centro = ((precios_actuales['centro'] - promedio_30d_centro) / promedio_30d_centro * 100)
                var_sur = ((precios_actuales['sur'] - promedio_30d_sur) / promedio_30d_sur * 100)
                
                fig_var_diesel = px.bar(
                    x=['Norte', 'Centro', 'Sur'],
                    y=[var_norte, var_centro, var_sur],
                    color=['#FF6B6B' if v > 0 else '#51CF66' for v in [var_norte, var_centro, var_sur]],
                    text_auto='.1f',
                    labels={'y': 'Variación (%)', 'x': 'Región'},
                    template='plotly_white'
                )
                fig_var_diesel.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_var_diesel, width='stretch')
            
            st.markdown("---")
            
            # Impacto en costos de operación
            st.markdown("**🎯 Impacto en Costos de Flota (Consumo típico: 0.25 L/km)**")
            
            col_imp1, col_imp2, col_imp3 = st.columns(3)
            
            consumo = 0.25
            
            with col_imp1:
                distancia = 1000
                costo = precios_actuales['norte'] * consumo * distancia
                st.markdown(f"""
                <div style="background: #FFE5E5; border-left: 4px solid #FF6B6B; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta NORTE</strong><br>
                    Distancia: {distancia} km<br>
                    Consumo: {consumo * distancia:.1f}L<br>
                    <strong style="color: #FF6B6B; font-size: 1.3em;">${costo:.2f} MXN</strong><br>
                    <small>Por km: ${costo/distancia:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_imp2:
                distancia = 500
                costo = precios_actuales['centro'] * consumo * distancia
                st.markdown(f"""
                <div style="background: #E5F7F6; border-left: 4px solid #4ECDC4; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta CENTRO</strong><br>
                    Distancia: {distancia} km<br>
                    Consumo: {consumo * distancia:.1f}L<br>
                    <strong style="color: #4ECDC4; font-size: 1.3em;">${costo:.2f} MXN</strong><br>
                    <small>Por km: ${costo/distancia:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_imp3:
                distancia = 800
                costo = precios_actuales['sur'] * consumo * distancia
                st.markdown(f"""
                <div style="background: #E5F2FF; border-left: 4px solid #45B7D1; padding: 15px; border-radius: 6px;">
                    <strong>🚛 Ruta SUR</strong><br>
                    Distancia: {distancia} km<br>
                    Consumo: {consumo * distancia:.1f}L<br>
                    <strong style="color: #45B7D1; font-size: 1.3em;">${costo:.2f} MXN</strong><br>
                    <small>Por km: ${costo/distancia:.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Análisis de Metricas
            st.markdown("**📊 Análisis del Mercado de Diesel**")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric(
                    "📈 Tendencia",
                    f"${metricas['variacion_pendiente']:.2f}/L",
                    f"{metricas['variacion_pendiente']/metricas['promedio_30d']*100:+.1f}%"
                )
            
            with col_m2:
                st.metric(
                    "📊 Volatilidad",
                    f"{metricas['volatilidad_cv']:.1f}%",
                    "CV (30d)"
                )
            
            with col_m3:
                st.metric(
                    "⬆️ Máximo 30d",
                    f"${metricas['maximo_30d']:.2f}/L"
                )
            
            with col_m4:
                st.metric(
                    "⬇️ Mínimo 30d",
                    f"${metricas['minimo_30d']:.2f}/L"
                )
            
            st.markdown("---")
            
            # Insights y recomendaciones
            st.markdown("**💡 Insights y Recomendaciones**")
            
            # Tendencia general
            if metricas['variacion_pendiente'] > 0.5:
                st.warning(f"🔴 MERCADO ALCISTA - Los precios aumentaron {metricas['variacion_pendiente']:.2f}/L en el último mes. Considera planes de abastecimiento")
            elif metricas['variacion_pendiente'] < -0.5:
                st.success(f"🟢 MERCADO BAJISTA - Los precios disminuyeron {abs(metricas['variacion_pendiente']):.2f}/L en el último mes. Buena oportunidad")
            else:
                st.info(f"→ MERCADO ESTABLE - Variación de {metricas['variacion_pendiente']:.2f}/L")
            
            # Diferencia entre zonas
            diff_max_min = max(precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']) - \
                          min(precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur'])
            zona_cara = ["Norte", "Centro", "Sur"][[precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']].index(max(precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']))]
            zona_barata = ["Norte", "Centro", "Sur"][[precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']].index(min(precios_actuales['norte'], precios_actuales['centro'], precios_actuales['sur']))]
            
            st.info(f"📍 {zona_cara} es ${diff_max_min:.2f}/L más caro que {zona_barata} - Diferencia de ${diff_max_min * consumo * 1000:.2f} en ruta de 1000km")
        
        except Exception as e:
            st.error(f"❌ Error cargando análisis de Diesel: {str(e)}")


if __name__ == '__main__':
    main()
