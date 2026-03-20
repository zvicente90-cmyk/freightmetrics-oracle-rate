# Modelo1 - Análisis de Tendencias de Mercado y Tarifas Spot
# FreightMetrics MVP - Algoritmo de predicción de tendencias

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TendenciasMercado:
    """
    Clase principal para análisis de tendencias del mercado de tarifas spot
    Modelo1 - Sistema de predicción basado en datos históricos
    """
    
    def __init__(self):
        self.datos_historicos = self._cargar_datos_historicos()
        self.factores_mercado = self._inicializar_factores()
        
    def _cargar_datos_historicos(self):
        """Carga datos históricos de tarifas desde archivos JSON"""
        archivos_datos = [
            "matriz_comparativa_mx.json",
            "dat_rates_historical.json"
        ]
        
        datos = {}
        for archivo in archivos_datos:
            try:
                ruta = os.path.join(os.path.dirname(__file__), archivo)
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos[archivo] = json.load(f)
            except FileNotFoundError:
                print(f"⚠️ Archivo {archivo} no encontrado")
                datos[archivo] = {}
                
        return datos
    
    def _inicializar_factores(self):
        """Factores que influyen en las tendencias del mercado"""
        return {
            "diesel": {"peso": 0.35, "tendencia": "alza"},
            "inflacion": {"peso": 0.25, "tendencia": "estable"},
            "demanda": {"peso": 0.20, "tendencia": "alta"},
            "oferta": {"peso": 0.15, "tendencia": "media"},
            "riesgo": {"peso": 0.05, "tendencia": "bajo"}
        }
    
    def analizar_tendencia_zona(self, zona: str, equipo: str, meses: int = 3) -> Dict:
        """
        Analiza la tendencia de precios para una zona específica
        Args:
            zona: Norte, Centro, Sur
            equipo: Tipo de equipo de transporte
            meses: Número de meses a analizar hacia atrás
        """
        try:
            matriz_data = self.datos_historicos.get("matriz_comparativa_mx.json", {})
            if not matriz_data or "matriz" not in matriz_data:
                return {"error": "No hay datos de matriz disponibles"}
            
            # Mapeo de equipos
            mapeo_equipos = {
                "Dry Van": "Caja Seca (Dry Van)",
                "Flatbed": "Plataforma (Flatbed)",  
                "Reefer": "Refrigerado (Reefer)",
                "Full": "Full (Doble)"
            }
            
            equipo_normalizado = mapeo_equipos.get(equipo, equipo)
            tendencia = []
            
            # Análisis por año y mes disponible
            for anio, datos_anio in matriz_data["matriz"].items():
                for mes, datos_mes in datos_anio.items():
                    if zona in datos_mes:
                        df_zona = pd.DataFrame(datos_mes[zona])
                        tarifa_rows = df_zona[df_zona["Componente"] == "TARIFA SPOT FINAL"]
                        
                        if not tarifa_rows.empty and equipo_normalizado in tarifa_rows.columns:
                            tarifa = tarifa_rows[equipo_normalizado].values[0]
                            if pd.notna(tarifa) and tarifa > 0:
                                tendencia.append({
                                    "periodo": f"{anio}-{mes}",
                                    "tarifa": float(tarifa),
                                    "zona": zona,
                                    "equipo": equipo_normalizado
                                })
            
            if not tendencia:
                return {"error": f"No hay datos suficientes para {zona} - {equipo}"}
            
            # Calcular estadísticas de tendencia
            df_tendencia = pd.DataFrame(tendencia)
            df_tendencia = df_tendencia.sort_values('periodo')
            
            if len(df_tendencia) < 2:
                return {"error": "Se necesitan al menos 2 períodos para calcular tendencia"}
            
            # Calcular variación porcentual
            primera_tarifa = df_tendencia.iloc[0]['tarifa']
            ultima_tarifa = df_tendencia.iloc[-1]['tarifa']
            variacion_pct = ((ultima_tarifa - primera_tarifa) / primera_tarifa) * 100
            
            # Determinar dirección de tendencia
            if variacion_pct > 2:
                direccion = "📈 Alza"
                color = "#10B981"
            elif variacion_pct < -2:
                direccion = "📉 Baja"
                color = "#EF4444"
            else:
                direccion = "➡️ Estable"
                color = "#6B7280"
            
            return {
                "zona": zona,
                "equipo": equipo_normalizado,
                "direccion": direccion,
                "variacion_pct": round(variacion_pct, 2),
                "color": color,
                "tarifa_inicial": primera_tarifa,
                "tarifa_actual": ultima_tarifa,
                "num_periodos": len(df_tendencia),
                "datos_completos": tendencia,
                "promedio": round(df_tendencia['tarifa'].mean(), 2),
                "maximo": round(df_tendencia['tarifa'].max(), 2),
                "minimo": round(df_tendencia['tarifa'].min(), 2)
            }
            
        except Exception as e:
            return {"error": f"Error en análisis: {str(e)}"}
    
    def prediccion_corto_plazo(self, zona: str, equipo: str) -> Dict:
        """
        Genera predicción de precios para los próximos 30 días
        Modelo1 - Predicción basada en tendencias y factores de mercado
        """
        analisis = self.analizar_tendencia_zona(zona, equipo)
        
        if "error" in analisis:
            return analisis
        
        # Aplicar factores de mercado
        tarifa_actual = analisis["tarifa_actual"]
        tendencia_base = analisis["variacion_pct"] / 100
        
        # Calcular influencia de factores externos
        influencia_total = 0
        for factor, config in self.factores_mercado.items():
            peso = config["peso"]
            if config["tendencia"] == "alza":
                influencia_total += peso * 0.02  # +2% por factor al alza
            elif config["tendencia"] == "baja":
                influencia_total -= peso * 0.02  # -2% por factor a la baja
            # tendencia "estable" o "media" no agrega cambios
        
        # Predicción combinando tendencia histórica y factores actuales
        factor_prediccion = tendencia_base + influencia_total
        tarifa_predicha = tarifa_actual * (1 + factor_prediccion)
        
        # Rango de confianza ±5%
        rango_min = tarifa_predicha * 0.95
        rango_max = tarifa_predicha * 1.05
        
        return {
            "zona": zona,
            "equipo": equipo,
            "tarifa_actual": round(tarifa_actual, 2),
            "tarifa_predicha": round(tarifa_predicha, 2),
            "cambio_esperado": round(factor_prediccion * 100, 2),
            "rango_confianza": {
                "minimo": round(rango_min, 2),
                "maximo": round(rango_max, 2)
            },
            "factores_aplicados": self.factores_mercado,
            "confianza": "75%" if len(analisis.get("datos_completos", [])) >= 3 else "50%"
        }
    
    def resumen_mercado_nacional(self) -> Dict:
        """Genera un resumen del estado del mercado a nivel nacional"""
        zonas = ["Norte", "Centro", "Sur"]
        equipos = ["Dry Van", "Flatbed", "Reefer"]
        
        resumen = {
            "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tendencias_por_zona": {},
            "promedios_nacionales": {},
            "factores_mercado": self.factores_mercado
        }
        
        # Análisis por zona
        for zona in zonas:
            resumen["tendencias_por_zona"][zona] = {}
            for equipo in equipos:
                analisis = self.analizar_tendencia_zona(zona, equipo)
                if "error" not in analisis:
                    resumen["tendencias_por_zona"][zona][equipo] = {
                        "direccion": analisis["direccion"],
                        "variacion_pct": analisis["variacion_pct"],
                        "tarifa_actual": analisis["tarifa_actual"]
                    }
        
        return resumen
    
    def exportar_reporte_tendencias(self, filepath: str = None) -> str:
        """Exporta un reporte completo de tendencias a archivo JSON"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filepath = f"reporte_tendencias_{timestamp}.json"
        
        reporte = {
            "generado": datetime.now().isoformat(),
            "version_modelo": "1.0",
            "resumen_nacional": self.resumen_mercado_nacional(),
            "metadata": {
                "fuentes": list(self.datos_historicos.keys()),
                "algoritmo": "Tendencias_de_mercado v1.0",
                "precision_estimada": "75%"
            }
        }
        
        ruta_completa = os.path.join(os.path.dirname(__file__), filepath)
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        return ruta_completa

# Función de prueba y ejemplo de uso
if __name__ == "__main__":
    print("🚛 Inicializando Modelo1 - Tendencias de Mercado FreightMetrics")
    
    # Crear instancia del analizador
    analizador = TendenciasMercado()
    
    # Ejemplo de análisis
    print("\n📊 Análisis de tendencia Norte - Dry Van:")
    resultado = analizador.analizar_tendencia_zona("Norte", "Dry Van")
    print(f"Resultado: {resultado}")
    
    # Ejemplo de predicción
    print("\n🔮 Predicción para Norte - Dry Van:")
    prediccion = analizador.prediccion_corto_plazo("Norte", "Dry Van")
    print(f"Predicción: {prediccion}")
    
    # Generar reporte completo
    print("\n📄 Generando reporte completo...")
    archivo_reporte = analizador.exportar_reporte_tendencias()
    print(f"Reporte guardado en: {archivo_reporte}")
    
    print("\n✅ Modelo1 ejecutado exitosamente!")