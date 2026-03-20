"""
FreightMetrics MVP - Motor de Inteligencia (Versión Simplificada)
Genera datos sintéticos y lógica de predicción considerando variables mexicanas
Versión sin scikit-learn para compatibilidad inmediata
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import os


class FreightMetricsEngine:
    """Motor de predicción de tarifas de transporte (versión simplificada)"""

    def __init__(self):
        self.is_trained = True  # Simulamos que está entrenado
        self.model_path = "freightmetrics_model.json"

    def generate_synthetic_data(self, n_samples=1000):
        """
        Genera datos sintéticos para simular el entrenamiento
        Considera variables específicas de México: Riesgo, Diesel, Cruce
        """
        np.random.seed(42)

        # Fechas de los últimos 6 meses
        start_date = datetime.now() - timedelta(days=180)
        dates = [start_date + timedelta(days=i) for i in range(n_samples)]

        data = []

        for date in dates:
            # Variables base
            distancia = np.random.uniform(100, 2000)  # km

            # Tipo de carga (0-4)
            tipo_carga = np.random.choice([0, 1, 2, 3, 4])

            # Variables específicas de México
            riesgo_pais = np.random.uniform(0.1, 0.9)
            precio_diesel = np.random.uniform(18, 25)
            tiempo_cruce = np.random.uniform(1, 48)

            # Variables económicas
            inflacion_mxn = np.random.uniform(3, 8)
            tipo_cambio = np.random.uniform(16, 20)

            # Variables de demanda y oferta
            demanda_mercado = np.random.uniform(0.3, 0.9)
            capacidad_disponible = np.random.uniform(0.2, 0.8)

            # Variables temporales
            mes = date.month
            dia_semana = date.weekday()
            es_fin_semana = 1 if dia_semana >= 5 else 0
            es_temporada_alta = 1 if mes in [11, 12, 3, 4] else 0

            # Ruido aleatorio
            ruido = np.random.normal(0, 0.1)

            # Cálculo simplificado de tarifa
            tarifa_base = (
                distancia * 1.8 +  # $1.8 por km base
                tipo_carga * 300 +  # Prima por tipo de carga
                riesgo_pais * 800 +  # Prima por riesgo
                precio_diesel * 8 +  # Impacto del diesel
                tiempo_cruce * 20 +  # Costo por tiempo de cruce
                (1 - capacidad_disponible) * 600 +  # Prima por escasez
                demanda_mercado * 400 +  # Prima por demanda
                es_temporada_alta * 200 +  # Prima temporada alta
                ruido * 500  # Ruido
            )

            # Ajuste final con tipo de cambio
            tarifa_usd = max(300, tarifa_base / tipo_cambio)

            data.append({
                'fecha': date.isoformat(),
                'distancia_km': distancia,
                'tipo_carga': tipo_carga,
                'riesgo_pais': riesgo_pais,
                'precio_diesel': precio_diesel,
                'tiempo_cruce': tiempo_cruce,
                'inflacion_mxn': inflacion_mxn,
                'tipo_cambio': tipo_cambio,
                'demanda_mercado': demanda_mercado,
                'capacidad_disponible': capacidad_disponible,
                'mes': mes,
                'dia_semana': dia_semana,
                'es_fin_semana': es_fin_semana,
                'es_temporada_alta': es_temporada_alta,
                'tarifa_usd': tarifa_usd
            })

        return data

    def train_model(self, force_retrain=False):
        """Entrena/simula el entrenamiento del modelo"""
        if os.path.exists(self.model_path) and not force_retrain:
            print("Cargando modelo existente...")
            with open(self.model_path, 'r') as f:
                self.model_data = json.load(f)
            self.is_trained = True
            return

        print("Generando datos sintéticos...")
        data = self.generate_synthetic_data()

        # Guardar datos de entrenamiento para referencia
        # Convertir tipos numpy a tipos nativos de Python para JSON
        sample_data_serializable = []
        for item in data[:10]:  # Solo guardar 10 ejemplos
            sample_data_serializable.append({
                'fecha': item['fecha'],
                'distancia_km': float(item['distancia_km']),
                'tipo_carga': int(item['tipo_carga']),
                'riesgo_pais': float(item['riesgo_pais']),
                'precio_diesel': float(item['precio_diesel']),
                'tiempo_cruce': float(item['tiempo_cruce']),
                'inflacion_mxn': float(item['inflacion_mxn']),
                'tipo_cambio': float(item['tipo_cambio']),
                'demanda_mercado': float(item['demanda_mercado']),
                'capacidad_disponible': float(item['capacidad_disponible']),
                'mes': int(item['mes']),
                'dia_semana': int(item['dia_semana']),
                'es_fin_semana': int(item['es_fin_semana']),
                'es_temporada_alta': int(item['es_temporada_alta']),
                'tarifa_usd': float(item['tarifa_usd'])
            })

        self.model_data = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(data),
            'features': ['distancia_km', 'tipo_carga', 'riesgo_pais', 'precio_diesel',
                        'tiempo_cruce', 'inflacion_mxn', 'tipo_cambio', 'demanda_mercado',
                        'capacidad_disponible', 'mes', 'dia_semana', 'es_fin_semana', 'es_temporada_alta'],
            'sample_data': sample_data_serializable
        }

        with open(self.model_path, 'w') as f:
            json.dump(self.model_data, f, indent=2)

        self.is_trained = True
        print(f"Modelo simplificado guardado en {self.model_path}")

    def predict_tariff(self, route_data):
        """
        Predice la tarifa para una ruta específica usando lógica simplificada

        Args:
            route_data (dict): Datos de la ruta

        Returns:
            float: Tarifa predicha en USD
        """
        if not self.is_trained:
            raise ValueError("El modelo no está entrenado. Ejecuta train_model() primero.")

        # Extraer variables
        distancia = route_data.get('distancia_km', 500)
        tipo_carga = route_data.get('tipo_carga', 0)
        riesgo_pais = route_data.get('riesgo_pais', 0.3)
        precio_diesel = route_data.get('precio_diesel', 22)
        tiempo_cruce = route_data.get('tiempo_cruce', 6)
        inflacion_mxn = route_data.get('inflacion_mxn', 5.5)
        tipo_cambio = route_data.get('tipo_cambio', 18)
        demanda_mercado = route_data.get('demanda_mercado', 0.7)
        capacidad_disponible = route_data.get('capacidad_disponible', 0.6)
        mes = route_data.get('mes', 2)
        es_temporada_alta = route_data.get('es_temporada_alta', 0)

        # Cálculo simplificado de tarifa (similar al de entrenamiento)
        tarifa_base = (
            distancia * 1.8 +  # $1.8 por km base
            tipo_carga * 300 +  # Prima por tipo de carga
            riesgo_pais * 800 +  # Prima por riesgo
            precio_diesel * 8 +  # Impacto del diesel
            tiempo_cruce * 20 +  # Costo por tiempo de cruce
            (1 - capacidad_disponible) * 600 +  # Prima por escasez
            demanda_mercado * 400 +  # Prima por demanda
            es_temporada_alta * 200  # Prima temporada alta
        )

        # Ajuste final con tipo de cambio
        tarifa_usd = max(300, tarifa_base / tipo_cambio)

        # Agregar variabilidad aleatoria para simular incertidumbre del modelo
        np.random.seed(hash(str(route_data)) % 2**32)
        variabilidad = np.random.uniform(0.9, 1.1)
        tarifa_usd *= variabilidad

        return tarifa_usd

    def get_feature_importance(self):
        """Retorna importancia simulada de características"""
        # Importancia simulada basada en lógica de negocio
        return {
            'riesgo_pais': 0.25,
            'precio_diesel': 0.18,
            'demanda_mercado': 0.15,
            'distancia_km': 0.12,
            'capacidad_disponible': 0.10,
            'tiempo_cruce': 0.08,
            'tipo_carga': 0.06,
            'tipo_cambio': 0.03,
            'inflacion_mxn': 0.02,
            'mes': 0.01,
            'dia_semana': 0.00,
            'es_fin_semana': 0.00,
            'es_temporada_alta': 0.00
        }


# Instancia global del motor
engine = FreightMetricsEngine()

if __name__ == "__main__":
    # Entrenar modelo si se ejecuta directamente
    engine.train_model(force_retrain=True)
    print("Modelo simplificado entrenado exitosamente!")

    # Ejemplo de predicción
    sample_route = {
        'distancia_km': 800,
        'tipo_carga': 0,
        'riesgo_pais': 0.3,
        'precio_diesel': 22,
        'tiempo_cruce': 6,
        'inflacion_mxn': 5.5,
        'tipo_cambio': 18,
        'demanda_mercado': 0.7,
        'capacidad_disponible': 0.6,
        'mes': 2,
        'dia_semana': 1,
        'es_fin_semana': 0,
        'es_temporada_alta': 0
    }

    prediction = engine.predict_tariff(sample_route)
    print(f"Predicción de tarifa: ${prediction:.2f} USD")