"""
Utilidades para gráficas dinámicas e insights
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st

class InsightGenerator:
    """Generador automático de insights cortos y precisos"""
    
    @staticmethod
    def generate_price_insights(df_actual, df_prev):
        """Genera insights sobre cambios de precio"""
        insights = []
        
        # Comparar zonas
        zonas_actual = df_actual.groupby('zona')['tarifa'].mean().sort_values(ascending=False)
        zona_mas_cara = zonas_actual.idxmax()
        zona_mas_barata = zonas_actual.idxmin()
        
        insights.append({
            'type': 'price_ranking',
            'text': f"📍 {zona_mas_cara} es {((zonas_actual[zona_mas_cara]/zonas_actual[zona_mas_barata]-1)*100):.1f}% más caro que {zona_mas_barata}",
            'emoji': '💰'
        })
        
        # Cambios vs período anterior
        if df_prev is not None and len(df_prev) > 0:
            for zona in zonas_actual.index:
                tarifa_actual = zonas_actual[zona]
                tarifa_prev = df_prev[df_prev['zona'] == zona]['tarifa'].mean() if 'zona' in df_prev.columns else None
                
                if tarifa_prev and tarifa_prev > 0:
                    cambio_pct = ((tarifa_actual - tarifa_prev) / tarifa_prev) * 100
                    if cambio_pct > 2:
                        insights.append({
                            'type': 'price_change',
                            'text': f"⚠️ {zona}: +{cambio_pct:.1f}% en el período",
                            'emoji': '📈'
                        })
                    elif cambio_pct < -2:
                        insights.append({
                            'type': 'price_change',
                            'text': f"✅ {zona}: {cambio_pct:.1f}% mejora de precio",
                            'emoji': '📉'
                        })
        
        return insights

    @staticmethod
    def generate_volatility_insights(df):
        """Genera insights sobre volatilidad"""
        insights = []
        
        if 'equipo' in df.columns:
            volatilidad_equipo = df.groupby('equipo')['tarifa'].apply(
                lambda x: (x.std() / x.mean() * 100) if x.mean() > 0 else 0
            ).sort_values(ascending=False)
            
            equipo_volatile = volatilidad_equipo.idxmax()
            equipo_estable = volatilidad_equipo.idxmin()
            
            if volatilidad_equipo[equipo_volatile] > volatilidad_equipo[equipo_estable]:
                insights.append({
                    'type': 'volatility',
                    'text': f"🎢 {equipo_volatile}: Mayor volatilidad ({volatilidad_equipo[equipo_volatile]:.1f}%)",
                    'emoji': '📊'
                })
                insights.append({
                    'type': 'stability',
                    'text': f"✨ {equipo_estable}: Más predecible ({volatilidad_equipo[equipo_estable]:.1f}%)",
                    'emoji': '🎯'
                })
        
        return insights

    @staticmethod
    def generate_demand_insights(df):
        """Genera insights sobre demanda si existen datos"""
        insights = []
        
        if 'demanda' in df.columns:
            demanda_por_zona = df.groupby('zona')['demanda'].mean()
            demanda_max = demanda_por_zona.idxmax()
            demanda_promedio = demanda_por_zona.mean()
            
            insights.append({
                'type': 'demand_peak',
                'text': f"🚚 {demanda_max} lidera en demanda (+{((demanda_por_zona[demanda_max]/demanda_promedio-1)*100):.0f}%)",
                'emoji': '📍'
            })
        
        return insights


class GraphicsLibrary:
    """Librería de gráficas dinámicas e interactivas"""
    
    @staticmethod
    def create_heatmap_tarifas(df, title="Matriz Tarifaria"):
        """Crea un heatmap interactivo de tarifas"""
        
        if 'zona' not in df.columns or 'equipo' not in df.columns or 'tarifa' not in df.columns:
            return None
            
        pivot_df = df.pivot_table(
            values='tarifa',
            index='zona',
            columns='equipo',
            aggfunc='mean'
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn_r',
            text=pivot_df.values.round(2),
            texttemplate='$%{text:.2f}',
            textfont={"size": 12},
            colorbar=dict(title="USD/km"),
            hovertemplate='<b>%{y}</b><br>%{x}<br>%{z:.3f} USD/km<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Tipo de Equipo",
            yaxis_title="Zona",
            height=400,
            template='plotly_white'
        )
        
        return fig

    @staticmethod
    def create_trend_chart(df, title="Tendencia de Tarifas"):
        """Crea gráfica de tendencias por zona"""
        
        if df.empty:
            return None
            
        fig = px.line(
            df,
            x='fecha' if 'fecha' in df.columns else df.index,
            y='tarifa',
            color='zona' if 'zona' in df.columns else None,
            title=title,
            markers=True,
            template='plotly_white',
            line_shape='spline'
        )
        
        fig.update_layout(
            hovermode='x unified',
            height=400,
            xaxis_title="Período",
            yaxis_title="Tarifa (USD/km)"
        )
        
        return fig

    @staticmethod
    def create_comparison_bars(df, metric='tarifa', group_by='zona', title="Comparativa"):
        """Crea gráfica de barras comparativas"""
        
        if group_by not in df.columns or metric not in df.columns:
            return None
            
        agg_df = df.groupby(group_by)[metric].mean().sort_values(ascending=False)
        
        fig = px.bar(
            x=agg_df.index,
            y=agg_df.values,
            title=title,
            template='plotly_white',
            text=agg_df.values.round(2),
            labels={'x': group_by.capitalize(), 'y': metric.capitalize()}
        )
        
        fig.update_traces(
            textposition='outside',
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'][:len(agg_df)]
        )
        
        fig.update_layout(height=400, showlegend=False)
        
        return fig

    @staticmethod
    def create_zone_comparison_radar(df):
        """Crea radar chart para comparación de zonas"""
        
        if 'zona' not in df.columns or 'tarifa' not in df.columns:
            return None
        
        # Preparar datos
        zonas_stats = df.groupby('zona').agg({
            'tarifa': ['mean', 'std', 'min', 'max']
        }).round(3)
        
        # Crear figura radar
        fig = go.Figure()
        
        categories = ['Promedio', 'Desv. Estándar', 'Mínimo', 'Máximo']
        colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#95E1D3']
        
        for i, (zona, row) in enumerate(zonas_stats.iterrows()):
            values = [
                row[('tarifa', 'mean')],
                row[('tarifa', 'std')],
                row[('tarifa', 'min')],
                row[('tarifa', 'max')]
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=zona,
                marker_color=colores[i % len(colores)],
                opacity=0.6
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max([v for v in values] + [1])])),
            showlegend=True,
            height=500,
            title="Análisis Estadístico por Zona"
        )
        
        return fig

    @staticmethod
    def create_box_plot(df, title="Distribución de Tarifas"):
        """Crea box plot para análisis de distribución"""
        
        if 'zona' not in df.columns or 'tarifa' not in df.columns:
            return None
        
        fig = px.box(
            df,
            x='zona',
            y='tarifa',
            title=title,
            template='plotly_white',
            points='outliers'
        )
        
        fig.update_layout(height=400)
        
        return fig

    @staticmethod
    def create_scatter_demand(df, title="Demanda vs Tarifa"):
        """Crea scatter plot de demanda vs tarifa"""
        
        if 'demanda' not in df.columns or 'tarifa' not in df.columns:
            return None
        
        fig = px.scatter(
            df,
            x='demanda',
            y='tarifa',
            color='zona' if 'zona' in df.columns else None,
            size='demanda',
            hover_data=['equipo'] if 'equipo' in df.columns else [],
            title=title,
            template='plotly_white'
        )
        
        fig.update_layout(height=400)
        
        return fig

    @staticmethod
    def create_kpi_metric_card(label, value, delta=None, delta_color='normal'):
        """Crea una tarjeta métrica KPI"""
        
        delta_text = ""
        delta_icon = ""
        
        if delta is not None:
            delta_pct = abs(delta)
            if delta > 0:
                delta_icon = "📈"
                delta_text = f"+{delta_pct:.1f}%"
            elif delta < 0:
                delta_icon = "📉"
                delta_text = f"{delta_pct:.1f}%"
            else:
                delta_icon = "→"
                delta_text = "0%"
        
        html = f"""
        <div style="
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            color: white;
        ">
            <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 10px;">{label}</div>
            <div style="font-size: 2.2em; font-weight: 700; margin: 10px 0;">{value}</div>
            {f'<div style="font-size: 1em; color: #FFD700;">{delta_icon} {delta_text}</div>' if delta_text else ''}
        </div>
        """
        
        return html
