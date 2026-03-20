import streamlit as st
from indice_tarifas_spot import main as show_indice_spot
from ai_assistant import FreightAI
from geo_service import GeoService
from dat_history_manager import DATHistoryManager
from diesel_prices_real import obtener_precios_reales
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import math
from pricing import show_subscription_plans
from faq_page import show_faq
from contacto_page import show_contact
from terminos_condiciones import show_terms_and_conditions
from politica_privacidad import show_privacy_policy

# ═════════════════════════════════════════════════════════════════════════════════
# 🔮 ORÁCULO IA - GERENTE SENIOR LOGÍSTICO (Gemini Analysis)
# ═════════════════════════════════════════════════════════════════════════════════

def analizar_tarifa_with_oraculo(prediction_data):
    """
    Analiza la tarifa spot calculada usando Gemini como Gerente Senior en Logística.
    NUEVO: Incluye tarifas DAT, análisis preciso de diesel y CONVERSIÓN CORRECTA DE UNIDADES.
    CORREGIDO: $1.90 USD/km = $3.06 USD/mi (NO $22.45)
    """
    try:
        # Validar que prediction_data tenga información
        if not prediction_data:
            return None
        
        # Extraer datos con valores por defecto
        origen = prediction_data.get('origin', 'N/A')
        destino = prediction_data.get('destination', 'N/A')
        equipo = prediction_data.get('tipo_equipo', 'N/A')
        distancia_km = prediction_data.get('distancia_km', 0)
        distancia_mi = prediction_data.get('distancia_mi', 0)
        tarifa_total = prediction_data.get('total_rate', 0)
        tarifa_km = prediction_data.get('rate_per_km', 0)
        tipo_ruta = prediction_data.get('tipo_ruta', 'N/A')
        moneda = prediction_data.get('moneda', 'USD')
        
        # Variables macroeconómicas
        precio_diesel = prediction_data.get('precio_diesel', 0)
        riesgo_pais = prediction_data.get('riesgo_pais', 0)
        inflacion = prediction_data.get('inflacion_mxn', 0)
        tipo_cambio = prediction_data.get('tipo_cambio', 0)
        demanda = prediction_data.get('demanda_mercado', 0)
        capacidad = prediction_data.get('capacidad_disponible', 0)
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # CONVERSIÓN CORRECTA DE UNIDADES: KM → MILLAS
        # ═════════════════════════════════════════════════════════════════════════════════
        # Calcular distancia en millas si no está disponible
        if distancia_km > 0:
            distancia_mi_calc = distancia_km * 0.621371
        else:
            distancia_mi_calc = distancia_mi if distancia_mi > 0 else 1
        
        # CONVERTIR TARIFA/KM A TARIFA/MILLA CORRECTAMENTE
        # Ejemplo: $1.90 USD/km ÷ 0.621371 = $3.06 USD/mi
        if moneda == 'USD':
            tarifa_per_mi = tarifa_km / 0.621371 if tarifa_km > 0 else 0
        else:
            # Si es MXN/km, convertir primero a USD/km, luego a USD/mi
            tarifa_per_mi = (tarifa_km / tipo_cambio) / 0.621371 if tarifa_km > 0 and tipo_cambio > 0 else 0
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # CARGAR TARIFAS DAT PARA COMPARACIÓN
        # ═════════════════════════════════════════════════════════════════════════════════
        tarifas_dat = {}
        try:
            with open('dat_rates_us.json', 'r', encoding='utf-8') as f:
                dat_data = json.load(f)
                tarifas_dat = dat_data.get('tarifas', {})
                fecha_dat = dat_data.get('fecha_actualizacion', 'N/A')
        except:
            fecha_dat = 'N/A'
        
        # Mapear equipo a tarifa DAT según tipo
        tarifa_dat_ref = None
        if 'Caja' in equipo or 'Van' in equipo:
            tarifa_dat_ref = tarifas_dat.get('Caja Seca (Dry Van)', 2.45)
        elif 'Reefer' in equipo or 'Refrigerado' in equipo:
            tarifa_dat_ref = tarifas_dat.get('Refrigerado (Reefer)', 2.87)
        elif 'Flatbed' in equipo or 'Plataforma' in equipo:
            tarifa_dat_ref = tarifas_dat.get('Plataforma (Flatbed)', 2.94)
        else:
            tarifa_dat_ref = 2.45  # Default para Van
        
        # Calcular variación respecto a DAT (AHORA CON UNIDADES COHERENTES: USD/mi vs USD/mi)
        variacion_dat = ((tarifa_per_mi - tarifa_dat_ref) / tarifa_dat_ref * 100) if tarifa_dat_ref > 0 else 0
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # DETECTAR TIPO DE RUTA PARA USAR UNIDADES CORRECTAS
        # ═════════════════════════════════════════════════════════════════════════════════
        es_ruta_usa = tipo_ruta == 'Internacional' or 'USA' in destino or 'Texas' in destino or 'doméstica USA' in tipo_ruta.lower()
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # SELECCIONAR REFERENCIA CORRECTA SEGÚN TIPO DE RUTA
        # ═════════════════════════════════════════════════════════════════════════════════
        if es_ruta_usa:
            # USA: Usar DAT como referencia
            tarifa_referencia = tarifa_dat_ref
            label_referencia = f"DAT ${tarifa_dat_ref:.2f}/mi"
            variacion_referencia = variacion_dat
        else:
            # MÉXICO: Usar tarifa base de FreightMetrics como referencia (sin diesel dinámico)
            try:
                from logic_rates import FreightMetricsCalculator, determinar_zona_geografica
                zona = determinar_zona_geografica(origen)
                costos_base = obtener_costos_por_equipo(equipo, zona)
                
                # Calcular tarifa sin ajuste dinámico (tarifa base FreightMetrics)
                calculator_ref = FreightMetricsCalculator(
                    diesel=costos_base['diesel'],
                    casetas=costos_base['casetas'],
                    sueldo=costos_base['sueldo'],
                    mantenimiento=costos_base['mantenimiento'],
                    riesgo=costos_base['riesgo'],
                    administracion=costos_base['inflacion'],
                    zona=zona,
                    utilidad_pct=0.18,
                    aplicar_factores_dinamicos=False
                )
                tarifa_ref_km = calculator_ref.tarifa_spot_final()
                tarifa_referencia = tarifa_ref_km
                label_referencia = f"FreightMetrics ${tarifa_ref_km:.2f}/km"
                variacion_referencia = ((tarifa_km - tarifa_ref_km) / tarifa_ref_km * 100) if tarifa_ref_km > 0 else 0
            except:
                # Fallback si hay error
                tarifa_referencia = tarifa_km
                label_referencia = "FreightMetrics Base"
                variacion_referencia = 0
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # ANÁLISIS DE DIESEL (ESPECIAL PARA AMBAS RUTAS)
        # ═════════════════════════════════════════════════════════════════════════════════
        if es_ruta_usa:
            sensibilidad_diesel = "Alta (USA): Mercado correlacionado a WTI, volatilidad moderada"
            diesel_impact = f"Cada +$1 USD/gal impacta +0.08 USD/mi"
        else:
            sensibilidad_diesel = "Alta (México): Precios CRE, volatilidad extrema por política"
            diesel_impact = f"Cada +$1 MXN/L impacta +0.15 MXN/km"
        
        # ═════════════════════════════════════════════════════════════════════════════════
        # CONSTRUIR PROMPT CON UNIDADES SEGÚN TIPO DE RUTA
        # ═════════════════════════════════════════════════════════════════════════════════
        
        if es_ruta_usa:
            # RUTAS USA/INTERNACIONALES: TODO EN MILLAS Y USD
            ruta_display = f"{origen} → {destino} ({distancia_mi_calc:.0f}mi)"
            tarifa_display = f"${tarifa_per_mi:.2f} USD/mi"
            tarifa_total_display = f"${tarifa_total:.2f} USD"
            unidad_diesel = "USD/gal"
        else:
            # RUTAS MÉXICO DOMÉSTICAS: TODO EN KM Y MXN
            ruta_display = f"{origen} → {destino} ({distancia_km:.0f}km)"
            tarifa_display = f"${tarifa_km:.2f} MXN/km"
            tarifa_total_display = f"${tarifa_total:.2f} MXN"
            unidad_diesel = "MXN/L"
        
        # Construir prompt PRECISO CON UNIDADES CORRECTAS SEGÚN RUTA
        prompt = f"""
ROLE: Eres GERENTE SENIOR en Logística México-USA con 20+ años. SÉ ANALÍTICO Y BREVE.

📍 RUTA: {ruta_display} | Equipo: {equipo}

💰 TARIFA COTIZADA (UNIDADES CORRECTAS PARA {tipo_ruta.upper()}):
  • {tarifa_display} ← UNIDADES ESTÁNDAR PARA ESTA RUTA
  • Total: {tarifa_total_display}
  • Referencia: {label_referencia}
  • Variación vs Referencia: {variacion_referencia:+.1f}%

⛽ DIESEL - FACTOR CRÍTICO DE RIESGO:
  • Precio Actual: ${precio_diesel:.2f} {unidad_diesel}
  • Sensibilidad {tipo_ruta}: {sensibilidad_diesel}
  • Impacto: {diesel_impact}
  • Riesgo: Si sube 15% → costo +12% aprox

📊 CONDICIONES (Marzo 2026):
  • Inflación: {inflacion:.2f}% | TC: {tipo_cambio:.2f} | Demanda: {demanda:.0%} | Riesgo: {riesgo_pais:.2f}

═══════════════════════════════════════════════════════════════════════════════

⚖️ ANÁLISIS EJECUTIVO (Máx 2 líneas cada sección):

1️⃣ COMPETITIVIDAD: Tarifa {tarifa_display} vs {label_referencia} ({variacion_referencia:+.1f}%). ¿Es competitiva? Sí/No.

2️⃣ DIESEL: ${precio_diesel:.2f} {unidad_diesel} actual. Para {tipo_ruta}: ¿Riesgo alto o tolerable?

3️⃣ 2 RIESGOS CRÍTICOS: Identifica los riesgos más graves específicos de esta ruta.

4️⃣ ACCIÓN: ACEPTAR / NEGOCIAR / RECHAZAR / ESPERAR + motivo (máx 15 palabras).

NO digas "falta información" - todos los datos están incluidos. Sé profesional.
"""
        
        print(f"[Oráculo DEBUG] Análisis iniciado: {origen} → {destino}")
        print(f"[Oráculo DEBUG] Tipo de ruta: {tipo_ruta} (USA: {es_ruta_usa})")
        print(f"[Oráculo DEBUG] Distancia: {distancia_mi_calc:.0f}mi | Tarifa: {tarifa_display}")
        print(f"[Oráculo DEBUG] Referencia: {label_referencia} | Variación: {variacion_referencia:+.1f}%")
        print(f"[Oráculo DEBUG] Diesel: ${precio_diesel:.2f} {unidad_diesel} ({sensibilidad_diesel})")
        
        # Usar FreightAI para análisis
        try:
            GEMINI_API_KEY = "AIzaSyDgXuU6LK6ktAmvlyxB84H2DFN_ubuWFcY"
            if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
                return None
            
            ai_engine = FreightAI(GEMINI_API_KEY)
            analisis = ai_engine.analyze_route_custom(prompt)
            
            if not analisis or analisis.strip() == "":
                print("[Oráculo] Análisis sin respuesta del modelo")
                return None
            
            return analisis
        except Exception as e:
            print(f"[Oráculo Error] {e}")
            return None
    
    except Exception as e:
        print(f"[Oráculo Critical Error] {e}")
        import traceback
        traceback.print_exc()
        return None

