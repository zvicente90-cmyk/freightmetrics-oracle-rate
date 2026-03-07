from auth_service_simple import login_ui, check_auth
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import streamlit as st
from Tendencias_de_mercado import main as show_tendencias_de_mercado
from ai_assistant import FreightAI
from report_gen import generate_pdf_report
from geo_service import GeoService
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import math
from pricing import show_subscription_plans
from faq_page import show_faq
from contacto_page import show_contact
from terminos_condiciones import show_terms_and_conditions
from politica_privacidad import show_privacy_policy

def obtener_costos_por_equipo(tipo_equipo):
    """
    Retorna los costos por km según el tipo de equipo basado en la
    Matriz FreightMetrics actualizada con Tabla Oficial de Costos (MXN/km) 2026
    """
    import json
    from datetime import datetime
    
    try:
        # Cargar matriz recalibrada
        with open('matriz_comparativa_mx.json', 'r', encoding='utf-8') as f:
            matriz = json.load(f)
        
        # Obtener mes actual
        mes_actual = datetime.now().strftime('%b')  # Ene, Feb, Mar
        zona = "Centro"  # Usar zona Centro como promedio nacional
        
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
                "mantenimiento": 2.2
            },
            "Plataforma (Flatbed)": {
                "diesel": 6.9,
                "inflacion": 1.6,
                "casetas": 3.3,
                "sueldo": 3.8,
                "riesgo": 1.5,
                "mantenimiento": 2.5
            },
            "Refrigerado (Reefer)": {
                "diesel": 7.9,
                "inflacion": 1.8,
                "casetas": 3.3,
                "sueldo": 4.4,
                "riesgo": 1.7,
                "mantenimiento": 2.8
            },
            "Full (Doble)": {
                "diesel": 9.0,
                "inflacion": 2.0,
                "casetas": 4.8,
                "sueldo": 4.9,
                "riesgo": 1.9,
                "mantenimiento": 3.2
            }
        }
        return costos_fallback.get(tipo_equipo, costos_fallback["Caja Seca (Dry Van)"])

