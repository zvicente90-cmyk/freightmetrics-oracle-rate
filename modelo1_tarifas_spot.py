# Modelo1 Tarifas Spot - FreightMetrics
# Algoritmo simplified para cálculo y análisis de tarifas spot México

import json
import os
import pandas as pd
from datetime import datetime

class Modelo1TarifasSpot:
    """
    Modelo1 - Sistema simplificado para cálculo de tarifas spot
    Versión original del algoritmo FreightMetrics
    """
    
    def __init__(self):
        self.version = "1.0"
        self.nombre = "Modelo1 Tarifas Spot"
        self.fecha_creacion = "2026-03-08"
        
        # Cargar datos base
        self.matriz_datos = self._cargar_matriz_comparativa()
        
        # Factores de ajuste por zona (Modelo1 original)
        self.factores_zona = {
            "Norte": {"factor_riesgo": 0.95, "factor_demanda": 1.08},
            "Centro": {"factor_riesgo": 1.02, "factor_demanda": 1.15},
            "Sur": {"factor_riesgo": 1.18, "factor_demanda": 0.92}
        }
        
        # Tipos de equipo con multiplicadores (Modelo1)
        self.equipos_multiplicador = {
            "Caja Seca (Dry Van)": 1.0,        # Base
            "Plataforma (Flatbed)": 1.12,     # +12% riesgo carga
            "Refrigerado (Reefer)": 1.35,     # +35% por refrigeración 
            "Full (Doble)": 1.78               # +78% por peso y tamaño
        }
    
    def _cargar_matriz_comparativa(self):
        """Carga la matriz de datos comparativos"""
        try:
            matriz_file = os.path.join(os.path.dirname(__file__), "matriz_comparativa_mx.json")
            with open(matriz_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Archivo matriz_comparativa_mx.json no encontrado")
            return {}
    
    def calcular_tarifa_spot_basica(self, zona, equipo, distancia_km=100):
        """
        Cálculo básico de tarifa spot usando Modelo1
        Fórmula original: Tarifa = (Costos Base * Factor Zona * Factor Equipo) / km
        """
        try:
            # Obtener datos de la matriz para 2026-Mar (datos más recientes)
            datos_zona = self.matriz_datos["matriz"]["2026"]["Mar"][zona]
            df_zona = pd.DataFrame(datos_zona)
            
            # Buscar la tarifa spot final
            tarifa_final_row = df_zona[df_zona["Componente"] == "TARIFA SPOT FINAL"]
            
            if tarifa_final_row.empty:
                return {"error": "No se encontró tarifa final en los datos"}
            
            if equipo not in tarifa_final_row.columns:
                return {"error": f"Equipo {equipo} no encontrado en datos"}
            
            # Tarifa base de la matriz
            tarifa_base = tarifa_final_row[equipo].values[0]
            
            if pd.isna(tarifa_base) or tarifa_base <= 0:
                return {"error": "Tarifa base inválida"}
            
            # Aplicar factores del Modelo1
            factor_zona = self.factores_zona[zona]["factor_demanda"]
            factor_equipo = self.equipos_multiplicador.get(equipo, 1.0)
            
            # Cálculo Modelo1
            tarifa_ajustada = tarifa_base * factor_zona * factor_equipo
            
            # Para viajes largos, aplicar descuento por volumen
            if distancia_km > 500:
                descuento_volumen = 0.95  # 5% descuento
                tarifa_ajustada *= descuento_volumen
            
            return {
                "zona": zona,
                "equipo": equipo,
                "distancia_km": distancia_km,
                "tarifa_base": round(tarifa_base, 2),
                "tarifa_por_km": round(tarifa_ajustada, 2),
                "tarifa_total": round(tarifa_ajustada * distancia_km, 2),
                "factores_aplicados": {
                    "factor_zona": factor_zona,
                    "factor_equipo": factor_equipo,
                    "descuento_volumen": 0.95 if distancia_km > 500 else 1.0
                },
                "modelo": self.nombre,
                "version": self.version
            }
            
        except Exception as e:
            return {"error": f"Error en cálculo: {str(e)}"}
    
    def comparar_zonas_por_equipo(self, equipo, distancia_km=100):
        """Compara tarifas del mismo equipo en todas las zonas"""
        zonas = ["Norte", "Centro", "Sur"]
        comparacion = {
            "equipo": equipo,
            "distancia_km": distancia_km,
            "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "resultados": {}
        }
        
        for zona in zonas:
            resultado = self.calcular_tarifa_spot_basica(zona, equipo, distancia_km)
            if "error" not in resultado:
                comparacion["resultados"][zona] = {
                    "tarifa_por_km": resultado["tarifa_por_km"],
                    "tarifa_total": resultado["tarifa_total"],
                    "factor_zona": resultado["factores_aplicados"]["factor_zona"]
                }
            else:
                comparacion["resultados"][zona] = {"error": resultado["error"]}
        
        # Encontrar la zona más económica y más cara
        tarifas_validas = {}
        for zona, datos in comparacion["resultados"].items():
            if "error" not in datos:
                tarifas_validas[zona] = datos["tarifa_total"]
        
        if tarifas_validas:
            zona_economica = min(tarifas_validas, key=tarifas_validas.get)
            zona_cara = max(tarifas_validas, key=tarifas_validas.get)
            
            comparacion["resumen"] = {
                "zona_mas_economica": zona_economica,
                "tarifa_minima": tarifas_validas[zona_economica],
                "zona_mas_cara": zona_cara,
                "tarifa_maxima": tarifas_validas[zona_cara],
                "diferencia_pct": round(
                    ((tarifas_validas[zona_cara] - tarifas_validas[zona_economica]) 
                     / tarifas_validas[zona_economica]) * 100, 2
                )
            }
        
        return comparacion
    
    def matriz_completa_tarifas(self):
        """Genera matriz completa de tarifas para todos los equipos y zonas"""
        zonas = ["Norte", "Centro", "Sur"]
        equipos = list(self.equipos_multiplicador.keys())
        
        matriz_completa = {
            "modelo": self.nombre,
            "version": self.version,
            "fecha_generacion": datetime.now().isoformat(),
            "distancia_base": 100,  # km
            "matriz": {}
        }
        
        for equipo in equipos:
            matriz_completa["matriz"][equipo] = {}
            for zona in zonas:
                resultado = self.calcular_tarifa_spot_basica(zona, equipo)
                if "error" not in resultado:
                    matriz_completa["matriz"][equipo][zona] = {
                        "tarifa_km": resultado["tarifa_por_km"],
                        "tarifa_100km": resultado["tarifa_total"]
                    }
                else:
                    matriz_completa["matriz"][equipo][zona] = {"error": resultado["error"]}
        
        return matriz_completa
    
    def exportar_modelo(self, archivo="modelo1_tarifas_spot.json"):
        """Exporta el modelo completo con todas las tarifas calculadas"""
        ruta_archivo = os.path.join(os.path.dirname(__file__), archivo)
        
        datos_exportacion = {
            "informacion_modelo": {
                "nombre": self.nombre,
                "version": self.version,
                "fecha_creacion": self.fecha_creacion,
                "fecha_exportacion": datetime.now().isoformat()
            },
            "parametros": {
                "factores_zona": self.factores_zona,
                "equipos_multiplicador": self.equipos_multiplicador
            },
            "matriz_tarifas": self.matriz_completa_tarifas()
        }
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_exportacion, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Modelo1 exportado a: {ruta_archivo}")
        return ruta_archivo

# Función principal de demostración
def ejecutar_modelo1():
    """Ejecuta una demostración completa del Modelo1"""
    print("🚛 Iniciando Modelo1 Tarifas Spot FreightMetrics")
    print("=" * 50)
    
    # Crear instancia del modelo
    modelo = Modelo1TarifasSpot()
    
    # Ejemplo 1: Cálculo básico
    print("\n📊 Ejemplo 1: Cálculo básico Norte - Dry Van, 100km")
    resultado1 = modelo.calcular_tarifa_spot_basica("Norte", "Caja Seca (Dry Van)", 100)
    if "error" not in resultado1:
        print(f"Tarifa por km: ${resultado1['tarifa_por_km']:.2f}")
        print(f"Tarifa total: ${resultado1['tarifa_total']:,.2f}")
    else:
        print(f"Error: {resultado1['error']}")
    
    # Ejemplo 2: Comparación entre zonas
    print("\n🔍 Ejemplo 2: Comparación Refrigerado entre zonas")
    comparacion = modelo.comparar_zonas_por_equipo("Refrigerado (Reefer)", 200)
    if "resumen" in comparacion:
        print(f"Zona más económica: {comparacion['resumen']['zona_mas_economica']}")
        print(f"Zona más cara: {comparacion['resumen']['zona_mas_cara']}")
        print(f"Diferencia: {comparacion['resumen']['diferencia_pct']:.1f}%")
    
    # Ejemplo 3: Exportar modelo completo
    print("\n💾 Ejemplo 3: Exportando modelo completo...")
    archivo_exportado = modelo.exportar_modelo()
    
    print(f"\n🎯 Modelo1 ejecutado exitosamente!")
    print(f"Archivo generado: {archivo_exportado}")
    
    return modelo

# Ejecutar si se llama directamente
if __name__ == "__main__":
    modelo1 = ejecutar_modelo1()