# ═════════════════════════════════════════════════════════════════════════════════

def obtener_costos_por_equipo(tipo_equipo, zona_geografica=None):
    """
    Retorna los costos por km según el tipo de equipo basado en la
    Matriz FreightMetrics actualizada con Tabla Oficial de Costos (MXN/km) 2026
    Args:
        tipo_equipo: Tipo de equipo de transporte
        zona_geografica: "Norte", "Centro", "Sur" (None para auto-detectar)
    """
    import json
    from datetime import datetime
    
    try:
        # Cargar matriz recalibrada
        with open('matriz_comparativa_mx.json', 'r', encoding='utf-8') as f:
            matriz = json.load(f)
        
        # Obtener mes actual
        mes_actual = datetime.now().strftime('%b')  # Ene, Feb, Mar
        
        # Usar zona específica o Centro como fallback
        zona = zona_geografica if zona_geografica in ["Norte", "Centro", "Sur"] else "Centro"
        
        # Buscar datos del mes y zona
        datos_zona = matriz['matriz']['2026'][mes_actual].get(zona, [])
        
        # Extraer componentes por tipo de equipo
        componentes = {}
        for fila in datos_zona:
            componente = fila['Componente']
            valor = fila.get(tipo_equipo, 0)
            
            if 'Diésel' in componente:
                componentes['diesel'] = valor
            elif 'Inflación' in componente:
                componentes['inflacion'] = valor
            elif 'Casetas' in componente:
                componentes['casetas'] = valor
            elif 'Sueldo' in componente:
                componentes['sueldo'] = valor
            elif 'Riesgo' in componente or 'Seguro' in componente:
                componentes['riesgo'] = valor
            elif 'Manto' in componente:
                componentes['mantenimiento'] = valor
        
        # Agregar información de zona utilizada
        componentes['zona_utilizada'] = zona
        return componentes
        
    except Exception as e:
        # Fallback a valores recalibrados básicos si hay error
        costos_fallback = {
            "Caja Seca (Dry Van)": {
                "diesel": 6.2,
                "inflacion": 1.4,
                "casetas": 3.3,
                "sueldo": 3.4,
                "riesgo": 1.3,
                "mantenimiento": 2.2,
                "zona_utilizada": zona_geografica or "Centro"
            },
            "Plataforma (Flatbed)": {
                "diesel": 6.9,
                "inflacion": 1.6,
                "casetas": 3.3,
                "sueldo": 3.8,
                "riesgo": 1.5,
                "mantenimiento": 2.5,
                "zona_utilizada": zona_geografica or "Centro"
            },
            "Refrigerado (Reefer)": {
                "diesel": 7.9,
                "inflacion": 1.8,
                "casetas": 3.3,
                "sueldo": 4.4,
                "riesgo": 1.7,
                "mantenimiento": 2.8,
                "zona_utilizada": zona_geografica or "Centro"
            },
            "Full (Doble)": {
                "diesel": 9.0,
                "inflacion": 2.0,
                "casetas": 4.8,
                "sueldo": 4.9,
                "riesgo": 1.9,
                "mantenimiento": 3.2,
                "zona_utilizada": zona_geografica or "Centro"
            }
        }
        return costos_fallback.get(tipo_equipo, costos_fallback["Caja Seca (Dry Van)"])

