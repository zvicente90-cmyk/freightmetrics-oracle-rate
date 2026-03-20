import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class DATHistoryManager:
    """
    Gestor de histórico de tarifas DAT para FreightMetrics
    Maneja datos semanales y mensuales de tarifas spot
    """
    
    def __init__(self, history_file="dat_rates_historical.json"):
        self.history_file = history_file
        self.current_file = "dat_rates_us.json"
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
        self.data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def create_empty_structure(self) -> Dict:
        """Crear estructura vacía para datos históricos"""
        return {
            "metadata": {
                "created": datetime.now().strftime('%Y-%m-%d'),
                "last_updated": datetime.now().strftime('%Y-%m-%d'),
                "source": "DAT Freight & Analytics",
                "notes": "Histórico de tarifas spot semanales y mensuales"
            },
            "weekly": {},
            "monthly": {},
            "current": {
                "semana_actual": f"week_{datetime.now().isocalendar()[1]:02d}",
                "mes_actual": f"{datetime.now().month:02d}",
                "año_actual": str(datetime.now().year)
            }
        }
    
    def add_weekly_data(self, year: str, month: str, week: str, 
                       fecha_inicio: str, fecha_fin: str, rates_data: Dict):
        """
        Agregar datos semanales
        
        rates_data formato ejemplo:
        {
            "Caja Seca (Dry Van)": {"promedio": 2.32, "minimo": 2.20, "maximo": 2.45},
            "Refrigerado (Reefer)": {"promedio": 2.81, "minimo": 2.65, "maximo": 2.95},
            "Plataforma (Flatbed)": {"promedio": 2.59, "minimo": 2.45, "maximo": 2.70}
        }
        """
        if year not in self.data["weekly"]:
            self.data["weekly"][year] = {}
        if month not in self.data["weekly"][year]:
            self.data["weekly"][year][month] = {}
        
        # Calcular variaciones si existe semana anterior
        previous_week_data = self.get_previous_week_data(year, month, week)
        
        weekly_entry = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "tarifas": {}
        }
        
        for equipo, data in rates_data.items():
            variacion_pct = 0
            tendencia = "estable"
            
            if previous_week_data and equipo in previous_week_data["tarifas"]:
                prev_promedio = previous_week_data["tarifas"][equipo]["promedio"]
                if prev_promedio:
                    variacion_pct = round(((data["promedio"] - prev_promedio) / prev_promedio) * 100, 2)
                    if variacion_pct > 1:
                        tendencia = "alcista"
                    elif variacion_pct < -1:
                        tendencia = "bajista"
            
            weekly_entry["tarifas"][equipo] = {
                "promedio": data["promedio"],
                "minimo": data["minimo"],
                "maximo": data["maximo"],
                "variacion_pct": variacion_pct,
                "tendencia": tendencia
            }
        
        self.data["weekly"][year][month][week] = weekly_entry
        self.save_historical_data()
        
        # Actualizar archivo actual con los nuevos datos
        self.update_current_rates(rates_data)
    
    def update_current_rates(self, rates_data: Dict):
        """Actualizar archivo de tarifas actual con los datos más recientes"""
        current_data = {
            "fecha_actualizacion": datetime.now().strftime('%Y-%m-%d'),
            "fuente": "DAT Freight & Analytics",
            "tarifas": {}
        }
        
        for equipo, data in rates_data.items():
            current_data["tarifas"][equipo] = data["promedio"]
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    def get_previous_week_data(self, year: str, month: str, week: str) -> Optional[Dict]:
        """Obtener datos de la semana anterior para calcular variaciones"""
        try:
            # Convertir week string a número
            current_week_num = int(week.replace('week_', ''))
            prev_week_num = current_week_num - 1
            prev_week_str = f"week_{prev_week_num:02d}"
            
            # Buscar en el mismo mes
            if (year in self.data["weekly"] and 
                month in self.data["weekly"][year] and 
                prev_week_str in self.data["weekly"][year][month]):
                return self.data["weekly"][year][month][prev_week_str]
            
            # Si no existe, buscar en el mes anterior
            prev_month_num = int(month) - 1
            if prev_month_num < 1:
                prev_month_num = 12
                prev_year = str(int(year) - 1)
            else:
                prev_year = year
            
            prev_month_str = f"{prev_month_num:02d}"
            
            if (prev_year in self.data["weekly"] and 
                prev_month_str in self.data["weekly"][prev_year]):
                # Buscar la última semana del mes anterior
                weeks = list(self.data["weekly"][prev_year][prev_month_str].keys())
                if weeks:
                    last_week = max(weeks)  # última semana disponible
                    return self.data["weekly"][prev_year][prev_month_str][last_week]
            
            return None
        except:
            return None
    
    def get_weekly_data(self, year: str, month: str, week: str) -> Optional[Dict]:
        """Obtener datos de una semana específica"""
        try:
            return self.data["weekly"][year][month][week]
        except KeyError:
            return None
    
    def get_monthly_average(self, year: str, month: str) -> Dict:
        """Calcular promedio mensual basado en datos semanales"""
        if (year not in self.data["weekly"] or 
            month not in self.data["weekly"][year]):
            return {}
        
        monthly_data = {}
        weeks_data = self.data["weekly"][year][month]
        
        # Obtener todas las semanas con datos
        valid_weeks = [week_data for week_data in weeks_data.values() 
                      if week_data["tarifas"]]
        
        if not valid_weeks:
            return {}
        
        # Calcular promedios por equipo
        equipos = ["Caja Seca (Dry Van)", "Refrigerado (Reefer)", "Plataforma (Flatbed)"]
        
        for equipo in equipos:
            promedios = []
            minimos = []
            maximos = []
            
            for week_data in valid_weeks:
                if (equipo in week_data["tarifas"] and 
                    week_data["tarifas"][equipo]["promedio"] is not None):
                    promedios.append(week_data["tarifas"][equipo]["promedio"])
                    minimos.append(week_data["tarifas"][equipo]["minimo"])
                    maximos.append(week_data["tarifas"][equipo]["maximo"])
            
            if promedios:
                monthly_data[equipo] = {
                    "promedio": round(sum(promedios) / len(promedios), 2),
                    "minimo": min(minimos),
                    "maximo": max(maximos)
                }
        
        return monthly_data
    
    def get_week_number(self, date_str: str) -> str:
        """Convertir fecha a número de semana"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            week_num = date_obj.isocalendar()[1]
            return f"week_{week_num:02d}"
        except:
            return f"week_{datetime.now().isocalendar()[1]:02d}"


def quick_add_rates():
    """
    Función de ayuda rápida para agregar datos manualmente
    Usar esta función para agregar datos DAT del lunes
    """
    manager = DATHistoryManager()
    
    print("🚛 FreightMetrics - Agregador Rápido de Tarifas DAT")
    print("=" * 50)
    
    # Obtener fecha actual
    today = datetime.now()
    year = str(today.year)
    month = f"{today.month:02d}"
    week = f"week_{today.isocalendar()[1]:02d}"
    
    print(f"Agregando datos para: {year}-{month}, {week}")
    print(f"Fecha: {today.strftime('%Y-%m-%d')}")
    print()
    
    # Solicitar datos
    rates_data = {}
    equipos = ["Caja Seca (Dry Van)", "Refrigerado (Reefer)", "Plataforma (Flatbed)"]
    
    for equipo in equipos:
        print(f"📦 {equipo}:")
        try:
            promedio = float(input(f"  Promedio (USD/mi): $"))
            minimo = float(input(f"  Mínimo (USD/mi): $"))
            maximo = float(input(f"  Máximo (USD/mi): $"))
            
            rates_data[equipo] = {
                "promedio": promedio,
                "minimo": minimo, 
                "maximo": maximo
            }
        except ValueError:
            print("  ❌ Error en los datos, usando valores por defecto")
            rates_data[equipo] = {"promedio": 2.30, "minimo": 2.10, "maximo": 2.50}
    
    # Calcular fechas de inicio y fin de semana
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    fecha_inicio = monday.strftime('%Y-%m-%d')
    fecha_fin = sunday.strftime('%Y-%m-%d')
    
    # Agregar datos
    manager.add_weekly_data(year, month, week, fecha_inicio, fecha_fin, rates_data)
    
    print(f"✅ Datos agregados exitosamente!")
    print(f"📅 Semana: {fecha_inicio} a {fecha_fin}")
    print(f"📊 Tarifas actualizadas en dat_rates_us.json")
    print(f"📈 Histórico actualizado en dat_rates_historical.json")


if __name__ == "__main__":
    # Ejecutar agregador rápido
    quick_add_rates()