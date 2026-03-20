"""
MATRIZ TARIFARIA MEJORADA: Visualización interactiva y análisis de mercado
Interfaz profesional para consulta de tarifas spot por zona y equipo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os

def cargar_matriz_json():
    """Carga datos de la matriz tarifaria desde JSON"""
    matriz_file = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
    
    try:
        with open(matriz_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Archivo de matriz no encontrado")
        return None
    except json.JSONDecodeError:
        st.error("❌ Error al decodificar JSON")
        return None

def obtener_tarifa_final(matriz_data, anio, mes, zona, equipo_json):
    """Extrae tarifa final del JSON"""
    try:
        if anio not in matriz_data["matriz"]:
            return None
        if mes not in matriz_data["matriz"][anio]:
            return None
        if zona not in matriz_data["matriz"][anio][mes]:
            return None
        
        zona_data = pd.DataFrame(matriz_data["matriz"][anio][mes][zona])
        tarifa_rows = zona_data[zona_data["Componente"] == "TARIFA SPOT FINAL"]
        
        if tarifa_rows.empty:
            return None
        
        valor = tarifa_rows[equipo_json].values[0] if equipo_json in tarifa_rows.columns else None
        
        if valor is None or pd.isna(valor):
            return None
        
        return float(valor)
    except Exception as e:
        st.error(f"Error extrayendo tarifa: {e}")
        return None

def crear_comparativa_zonas(matriz_data, anio, mes, equipo_json):
    """Crea análisis comparativo entre zonas"""
    datos = []
    
    for zona in ["Norte", "Centro", "Sur"]:
        tarifa = obtener_tarifa_final(matriz_data, anio, mes, zona, equipo_json)
        if tarifa:
            datos.append({"zona": zona, "tarifa": tarifa})
    
    return pd.DataFrame(datos) if datos else None

def crear_matriz_completa(matriz_data, anio, mes):
    """Crea matriz completa de todas las tarifas"""
    zonas = ["Norte", "Centro", "Sur"]
    equipos_mapeo = {
        "Caja Seca (Dry Van)": "Caja Seca (Dry Van)",
        "Plataforma (Flatbed)": "Plataforma (Flatbed)", 
        "Refrigerado (Reefer)": "Refrigerado (Reefer)",
        "Full (Doble)": "Full (Doble)"
    }
    
    datos = []
    
    for zona in zonas:
        for equipo, equipo_json in equipos_mapeo.items():
            tarifa = obtener_tarifa_final(matriz_data, anio, mes, zona, equipo_json)
            if tarifa:
                datos.append({
                    "Zona": zona,
                    "Equipo": equipo,
                    "Tarifa": tarifa
                })
    
    return pd.DataFrame(datos) if datos else None

def main():
    st.set_page_config(page_title="📊 Matriz Tarifaria - FreightMetrics", layout="wide")
    
    # Estilos
    st.markdown("""
    <style>
        .header {
            background: linear-gradient(135deg, #1A365D 0%, #4A90E2 100%);
            padding: 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 20px;
        }
        .insight-box {
            background: rgba(74, 144, 226, 0.1);
            border-left: 4px solid #4A90E2;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        .tarifa-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-top: 4px solid #4A90E2;
        }
        .tarifa-card-large {
            font-size: 1.8em;
            font-weight: 700;
            color: #1A365D;
            margin: 15px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Encabezado
    st.markdown("""
    <div class="header">
        <h1>📊 Matriz Tarifaria Spot - México</h1>
        <p>Tarifas actualizadas de transporte de carga por zona y tipo de equipo</p>
        <small>Basado en metodología SCT e indicadores INEGI | Precios en MXN/km</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    matriz_data = cargar_matriz_json()
    
    if not matriz_data:
        return
    
    # CONTROLES
    st.markdown("## 🔍 Filtros de Búsqueda")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        anios = sorted(list(matriz_data["matriz"].keys()), reverse=True)
        anio_sel = st.selectbox("📅 Año", anios, index=0)
    
    with col_filtro2:
        meses = sorted(list(matriz_data["matriz"][anio_sel].keys()))
        mes_sel = st.selectbox("📆 Mes", meses, index=0)
    
    with col_filtro3:
        equipos = ["Caja Seca (Dry Van)", "Plataforma (Flatbed)", "Refrigerado (Reefer)", "Full (Doble)"]
        equipo_sel = st.selectbox("🚛 Tipo de Equipo", equipos, index=0)
        
        equipos_mapeo = {
            "Caja Seca (Dry Van)": "Caja Seca (Dry Van)",
            "Plataforma (Flatbed)": "Plataforma (Flatbed)",
            "Refrigerado (Reefer)": "Refrigerado (Reefer)",
            "Full (Doble)": "Full (Doble)"
        }
        equipo_json = equipos_mapeo.get(equipo_sel)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 1: COMPARATIVA POR ZONAS
    # ========================================================================
    st.markdown("## 💰 Tarifas por Zona")
    
    df_comparativa = crear_comparativa_zonas(matriz_data, anio_sel, mes_sel, equipo_json)
    
    if df_comparativa is not None and not df_comparativa.empty:
        # KPIs de zonas
        col_norte, col_centro, col_sur = st.columns(3)
        
        colores_zona = {"Norte": "#FF6B6B", "Centro": "#4ECDC4", "Sur": "#45B7D1"}
        
        for idx, (_, row) in enumerate(df_comparativa.iterrows()):
            zona = row["zona"]
            tarifa = row["tarifa"]
            color = colores_zona.get(zona, "#4A90E2")
            
            with [col_norte, col_centro, col_sur][idx]:
                st.markdown(f"""
                <div class="tarifa-card" style="border-top-color: {color};">
                    <div style="font-size: 1.2em; font-weight: 600; color: {color};">🌍 {zona}</div>
                    <div class="tarifa-card-large">${tarifa:.2f}</div>
                    <div style="color: #666; font-size: 0.9em;">MXN/km</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Gráfica comparativa
        col_bar, col_insights = st.columns([2, 1])
        
        with col_bar:
            fig_barras = px.bar(
                df_comparativa.sort_values("tarifa", ascending=False),
                x="zona",
                y="tarifa",
                title="📊 Comparativa de Tarifas por Zona",
                labels={"tarifa": "Tarifa (MXN/km)", "zona": "Zona"},
                template="plotly_white",
                text="tarifa",
                color="zona",
                color_discrete_map=colores_zona
            )
            
            fig_barras.update_traces(
                texttemplate="$%{text:.2f}",
                textposition="outside",
                marker_line_width=2,
                marker_line_color="white"
            )
            
            fig_barras.update_layout(
                height=400,
                showlegend=False,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col_insights:
            st.markdown("### 📌 Análisis")
            
            tarifa_max = df_comparativa["tarifa"].max()
            tarifa_min = df_comparativa["tarifa"].min()
            diferencia_pct = ((tarifa_max - tarifa_min) / tarifa_min * 100)
            
            zona_cara = df_comparativa.loc[df_comparativa["tarifa"].idxmax(), "zona"]
            zona_barata = df_comparativa.loc[df_comparativa["tarifa"].idxmin(), "zona"]
            
            st.markdown(f"""
            <div class="insight-box">
                <strong>💵 Más Caro:</strong><br>{zona_cara} - ${tarifa_max:.2f}
            </div>
            <div class="insight-box">
                <strong>💚 Más Económico:</strong><br>{zona_barata} - ${tarifa_min:.2f}
            </div>
            <div class="insight-box">
                <strong>📈 Diferencia:</strong><br>{diferencia_pct:.1f}%
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 2: MATRIZ COMPLETA
    # ========================================================================
    st.markdown("## 🔥 Matriz Completa (Todas las Combinaciones)")
    
    df_matriz_completa = crear_matriz_completa(matriz_data, anio_sel, mes_sel)
    
    if df_matriz_completa is not None and not df_matriz_completa.empty:
        col_heatmap, col_tabla = st.columns([2, 1])
        
        with col_heatmap:
            # Crear pivot para heatmap
            pivot = df_matriz_completa.pivot_table(
                values="Tarifa",
                index="Zona",
                columns="Equipo",
                aggfunc="mean"
            )
            
            # Reordenar columnas para mejor visualización
            pivot = pivot[["Caja Seca (Dry Van)", "Plataforma (Flatbed)", 
                          "Refrigerado (Reefer)", "Full (Doble)"]]
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale="RdYlGn_r",
                text=[[f"${pivot.iloc[i,j]:.2f}" for j in range(len(pivot.columns))] 
                      for i in range(len(pivot.index))],
                texttemplate="%{text}",
                textfont={"size": 14, "color": "white"},
                colorbar=dict(title="MXN/km"),
                hovertemplate="<b>%{y}</b> | %{x}<br>Tarifa: $%{z:.2f}/km<extra></extra>"
            ))
            
            fig_heatmap.update_layout(
                height=400,
                template="plotly_white",
                title="Tarifas Spot por Zona y Equipo",
                xaxis_title="Tipo de Equipo",
                yaxis_title="Zona"
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with col_tabla:
            st.markdown("### 📊 Rangos por Zona")
            
            for zona in ["Norte", "Centro", "Sur"]:
                zona_data = df_matriz_completa[df_matriz_completa["Zona"] == zona]
                min_val = zona_data["Tarifa"].min()
                max_val = zona_data["Tarifa"].max()
                
                st.markdown(f"""
                <div class="tarifa-card">
                    <strong>{zona}</strong><br>
                    <small>Mín: ${min_val:.2f}</small><br>
                    <small>Máx: ${max_val:.2f}</small><br>
                    <strong style="color: #4A90E2;">Rango: ${max_val-min_val:.2f}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 3: DESGLOSE DETALLADO
    # ========================================================================
    st.markdown("## 📋 Tabla Detallada")
    
    if df_matriz_completa is not None and not df_matriz_completa.empty:
        # Ordenar por zona y tarifa descendente
        df_mostrar = df_matriz_completa.sort_values(["Zona", "Tarifa"], ascending=[True, False])
        
        # Crear tabla formatada
        df_display = df_mostrar.copy()
        df_display["Tarifa"] = df_display["Tarifa"].apply(lambda x: f"${x:.3f}")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Zona": st.column_config.Column("Zona", width="medium"),
                "Equipo": st.column_config.Column("Tipo de Equipo", width="large"),
                "Tarifa": st.column_config.Column("Tarifa (MXN/km)", width="medium")
            }
        )
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas Generales")
        
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        tarifa_prom = df_matriz_completa["Tarifa"].mean()
        tarifa_med = df_matriz_completa["Tarifa"].median()
        tarifa_max_global = df_matriz_completa["Tarifa"].max()
        tarifa_min_global = df_matriz_completa["Tarifa"].min()
        
        with col_stats1:
            st.metric("Promedio General", f"${tarifa_prom:.2f}/km")
        
        with col_stats2:
            st.metric("Mediana", f"${tarifa_med:.2f}/km")
        
        with col_stats3:
            st.metric("Máximo", f"${tarifa_max_global:.2f}/km")
        
        with col_stats4:
            st.metric("Mínimo", f"${tarifa_min_global:.2f}/km")
        
        # Ranking de equipos
        st.markdown("### 🏆 Ranking: Equipos Más Caros en Promedio")
        
        ranking_equipos = df_matriz_completa.groupby("Equipo")["Tarifa"].mean().sort_values(ascending=False)
        
        for idx, (equipo, tarifa) in enumerate(ranking_equipos.items(), 1):
            emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            st.markdown(f"{emoji} **{equipo}** - ${tarifa:.2f}/km promedio")
    
    # ========================================================================
    # NOTA METODOLÓGICA
    # ========================================================================
    st.markdown("---")
    
    st.markdown("""
    <div class="insight-box">
        <strong>📌 Nota Metodológica:</strong><br>
        Las tarifas mostradas son calculadas conforme a la metodología de costos de operación 
        establecida por la SCT (Secretaría de Comunicaciones y Transportes). 
        Incluyen indexación con indicadores de inflación sectorial del INEGI y precios 
        regionales de energía de la CRE. FreightMetrics actúa como agregador de datos 
        para facilitar la toma de decisiones en el mercado de transporte spot en México.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.85em; margin-top: 30px;">
        <p>FreightMetrics MVP | Matriz Tarifaria Interactiva</p>
        <p>Período: {} {} | Actualización diaria</p>
    </div>
    """.format(mes_sel, anio_sel), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