def mostrar_cotizacion_profesional(dist_km, equipo, origen=None, destino=None, tipo_carga=None, 
                                   riesgo_pais=0.3, precio_diesel=22.0, tiempo_cruce=6,
                                   inflacion_mxn=5.5, tipo_cambio=18.0, demanda_mercado=0.7, 
                                   capacidad_disponible=0.6):
    # DEBUG
    print(f"[DEBUG mostrar_cotizacion_profesional] dist_km={dist_km}, equipo={equipo}, origen={origen}, destino={destino}")
    
    # Validar que equipo sea uno de los valores conocidos
    equipos_validos = ["Caja Seca (Dry Van)", "Refrigerado (Reefer)", "Plataforma (Flatbed)", 
                       "Contenedor 20'", "Contenedor 40'", "Full (Doble)"]
    if equipo not in equipos_validos:
        print(f"[WARNING] equipo inválido: {equipo}, usando default Caja Seca")
        equipo = "Caja Seca (Dry Van)"
    
    # Botón de descarga de PDF profesional solo para usuarios PRO o ENTERPRISE
    usuario = st.session_state.get('user', {})
    plan = usuario.get('plan', 'free')
    
    # Usar parámetros pasados o fallback a session_state
    if not origen:
        origen = st.session_state.get('origin_input', '')
    if not destino:
        destino = st.session_state.get('dest_input', '')
    # Detectar país usando GeoService
    try:
        geo_tool = st.session_state.get('geo_tool', None)
        if geo_tool is None:
            from geo_service import GeoService
            geo_tool = GeoService(api_key="AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8")
            st.session_state['geo_tool'] = geo_tool
        pais_origen = geo_tool.get_city_country(origen)
        pais_destino = geo_tool.get_city_country(destino)
    except Exception as e:
        pais_origen = None
        pais_destino = None
    # Pasar país como hint en el nombre si se detecta
    origen_hint = f"{origen} [{pais_origen}]" if pais_origen else origen
    destino_hint = f"{destino} [{pais_destino}]" if pais_destino else destino
    
    # Lógica especial para rutas domésticas USA: usar tarifas DAT por milla
    # Leer tarifas DAT desde archivo externo
    # 📊 CARGAR TARIFAS DAT (Para USA Domésticas e Internacionales)
    import json
    import os
    
    # Cargar datos históricos si están disponibles
    try:
        dat_history = DATHistoryManager()
        today = datetime.now()
        year = str(today.year)
        month = f"{today.month:02d}"
        week = f"week_{today.isocalendar()[1]:02d}"
        
        # Intentar obtener datos de la semana actual
        current_week_data = dat_history.get_weekly_data(year, month, week)
        if current_week_data and current_week_data.get("tarifas"):
            # Usar datos históricos de la semana actual
            tarifa_dat_por_milla = {}
            for equipo, data in current_week_data["tarifas"].items():
                if data["promedio"] is not None:
                    tarifa_dat_por_milla[equipo] = data["promedio"]
            fuente_dat = f"DAT Freight & Analytics - Semana {week} ({current_week_data['fecha_inicio']} - {current_week_data['fecha_fin']})"
            print(f"🔄 Usando datos históricos DAT: {week}")
        else:
            # Fallback a archivo actual
            raise Exception("No hay datos de semana actual, usar archivo estático")
            
    except Exception:
        # Usar archivo estático como fallback
        dat_file = os.path.join(os.path.dirname(__file__), "dat_rates_us.json")
        try:
            with open(dat_file, "r", encoding="utf-8") as f:
                dat_data = json.load(f)
            tarifa_dat_por_milla = dat_data.get("tarifas", {})
            fuente_dat = f"{dat_data.get('fuente', 'DAT Freight & Analytics')} (Actualizado: {dat_data.get('fecha_actualizacion', '')})"
        except Exception as e:
            # Tarifas DAT fallback (Marzo 2026)
            tarifa_dat_por_milla = {
                "Caja Seca (Dry Van)": 2.32,
                "Refrigerado (Reefer)": 2.81,
                "Plataforma (Flatbed)": 2.59
            }
            fuente_dat = "DAT Freight & Analytics (Marzo 2026 - Fallback)"
    # Determinar tipo de ruta PRIMERO
    debug_info = f"DEBUG: pais_origen='{pais_origen}', pais_destino='{pais_destino}'"
    
    if pais_origen and pais_destino:
        if 'Mexico' in pais_origen and 'Mexico' in pais_destino:
            tipo_ruta = 'Doméstica México'
        elif 'United States' in pais_origen and 'United States' in pais_destino:
            tipo_ruta = 'Doméstica USA'
        else:
            tipo_ruta = 'Internacional USA-México'
    else:
        tipo_ruta = 'Ruta General'
    
    # Mostrar debug en desarrollo
    print(f"{debug_info} -> {tipo_ruta}")  # DEBUG visible
    st.info(f"🔍 TIPO RUTA: {tipo_ruta} | Origen: {pais_origen} | Destino: {pais_destino}")

    # 🚛 CÁLCULO DE TARIFAS SEGÚN TIPO DE RUTA
    # ═══════════════════════════════════════════════════════════════
    # 🇺🇸 USA DOMÉSTICA: DAT tarifas directas (USD)
    # 🌍 INTERNACIONAL: DAT tarifas + cruce y documentación (USD) 
    # 🇲🇽 MÉXICO DOMÉSTICA: FreightMetrics matriz (MXN)
    # ═══════════════════════════════════════════════════════════════
    
    if tipo_ruta == 'Doméstica USA':
        # 🇺🇸 RUTAS DOMÉSTICAS USA → usar DAT tarifas directas
        equipo_key = equipo
        if equipo_key.startswith("Caja Seca"):
            equipo_key = "Caja Seca (Dry Van)"
        elif equipo_key.startswith("Refrigerado"):
            equipo_key = "Refrigerado (Reefer)"
        elif equipo_key.startswith("Plataforma"):
            equipo_key = "Plataforma (Flatbed)"
        
        tarifa_milla = tarifa_dat_por_milla.get(equipo_key, 2.32)
        distancia_mi = round(dist_km * 0.621371, 2)
        tarifa_total = round(tarifa_milla * distancia_mi, 2)
        base_ref = tarifa_total  # DAT no tiene desglose, es tarifa spot directa
        fuente_tarifa = fuente_dat
        justificacion = f"✅ Tarifa DAT USA: ${tarifa_milla}/mi para {equipo_key}. {fuente_dat}"
        moneda = 'USD'
        
    elif tipo_ruta == 'Internacional USA-México':
        # 🌍 RUTAS INTERNACIONALES → usar DAT + cruce y documentación
        equipo_key = equipo
        if equipo_key.startswith("Caja Seca"):
            equipo_key = "Caja Seca (Dry Van)"
        elif equipo_key.startswith("Refrigerado"):
            equipo_key = "Refrigerado (Reefer)"
        elif equipo_key.startswith("Plataforma"):
            equipo_key = "Plataforma (Flatbed)"
        
        # Base DAT + 25% por cruce fronterizo y documentación
        tarifa_base_milla = tarifa_dat_por_milla.get(equipo_key, 2.32)
        costo_cruce_doc = 0.25  # 25% por cruce fronterizo y documentación
        tarifa_internacional_milla = tarifa_base_milla * (1 + costo_cruce_doc)
        
        distancia_mi = round(dist_km * 0.621371, 2)
        tarifa_total = round(tarifa_internacional_milla * distancia_mi, 2)
        base_ref = round(tarifa_base_milla * distancia_mi, 2)  # Base DAT sin costos de cruce
        
        fuente_tarifa = f"DAT + Cruce y Documentación ({costo_cruce_doc*100:.0f}%)"
        justificacion = f"✅ Tarifa Internacional DAT: Base ${tarifa_base_milla:.2f}/mi + {costo_cruce_doc*100:.0f}% cruce/docs = ${tarifa_internacional_milla:.2f}/mi. {fuente_dat}"
        moneda = 'USD'
        
    else:
        # 🇲🇽 RUTAS DOMÉSTICAS MÉXICO → usar FreightMetrics matriz (MXN)
        from logic_rates import FreightMetricsCalculator, determinar_zona_geografica
        
        # Determinar zona geográfica basada en origen
        zona_calculada = determinar_zona_geografica(origen)
        
        costos_base = obtener_costos_por_equipo(equipo, zona_calculada)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ⚡ AJUSTE DINÁMICO DE DIESEL: Aplicar factor proporcional sobre matriz
        # ═══════════════════════════════════════════════════════════════════════════
        # La matriz se calibró con diesel a precio referencia de ~$24.5 MXN/L
        precio_referencia_matriz = 24.5  # Precio base con el que se calculó la matriz
        
        # Factor de ajuste: nuevo precio / precio de referencia
        factor_diesel = precio_diesel / precio_referencia_matriz
        
        # Aplicar factor al componente diesel de la matriz (ajuste proporcional)
        diesel_matriz = costos_base['diesel']
        diesel_ajustado = diesel_matriz * factor_diesel
        
        print(f"[DIESEL DINÁMICO] Precio referencia matriz: ${precio_referencia_matriz:.2f} MXN/L")
        print(f"[DIESEL DINÁMICO] Precio actual seleccionado: ${precio_diesel:.2f} MXN/L")
        print(f"[DIESEL DINÁMICO] Factor de ajuste: {factor_diesel:.4f}x")
        print(f"[DIESEL DINÁMICO] Costo diesel matriz: ${diesel_matriz:.2f} MXN/km")
        print(f"[DIESEL DINÁMICO] Costo diesel ajustado: ${diesel_ajustado:.2f} MXN/km")
        print(f"[DIESEL DINÁMICO] Cambio: ${(diesel_ajustado - diesel_matriz):.2f} MXN/km ({((factor_diesel-1)*100):.1f}%)")
        
        calculator = FreightMetricsCalculator(
            diesel=diesel_ajustado,  # CAMBIO: Usar componente diesel ajustado por precio actual
            casetas=costos_base['casetas'],
            sueldo=costos_base['sueldo'],
            mantenimiento=costos_base['mantenimiento'],
            riesgo=costos_base['riesgo'],
            administracion=costos_base['inflacion'],
            zona=zona_calculada,
            utilidad_pct=0.18,
            aplicar_factores_dinamicos=True  # Usar factores dinámicos por defecto
        )
        costo_por_km = calculator.tarifa_spot_final()
        tarifa_total = round(costo_por_km * dist_km, 2)
        base_ref = round(calculator.costo_operativo_ajustado() * dist_km, 2)
        fuente_tarifa = f"FreightMetrics - Zona {zona_calculada} + Ajuste Diesel Actual"
        justificacion = f'✅ Tarifa México Zona {zona_calculada}: {equipo} con ajuste diesel ${precio_diesel:.2f}/L (factor {factor_diesel:.2f}x) → ${costo_por_km:.2f}/km para {dist_km} km'
        moneda = 'MXN'
    
    # FSC solo aplica para rutas internacionales (coherente con moneda)
    fsc_estimado = 0
    fsc_moneda = moneda  # FSC en la misma moneda que la tarifa
    
    if tipo_ruta == 'Internacional USA-México':
        fsc_estimado = round(tarifa_total * 0.15, 2)  # 15% FSC en USD
    
    datos = {
        'total': tarifa_total,
        'base_ref': base_ref,
        'tipo_ruta': tipo_ruta,
        'distancia_km': dist_km,
        'fsc_estimado': fsc_estimado,
        'justificacion': justificacion,
        'moneda': moneda,
        'fsc_moneda': fsc_moneda,  # Para claridad en el oráculo
        'prediccion_7d': 0,
        'cambio_pct': 0,
        'origen_hint': origen_hint,
        'destino_hint': destino_hint,
        'tipo_equipo': equipo,
        'fuente_tarifa': fuente_tarifa,
        'pais_origen': pais_origen,
        'pais_destino': pais_destino,
        'debug_tipo_ruta': f"{pais_origen} -> {pais_destino} = {tipo_ruta}",
        'calculator': calculator if 'calculator' in locals() else None  # Para factores dinámicos
    }
    # Ejemplo de cálculo de cambio porcentual entre base_ref y total
    try:
        if datos['base_ref'] and datos['total']:
            cambio_pct = round(((datos['total'] - datos['base_ref']) / datos['base_ref']) * 100, 2)
        else:
            cambio_pct = 0
    except Exception:
        cambio_pct = 0

    # Mostrar visualización diferente según tipo de ruta
    if datos['tipo_ruta'] == 'Doméstica USA':
        # Para rutas domésticas USA: solo mostrar tarifa DAT (sin desglose)
        # Calcular información adicional para USA (incluir tendencias si están disponibles)
        distancia_mi = round(dist_km * 0.621371, 2)
        tarifa_por_milla = round(datos['total'] / distancia_mi, 2) if distancia_mi > 0 else 0
        
        # Obtener información de tendencia si está disponible
        try:
            dat_history = DATHistoryManager()
            today = datetime.now()
            year = str(today.year)
            month = f"{today.month:02d}"
            week = f"week_{today.isocalendar()[1]:02d}"
            current_week_data = dat_history.get_weekly_data(year, month, week)
            
            if current_week_data and datos['tipo_equipo'] in current_week_data["tarifas"]:
                trend_data = current_week_data["tarifas"][datos['tipo_equipo']]
                variacion_pct = trend_data.get("variacion_pct", 0)
                tendencia = trend_data.get("tendencia", "estable")
                trend_icon = "📈" if tendencia == "alcista" else "📉" if tendencia == "bajista" else "➡️"
                trend_text = f"{trend_icon} {tendencia.capitalize()} ({variacion_pct:+.1f}%)"
            else:
                trend_text = "➡️ Datos limitados"
        except:
            trend_text = "📊 Seguimiento DAT"
        
        st.markdown(f"""
            <div style='display:flex; justify-content:center; align-items:stretch; width:100%; margin-bottom:32px; gap:16px;'>
                <div style='flex:1; text-align:center; padding:24px; border:2px solid #4A90E2; border-radius:12px; background:#f8fafc;'>
                    <div style='font-size:2.4rem; font-weight:800; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda}</div>
                    <div style='font-size:1.2rem; color:#4A90E2; margin-top:8px; font-weight:600;'>Tarifa DAT Spot ({moneda})</div>
                    <div style='font-size:0.9rem; color:#666; margin-top:4px;'>{datos['fuente_tarifa']}</div>
                </div>
                <div style='flex:1; text-align:center; padding:24px; border:2px solid #28a745; border-radius:12px; background:#f8fff9;'>
                    <div style='font-size:1.8rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${tarifa_por_milla:.2f}/mi</div>
                    <div style='font-size:1.1rem; color:#28a745; margin-top:8px; font-weight:600;'>Por Milla</div>
                    <div style='font-size:0.85rem; color:#666; margin-top:4px;'>🚛 {datos['tipo_equipo']}</div>
                    <div style='font-size:0.85rem; color:#666;'>📏 {datos['distancia_km']} km / {distancia_mi} mi</div>
                    <div style='font-size:0.8rem; color:#e67e22; margin-top:4px; font-weight:600;'>{trend_text}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif datos['tipo_ruta'] == 'Internacional USA-México':
        # Para rutas internacionales: mostrar base DAT + cruce y documentación
        # Calcular información adicional para Internacional
        distancia_mi = round(dist_km * 0.621371, 2)
        tarifa_por_milla = round(datos['total'] / distancia_mi, 2) if distancia_mi > 0 else 0
        
        # Obtener información de tendencia DAT si está disponible
        try:
            dat_history = DATHistoryManager()
            today = datetime.now()
            year = str(today.year)
            month = f"{today.month:02d}"
            week = f"week_{today.isocalendar()[1]:02d}"
            current_week_data = dat_history.get_weekly_data(year, month, week)
            
            if current_week_data and datos['tipo_equipo'] in current_week_data["tarifas"]:
                trend_data = current_week_data["tarifas"][datos['tipo_equipo']]
                variacion_pct = trend_data.get("variacion_pct", 0)
                tendencia = trend_data.get("tendencia", "estable")
                trend_icon = "📈" if tendencia == "alcista" else "📉" if tendencia == "bajista" else "➡️"
                trend_text = f"{trend_icon} {tendencia.capitalize()}"
                trend_detail = f"({variacion_pct:+.1f}% vs sem. anterior)"
            else:
                trend_text = "📊 Base DAT"
                trend_detail = "(Datos limitados)"
        except:
            trend_text = "📊 Base DAT"  
            trend_detail = "(Seguimiento estándar)"
        
        st.markdown(f"""
            <div style='display:flex; justify-content:space-evenly; align-items:stretch; width:100%; margin-bottom:32px; gap:16px;'>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #4A90E2; border-radius:12px; background:#f8fafc;'>
                    <div style='font-size:2.0rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda} <span style='font-size:1.0rem; color:#888;'>(+{cambio_pct}%)</span></div>
                    <div style='font-size:1.0rem; color:#666; margin-top:6px;'>Tarifa Total ({moneda})</div>
                    <div style='font-size:0.85rem; color:#4A90E2; margin-top:4px;'>DAT + Cruce y Documentación</div>
                </div>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #22543d; border-radius:12px; background:#f0fdf4;'>
                    <div style='font-size:2.0rem; font-weight:700; color:#22543d; letter-spacing:1px;'>${datos['base_ref']} {moneda}</div>
                    <div style='font-size:1.0rem; color:#666; margin-top:6px;'>Base DAT</div>
                    <div style='font-size:0.85rem; color:#22543d; margin-top:4px;'>Solo Transporte</div>
                    <div style='font-size:0.75rem; color:#e67e22; margin-top:2px; font-weight:600;'>{trend_text}</div>
                </div>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #dc3545; border-radius:12px; background:#fff5f5;'>
                    <div style='font-size:1.6rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${tarifa_por_milla:.2f}/mi</div>
                    <div style='font-size:1.0rem; color:#dc3545; margin-top:6px; font-weight:600;'>Por Milla</div>
                    <div style='font-size:0.8rem; color:#666; margin-top:4px;'>🚛 {datos['tipo_equipo']}</div>
                    <div style='font-size:0.8rem; color:#666;'>📏 {datos['distancia_km']} km</div>
                    <div style='font-size:0.8rem; color:#666;'>🌍 {datos['tipo_ruta']}</div>
                    <div style='font-size:0.75rem; color:#e67e22; margin-top:2px;'>{trend_detail}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Para rutas domésticas México: mostrar desglose FreightMetrics
        # Calcular información adicional para México
        tarifa_por_km = round(datos['total'] / datos['distancia_km'], 2) if datos['distancia_km'] > 0 else 0
        
        st.markdown(f"""
            <div style='display:flex; justify-content:space-evenly; align-items:stretch; width:100%; margin-bottom:32px; gap:16px;'>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #4A90E2; border-radius:12px; background:#f8fafc;'>
                    <div style='font-size:2.0rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda}</div>
                    <div style='font-size:1.0rem; color:#666; margin-top:6px;'>Tarifa Total ({moneda})</div>
                    <div style='font-size:0.85rem; color:#4A90E2; margin-top:4px;'>FreightMetrics</div>
                </div>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #22543d; border-radius:12px; background:#f0fdf4;'>
                    <div style='font-size:2.0rem; font-weight:700; color:#22543d; letter-spacing:1px;'>${datos['base_ref']} {moneda} <span style='font-size:1.0rem; color:#888;'>({cambio_pct}%)</span></div>
                    <div style='font-size:1.0rem; color:#666; margin-top:6px;'>Base de Cálculo</div>
                    <div style='font-size:0.85rem; color:#22543d; margin-top:4px;'>Costo Operativo</div>
                </div>
                <div style='flex:1; text-align:center; padding:20px; border:2px solid #28a745; border-radius:12px; background:#f8fff9;'>
                    <div style='font-size:1.6rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${tarifa_por_km:.2f}/km</div>
                    <div style='font-size:1.0rem; color:#28a745; margin-top:6px; font-weight:600;'>Por Kilómetro</div>
                    <div style='font-size:0.8rem; color:#666; margin-top:4px;'>🚛 {datos['tipo_equipo']}</div>
                    <div style='font-size:0.8rem; color:#666;'>📏 {datos['distancia_km']} km</div>
                    <div style='font-size:0.8rem; color:#666;'>🌎 Doméstica MX</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # Mostrar fuente y justificación de manera prominente
    st.markdown("### 📋 **Fuente y Metodología**")
    col_fuente1, col_fuente2 = st.columns(2)
    with col_fuente1:
        st.info(f"**📊 Fuente:** {datos['fuente_tarifa']}")
    with col_fuente2:
        st.success(f"**✅ Ruta:** {datos['origen_hint']} → {datos['destino_hint']}")

    # Mostrar información de factores dinámicos si es ruta México
    if moneda == 'MXN' and datos.get('calculator'):
        st.markdown("### 🎯 **Análisis de Factores Dinámicos**")
        calculator = datos['calculator']
        desglose = calculator.desglose_completo()
        
        col_fact1, col_fact2, col_fact3 = st.columns(3)
        with col_fact1:
            st.metric(
                "🗺️ Zona Geográfica", 
                desglose['zona'],
                help="Zona determinada automáticamente según origen"
            )
        with col_fact2:
            st.metric(
                "📈 Factor Dinámico",
                f"{desglose['factor_zona_dinamico']:.3f}",
                f"{((desglose['factor_zona_dinamico'] - 1) * 100):+.1f}%",
                help="Factor que ajusta la tarifa según condiciones de mercado actuales"
            )
        with col_fact3:
            st.metric(
                "⚙️ Utilidad Aplicada",
                f"{desglose['utilidad_pct']:.0f}%",
                f"${desglose['utilidad_mxn']:.2f}",
                help="Margen de utilidad incluido en la tarifa"
            )
        
        # Expandible con desglose de componentes
        with st.expander("🔍 **Ver Desglose Detallado de Componentes**"):
            st.markdown("**Componentes Base por Kilómetro:**")
            componentes = desglose['componentes_base']
            
            col_comp1, col_comp2 = st.columns(2)
            with col_comp1:
                st.markdown(f"🛢️ **Diésel:** ${componentes['diesel']:.2f}")
                st.markdown(f"🛣️ **Casetas:** ${componentes['casetas']:.2f}")
                st.markdown(f"👷 **Sueldo:** ${componentes['sueldo']:.2f}")
            with col_comp2:
                st.markdown(f"🔧 **Mantenimiento:** ${componentes['mantenimiento']:.2f}")
                st.markdown(f"⚠️ **Riesgo/Seguro:** ${componentes['riesgo']:.2f}")
                st.markdown(f"📊 **Administración:** ${componentes['administracion']:.2f}")
            
            st.markdown("---")
            st.markdown(f"**💰 Costo Base Total:** ${desglose['costo_operativo_base']:.2f}/km")
            st.markdown(f"**📈 Después Factores Dinámicos:** ${desglose['costo_operativo_ajustado']:.2f}/km")
            st.markdown(f"**🎯 Tarifa Final con Utilidad:** ${desglose['tarifa_spot_final']:.2f}/km")

    # Guardar todos los datos relevantes para el Oráculo en session_state

    total_rate = datos['total']
    distancia_km = datos['distancia_km']
    distancia_mi = round(distancia_km * 0.621371, 2)
    # Costo por milla en MXN si es ruta nacional México
    if moneda == 'MXN':
        rate_per_mile = round((total_rate * 20) / distancia_mi, 2) if distancia_mi > 0 else None  # 20 es tipo_cambio fijo
    else:
        rate_per_mile = round(total_rate / distancia_mi, 2) if distancia_mi > 0 else None

    # Calcular predicción a 7 días basada en el cambio porcentual
    # Si cambio_pct es positivo, la tarifa sube; si es negativo, baja
    pred_7 = round(total_rate * (1 + cambio_pct / 100), 2) if cambio_pct else total_rate

    st.session_state['prediction_result'] = {
        'origin': origen,
        'destination': destino,
        'tipo_equipo': equipo,
        'distancia_km': distancia_km,
        'distancia_mi': distancia_mi,
        'total_rate': total_rate,
        'prediccion_7d': pred_7,
        # `spot_rate` debe ser la tarifa por kilómetro (MXN/km) cuando la moneda es MXN,
        # o la tarifa base (total) cuando sea DAT/USD. Añadimos también `rate_per_km`.
        'rate_per_km': round(total_rate / distancia_km, 2) if distancia_km > 0 else None,
        'spot_rate': round(total_rate / distancia_km, 2) if moneda == 'MXN' and distancia_km > 0 else datos.get('base_ref', ''),
        'base_ref': datos.get('base_ref', ''),
        'tipo_ruta': datos.get('tipo_ruta', ''),
        'rate_per_mile': rate_per_mile,
        'moneda': moneda,
        # Usar parámetros pasados a la función (PRIORITARIOS)
        'riesgo_pais': riesgo_pais,
        'precio_diesel': precio_diesel,
        'tiempo_cruce': tiempo_cruce,
        'inflacion_mxn': inflacion_mxn,
        'tipo_cambio': tipo_cambio,
        'demanda_mercado': demanda_mercado,
        'capacidad_disponible': capacidad_disponible,
        'pais_origen': datos.get('pais_origen', ''),
        'pais_destino': datos.get('pais_destino', ''),
        'origen_hint': datos.get('origen_hint', origen),
        'destino_hint': datos.get('destino_hint', destino),
        # Variables adicionales para el Oráculo
        'tarifa_km': round(total_rate / distancia_km, 2) if distancia_km > 0 else 0,
        'rate_per_km_display': f"${round(total_rate / distancia_km, 2):.2f}" if distancia_km > 0 else "N/A"
    }

    # ═════════════════════════════════════════════════════════════════════════════════
    # 🔮 ANÁLISIS DEL ORÁCULO IA (Gerente Senior Logístico)
    # ═════════════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    
    with st.expander("🔮 **ANÁLISIS DEL ORÁCULO IA** - Evaluación del Gerente Senior", expanded=True):
        st.markdown("""
        <div style='background: rgba(102, 126, 234, 0.1); padding: 15px; border-radius: 12px; border-left: 5px solid #667eea;'>
        <p style='margin: 0; color: #333; font-size: 0.95rem;'>
        <strong>🎯 Gerente Senior en Logística</strong> con 20+ años de experiencia analiza tu tarifa spot.
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        # DEBUG: Verificar que el diccionario tiene datos
        prediction_data = st.session_state.get('prediction_result', {})
        print(f"\n[Oráculo DEBUG] Datos recibidos:")
        print(f"  - Origen: {prediction_data.get('origin', 'FALTA')}")
        print(f"  - Destino: {prediction_data.get('destination', 'FALTA')}")
        print(f"  - Distancia: {prediction_data.get('distancia_km', 'FALTA')} km")
        print(f"  - Tarifa Total: ${prediction_data.get('total_rate', 'FALTA')} {prediction_data.get('moneda', 'USD')}")
        print(f"  - Precio Diesel: ${prediction_data.get('precio_diesel', 'FALTA')} MXN/L")
        print(f"  - Tipo Cambio: {prediction_data.get('tipo_cambio', 'FALTA')}")
        print(f"  - Demanda Mercado: {prediction_data.get('demanda_mercado', 'FALTA')}")
        
        analisis = analizar_tarifa_with_oraculo(prediction_data)
        
        if analisis and analisis.strip() != "":
            st.info(analisis)
        else:
            # Fallback análisis si API falla
            st.warning("""
            ⚠️ **Análisis Temporal No Disponible**
            
            Para obtener un análisis experto completo con recomendaciones profesionales,
            actualiza tu suscripción o contacta a nuestro equipo.
            
            *Los datos de tu cotización se han guardado y pueden consultarse en cualquier momento.*
            """)

    # Mostrar encabezado del resultado justo después de la predicción (solo en la sección de cotización)
    try:
        # Header eliminado: "Tarifa Spot - Resultado de Cotización"
        pass
    except Exception:
        pass

def show_subscription_levels():
    st.markdown("""
| Nivel      | Funciones Incluidas                                 | Precio Sugerido   |
|------------|----------------------------------------------------|-------------------|
| **Free**   | 3 cotizaciones/mes, solo rutas MX                  | $0                |
| **Pro**    | Cotizaciones ilimitadas, USA-MX, PDF               | $49 USD/mes       |
| **Enterprise** | API Access, Auditoría de IA avanzada           | $199 USD/mes      |
""")

st.set_page_config(
    page_title="FreightMetrics Oracle Rate",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL base de la API
API_BASE_URL = "http://localhost:8000"

# Configuración de Google Maps API
try:
    google_api_key = "AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8"
    geo_tool = GeoService(api_key=google_api_key)
except NameError:
    geo_tool = None

# Función para hacer llamadas a la API
def call_api(endpoint, method="GET", data=None):
    # Funcion helper para llamadas a la API
    try:
        url = f"{API_BASE_URL}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception as e:
        print(f"Error en llamada a API: {e}")
        return None

def calcular_distancia(coord1, coord2):
    # Calcula la distancia aproximada por carretera en kilometros entre dos puntos
    # usando la formula de Haversine multiplicada por un factor de correccion para rutas terrestres
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convertir a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Formula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # Radio de la Tierra en kilometros
    radio_tierra = 6371

    distancia_linea_recta = radio_tierra * c
    
    # Factor de correccion para distancia por carretera (aproximadamente 1.09x para rutas en Mexico)
    # Basado en comparacion con rutas reales como Tijuana-Tlaquepaque
    factor_carretera = 1.09
    
    distancia_carretera = distancia_linea_recta * factor_carretera
    return distancia_carretera

# Función para verificar conexión con la API
def check_api_connection():
    # Verifica si la API esta disponible
    try:
        response = call_api("/")
        return response is not None
    except:
        return False

# Header principal
def render_header():
    # Renderiza el header de la aplicacion
    html = (
        "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
        "color: white; padding: 40px 50px; border-radius: 20px; margin-bottom: 40px; "
        "box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4); text-align: left;'>"
        
        # Título Principal
        "<h1 style='color: white; margin: 0 0 15px 0; font-size: 3.2rem; font-weight: 800; text-align: center;'>"
        "FreightMetrics Oracle Rate"
        "</h1>"
        
        # Subtítulo
        "<h2 style='color: rgba(255,255,255,0.95); font-size: 1.4rem; font-weight: 600; "
        "text-align: center; margin: 0 0 25px 0; letter-spacing: 0.5px;'>"
        "La primera plataforma en México en desarrollar el Sistema Actuarial de Cálculo para Tarifas Spot de Autotransporte"
        "</h2>"
        
        # Descripción Principal
        "<div style='background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; margin: 20px 0; "
        "border-left: 5px solid #FFF;'>"
        "<p style='color: rgba(255,255,255,0.95); font-size: 1.1rem; line-height: 1.6; margin: 0 0 15px 0;'>"
        "<strong>FreightMetrics redefine el estándar logístico en México.</strong> Somos la tecnología pionera que transforma "
        "la Matriz de Costos de la SCT en una herramienta predictiva en tiempo real. Nuestro algoritmo procesa y audita "
        "variables macroeconómicas oficiales para determinar el costo operativo real por kilómetro (CPK), integrando de forma única:"
        "</p>"
        
        # Variables Integradas
        "<div style='margin: 20px 0;'>"
        "<p style='color: #FFD700; font-size: 1rem; font-weight: 600; margin: 8px 0;'>"
        "⚡ <strong>Variación Energética:</strong> Indexado diario con los precios regionales de la CRE"
        "</p>"
        "<p style='color: #FFD700; font-size: 1rem; font-weight: 600; margin: 8px 0;'>"
        "📊 <strong>Inflación Sectorial:</strong> Ajuste dinámico basado en el INPP del INEGI (Rubro 611)"
        "</p>"
        "<p style='color: #FFD700; font-size: 1rem; font-weight: 600; margin: 8px 0;'>"
        "🛡️ <strong>Riesgo Logístico:</strong> Evaluación de seguridad por corredor y nodo industrial 2026"
        "</p>"
        "</div>"
        "</div>"
        
        # Innovación y Transparencia - OCULTO
        # "<div style='display: flex; gap: 20px; margin-top: 20px;'>"
        # "<div style='flex: 1; background: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px;'>"
        # "<h3 style='color: #00FF88; font-size: 1.1rem; font-weight: 700; margin: 0 0 10px 0;'>🚀 Innovación</h3>"
        # "<p style='color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.5; margin: 0;'>"
        # "Somos los primeros en México en automatizar el análisis de las variables que la SCT y el INEGI publican, "
        # "eliminando el error humano y el retraso de los tabuladores manuales."
        # "</p>"
        # "</div>"
        # "<div style='flex: 1; background: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px;'>"
        # "<h3 style='color: #00BFFF; font-size: 1.1rem; font-weight: 700; margin: 0 0 10px 0;'>🔍 Transparencia</h3>"
        # "<p style='color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.5; margin: 0;'>"
        # "Cualquier tarifa mostrada puede ser auditada contra el precio del diésel de la CRE del día de hoy "
        # "y el INPP del último mes."
        # "</p>"
        # "</div>"
        # "</div>"
        
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

# Función para obtener datos de ejemplo
@st.cache_data(ttl=300)
def get_example_data():
    # Obtiene datos de ejemplo de la API
    return call_api("/examples/route")

# Función principal de predicción
def render_prediction_interface():
    # Renderiza la interfaz de cotización

    # ═══════════════════════════════════════════════════════════════
    # 1. INICIALIZAR SERVICIO GEOGRÁFICO
    # ═══════════════════════════════════════════════════════════════
    api_key = "AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8"
    geo_tool_local = None
    try:
        geo_tool_local = GeoService(api_key=api_key)
    except Exception as e:
        print(f"[GeoService ERROR] {e}")
        st.error(f"[GeoService ERROR] {e}")
        geo_tool_local = None

    # ═══════════════════════════════════════════════════════════════
    # 2. COLUMNA 1: DATOS DE RUTA (Origen, Destino, Tipo de Carga)
    # ═══════════════════════════════════════════════════════════════
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📍 Configuración de Ruta")
        origin_input = st.text_input("Origen (Ciudad, Estado o CP)", placeholder="Ej: Querétaro, MX", key="origin_input")
        dest_input = st.text_input("Destino (Ciudad, Estado o CP)", placeholder="Ej: Chicago, IL", key="dest_input")
        
        tipos_carga_nombres = {
            0: "Dry Van - Caja seca",
            1: "Reefer - Carga refrigerada",
            2: "Flatbed - Carga plana",
            3: "Contenedor 20'",
            4: "Contenedor 40'",
            5: "Doble Articulado/ Full"
        }
        
        tipo_carga = st.selectbox(
            "Tipo de Carga",
            options=[0, 1, 2, 3, 4, 5],
            format_func=lambda x: tipos_carga_nombres.get(x, "Desconocido"),
            index=0,
            help="Tipo de vehículo o contenedor requerido"
        )

    # ═══════════════════════════════════════════════════════════════
    # 3. VALIDAR Y CALCULAR DISTANCIA
    # ═══════════════════════════════════════════════════════════════
    distancia_km = None
    origin_coords = None
    dest_coords = None
    
    if not origin_input or not dest_input:
        st.warning("⚠️ Por favor ingresa un origen y un destino.")
    elif geo_tool_local is None:
        st.warning("⚠️ Google Maps API no está configurada.")
    else:
        with st.spinner('⏳ Validando ciudades y calculando ruta...'):
            origin_clean = geo_tool_local.validate_city(origin_input)
            dest_clean = geo_tool_local.validate_city(dest_input)
            
            if isinstance(origin_clean, dict) and 'lat' in origin_clean and 'lng' in origin_clean:
                origin_coords = (origin_clean['lat'], origin_clean['lng'])
            if isinstance(dest_clean, dict) and 'lat' in dest_clean and 'lng' in dest_clean:
                dest_coords = (dest_clean['lat'], dest_clean['lng'])
            
            route_info = geo_tool_local.get_route_data(origin_clean, dest_clean)
            if route_info:
                distancia_km = route_info['distance']
                st.success(f"✅ Distancia real: {distancia_km} km")
            else:
                st.error("❌ No se pudo calcular la distancia. Verifica los datos.")

    # ═══════════════════════════════════════════════════════════════
    # 4. COLUMNA 2: VARIABLES MÉXICO / USA
    # ═══════════════════════════════════════════════════════════════
    with col2:
        st.markdown("#### 🇲🇽 Variables Mexicanas / USA")
        
        riesgo_pais = st.slider(
            "Riesgo País (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Nivel de riesgo político/económico",
            key="riesgo_pais"
        )

        # Obtener precio de diesel actual desde PetroIntelligencia
        @st.cache_data(ttl=86400)
        def get_diesel_price_cotizador():
            precios, fuente = obtener_precios_reales()
            return precios["promedio_nacional"], fuente
        
        precio_diesel_actual, fuente_diesel = get_diesel_price_cotizador()
        
        # Mostrar el precio actual y botón de actualización
        col_diesel_info, col_diesel_btn = st.columns([3, 1])
        with col_diesel_info:
            st.info(f"⛽ Precio Actual: **${precio_diesel_actual:.2f} MXN/L** ({fuente_diesel})")
        with col_diesel_btn:
            if st.button("🔄 Actualizar", key="diesel_cotizador_refresh", help="Obtener precio actual de PetroIntelligencia"):
                st.cache_data.clear()
                st.rerun()

        precio_diesel = st.slider(
            "Precio Diesel (MXN/L)",
            min_value=15.0,
            max_value=30.0,
            value=precio_diesel_actual,
            step=0.5,
            help="Ajusta el precio si deseas simular otro escenario",
            key="precio_diesel"
        )

        tiempo_cruce = st.slider(
            "Tiempo de Cruce (horas)",
            min_value=1,
            max_value=72,
            value=6,
            step=1,
            help="Tiempo estimado fronterizo",
            key="tiempo_cruce"
        )

    # ═══════════════════════════════════════════════════════════════
    # 5. COLUMNA 3: DATOS DE MERCADO
    # ═══════════════════════════════════════════════════════════════
    with col3:
        st.markdown("#### 📊 Mercado")
        
        inflacion_mxn = st.slider(
            "Inflación MXN (%)",
            min_value=2.0,
            max_value=10.0,
            value=5.5,
            step=0.1,
            key="inflacion_mxn"
        )

        tipo_cambio = st.slider(
            "Tipo de Cambio (MXN/USD)",
            min_value=15.0,
            max_value=25.0,
            value=18.0,
            step=0.1,
            key="tipo_cambio"
        )

        demanda_mercado = st.slider(
            "Demanda del Mercado (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="demanda_mercado"
        )

        capacidad_disponible = st.slider(
            "Capacidad Disponible (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            key="capacidad_disponible"
        )

    # ═══════════════════════════════════════════════════════════════
    # 6. BOTÓN DE COTIZACIÓN
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    
    if st.button("📋 Ver Tarifa Spot FreightMetrics", use_container_width=True):
        # Validar todos los inputs antes de procesar
        if not distancia_km:
            st.error("❌ Primero calcula la distancia válida entre origen y destino.")
            return
        
        if not origin_input or not dest_input:
            st.error("❌ Ingresa origen y destino válidos.")
            return
        
        if tipo_carga is None:
            st.error("❌ Selecciona un tipo de carga.")
            return
        
        # Mapear tipo_carga a etiqueta de equipo
        tipos_equipo = {
            0: "Caja Seca (Dry Van)",
            1: "Refrigerado (Reefer)",
            2: "Plataforma (Flatbed)",
            3: "Contenedor 20'",
            4: "Contenedor 40'",
            5: "Full (Doble)"
        }
        equipo = tipos_equipo.get(tipo_carga, "Caja Seca (Dry Van)")
        
        # DEBUG
        print(f"[COTIZACIÓN] Origen={origin_input}, Destino={dest_input}, Distancia={distancia_km}km, Equipo={equipo}")
        
        # Llamar función de cotización con TODOS los parámetros necesarios
        mostrar_cotizacion_profesional(
            dist_km=distancia_km,
            equipo=equipo,
            origen=origin_input,
            destino=dest_input,
            tipo_carga=tipo_carga,
            riesgo_pais=riesgo_pais,
            precio_diesel=precio_diesel,
            tiempo_cruce=tiempo_cruce,
            inflacion_mxn=inflacion_mxn,
            tipo_cambio=tipo_cambio,
            demanda_mercado=demanda_mercado,
            capacidad_disponible=capacidad_disponible
        )

# Función para mostrar información del sistema
def render_system_info():
    # Muestra informacion del sistema y modelo

    with st.expander("ℹ️ Información del Sistema", expanded=False):

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔗 Estado de la API")
            api_status = check_api_connection()
            if api_status:
                st.success("✅ API conectada")
            else:
                st.error("❌ API desconectada")

        with col2:
            st.markdown("#### 🤖 Estado del Modelo")
            model_info = call_api("/model/info")
            if model_info:
                st.success("✅ Modelo entrenado")
                st.info(f"📊 {model_info['numero_features']} variables")
                st.info(f"🎯 Features principales: {', '.join([f[0] for f in model_info['features_principales'][:3]])}")
            else:
                st.error("❌ Modelo no disponible")

        # Métricas del sistema
        st.markdown("#### 📈 Métricas del Sistema")
        metrics = call_api("/metrics")
        if metrics:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Estado", metrics['status'].title())
            with col_b:
                st.metric("Modelo", "Entrenado" if metrics['model_trained'] else "No entrenado")
            with col_c:
                st.metric("Timestamp", datetime.fromisoformat(metrics['timestamp']).strftime("%H:%M:%S"))

# Función principal
def main():

    # --- USER PROFILE LOAD LOGIC ---
    user = st.session_state.get('user', {})
    if user and not st.session_state.get('user_profile'):
        try:
            from auth_service import AuthService
            auth_service = AuthService()
            user_id = user.get('sub') or user.get('user_id') or user.get('uid') or user.get('email')
            if user_id:
                user_profile = auth_service.get_user_data(user_id)
                st.session_state['user_profile'] = user_profile
        except Exception as e:
            st.session_state['user_profile'] = None

    # Verificar conexión con la API
    if not check_api_connection():
        st.error("🚨 No se puede conectar con la API backend. Asegúrate de que el servidor esté ejecutándose en http://localhost:8000")
        st.info("Ejecuta: `python main.py` en la terminal para iniciar el servidor.")
        return

    # Footer común para todas las páginas
    footer_html = (
        "<div style='position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; "
        "color: #333; text-decoration: none; text-align: center; padding: 8px 0; z-index: 1000; "
        "font-size: 12px; line-height: 1.4; border-top: 1px solid #ddd;'>"
        "<p style='margin: 0; font-weight: 600;'>Considerando variables mexicanas: Riesgo País, Precio Diesel, Tiempos de Cruce</p>"
        "<p style='margin: 2px 0 0 0; font-size: 10px; color: #666;'>"
        "© 2026 FreightMetrics - Todos los derechos reservados | Desarrollado en Tijuana, BC 🇲🇽 | FreightMetrics® Marca Registrada"
        "</p>"
        "</div>"
    )
    st.markdown(footer_html, unsafe_allow_html=True)

    with st.sidebar:
        page = st.radio("Menu Principal", ["📊 FreightMetrics Oracle Rate", "📈 Tendencia de Tarifas Spot", "⭐ Suscripción", "❓ FAQ", "📩 Contacto", "📋 Términos y Condiciones", "🔒 Política de Privacidad"])

    if page == "📊 FreightMetrics Oracle Rate":
        # Renderizar interfaz del cotizador
        render_header()
        render_prediction_interface()
        render_system_info()
        

    elif page == "📈 Tendencia de Tarifas Spot":
        show_indice_spot()
    elif page == "⭐ Suscripción":
        show_subscription_plans()
    elif page == "❓ FAQ":
        show_faq()
    elif page == "📩 Contacto":
        show_contact()
    elif page == "📋 Términos y Condiciones":
        show_terms_and_conditions()
    elif page == "🔒 Política de Privacidad":
        show_privacy_policy()

if __name__ == "__main__":
    main()