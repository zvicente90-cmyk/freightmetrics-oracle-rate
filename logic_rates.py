# Arquitectura para cálculo de tarifa Tendencia Spot FreightMetrics
# Tarifa spot = [(CF + CV) * Mn] + Casetas + Factores Dinámicos

import json
import os
from datetime import datetime

class FreightMetricsEngine:
    def __init__(self, costo_fijo, costo_variable, multiplicador_mercado, costo_casetas):
        self.costo_fijo = costo_fijo
        self.costo_variable = costo_variable
        self.multiplicador_mercado = multiplicador_mercado
        self.costo_casetas = costo_casetas

    def calcular_tarifa(self):
        tarifa_base = (self.costo_fijo + self.costo_variable) * self.multiplicador_mercado
        tarifa_final = tarifa_base + self.costo_casetas
        return tarifa_final

# Factores dinámicos del mercado (actualizados en tiempo real)
class FactoresDinamicosMercado:
    def __init__(self):
        self.factores = {
            "diesel_trend": {"valor": 1.05, "descripcion": "Tendencia semanal del diesel (+5%)"},
            "inflacion_sectorial": {"valor": 1.086, "descripcion": "Inflación sectorial autotransporte (8.6%)"},
            "demanda_vs_oferta": {"valor": 1.12, "descripcion": "Relación demanda/oferta actual (+12%)"},
            "temporada": {"valor": self._factor_temporada(), "descripcion": "Factor estacional"},
            "riesgo_zona": {"valor": 1.0, "descripcion": "Ajuste por zona geográfica"}
        }
    
    def _factor_temporada(self):
        """Calcula factor estacional basado en el mes actual"""
        mes_actual = datetime.now().month
        # Temporada alta: Nov-Ene y Jun-Ago
        if mes_actual in [11, 12, 1] or mes_actual in [6, 7, 8]:
            return 1.08  # +8% temporada alta
        # Temporada baja: Feb-Mar y Sep-Oct  
        elif mes_actual in [2, 3] or mes_actual in [9, 10]:
            return 0.96  # -4% temporada baja
        else:
            return 1.0   # Normal
    
    def factor_compuesto_zona(self, zona):
        """Calcula factor dinámico compuesto por zona geográfica"""
        # Factores base por zona (más diferenciados)
        factores_zona = {
            "Norte": {"riesgo": 0.92, "demanda": 1.05, "combustible": 1.02, "operativo": 0.95},
            "Centro": {"riesgo": 1.08, "demanda": 1.18, "combustible": 1.00, "operativo": 1.05},
            "Sur": {"riesgo": 1.25, "demanda": 0.88, "combustible": 0.97, "operativo": 1.12}
        }
        
        factor_zona = factores_zona.get(zona, factores_zona["Centro"])
        
        # Combinar factores de manera más balanceada
        factor_base = (
            self.factores["diesel_trend"]["valor"] * factor_zona["combustible"]  # Impacto combustible
        ) * 0.3 + 0.7  # 30% peso combustible
        
        factor_mercado = (
            self.factores["demanda_vs_oferta"]["valor"] * factor_zona["demanda"] * 0.2 + 0.8  # 20% peso demanda
        )
        
        factor_inflacion = self.factores["inflacion_sectorial"]["valor"] * 0.15 + 0.85  # 15% peso inflación
        
        factor_estacional = self.factores["temporada"]["valor"] * 0.1 + 0.9  # 10% peso temporada
        
        factor_operativo_zona = factor_zona["operativo"]  # Factor específico de eficiencia por zona
        
        # Factor compuesto final (más conservador y diferenciado)
        factor_dinamico = (
            factor_base * factor_mercado * factor_inflacion * factor_estacional * factor_operativo_zona
        )
        
        # Limitar variación entre 80% y 130% para mantener estabilidad
        return min(max(factor_dinamico, 0.80), 1.30)
    
    def obtener_resumen_factores(self, zona):
        """Obtiene descripción legible de los factores aplicados"""
        return {
            "zona": zona,
            "factor_compuesto": self.factor_compuesto_zona(zona),
            "desglose": self.factores,
            "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

# Nuevo modelo de cálculo de tarifa spot por componentes CON zonas geográficas
class FreightMetricsCalculator:
    def __init__(self, diesel, casetas, sueldo, mantenimiento, riesgo, administracion, 
                 zona="Centro", utilidad_pct=0.18, aplicar_factores_dinamicos=True):
        self.diesel = diesel
        self.casetas = casetas
        self.sueldo = sueldo
        self.mantenimiento = mantenimiento
        self.riesgo = riesgo
        self.administracion = administracion
        self.zona = zona
        self.utilidad_pct = utilidad_pct
        self.aplicar_factores_dinamicos = aplicar_factores_dinamicos
        
        # Inicializar factores dinámicos
        if self.aplicar_factores_dinamicos:
            self.factores_dinamicos = FactoresDinamicosMercado()
        else:
            self.factores_dinamicos = None

    def costo_operativo_base(self):
        """Calcula costo operativo sin factores dinámicos"""
        return (
            self.diesel +
            self.casetas +
            self.sueldo +
            self.mantenimiento +
            self.riesgo +
            self.administracion
        )
    
    def factor_zona_aplicado(self):
        """Devuelve el factor dinámico aplicado por zona"""
        if self.factores_dinamicos:
            return self.factores_dinamicos.factor_compuesto_zona(self.zona)
        else:
            return 1.0

    def costo_operativo_ajustado(self):
        """Calcula costo operativo con ajustes dinámicos por zona"""
        costo_base = self.costo_operativo_base()
        factor_zona = self.factor_zona_aplicado()
        return costo_base * factor_zona
    
    def tarifa_spot_final(self):
        """Calcula tarifa spot final con todos los factores aplicados"""
        cpk_ajustado = self.costo_operativo_ajustado()
        utilidad = cpk_ajustado * self.utilidad_pct
        return round(cpk_ajustado + utilidad, 2)
    
    def desglose_completo(self):
        """Proporciona desglose detallado del cálculo"""
        costo_base = self.costo_operativo_base()
        factor_zona = self.factor_zona_aplicado()
        costo_ajustado = self.costo_operativo_ajustado()
        utilidad = costo_ajustado * self.utilidad_pct
        tarifa_final = costo_ajustado + utilidad
        
        desglose = {
            "zona": self.zona,
            "componentes_base": {
                "diesel": self.diesel,
                "casetas": self.casetas,
                "sueldo": self.sueldo,
                "mantenimiento": self.mantenimiento,
                "riesgo": self.riesgo,
                "administracion": self.administracion
            },
            "costo_operativo_base": round(costo_base, 2),
            "factor_zona_dinamico": round(factor_zona, 4),
            "costo_operativo_ajustado": round(costo_ajustado, 2),
            "utilidad_pct": self.utilidad_pct * 100,
            "utilidad_mxn": round(utilidad, 2),
            "tarifa_spot_final": round(tarifa_final, 2)
        }
        
        if self.factores_dinamicos:
            desglose["factores_dinamicos"] = self.factores_dinamicos.obtener_resumen_factores(self.zona)
        
        return desglose

# Función mejorada para determinar zona geográfica basada en ubicación
def determinar_zona_geografica(origen_ciudad, destino_ciudad=None):
    """
    Determina la zona geográfica mexicana basada en la ciudad de origen
    Args:
        origen_ciudad: Ciudad de origen (ej: "Tijuana", "CDMX", "Mérida") 
        destino_ciudad: Ciudad de destino (opcional para promedio)
    Returns:
        str: "Norte", "Centro", o "Sur"
    """
    ciudades_norte = [
        "tijuana", "mexicali", "hermosillo", "culiacán", "mazatlán", "la paz",
        "chihuahua", "ciudad juárez", "torreón", "saltillo", "monterrey", 
        "nuevo laredo", "matamoros", "reynosa", "durango", "aguascalientes"
    ]
    
    ciudades_sur = [
        "acapulco", "chilpancingo", "oaxaca", "tuxtla", "villahermosa", 
        "campeche", "mérida", "cancún", "chetumal", "tapachula", "veracruz",
        "xalapa", "minatitlán", "coatzacoalcos"
    ]
    
    # Normalizar texto
    origen_norm = origen_ciudad.lower().strip()
    
    if any(ciudad in origen_norm for ciudad in ciudades_norte):
        return "Norte"
    elif any(ciudad in origen_norm for ciudad in ciudades_sur):
        return "Sur"
    else:
        return "Centro"  # Por defecto y para CDMX, Guadalajara, etc.

# Ejemplo de uso mejorado:
if __name__ == "__main__":
    print("🚛 FreightMetrics Calculator v2.0 - Con Zonas Geográficas y Factores Dinámicos")
    print("=" * 70)
    
    # Ejemplo 1: Norte con factores dinámicos
    calc_norte = FreightMetricsCalculator(
        diesel=11.40,
        casetas=5.40,
        sueldo=4.50,
        mantenimiento=3.00,
        riesgo=1.60,
        administracion=1.20,
        zona="Norte",
        utilidad_pct=0.18,
        aplicar_factores_dinamicos=True
    )
    
    print(f"\n📊 NORTE - Con factores dinámicos:")
    print(f"Tarifa spot final: ${calc_norte.tarifa_spot_final():.2f}/km")
    
    # Ejemplo 2: Centro sin factores dinámicos (modelo clásico)
    calc_centro = FreightMetricsCalculator(
        diesel=11.40,
        casetas=5.40,
        sueldo=4.50,
        mantenimiento=3.00,
        riesgo=1.60,
        administracion=1.20,
        zona="Centro",
        utilidad_pct=0.18,
        aplicar_factores_dinamicos=False
    )
    
    print(f"\n📊 CENTRO - Modelo clásico:")
    print(f"Tarifa spot final: ${calc_centro.tarifa_spot_final():.2f}/km")
    
    # Ejemplo 3: Desglose completo Sur
    calc_sur = FreightMetricsCalculator(
        diesel=11.40,
        casetas=5.40,
        sueldo=4.50,
        mantenimiento=3.00,
        riesgo=1.60,
        administracion=1.20,
        zona="Sur",
        utilidad_pct=0.18
    )
    
    print(f"\n📊 SUR - Desglose completo:")
    desglose = calc_sur.desglose_completo()
    print(f"Factor zona dinámico: {desglose['factor_zona_dinamico']}")
    print(f"Costo base: ${desglose['costo_operativo_base']:.2f}/km")
    print(f"Costo ajustado: ${desglose['costo_operativo_ajustado']:.2f}/km") 
    print(f"Tarifa final: ${desglose['tarifa_spot_final']:.2f}/km")
    
    # Ejemplo 4: Determinación automática de zona
    print(f"\n📍 Determinación automática de zonas:")
    ejemplos_ciudades = ["Tijuana, BC", "Ciudad de México", "Mérida, YUC", "Guadalajara, JAL"]
    for ciudad in ejemplos_ciudades:
        zona = determinar_zona_geografica(ciudad)
        print(f"{ciudad} → Zona {zona}")
    
    print(f"\n✅ Ejemplos ejecutados correctamente!")