def mostrar_cotizacion_profesional(dist_km, equipo):
    # Botón de descarga de PDF profesional solo para usuarios PRO o ENTERPRISE
    usuario = st.session_state.get('user', {})
    plan = usuario.get('plan', 'free')
    origen = st.session_state.get('origin_input', '')
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
    # print(f"{debug_info} -> {tipo_ruta}")  # Comentado para producción

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
        from logic_rates import FreightMetricsCalculator
        costos_base = obtener_costos_por_equipo(equipo)
        calculator = FreightMetricsCalculator(
            diesel=costos_base['diesel'],
            casetas=costos_base['casetas'],
            sueldo=costos_base['sueldo'],
            mantenimiento=costos_base['mantenimiento'],
            riesgo=costos_base['riesgo'],
            administracion=costos_base['inflacion'],
            utilidad_pct=0.18
        )
        costo_por_km = calculator.tarifa_spot_final()
        tarifa_total = round(costo_por_km * dist_km, 2)
        base_ref = round(calculator.costo_operativo() * dist_km, 2)
        fuente_tarifa = "FreightMetrics - Tabla Oficial de Costos por Componente"
        justificacion = f'✅ Tarifa México: {equipo} usando modelo FreightMetrics ${costo_por_km:.2f}/km para {dist_km} km'
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
        'debug_tipo_ruta': f"{pais_origen} -> {pais_destino} = {tipo_ruta}"
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
        st.markdown(f"""
            <div style='display:flex; justify-content:center; align-items:stretch; width:100%; margin-bottom:32px; gap:32px;'>
                <div style='flex:1; text-align:center; padding:24px; border:2px solid #4A90E2; border-radius:12px; background:#f8fafc;'>
                    <div style='font-size:2.4rem; font-weight:800; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda}</div>
                    <div style='font-size:1.2rem; color:#4A90E2; margin-top:8px; font-weight:600;'>Tarifa DAT Spot ({moneda})</div>
                    <div style='font-size:0.9rem; color:#666; margin-top:4px;'>{datos['fuente_tarifa']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif datos['tipo_ruta'] == 'Internacional USA-México':
        # Para rutas internacionales: mostrar base DAT + cruce y documentación
        st.markdown(f"""
            <div style='display:flex; justify-content:space-evenly; align-items:stretch; width:100%; margin-bottom:32px; gap:32px;'>
                <div style='flex:1; text-align:center; padding:24px 0;'>
                    <div style='font-size:2.2rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda} <span style='font-size:1.1rem; color:#888;'>(+{cambio_pct}%)</span></div>
                    <div style='font-size:1.1rem; color:#666; margin-top:8px;'>Tarifa Total ({moneda})</div>
                    <div style='font-size:0.9rem; color:#4A90E2; margin-top:4px;'>DAT + Cruce y Documentación</div>
                </div>
                <div style='flex:1; text-align:center; padding:24px 0;'>
                    <div style='font-size:2.2rem; font-weight:700; color:#22543d; letter-spacing:1px;'>${datos['base_ref']} {moneda}</div>
                    <div style='font-size:1.1rem; color:#666; margin-top:8px;'>Base DAT</div>
                    <div style='font-size:0.9rem; color:#22543d; margin-top:4px;'>Solo Transporte</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Para rutas domésticas México: mostrar desglose FreightMetrics
        st.markdown(f"""
            <div style='display:flex; justify-content:space-evenly; align-items:stretch; width:100%; margin-bottom:32px; gap:32px;'>
                <div style='flex:1; text-align:center; padding:24px 0;'>
                    <div style='font-size:2.2rem; font-weight:700; color:#2d3748; letter-spacing:1px;'>${datos['total']} {moneda}</div>
                    <div style='font-size:1.1rem; color:#666; margin-top:8px;'>Tarifa Total ({moneda})</div>
                </div>
                <div style='flex:1; text-align:center; padding:24px 0;'>
                    <div style='font-size:2.2rem; font-weight:700; color:#22543d; letter-spacing:1px;'>${datos['base_ref']} {moneda} <span style='font-size:1.1rem; color:#888;'>({cambio_pct}%)</span></div>
                    <div style='font-size:1.1rem; color:#666; margin-top:8px;'>Base de Cálculo</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 Ver desglose de costos y auditoría"):
        st.write(f"**Tipo de Ruta:** {datos['tipo_ruta']}")
        st.write(f"**Base de Cálculo:** {datos['base_ref']}")
        st.write(f"**Distancia:** {datos['distancia_km']} km")
        # FSC solo para rutas internacionales
        if datos['tipo_ruta'] == 'Internacional USA-México' and datos['fsc_estimado'] > 0:
            st.write(f"**FSC Estimado (15%):** ${datos['fsc_estimado']} USD")
        st.write("**Estatus:** Mercado Volátil 📈")
        # Mostrar tarifa por milla o por km según el tipo de ruta
        if datos['tipo_ruta'] == 'Doméstica USA':
            tarifa_milla = None
            try:
                # Leer tarifa DAT desde archivo
                import json, os
                dat_file = os.path.join(os.path.dirname(__file__), "dat_rates_us.json")
                with open(dat_file, "r", encoding="utf-8") as f:
                    dat_data = json.load(f)
                tarifas = dat_data.get("tarifas", {})
                equipo_key = equipo
                if equipo_key.startswith("Caja Seca"):
                    equipo_key = "Caja Seca (Dry Van)"
                elif equipo_key.startswith("Refrigerado"):
                    equipo_key = "Refrigerado (Reefer)"
                elif equipo_key.startswith("Plataforma"):
                    equipo_key = "Plataforma (Flatbed)"
                tarifa_milla = tarifas.get(equipo_key, None)
            except Exception:
                tarifa_milla = None
            if tarifa_milla:
                st.write(f"**Tarifa Spot DAT:** ${tarifa_milla} USD/mi")
        elif datos['tipo_ruta'] == 'Doméstica México':
            # Calcular tarifa por km
            try:
                from logic_rates import FreightMetricsCalculator
                costos_base = obtener_costos_por_equipo(equipo)
                calculator = FreightMetricsCalculator(
                    diesel=costos_base['diesel'],
                    casetas=costos_base['casetas'],
                    sueldo=costos_base['sueldo'],
                    mantenimiento=costos_base['mantenimiento'],
                    riesgo=costos_base['riesgo'],
                    administracion=costos_base['inflacion'],
                    utilidad_pct=0.18
                )
                tarifa_km = calculator.tarifa_spot_final()
                st.write(f"**Tarifa Spot FreightMetrics:** ${tarifa_km} MXN/km")
            except Exception:
                pass
        if datos.get('fuente_tarifa'):
            st.info(f"Fuente tarifa: {datos['fuente_tarifa']}")
        # Mostrar justificación solo a usuarios PRO o ENTERPRISE
        usuario = st.session_state.get('user', {})
        plan = usuario.get('plan', 'free')
        if plan in ['pro', 'enterprise'] and 'justificacion' in datos:
            st.info(f"📝 Justificación: {datos['justificacion']}")

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
        'spot_rate': datos.get('base_ref', ''),
        'base_ref': datos.get('base_ref', ''),
        'tipo_ruta': datos.get('tipo_ruta', ''),
        'rate_per_mile': rate_per_mile,
        'moneda': moneda,
        'moneda_real': moneda,  # redundante para claridad
        'riesgo_pais': st.session_state.get('riesgo_pais', 0),
        'precio_diesel': st.session_state.get('precio_diesel', 0),
        'tiempo_cruce': st.session_state.get('tiempo_cruce', 0),
        'inflacion_mxn': st.session_state.get('inflacion_mxn', 0),
        'tipo_cambio': st.session_state.get('tipo_cambio', 0),
        'demanda_mercado': st.session_state.get('demanda_mercado', 0),
        'capacidad_disponible': st.session_state.get('capacidad_disponible', 0)
    }

    if st.button("🔮 Auditar Tarifa Spot con FreightMetrics"):
        st.session_state['analisis_ia'] = None
        st.experimental_rerun()

def show_subscription_levels():
    st.markdown("""
| Nivel      | Funciones Incluidas                                 | Precio Sugerido   |
|------------|----------------------------------------------------|-------------------|
| **Free**   | 3 cotizaciones/mes, solo rutas MX                  | $0                |
| **Pro**    | Cotizaciones ilimitadas, USA-MX, PDF               | $49 USD/mes       |
| **Enterprise** | API Access, Auditoría de IA avanzada           | $199 USD/mes      |
""")

geo_imported = False

 
st.set_page_config(
    page_title="FreightMetrics Oracle Rate",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    geo_imported = True
    google_api_key = "AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8"
    geo_tool = GeoService(api_key=google_api_key)
except NameError:
    geo_imported = False
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
        
        # Innovación y Transparencia
        "<div style='display: flex; gap: 20px; margin-top: 20px;'>"
        "<div style='flex: 1; background: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px;'>"
        "<h3 style='color: #00FF88; font-size: 1.1rem; font-weight: 700; margin: 0 0 10px 0;'>🚀 Innovación</h3>"
        "<p style='color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.5; margin: 0;'>"
        "Somos los primeros en México en automatizar el análisis de las variables que la SCT y el INEGI publican, "
        "eliminando el error humano y el retraso de los tabuladores manuales."
        "</p>"
        "</div>"
        "<div style='flex: 1; background: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px;'>"
        "<h3 style='color: #00BFFF; font-size: 1.1rem; font-weight: 700; margin: 0 0 10px 0;'>🔍 Transparencia</h3>"
        "<p style='color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.5; margin: 0;'>"
        "Cualquier tarifa mostrada puede ser auditada contra el precio del diésel de la CRE del día de hoy "
        "y el INPP del último mes."
        "</p>"
        "</div>"
        "</div>"
        
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
    # Renderiza la interfaz de prediccion

    # API Key para Google Maps (opcional)
    # FIJAR LA API KEY DIRECTAMENTE
    api_key = "AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8"
    geo_tool_local = None
    try:
        geo_tool_local = GeoService(api_key=api_key)
    except Exception as e:
        print(f"[GeoService ERROR] {e}")
        st.error(f"[GeoService ERROR] {e}")
        geo_tool_local = None

    # Crear columnas para los inputs
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📍 Configuración de Ruta")
        origin_input = st.text_input("Origen (Ciudad, Estado o CP)", placeholder="Ej: Querétaro, MX", key="origin_input")
        dest_input = st.text_input("Destino (Ciudad, Estado o CP)", placeholder="Ej: Chicago, IL", key="dest_input")
        tipo_carga = st.selectbox(
            "Tipo de Carga",
            options=[
                (0, "Dry Van - Carga seca general"),
                (1, "Reefer - Carga refrigerada"),
                (2, "Flatbed - Carga plana"),
                (3, "Contenedor 20'"),
                (4, "Contenedor 40'"),
                (5, "Doble Articulado/ Full")
            ],
            format_func=lambda x: x[1],
            help="Tipo de vehículo o contenedor requerido",
            key="tipo_carga_select"
        )[0]

    # Validar inputs y calcular distancia
    distancia_km = None
    origin_coords = None
    dest_coords = None
    if not origin_input or not dest_input:
        st.warning("Por favor ingresa un origen y un destino.")
    elif geo_tool_local is None:
        st.warning("Google Maps API no está configurada. Ingresa una API Key válida en la configuración para habilitar la validación de ciudades y cálculo de distancia.")
    else:
        with st.spinner('Validando ciudades y calculando ruta...'):
            origin_clean = geo_tool_local.validate_city(origin_input)
            dest_clean = geo_tool_local.validate_city(dest_input)
            # Extraer coordenadas si están disponibles
            if isinstance(origin_clean, dict) and 'lat' in origin_clean and 'lng' in origin_clean:
                origin_coords = (origin_clean['lat'], origin_clean['lng'])
            if isinstance(dest_clean, dict) and 'lat' in dest_clean and 'lng' in dest_clean:
                dest_coords = (dest_clean['lat'], dest_clean['lng'])
            route_info = geo_tool_local.get_route_data(origin_clean, dest_clean)
            if route_info:
                distancia_km = route_info['distance']
                st.success(f"Distancia real: {distancia_km} km")
                # Mostrar coordenadas
                if origin_coords:
                    st.info(f"Coordenadas origen: {origin_coords}")
                if dest_coords:
                    st.info(f"Coordenadas destino: {dest_coords}")
            else:
                st.error("No se pudo calcular la distancia. Verifica los datos ingresados.")

    import requests
    with col2:
        st.markdown("#### 🇲🇽 Variables Mexicanas / USA")
        riesgo_pais = st.slider(
            "Riesgo País (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Nivel de riesgo político/económico en México (0=bajo, 1=alto)",
            key="riesgo_pais"
        )

        # Detectar si la ruta es doméstica USA
        origen = st.session_state.get('origin_input', '').lower()
        destino = st.session_state.get('dest_input', '').lower()
        estados_usa = ['usa', 'united states', 'san diego', 'texas', 'chicago', 'california', 'georgia', 'atlanta', 'new york', 'florida', 'arizona', 'nevada', 'colorado', 'illinois', 'ohio', 'michigan', 'wisconsin', 'minnesota', 'missouri', 'kansas', 'oklahoma', 'louisiana', 'alabama', 'tennessee', 'kentucky', 'indiana', 'iowa', 'arkansas', 'mississippi', 'north carolina', 'south carolina', 'virginia', 'west virginia', 'maryland', 'pennsylvania', 'massachusetts', 'connecticut', 'new jersey', 'delaware', 'rhode island', 'new hampshire', 'vermont', 'maine']
        es_usa = lambda x: any(e in x for e in estados_usa)
        es_mexico = lambda x: 'mx' in x or 'méxico' in x or 'tijuana' in x or 'guadalajara' in x or 'querétaro' in x or 'tlaquepaque' in x
        tipo_cambio = st.session_state.get('tipo_cambio', 18.0)
        precio_diesel = None
        diesel_source = "manual"
        if (es_usa(origen) and es_usa(destino)):
            # Obtener precio diesel USA EIA (USD/galón)
            try:
                eia_url = "https://api.eia.gov/series/?api_key=DEMO_KEY&series_id=PET.EMD_EPD2D_PTE_NUS_DPG.W"
                r = requests.get(eia_url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    usd_per_gal = float(data['series'][0]['data'][0][1])
                    # Convertir a MXN/L
                    gal_to_l = 3.78541
                    precio_diesel = round(usd_per_gal * tipo_cambio / gal_to_l, 2)
                    diesel_source = f"EIA (USD/gal: {usd_per_gal})"
                else:
                    precio_diesel = st.slider(
                        "Precio Diesel (MXN/L)",
                        min_value=15.0,
                        max_value=30.0,
                        value=22.0,
                        step=0.5,
                        help="Precio actual del diesel en México",
                        key="precio_diesel"
                    )
            except Exception as e:
                precio_diesel = st.slider(
                    "Precio Diesel (MXN/L)",
                    min_value=15.0,
                    max_value=30.0,
                    value=22.0,
                    step=0.5,
                    help="Precio actual del diesel en México",
                    key="precio_diesel"
                )
        else:
            # Intentar obtener el precio real del diesel en México
            try:
                from data.market_updates import get_real_diesel_price
                precio_real = get_real_diesel_price()
                if precio_real:
                    precio_diesel = st.number_input(
                        "Precio Diesel (MXN/L) [Automático]",
                        min_value=15.0,
                        max_value=30.0,
                        value=float(precio_real),
                        step=0.1,
                        help="Precio real consultado automáticamente. Puedes ajustar si lo deseas.",
                        key="precio_diesel"
                    )
                    st.info(f"Precio Diesel México (Automático): {precio_real} MXN/L | Fuente: PETROIntelligence/CRE")
                else:
                    raise Exception("No se pudo obtener el precio real")
            except Exception:
                precio_diesel = st.slider(
                    "Precio Diesel (MXN/L)",
                    min_value=15.0,
                    max_value=30.0,
                    value=22.0,
                    step=0.5,
                    help="Precio actual del diesel en México",
                    key="precio_diesel"
                )
                st.caption("Precio ingresado manualmente")

        tiempo_cruce = st.slider(
            "Tiempo de Cruce (horas)",
            min_value=1,
            max_value=72,
            value=6,
            step=1,
            help="Tiempo estimado para cruzar la frontera",
            key="tiempo_cruce"
        )

    with col3:
        st.markdown("#### 📊 Mercado")
        inflacion_mxn = st.slider(
            "Inflación MXN (%)",
            min_value=2.0,
            max_value=10.0,
            value=5.5,
            step=0.1,
            help="Tasa de inflación actual en México",
            key="inflacion_mxn"
        )

        tipo_cambio = st.slider(
            "Tipo de Cambio (MXN/USD)",
            min_value=15.0,
            max_value=25.0,
            value=18.0,
            step=0.1,
            help="Tipo de cambio peso mexicano por dólar",
            key="tipo_cambio"
        )

        demanda_mercado = st.slider(
            "Demanda del Mercado (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Nivel de demanda actual (0=baja, 1=alta)",
            key="demanda_mercado"
        )

        capacidad_disponible = st.slider(
            "Capacidad Disponible (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Capacidad de transporte disponible (0=escasa, 1=abundante)",
            key="capacidad_disponible"
        )

    # Variables temporales (calculadas automáticamente)
    now = datetime.now()
    mes = now.month
    dia_semana = now.weekday()
    es_fin_semana = 1 if dia_semana >= 5 else 0
    es_temporada_alta = 1 if mes in [11, 12, 3, 4] else 0  # Temporada alta

    # Botón de tarifa spot y predicción
    col_prof, col_pred = st.columns([1, 1])
    with col_prof:
        if st.button("📋 Ver Tarifa Spot FreightMetrics", width='stretch'):
            if distancia_km and tipo_carga is not None:
                # Mapear tipo_carga numérico a texto
                tipos_equipo = {
                    0: "Caja Seca (Dry Van)",
                    1: "Refrigerado (Reefer)",
                    2: "Plataforma (Flatbed)",
                    3: "Caja Seca (Dry Van)",
                    4: "Caja Seca (Dry Van)",
                    5: "Full (Doble)"
                }
                equipo = tipos_equipo.get(tipo_carga, "Caja Seca (Dry Van)")
                # Solo guardar en session_state los campos que NO son claves de widgets
                st.session_state['tipo_carga'] = tipo_carga
                mostrar_cotizacion_profesional(distancia_km, equipo)
            else:
                st.warning("Primero ingresa origen, destino y tipo de carga válidos.")


    # Botón de predicción IA oculto en el frontend para evitar confusión, pero el código sigue disponible
    # with col_pred:
    #     predict_button = st.button("🔮 Predecir Tarifa (IA)", type="primary", use_container_width=True)
    predict_button = False  # Oculto para el usuario

    # Resultados de predicción
    if predict_button:
        with st.spinner("Consultando Oracle Rate..."):
            route_data = {
                "origin": origin_input,
                "destination": dest_input,
                "distancia_km": distancia_km,
                "tipo_carga": tipo_carga,
                "riesgo_pais": riesgo_pais,
                "precio_diesel": precio_diesel,
                "tiempo_cruce": tiempo_cruce,
                "inflacion_mxn": inflacion_mxn,
                "tipo_cambio": tipo_cambio,
                "demanda_mercado": demanda_mercado,
                "capacidad_disponible": capacidad_disponible,
                "mes": mes,
                "dia_semana": dia_semana,
                "es_fin_semana": es_fin_semana,
                "es_temporada_alta": es_temporada_alta
            }
            prediction_request = {
                "route": route_data,
                "prediction_days": 7
            }
            result = call_api("/predict", method="POST", data=prediction_request)

            if result:
                # Guardar el resultado completo para el Oráculo IA
                st.session_state['prediction_result'] = result

                # Mostrar resultados
                st.success("✅ Predicción completada exitosamente!")
                st.markdown(f"**Origen:** {origin_input}")
                st.markdown(f"**Destino:** {dest_input}")
                col_actual, col_predicha, col_cambio, col_confianza = st.columns(4)
                with col_actual:
                    st.metric("Tarifa Actual", f"${result['tarifa_actual']:,.0f}", help="Tarifa estimada para hoy")
                with col_predicha:
                    st.metric("Predicción 7 días", f"${result['tarifa_predicha']:,.0f}", help="Tarifa estimada en 7 días")
                with col_cambio:
                    cambio = result['cambio_porcentual']
                    color = "inverse" if cambio < 0 else "normal"
                    st.metric("Cambio", f"{cambio:+.1f}%", help="Cambio porcentual esperado", delta_color=color)
                with col_confianza:
                    confianza = result['confianza_modelo']
                    st.metric("Confianza Modelo", f"{confianza:.1f}%", help="Precisión estimada del modelo")
                st.markdown("### 📊 Comparación Tarifa Actual vs Predicción")
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Tarifa Actual', x=['Hoy'], y=[result['tarifa_actual']], marker_color='#667eea'))
                fig.add_trace(go.Bar(name='Predicción 7 días', x=['En 7 días'], y=[result['tarifa_predicha']], marker_color='#764ba2'))
                fig.update_layout(title="Comparación de Tarifas", yaxis_title="Tarifa (USD)", showlegend=True, height=400)
                st.plotly_chart(fig, width='stretch')
                st.markdown("### 🎯 Factores de Influencia")
                factores = result['factores_influencia']
                df_factores = pd.DataFrame({'Factor': list(factores.keys()), 'Importancia': list(factores.values())}).sort_values('Importancia', ascending=True)
                fig_factores = px.bar(df_factores, y='Factor', x='Importancia', orientation='h', title="Importancia de Variables en la Predicción", labels={'Importancia': 'Importancia (%)'})
                fig_factores.update_layout(height=400)
                st.plotly_chart(fig_factores, width='stretch')
                st.markdown("### 💡 Recomendación Estratégica")
                cambio = result['cambio_porcentual']
                confianza = result['confianza_modelo']
                if cambio > 5 and confianza > 80:
                    recomendacion = "⚠️ **ESPERAR**: La tarifa tiende a subir. Considera programar el envío pronto."
                    color_rec = "#ff9800"
                elif cambio < -5 and confianza > 80:
                    recomendacion = "✅ **CONTRATAR AHORA**: La tarifa bajará. Es un buen momento para negociar."
                    color_rec = "#4caf50"
                elif confianza < 75:
                    recomendacion = "🤔 **MONITOREAR**: Alta incertidumbre. Revisa nuevamente en 24 horas."
                    color_rec = "#2196f3"
                else:
                    recomendacion = "📊 **TARIFA ESTABLE**: No hay cambios significativos esperados."
                    color_rec = "#607d8b"
                html_rec = (f"<div style='background-color: {color_rec}20; border-left: 5px solid {color_rec}; padding: 20px; border-radius: 10px; margin: 10px 0;'>" f"<h4 style='color: {color_rec}; margin: 0 0 10px 0;'>Recomendación</h4>" f"<p style='color: #333; margin: 0; font-size: 1.1rem;'>{recomendacion}</p>" "</div>")
                st.markdown(html_rec, unsafe_allow_html=True)
            else:
                st.error("❌ Error al obtener la predicción. Verifica la conexión con la API.")

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
        page = st.radio("Menu Principal", ["📊 Cotizador", "📈 Índice Tarifas Spot", "⭐ Suscripción", "❓ FAQ", "📩 Contacto", "📋 Términos y Condiciones", "🔒 Política de Privacidad"])

    if page == "📊 Cotizador":
        # Renderizar encabezado profesional
        equipo = st.session_state.get('prediction_result', {}).get('tipo_equipo', None)
        if equipo:
            st.markdown(f"""
                <div style='font-size:2.6rem; font-weight:800; text-align:center; margin: 30px 0 20px 0; color:#2d3748;'>
                    Tarifa Spot - Resultado de Cotización: {equipo}
                </div>
            """, unsafe_allow_html=True)
        
        # Renderizar interfaz del cotizador
        render_header()
        render_prediction_interface()
        render_system_info()
        
        # Auditoría IA (después de la predicción)
        st.markdown("---")
        st.markdown("### 🛡️ Auditoría del Oráculo (IA)")
        with st.container():
            # Usar los datos reales de la predicción si existen
            if 'prediction_result' in st.session_state:
                pred = st.session_state['prediction_result']
                
                # Datos específicos de DAT si es ruta internacional/USA
                dat_info = {}
                if pred.get('tipo_ruta', '') in ['USA Doméstica', 'Internacional']:
                    dat_info = {
                        'dat_rate': pred.get('base_ref', 0),
                        'dat_source': 'DAT USA Doméstica' if 'USA' in pred.get('tipo_ruta', '') else 'DAT Internacional',
                        'dat_rate_per_mile': pred.get('rate_per_mile', 0),
                        'dat_equipement': pred.get('tipo_equipo', ''),
                        'usa_domestic': 'USA' in pred.get('tipo_ruta', '') and 'Internacional' not in pred.get('tipo_ruta', '')
                    }
                
                ai_data = {
                    'origin': pred.get('origin', ''),
                    'destination': pred.get('destination', ''), 
                    'distancia_km': pred.get('distancia_km', 0),
                    'distancia_mi': pred.get('distancia_mi', 0),
                    'total_rate': pred.get('total_rate', pred.get('tarifa_actual', 0)),
                    'prediccion_7d': pred.get('prediccion_7d', ''),
                    'spot_rate': pred.get('spot_rate', ''),
                    'risk_level': pred.get('riesgo_pais', 0),
                    'tipo_equipo': pred.get('tipo_equipo', 'N/A'),
                    'rate_per_mile': pred.get('rate_per_mile', 'N/A'),
                    'riesgo_pais': pred.get('riesgo_pais', 0),
                    'precio_diesel': pred.get('precio_diesel', 0),
                    'tiempo_cruce': pred.get('tiempo_cruce', 0),
                    'inflacion_mxn': pred.get('inflacion_mxn', 0),
                    'tipo_cambio': pred.get('tipo_cambio', 0),
                    'demanda_mercado': pred.get('demanda_mercado', 0),
                    'capacidad_disponible': pred.get('capacidad_disponible', 0),
                    'tipo_ruta': pred.get('tipo_ruta', ''),
                    'base_ref': pred.get('base_ref', ''),
                    'moneda': pred.get('moneda', 'USD'),
                    'pais_origen': pred.get('pais_origen', ''),
                    'pais_destino': pred.get('pais_destino', ''),
                    'debug_info': f"Origen: {pred.get('origen_hint', '')}, Destino: {pred.get('destino_hint', '')}",
                    # Información específica de DAT
                    **dat_info
                }
            else:
                ai_data = {
                    'origin': '',
                    'destination': '',
                    'distancia_km': 0,
                    'distancia_mi': 0,
                    'total_rate': 0,
                    'prediccion_7d': '',
                    'spot_rate': '',
                    'risk_level': 0,
                    'tipo_equipo': 'N/A',
                    'rate_per_mile': 'N/A',
                    'riesgo_pais': 0,
                    'precio_diesel': 0,
                    'tiempo_cruce': 0,
                    'inflacion_mxn': 0,
                    'tipo_cambio': 0,
                    'demanda_mercado': 0,
                    'capacidad_disponible': 0
                }

            # Validar datos antes de permitir análisis IA
            datos_faltantes = []
            if not ai_data['origin']:
                datos_faltantes.append('Origen')
            if not ai_data['destination']:
                datos_faltantes.append('Destino')
            if not ai_data['tipo_equipo'] or ai_data['tipo_equipo'] == 'N/A':
                datos_faltantes.append('Tipo de equipo')
            if not ai_data['distancia_km']:
                datos_faltantes.append('Distancia')
            if not ai_data['total_rate']:
                datos_faltantes.append('Tarifa Total')
            if not ai_data['spot_rate']:
                datos_faltantes.append('Spot Rate')
            for var in ['riesgo_pais','precio_diesel','tiempo_cruce','inflacion_mxn','tipo_cambio','demanda_mercado','capacidad_disponible']:
                if ai_data[var] in [None, 0, '']:
                    datos_faltantes.append(var.replace('_',' ').capitalize())

            if datos_faltantes:
                st.error(f"⚠️ Faltan datos clave para el análisis del Oráculo: {', '.join(set(datos_faltantes))}. Completa la tarifa spot o la predicción IA antes de auditar.")

            GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else st.text_input("Gemini API Key", type="password")

            # Botón para auditar tarifa spot
            if st.button("🔮 Auditar Tarifa Spot con FreightMetrics", key="ai_analyze_button"):
                # Limpiar análisis anterior
                if 'analisis_ia' in st.session_state:
                    del st.session_state['analisis_ia']
                if GEMINI_API_KEY:
                    try:
                        ai_engine = FreightAI(GEMINI_API_KEY)
                        with st.spinner(f"Analizando ruta {ai_data['origin']} a {ai_data['destination']}..."):
                            st.session_state['analisis_ia'] = ai_engine.analyze_route(ai_data)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creando modelo Gemini: {e}")
                else:
                    st.warning("Por favor ingresa tu Gemini API Key para usar el Oráculo de Auditoría IA.")

            # Mostrar el análisis si existe
            if 'analisis_ia' in st.session_state:
                st.info(st.session_state['analisis_ia'])
    elif page == "📈 Índice Tarifas Spot":
        show_tendencias_de_mercado()
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