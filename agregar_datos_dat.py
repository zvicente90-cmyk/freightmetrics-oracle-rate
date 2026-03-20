"""
🚛 FREIGHTMETRICS - ACTUALIZADOR DE TARIFAS DAT
================================================

INSTRUCCIONES PARA EL LUNES:
1. Entra a DAT y obtén las tarifas actuales
2. Ejecuta este script: python agregar_datos_dat.py  
3. Ingresa las tarifas cuando te las pida
4. ¡Automáticamente actualizará el histórico y las tarifas actuales!

FORMATOS DE DATOS QUE NECESITAS DE DAT:
- Caja Seca (Dry Van): Promedio, Mínimo, Máximo (USD por milla)
- Refrigerado (Reefer): Promedio, Mínimo, Máximo (USD por milla)  
- Plataforma (Flatbed): Promedio, Mínimo, Máximo (USD por milla)
"""

from dat_history_manager import DATHistoryManager, quick_add_rates
from datetime import datetime
import json

def main():
    print("🚛" + "="*60)
    print("   FREIGHTMETRICS - ACTUALIZADOR DE TARIFAS DAT")  
    print("="*62)
    print()
    print("📅 Fecha actual:", datetime.now().strftime('%Y-%m-%d %H:%M'))
    print("📊 Sistema listo para recibir datos DAT")
    print()
    
    # Mostrar datos actuales
    try:
        with open('dat_rates_us.json', 'r') as f:
            current_data = json.load(f)
        print("📋 TARIFAS ACTUALES:")
        print(f"   Última actualización: {current_data.get('fecha_actualizacion', 'N/A')}")
        for equipo, tarifa in current_data.get('tarifas', {}).items():
            print(f"   {equipo}: ${tarifa:.2f} USD/mi")
        print()
    except:
        print("⚠️  Archivo de tarifas actuales no encontrado")
        print()
    
    print("Selecciona una opción:")
    print("1. 📝 Agregar nuevas tarifas DAT (RECOMENDADO)")
    print("2. 📊 Ver histórico de tarifas")
    print("3. 🔄 Salir")
    print()
    
    try:
        opcion = input("Ingresa tu opción (1-3): ")
        
        if opcion == "1":
            print("\n🚀 Iniciando agregador de tarifas...")
            print("-" * 40)
            quick_add_rates()
            
        elif opcion == "2":
            mostrar_historico()
            
        elif opcion == "3":
            print("👋 ¡Hasta luego!")
            
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def mostrar_historico():
    """Mostrar resumen del histórico"""
    manager = DATHistoryManager()
    
    print("\n📈 HISTÓRICO DE TARIFAS DAT")
    print("="*40)
    
    try:
        # Mostrar datos de este año/mes
        year = str(datetime.now().year)
        month = f"{datetime.now().month:02d}"
        
        if year in manager.data["weekly"] and month in manager.data["weekly"][year]:
            print(f"📅 {year}-{month}:")
            weeks = manager.data["weekly"][year][month]
            
            for week_key, week_data in sorted(weeks.items()):
                if week_data.get("tarifas"):
                    print(f"   {week_key} ({week_data['fecha_inicio']} - {week_data['fecha_fin']}):")
                    for equipo, datos in week_data["tarifas"].items():
                        if datos["promedio"] is not None:
                            trend_icon = "📈" if datos["variacion_pct"] > 1 else "📉" if datos["variacion_pct"] < -1 else "➡️"
                            print(f"     {trend_icon} {equipo}: ${datos['promedio']:.2f} ({datos['variacion_pct']:+.1f}%)")
                    print()
        else:
            print("   No hay datos disponibles para este mes")
            
    except Exception as e:
        print(f"❌ Error mostrando histórico: {e}")

if __name__ == "__main__":
    main()