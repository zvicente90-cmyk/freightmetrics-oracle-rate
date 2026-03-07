import streamlit as st
import pandas as pd
from pdf_generator import dataframe_to_pdf

def main():

    # estructura_indice = pd.DataFrame([
    #     {"Elemento del Índice": "Combustible (Diésel)", "Costo por KM (Estimado)": "$11.30", "% del Total": "42%", "Factor de Variación (Justificación)": "Varía diario según CRE. Sensible al peso de carga."},
    #     {"Elemento del Índice": "Casetas (Peajes)", "Costo por KM (Estimado)": "$5.40", "% del Total": "20%", "Factor de Variación (Justificación)": "Costo fijo de la SICT. Sube anualmente (febrero)."},
    #     {"Elemento del Índice": "Sueldo Operador", "Costo por KM (Estimado)": "$4.50", "% del Total": "17%", "Factor de Variación (Justificación)": "Incluye viáticos y retención de talento."},
    #     {"Elemento del Índice": "Mantenimiento y Llantas", "Costo por KM (Estimado)": "$3.00", "% del Total": "11%", "Factor de Variación (Justificación)": "Refacciones dolarizadas e inflación mecánica."},
    #     {"Elemento del Índice": "Seguros y Riesgo", "Costo por KM (Estimado)": "$1.60", "% del Total": "6%", "Factor de Variación (Justificación)": "Prima por zona roja (Inseguridad en ruta)."},
    #     {"Elemento del Índice": "Administración y Fijos", "Costo por KM (Estimado)": "$1.20", "% del Total": "4%", "Factor de Variación (Justificación)": "Depreciación de la unidad y staff de oficina."},
    #     {"Elemento del Índice": "SUBTOTAL COSTO OPERATIVO", "Costo por KM (Estimado)": "$27.00", "% del Total": "100%", "Factor de Variación (Justificación)": "Punto de Equilibrio (Break-even)"},
    #     {"Elemento del Índice": "Margen de Utilidad (20%)", "Costo por KM (Estimado)": "$5.40", "% del Total": "-", "Factor de Variación (Justificación)": "Ganancia neta para reinversión y socios."},
    #     {"Elemento del Índice": "TARIFA SPOT FINAL", "Costo por KM (Estimado)": "$33.22", "% del Total": "Total", "Factor de Variación (Justificación)": "Precio Justo Sugerido"}
    # ])
    # st.dataframe(estructura_indice, width='stretch', hide_index=True)

    st.markdown("### Tendencia de Mercado")
    st.caption("Análisis de Tarifas Spot FreightMetrics México - Basado en Diésel CRE 26.401 MXN/L.")
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
            equipos = ["Caja Seca (Dry Van)", "Plataforma (Flatbed)", "Refrigerado (Reefer)", "Full (Doble)"]
            equipo_sel = st.selectbox("Equipo", equipos, index=0)
            
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
                    
                if equipo_sel not in tarifa_final_rows.columns:
                    st.warning(f"⚠️ No hay datos para {equipo_sel} en {zona}")
                    continue
                    
                valor = tarifa_final_rows[equipo_sel].values[0]
                
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
        
        # TODO: Leyenda de colores temporalmente oculta - usar más adelante
        # st.markdown("### 📊 Leyenda de Tarifas")
        # col1, col2, col3 = st.columns(3)
        # with col1:
        #     st.markdown("🔵 **Económica**<br>< $25.00/km", unsafe_allow_html=True)
        # with col2:
        #     st.markdown("🔷 **Moderada**<br>$25.00 - $30.00/km", unsafe_allow_html=True)
        # with col3:
        #     st.markdown("🟦 **Elevada**<br>> $30.00/km", unsafe_allow_html=True)
        
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
                
                if tarifa_rows.empty or equipo_sel not in tarifa_rows.columns:
                    resumen_tarifas.append({"Zona": zona, "Tarifa Spot Final (MXN/km)": "N/A"})
                    continue
                    
                tarifa = tarifa_rows[equipo_sel].values[0]
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
        
        # Métricas adicionales estilo DAT con formato profesional
        if tarifas_valores:
            st.markdown("### 📈 Análisis del Mercado")
            
            # CSS para métricas profesionales
            st.markdown("""
            <style>
            .metric-container {
                background: rgba(74, 144, 226, 0.08);
                border-radius: 12px;
                padding: 15px;
                margin: 10px 0;
            }
            .stMetric > div {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(226, 232, 240, 0.9) 100%);
                border-radius: 10px;
                padding: 15px;
                border-left: 4px solid #4A90E2;
                box-shadow: 0 4px 15px rgba(74, 144, 226, 0.1);
                transition: transform 0.2s ease;
            }
            .stMetric > div:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(74, 144, 226, 0.2);
            }
            .stMetric label {
                color: #2C5F8A !important;
                font-weight: 600 !important;
                font-size: 0.95em !important;
            }
            .stMetric [data-testid="metric-container"] > div:first-child {
                color: #1A365D !important;
                font-size: 1.8em !important;
                font-weight: 700 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💼 Tarifa Promedio", f"${sum(tarifas_valores)/len(tarifas_valores):.2f}/km")
            with col2:
                st.metric("📊 Tarifa Más Alta", f"${max(tarifas_valores):.2f}/km", f"+${max(tarifas_valores) - min(tarifas_valores):.2f}")
            with col3:
                st.metric("💰 Tarifa Más Baja", f"${min(tarifas_valores):.2f}/km")
            with col4:
                variacion = ((max(tarifas_valores) - min(tarifas_valores)) / min(tarifas_valores) * 100)
                st.metric("📈 Variación Nacional", f"{variacion:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error cargando matriz comparativa: {e}")

    # Tabla Index Spot Tarifas (movida debajo del mapa)
    st.markdown("---")  # Separador visual
    st.markdown("### 📊 Índice Spot FreightMetrics - Tabla Detallada")
    import json, os
    index_file = os.path.join(os.path.dirname(__file__), "index_spot_tarifas.json")
    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)
    
    # Filtros para la tabla en una fila
    col1, col2 = st.columns(2)
    with col1:
        meses = [item["mes"] for item in index_data["tarifas"]]
        anios_disponibles = sorted(list(set([m.split("-")[0] for m in meses])))
        anio_tabla = st.selectbox("Año (Tabla)", anios_disponibles, index=len(anios_disponibles)-1, key="anio_tabla")
    with col2:
        meses_filtrados = [m for m in meses if m.startswith(anio_tabla)]
        mes_tabla = st.selectbox("Mes (Tabla)", meses_filtrados, index=len(meses_filtrados)-1, key="mes_tabla")
    
    # Buscar la tabla correspondiente
    tabla = next((item["tabla"] for item in index_data["tarifas"] if item["mes"] == mes_tabla), [])
    if tabla:
        tabla_maestra = pd.DataFrame(tabla)
        # Reemplazar encabezado 'Parque' por 'Origen' y agregar 'Destino' si no existen
        if 'Parque' in tabla_maestra.columns:
            tabla_maestra = tabla_maestra.rename(columns={'Parque': 'Origen'})
        # Si 'Destino' no existe, intentar inferirlo de 'Nodo' o dejarlo vacío
        if 'Destino' not in tabla_maestra.columns:
            if 'Nodo' in tabla_maestra.columns:
                tabla_maestra['Destino'] = tabla_maestra['Nodo']
            else:
                tabla_maestra['Destino'] = ''
        # Reordenar columnas para mostrar Origen y Destino al inicio
        cols = list(tabla_maestra.columns)
        for col in ['Origen', 'Destino']:
            if col in cols:
                cols.insert(1, cols.pop(cols.index(col)))
        tabla_maestra = tabla_maestra[cols]
        # Formatear tarifa para visualización
        tabla_maestra["Tarifa Spot Est. (MXN)"] = tabla_maestra["Tarifa_MXN"].apply(lambda x: f"${x:,.0f}")
        
        # CSS para tabla maestra con formato profesional
        st.markdown("""
        <style>
        .stDataFrame > div {
            background: linear-gradient(135deg, rgba(74, 144, 226, 0.05) 0%, rgba(53, 122, 189, 0.05) 100%);
            border-radius: 10px;
            border: 2px solid #4A90E2;
        }
        .stDataFrame [data-testid="stDataFrameResizeHandle"] {
            background-color: #357ABD;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Crear configuración personalizada para el dataframe
        column_config = {
            "Origen": st.column_config.TextColumn(
                "🚛 Origen",
                help="Ciudad de origen del envío",
                width="medium"
            ),
            "Destino": st.column_config.TextColumn(
                "🎯 Destino", 
                help="Ciudad de destino del envío",
                width="medium"
            ),
            "Tarifa Spot Est. (MXN)": st.column_config.TextColumn(
                "💰 Tarifa Estimada",
                help="Tarifa spot estimada en pesos mexicanos",
                width="large"
            )
        }
        
        st.dataframe(
            tabla_maestra.drop(columns=["Tarifa_MXN"]), 
            width='stretch', 
            hide_index=True,
            column_config=column_config
        )
            
        # Análisis comparativo mes anterior
        st.markdown("---")  # Separador
        st.markdown("### 📈 Análisis Comparativo Mensual")
        
        # Obtener datos del mes anterior para comparar
        mes_anterior = None
        mes_actual_data = tabla_maestra
        
        # Lógica para encontrar el mes anterior
        if mes_tabla == "2026-03":
            mes_anterior = "2026-02"
        elif mes_tabla == "2026-02":
            mes_anterior = "2026-01"  # Si existiera
        elif mes_tabla == "2026-04":
            mes_anterior = "2026-03"
        # Se pueden agregar más meses según sea necesario
        
        if mes_anterior:
            # Buscar datos del mes anterior en el JSON
            mes_anterior_data = None
            for item in index_data["tarifas"]:
                if item["mes"] == mes_anterior:
                    mes_anterior_data = pd.DataFrame(item["tabla"])
                    break
            
            if mes_anterior_data is not None and not mes_anterior_data.empty:
                # Calcular promedios
                promedio_anterior = mes_anterior_data['Tarifa_MXN'].mean()
                promedio_actual = mes_actual_data['Tarifa_MXN'].mean()
                
                diferencia_absoluta = promedio_actual - promedio_anterior
                diferencia_porcentual = (diferencia_absoluta / promedio_anterior * 100)
                
                # Determinar tendencia
                if diferencia_porcentual > 0:
                    trend_color = "#10B981"  # Verde
                    trend_emoji = "📈"
                    trend_text = "al alza"
                    trend_desc = "incremento"
                elif diferencia_porcentual < 0:
                    trend_color = "#EF4444"  # Rojo
                    trend_emoji = "📉"  
                    trend_text = "a la baja"
                    trend_desc = "descenso"
                else:
                    trend_color = "#6B7280"  # Gris
                    trend_emoji = "➡️"
                    trend_text = "estables"
                    trend_desc = "estabilidad"
                
                # CSS para el análisis comparativo
                st.markdown("""
                <style>
                .comparativo-container {
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%);
                    border-radius: 15px;
                    padding: 25px;
                    margin: 20px 0;
                    border-left: 5px solid #4A90E2;
                }
                .comp-header {
                    font-size: 1.3em;
                    font-weight: bold;
                    text-align: center;
                    margin-bottom: 20px;
                    color: #2D3748;
                }
                .comp-stats {
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: wrap;
                }
                .comp-stat-box {
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 5px;
                    flex: 1;
                    min-width: 200px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .comp-value {
                    font-size: 1.5em;
                    font-weight: bold;
                    margin: 10px 0;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Mostrar análisis comparativo
                mes_anterior_nombre = mes_anterior.split("-")[1]
                mes_actual_nombre = mes_tabla.split("-")[1]
                
                st.markdown(f"""
                <div class="comparativo-container">
                    <div class="comp-header">{trend_emoji} Comparativo {mes_anterior_nombre}/{mes_actual_nombre} 2026</div>
                    <div class="comp-stats">
                        <div class="comp-stat-box">
                            <div style="color: #6B7280; font-size: 0.9em;">PROMEDIO {mes_anterior_nombre.upper()}</div>
                            <div class="comp-value" style="color: #4A90E2;">${promedio_anterior:,.0f}</div>
                        </div>
                        <div class="comp-stat-box">
                            <div style="color: #6B7280; font-size: 0.9em;">PROMEDIO {mes_actual_nombre.upper()}</div>
                            <div class="comp-value" style="color: #4A90E2;">${promedio_actual:,.0f}</div>
                        </div>
                        <div class="comp-stat-box">
                            <div style="color: #6B7280; font-size: 0.9em;">VARIACIÓN</div>
                            <div class="comp-value" style="color: {trend_color};">{diferencia_porcentual:+.2f}%</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Análisis detallado por ruta con expander
                with st.expander(f"🔍 **Análisis Detallado por Ruta - {mes_anterior_nombre} vs {mes_actual_nombre}**"):
                    st.markdown("**Comparativo de Cambios por Ruta:**")
                    
                    # Crear comparativo ruta por ruta
                    for i, ruta_actual in mes_actual_data.iterrows():
                        # Buscar ruta equivalente en mes anterior
                        ruta_anterior = mes_anterior_data[
                            (mes_anterior_data['Origen'] == ruta_actual['Origen']) & 
                            (mes_anterior_data['Destino'] == ruta_actual['Destino'])
                        ]
                        
                        if not ruta_anterior.empty:
                            tarifa_anterior = ruta_anterior['Tarifa_MXN'].iloc[0]
                            tarifa_actual = ruta_actual['Tarifa_MXN']
                            cambio = tarifa_actual - tarifa_anterior
                            cambio_pct = (cambio / tarifa_anterior * 100) if tarifa_anterior != 0 else 0
                            
                            # Emoji según cambio
                            emoji_cambio = "🔴" if cambio < 0 else "🟢" if cambio > 0 else "⚪"
                            
                            st.markdown(f"""
                            **{emoji_cambio} {ruta_actual['Origen']} → {ruta_actual['Destino']}**  
                            `${tarifa_anterior:,.0f}` → `${tarifa_actual:,.0f}` *({cambio_pct:+.1f}%)*
                            """)
            else:
                st.info(f"No hay datos disponibles del mes anterior ({mes_anterior}) para realizar la comparación.")
        else:
            st.info("Seleccione un mes con datos del mes anterior disponible para ver el análisis comparativo.")
    else:
        st.warning("No hay datos para el mes seleccionado.")

    # Botón de descarga con estilo profesional
    st.markdown("### 📄 Exportar Reporte")
    
    # CSS para botón profesional
    st.markdown("""
    <style>
    .download-section {
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.08) 0%, rgba(53, 122, 189, 0.08) 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        border: 1px solid rgba(74, 144, 226, 0.2);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 1.1em !important;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(74, 144, 226, 0.4) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #2C5F8A 0%, #1A365D 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 1.1em !important;
        box-shadow: 0 4px 15px rgba(44, 95, 138, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(44, 95, 138, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.markdown("**📊 Generar reporte completo en formato PDF**")
    
    if st.button("🔄 Generar Reporte PDF"):
        with st.spinner("Generando reporte profesional..."):
            pdf_bytes = dataframe_to_pdf(tabla_maestra, title="Reporte FreightMetrics")
            st.success("✅ Reporte generado exitosamente")
            st.download_button(
                "📥 Descargar PDF", 
                data=pdf_bytes, 
                file_name=f"reporte_freightmetrics_{anio_sel}_{mes_sel}.pdf", 
                mime="application/pdf"
            )
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
