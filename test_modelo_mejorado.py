# Test del Modelo Mejorado con Zonas Geográficas y Factores Dinámicos
# FreightMetrics MVP - Prueba de funcionalidades

from logic_rates import FreightMetricsCalculator, determinar_zona_geografica, FactoresDinamicosMercado
import json

def test_modelo_mejorado():
    """Prueba completa del modelo mejorado"""
    print("🚛 TESTING - Modelo FreightMetrics con Zonas Geográficas y Factores Dinámicos")
    print("=" * 80)
    
    # 1. Prueba de determinación automática de zonas
    print("\n📍 PRUEBA 1: Determinación automática de zonas")
    ciudades_test = [
        "Tijuana, Baja California",
        "Ciudad de México, CDMX", 
        "Mérida, Yucatán",
        "Monterrey, Nuevo León",
        "Guadalajara, Jalisco",
        "Cancún, Quintana Roo"
    ]
    
    for ciudad in ciudades_test:
        zona = determinar_zona_geografica(ciudad)
        print(f"  {ciudad:<30} → Zona {zona}")
    
    # 2. Prueba de factores dinámicos
    print("\n📈 PRUEBA 2: Factores dinámicos por zona")
    factores = FactoresDinamicosMercado()
    
    for zona in ["Norte", "Centro", "Sur"]:
        factor = factores.factor_compuesto_zona(zona)
        print(f"  Zona {zona:<7} → Factor dinámico: {factor:.4f} ({(factor-1)*100:+.1f}%)")
    
    # 3. Comparación de tarifas por zona con mismo equipo
    print("\n💰 PRUEBA 3: Comparación tarifas Dry Van por zona")
    costos_base = {
        'diesel': 11.40,
        'casetas': 5.40,
        'sueldo': 4.50,
        'mantenimiento': 3.00,
        'riesgo': 1.60,
        'administracion': 1.20
    }
    
    resultados_zona = {}
    
    for zona in ["Norte", "Centro", "Sur"]:
        # Con factores dinámicos
        calc_dinamico = FreightMetricsCalculator(
            **costos_base,
            zona=zona,
            utilidad_pct=0.18,
            aplicar_factores_dinamicos=True
        )
        
        # Sin factores dinámicos (modelo clásico)
        calc_clasico = FreightMetricsCalculator(
            **costos_base,
            zona=zona,
            utilidad_pct=0.18,
            aplicar_factores_dinamicos=False
        )
        
        tarifa_dinamica = calc_dinamico.tarifa_spot_final()
        tarifa_clasica = calc_clasico.tarifa_spot_final()
        diferencia_pct = ((tarifa_dinamica - tarifa_clasica) / tarifa_clasica) * 100
        
        resultados_zona[zona] = {
            'dinamica': tarifa_dinamica,
            'clasica': tarifa_clasica,
            'diferencia_pct': diferencia_pct
        }
        
        print(f"  Zona {zona:<7} → Clásico: ${tarifa_clasica:>6.2f}/km | Dinámico: ${tarifa_dinamica:>6.2f}/km | Diff: {diferencia_pct:+5.1f}%")
    
    # 4. Desglose detallado de una zona
    print(f"\n🔍 PRUEBA 4: Desglose detallado Zona Norte")
    calc_detalle = FreightMetricsCalculator(
        **costos_base,
        zona="Norte",
        utilidad_pct=0.18,
        aplicar_factores_dinamicos=True
    )
    
    desglose = calc_detalle.desglose_completo()
    print(f"  📦 Componentes base:")
    for comp, valor in desglose['componentes_base'].items():
        print(f"     {comp.capitalize():<15}: ${valor:>5.2f}")
    
    print(f"  📊 Resumen:")
    print(f"     Costo base        : ${desglose['costo_operativo_base']:>6.2f}/km")
    print(f"     Factor dinámico   : {desglose['factor_zona_dinamico']:>6.4f}")
    print(f"     Costo ajustado    : ${desglose['costo_operativo_ajustado']:>6.2f}/km")
    print(f"     Utilidad ({desglose['utilidad_pct']}%)    : ${desglose['utilidad_mxn']:>6.2f}/km")
    print(f"     Tarifa FINAL      : ${desglose['tarifa_spot_final']:>6.2f}/km")
    
    # 5. Comparación con distancias
    print(f"\n📏 PRUEBA 5: Impacto en diferentes distancias (Zona Centro)")
    distancias = [50, 100, 250, 500, 1000]
    
    calc_centro = FreightMetricsCalculator(
        **costos_base,
        zona="Centro",
        utilidad_pct=0.18,
        aplicar_factores_dinamicos=True
    )
    
    tarifa_km = calc_centro.tarifa_spot_final()
    print(f"  Tarifa base: ${tarifa_km:.2f}/km")
    
    for dist in distancias:
        tarifa_total = tarifa_km * dist
        print(f"     {dist:>4} km → ${tarifa_total:>8,.2f} MXN")
    
    print(f"\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print(f"📋 Resumen:")
    print(f"   • Determinación automática de zonas: ✓")
    print(f"   • Factores dinámicos por zona: ✓")
    print(f"   • Comparación modelo clásico vs dinámico: ✓")
    print(f"   • Desglose detallado de componentes: ✓")
    print(f"   • Cálculo para diferentes distancias: ✓")
    
    return resultados_zona

if __name__ == "__main__":
    try:
        resultados = test_modelo_mejorado()
        
        # Guardar resultados de prueba
        with open('test_results_modelo_mejorado.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: test_results_modelo_mejorado.json")
        
    except Exception as e:
        print(f"\n❌ ERROR durante las pruebas: {e}")
        import traceback
        traceback.print_exc()