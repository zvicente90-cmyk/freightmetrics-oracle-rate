import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import pandas as pd

class FreightMetricsHistoryManager:
    """
    Gestor de histórico de tarifas FreightMetrics
    Maneja datos semanales, mensuales y por rutas específicas de tarifas spot MX
    """
    
    def __init__(self, history_file="freightmetrics_historical.json"):
        self.history_file = history_file
        self.current_file = "index_spot_tarifas.json"
        self.data = self.load_historical_data()
    
    def load_historical_data(self) -> Dict:
        """Cargar datos históricos desde el archivo JSON"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_empty_structure()
    
    def save_historical_data(self):
        """Guardar datos históricos al archivo JSON"""
        self.data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def create_empty_structure(self) -> Dict:
        """Crear estructura vacía para datos históricos FreightMetrics"""
        return {
            "metadata": {
                "created": datetime.now().strftime('%Y-%m-%d'),
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "source": "FreightMetrics México",
                "currency": "MXN",
                "notes": "Histórico de tarifas spot mexicanas por rutas y regiones"
            },
            "weekly": {},      # Datos por semana
            "monthly": {},     # Datos por mes
            "routes": {},      # Datos por ruta específica
            "regions": {},     # Datos agregados por región
            "equipment": {},   # Datos agregados por tipo de equipo
            "current": {
                "semana_actual": f"week_{datetime.now().isocalendar()[1]:02d}",
                "mes_actual": f"{datetime.now().year}-{datetime.now().month:02d}",
                "año_actual": str(datetime.now().year)
            }
        }
    
    def add_monthly_data(self, year_month: str, routes_data: List[Dict]):
        """
        Agregar datos mensuales completos
        
        routes_data formato:
        [
            {
                "Región": "Querétaro",
                "Origen": "Querétaro", 
                "Destino": "Nuevo Laredo",
                "Nodo": "Nuevo Laredo",
                "Distancia_km": 815,
                "Equipo": "Caja Seca 53'",
                "Tarifa_MXN": 26551
            },
            ...
        ]
        """
        year = year_month[:4]
        month = year_month[5:7]
        
        # Inicializar estructura si no existe
        if year not in self.data["monthly"]:
            self.data["monthly"][year] = {}
        
        # Calcular variaciones comparando con mes anterior
        previous_month_data = self.get_previous_month_data(year, month)
        
        # Procesar datos por rutas
        monthly_entry = {
            "fecha": year_month,
            "total_rutas": len(routes_data),
            "rutas": {}
        }
        
        route_variations = {}
        
        for route in routes_data:
            route_key = f"{route['Región']}_{route['Origen']}_{route['Destino']}_{route['Equipo']}"
            
            # Calcular variación vs mes anterior
            variacion_pct = 0
            tendencia = "nuevo"  # nuevo, estable, alcista, bajista
            
            if (previous_month_data and 
                "rutas" in previous_month_data and 
                route_key in previous_month_data["rutas"]):
                prev_tarifa = previous_month_data["rutas"][route_key]["tarifa"]
                if prev_tarifa:
                    variacion_pct = round(((route['Tarifa_MXN'] - prev_tarifa) / prev_tarifa) * 100, 2)
                    if variacion_pct > 2:
                        tendencia = "alcista"
                    elif variacion_pct < -2:
                        tendencia = "bajista"
                    else:
                        tendencia = "estable"
            
            monthly_entry["rutas"][route_key] = {
                "region": route['Región'],
                "origen": route['Origen'],
                "destino": route['Destino'], 
                "nodo": route['Nodo'],
                "distancia_km": route['Distancia_km'],
                "equipo": route['Equipo'],
                "tarifa": route['Tarifa_MXN'],
                "tarifa_por_km": round(route['Tarifa_MXN'] / route['Distancia_km'], 2),
                "variacion_pct": variacion_pct,
                "tendencia": tendencia
            }
            
            route_variations[route_key] = variacion_pct
        
        # Calcular estadísticas generales del mes
        tarifas = [route['Tarifa_MXN'] for route in routes_data]
        tarifas_por_km = [route['Tarifa_MXN'] / route['Distancia_km'] for route in routes_data]
        
        monthly_entry["estadisticas"] = {
            "tarifa_promedio": round(sum(tarifas) / len(tarifas), 2),
            "tarifa_minima": min(tarifas),
            "tarifa_maxima": max(tarifas),
            "tarifa_por_km_promedio": round(sum(tarifas_por_km) / len(tarifas_por_km), 2),
            "rutas_alcistas": len([v for v in route_variations.values() if v > 2]),
            "rutas_bajistas": len([v for v in route_variations.values() if v < -2]),
            "rutas_estables": len([v for v in route_variations.values() if -2 <= v <= 2])
        }
        
        self.data["monthly"][year][month] = monthly_entry
        
        # Agregar datos agregados por región y equipo
        self._update_region_aggregates(year_month, routes_data)
        self._update_equipment_aggregates(year_month, routes_data)
        
        self.save_historical_data()
        print(f"✅ Datos mensuales agregados: {year_month} ({len(routes_data)} rutas)")
    
    def _update_region_aggregates(self, year_month: str, routes_data: List[Dict]):
        """Actualizar agregados por región"""
        region_stats = {}
        
        for route in routes_data:
            region = route['Región']
            if region not in region_stats:
                region_stats[region] = {
                    'tarifas': [],
                    'distancias': [],
                    'equipos': set(),
                    'rutas_count': 0
                }
            
            region_stats[region]['tarifas'].append(route['Tarifa_MXN'])
            region_stats[region]['distancias'].append(route['Distancia_km'])
            region_stats[region]['equipos'].add(route['Equipo'])
            region_stats[region]['rutas_count'] += 1
        
        # Guardar estadísticas por región
        if year_month not in self.data["regions"]:
            self.data["regions"][year_month] = {}
        
        for region, stats in region_stats.items():
            self.data["regions"][year_month][region] = {
                'tarifa_promedio': round(sum(stats['tarifas']) / len(stats['tarifas']), 2),
                'tarifa_minima': min(stats['tarifas']),
                'tarifa_maxima': max(stats['tarifas']),
                'distancia_promedio': round(sum(stats['distancias']) / len(stats['distancias']), 2),
                'tipos_equipo': list(stats['equipos']),
                'total_rutas': stats['rutas_count']
            }
    
    def _update_equipment_aggregates(self, year_month: str, routes_data: List[Dict]):
        """Actualizar agregados por tipo de equipo"""
        equipment_stats = {}
        
        for route in routes_data:
            equipo = route['Equipo']
            if equipo not in equipment_stats:
                equipment_stats[equipo] = {
                    'tarifas': [],
                    'distancias': [],
                    'regiones': set(),
                    'rutas_count': 0
                }
            
            equipment_stats[equipo]['tarifas'].append(route['Tarifa_MXN'])
            equipment_stats[equipo]['distancias'].append(route['Distancia_km'])
            equipment_stats[equipo]['regiones'].add(route['Región'])
            equipment_stats[equipo]['rutas_count'] += 1
        
        # Guardar estadísticas por equipo
        if year_month not in self.data["equipment"]:
            self.data["equipment"][year_month] = {}
        
        for equipo, stats in equipment_stats.items():
            self.data["equipment"][year_month][equipo] = {
                'tarifa_promedio': round(sum(stats['tarifas']) / len(stats['tarifas']), 2),
                'tarifa_minima': min(stats['tarifas']),
                'tarifa_maxima': max(stats['tarifas']),
                'tarifa_por_km_promedio': round(
                    sum(t/d for t, d in zip(stats['tarifas'], stats['distancias'])) / len(stats['tarifas']), 2
                ),
                'regiones': list(stats['regiones']),
                'total_rutas': stats['rutas_count']
            }
    
    def get_previous_month_data(self, year: str, month: str) -> Optional[Dict]:
        """Obtener datos del mes anterior para calcular variaciones"""
        try:
            prev_month_num = int(month) - 1
            if prev_month_num < 1:
                prev_month_num = 12
                prev_year = str(int(year) - 1)
            else:
                prev_year = year
                
            prev_month_str = f"{prev_month_num:02d}"
            
            if (prev_year in self.data["monthly"] and 
                prev_month_str in self.data["monthly"][prev_year]):
                return self.data["monthly"][prev_year][prev_month_str]
                
            return None
        except:
            return None
    
    def get_monthly_data(self, year: str, month: str) -> Optional[Dict]:
        """Obtener datos de un mes específico"""
        try:
            return self.data["monthly"][year][month]
        except KeyError:
            return None
    
    def get_route_history(self, region: str, origen: str, destino: str, equipo: str) -> List[Dict]:
        """Obtener historial completo de una ruta específica"""
        route_key = f"{region}_{origen}_{destino}_{equipo}"
        history = []
        
        for year, months in self.data["monthly"].items():
            for month, month_data in months.items():
                if ("rutas" in month_data and 
                    route_key in month_data["rutas"]):
                    
                    route_data = month_data["rutas"][route_key].copy()
                    route_data["fecha"] = f"{year}-{month}"
                    history.append(route_data)
        
        return sorted(history, key=lambda x: x["fecha"])
    
    def get_region_summary(self, region: str, last_n_months: int = 6) -> Dict:
        """Obtener resumen de una región específica"""
        region_data = []
        
        # Obtener datos de los últimos N meses
        for year_month in sorted(self.data["regions"].keys(), reverse=True)[:last_n_months]:
            if region in self.data["regions"][year_month]:
                data = self.data["regions"][year_month][region].copy()
                data["fecha"] = year_month
                region_data.append(data)
        
        if not region_data:
            return {}
        
        # Calcular tendencias
        tarifas_promedio = [d['tarifa_promedio'] for d in region_data]
        if len(tarifas_promedio) >= 2:
            tendencia_general = "alcista" if tarifas_promedio[0] > tarifas_promedio[-1] else "bajista"
            variacion_periodo = round(((tarifas_promedio[0] - tarifas_promedio[-1]) / tarifas_promedio[-1]) * 100, 2)
        else:
            tendencia_general = "insuficiente_data"
            variacion_periodo = 0
        
        return {
            "region": region,
            "periodo_analizado": last_n_months,
            "datos_mensuales": region_data,
            "tendencia_general": tendencia_general,
            "variacion_periodo_pct": variacion_periodo,
            "tarifa_promedio_actual": tarifas_promedio[0] if tarifas_promedio else 0,
            "tarifa_promedio_historica": round(sum(tarifas_promedio) / len(tarifas_promedio), 2) if tarifas_promedio else 0
        }
    
    def get_equipment_summary(self, equipo: str, last_n_months: int = 6) -> Dict:
        """Obtener resumen de un tipo de equipo específico"""
        equipment_data = []
        
        # Obtener datos de los últimos N meses
        for year_month in sorted(self.data["equipment"].keys(), reverse=True)[:last_n_months]:
            if equipo in self.data["equipment"][year_month]:
                data = self.data["equipment"][year_month][equipo].copy()
                data["fecha"] = year_month
                equipment_data.append(data)
        
        if not equipment_data:
            return {}
        
        # Calcular tendencias
        tarifas_promedio = [d['tarifa_promedio'] for d in equipment_data]
        tarifas_por_km = [d['tarifa_por_km_promedio'] for d in equipment_data]
        
        if len(tarifas_promedio) >= 2:
            tendencia_general = "alcista" if tarifas_promedio[0] > tarifas_promedio[-1] else "bajista"
            variacion_periodo = round(((tarifas_promedio[0] - tarifas_promedio[-1]) / tarifas_promedio[-1]) * 100, 2)
        else:
            tendencia_general = "insuficiente_data"
            variacion_periodo = 0
        
        return {
            "equipo": equipo,
            "periodo_analizado": last_n_months,
            "datos_mensuales": equipment_data,
            "tendencia_general": tendencia_general,
            "variacion_periodo_pct": variacion_periodo,
            "tarifa_promedio_actual": tarifas_promedio[0] if tarifas_promedio else 0,
            "tarifa_por_km_actual": tarifas_por_km[0] if tarifas_por_km else 0,
            "tarifa_promedio_historica": round(sum(tarifas_promedio) / len(tarifas_promedio), 2) if tarifas_promedio else 0
        }
    
    def import_from_current_file(self):
        """Importar datos desde el archivo actual index_spot_tarifas.json"""
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            if "tarifas" in current_data:
                for month_data in current_data["tarifas"]:
                    year_month = month_data["mes"]
                    routes_data = month_data["tabla"]
                    
                    print(f"📥 Importando datos de {year_month}...")
                    self.add_monthly_data(year_month, routes_data)
            
            print(f"✅ Importación completada desde {self.current_file}")
                    
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {self.current_file}")
        except Exception as e:
            print(f"❌ Error durante la importación: {str(e)}")
    
    def export_to_excel(self, filename: str = None):
        """Exportar todos los datos históricos a Excel"""
        if not filename:
            filename = f"freightmetrics_historical_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja de resumen por regiones
            regions_summary = []
            for year_month, regions in self.data["regions"].items():
                for region, stats in regions.items():
                    row = {"fecha": year_month, "region": region}
                    row.update(stats)
                    regions_summary.append(row)
            
            if regions_summary:
                pd.DataFrame(regions_summary).to_excel(writer, sheet_name="Regiones", index=False)
            
            # Hoja de resumen por equipos
            equipment_summary = []
            for year_month, equipos in self.data["equipment"].items():
                for equipo, stats in equipos.items():
                    row = {"fecha": year_month, "equipo": equipo}
                    row.update({k: v for k, v in stats.items() if k != "regiones"})
                    equipment_summary.append(row)
            
            if equipment_summary:
                pd.DataFrame(equipment_summary).to_excel(writer, sheet_name="Equipos", index=False)
            
            # Hoja con todas las rutas
            all_routes = []
            for year, months in self.data["monthly"].items():
                for month, month_data in months.items():
                    if "rutas" in month_data:
                        for route_key, route_data in month_data["rutas"].items():
                            row = {"fecha": f"{year}-{month}"}
                            row.update(route_data)
                            all_routes.append(row)
            
            if all_routes:
                pd.DataFrame(all_routes).to_excel(writer, sheet_name="Rutas_Detallado", index=False)
        
        print(f"✅ Datos exportados a: {filename}")


def quick_import_freightmetrics():
    """
    Función de ayuda rápida para importar datos desde index_spot_tarifas.json
    """
    print("🚛 FreightMetrics - Importador Histórico")
    print("=" * 50)
    
    manager = FreightMetricsHistoryManager()
    manager.import_from_current_file()
    
    print(f"📊 Archivo histórico actualizado: {manager.history_file}")


def generate_reports():
    """
    Generar reportes de análisis de todas las regiones y equipos
    """
    print("📈 FreightMetrics - Generador de Reportes")
    print("=" * 50)
    
    manager = FreightMetricsHistoryManager()
    
    # Reporte por regiones
    print("\n🗺️ ANÁLISIS POR REGIONES:")
    print("-" * 30)
    
    regiones_disponibles = set()
    for year_month, regions in manager.data["regions"].items():
        regiones_disponibles.update(regions.keys())
    
    for region in sorted(regiones_disponibles):
        summary = manager.get_region_summary(region, 3)  # Últimos 3 meses
        if summary:
            print(f"📍 {region}:")
            print(f"   Tarifa actual: ${summary['tarifa_promedio_actual']:,.2f} MXN")
            print(f"   Tendencia: {summary['tendencia_general'].upper()}")
            print(f"   Variación: {summary['variacion_periodo_pct']:+.1f}%")
            print()
    
    # Reporte por equipos
    print("\n🚚 ANÁLISIS POR TIPO DE EQUIPO:")
    print("-" * 30)
    
    equipos_disponibles = set()
    for year_month, equipment in manager.data["equipment"].items():
        equipos_disponibles.update(equipment.keys())
    
    for equipo in sorted(equipos_disponibles):
        summary = manager.get_equipment_summary(equipo, 3)  # Últimos 3 meses
        if summary:
            print(f"🚛 {equipo}:")
            print(f"   Tarifa promedio: ${summary['tarifa_promedio_actual']:,.2f} MXN")
            print(f"   Tarifa por km: ${summary['tarifa_por_km_actual']:.2f} MXN/km")
            print(f"   Tendencia: {summary['tendencia_general'].upper()}")
            print(f"   Variación: {summary['variacion_periodo_pct']:+.1f}%")
            print()
    
    # Exportar a Excel
    manager.export_to_excel()
    print("✅ Reportes generados y exportados a Excel")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "import":
            quick_import_freightmetrics()
        elif sys.argv[1] == "report":
            generate_reports()
        else:
            print("Uso: python freightmetrics_history_manager.py [import|report]")
    else:
        # Ejecutar importador por defecto
        quick_import_freightmetrics()