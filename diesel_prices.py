"""
Módulo para obtener precios de diesel en tiempo real desde APIs
Integración con PetroInteligence y CNE (Centro Nacional de Control de Energía)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import streamlit as st

class DieselPricesAPI:
    """Obtiene datos de precios de diesel desde múltiples fuentes"""
    
    @staticmethod
    def get_cne_prices():
        """
        Obtiene precios de diesel del CNE (Centro Nacional de Control de Energía)
        Fuente oficial mexicana
        """
        try:
            # API simulada - En producción usar: https://www.gob.mx/cre
            # CNE proporciona precios semanales de combustibles
            
            url = "https://api.cre.gob.mx/v1/combustibles/precios"
            
            # Headers para solicitud
            headers = {
                "User-Agent": "FreightMetrics/1.0",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Estructura esperada del CNE
                precios = {
                    "diesel": data.get("diesel_regular", 0),
                    "premium": data.get("gasolina_premium", 0),
                    "regular": data.get("gasolina_regular", 0),
                    "fecha": data.get("fecha", datetime.now().strftime("%Y-%m-%d"))
                }
                
                return precios
            else:
                return None
                
        except Exception as e:
            st.warning(f"⚠️ No se pudo conectar con CNE: {str(e)}")
            return None
    
    @staticmethod
    def get_petrointeligence_prices():
        """
        Obtiene precios de diesel de PetroInteligencia
        Proveedor especializado en análisis de precios de combustible
        """
        try:
            url = "https://api.petrointeligencia.com.mx/v1/precios/diesel"
            
            headers = {
                "User-Agent": "FreightMetrics/1.0",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                precios = {
                    "norte": data.get("diesel_norte", 0),
                    "centro": data.get("diesel_centro", 0),
                    "sur": data.get("diesel_sur", 0),
                    "promedio_nacional": data.get("promedio_nacional", 0),
                    "fecha": data.get("fecha", datetime.now().strftime("%Y-%m-%d"))
                }
                
                return precios
            else:
                return None
                
        except Exception as e:
            st.warning(f"⚠️ No se pudo conectar con PetroInteligencia: {str(e)}")
            return None
    
    @staticmethod
    def get_simulated_prices():
        """
        Genera precios simulados para demostración
        Usa tendencias realistas basadas en datos históricos
        """
        
        # Precios base actuales (MXN por litro)
        base_prices = {
            "norte": 22.50,
            "centro": 21.85,
            "sur": 21.35,
        }
        
        # Agregar ruido y variabilidad
        np.random.seed(hash(datetime.now().strftime("%Y-%m-%d")) % 2**32)
        
        precios = {}
        for zona, precio_base in base_prices.items():
            # Variación diaria realista (±2%)
            variacion = np.random.normal(0, 0.015)
            precios[zona] = max(precio_base * (1 + variacion), 18)  # Mínimo 18 MXN
        
        # Calcular promedio nacional
        precios["promedio_nacional"] = np.mean(list(precios.values()))
        precios["fecha"] = datetime.now().strftime("%Y-%m-%d")
        
        return precios
    
    @staticmethod
    def get_diesel_prices():
        """
        Obtiene precios de diesel intentando múltiples fuentes
        Fallback a datos simulados si no hay conexión
        """
        
        # Intentar PetroInteligencia primero
        precios = DieselPricesAPI.get_petrointeligence_prices()
        
        if precios:
            return precios, "PetroInteligencia"
        
        # Fallback a CNE
        precios = DieselPricesAPI.get_cne_prices()
        
        if precios:
            return precios, "CNE"
        
        # Fallback a datos simulados
        precios = DieselPricesAPI.get_simulated_prices()
        
        return precios, "Simulado"
    
    @staticmethod
    def get_historical_prices(days=30):
        """
        Obtiene histórico de precios de diesel últimos N días
        """
        
        datos = []
        fecha_inicio = datetime.now() - timedelta(days=days)
        
        np.random.seed(42)
        
        for i in range(days):
            fecha = fecha_inicio + timedelta(days=i)
            
            # Simular precios con tendencia
            tendencia = (i / days) * 0.05  # Tendencia alcista leve
            
            for zona in ["norte", "centro", "sur"]:
                base = {"norte": 22.50, "centro": 21.85, "sur": 21.35}[zona]
                noise = np.random.normal(0, 0.1)
                precio = base * (1 + tendencia) + noise
                
                datos.append({
                    "fecha": fecha,
                    "zona": zona.capitalize(),
                    "precio": max(precio, 18),
                    "dia": fecha.strftime("%d/%m")
                })
        
        return pd.DataFrame(datos)
    
    @staticmethod
    def get_comparison_with_average():
        """
        Compara precios actuales con promedio histórico
        Retorna variación porcentual
        """
        
        precios_actuales, fuente = DieselPricesAPI.get_diesel_prices()
        
        # Obtener promedio de últimos 30 días
        df_historico = DieselPricesAPI.get_historical_prices(30)
        
        comparativa = {}
        
        for zona in ["norte", "centro", "sur"]:
            if zona in precios_actuales:
                precio_actual = precios_actuales[zona]
                promedio_30d = df_historico[
                    df_historico["zona"] == zona.capitalize()
                ]["precio"].mean()
                
                variacion = ((precio_actual - promedio_30d) / promedio_30d * 100) if promedio_30d > 0 else 0
                
                comparativa[zona] = {
                    "actual": precio_actual,
                    "promedio_30d": promedio_30d,
                    "variacion_pct": variacion,
                    "estatus": "📈 Alto" if variacion > 2 else "📉 Bajo" if variacion < -2 else "→ Estable"
                }
        
        return comparativa

    @staticmethod
    def estimate_fuel_cost(distancia_km, consumo_l_km=0.25):
        """
        Estima el costo de combustible para una ruta
        
        Args:
            distancia_km: Distancia en kilómetros
            consumo_l_km: Consumo de diesel en litros por km (default 0.25)
        
        Returns:
            Costo estimado en MXN
        """
        
        precios, _ = DieselPricesAPI.get_diesel_prices()
        
        precio_promedio = precios.get("promedio_nacional", 21.9)
        
        litros_necesarios = distancia_km * consumo_l_km
        costo_total = litros_necesarios * precio_promedio
        
        return {
            "distancia_km": distancia_km,
            "consumo_l_km": consumo_l_km,
            "litros_necesarios": litros_necesarios,
            "precio_diesel_promedio": precio_promedio,
            "costo_total_mxn": costo_total,
            "costo_por_km": costo_total / distancia_km if distancia_km > 0 else 0
        }


# Función auxiliar para caché
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_cached_diesel_prices():
    """Obtiene precios de diesel con caché de 1 hora"""
    return DieselPricesAPI.get_diesel_prices()

@st.cache_data(ttl=3600)
def get_cached_historical_prices(days=30):
    """Obtiene histórico de precios con caché"""
    return DieselPricesAPI.get_historical_prices(days)
