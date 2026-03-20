import google.generativeai as genai

class FreightAI:
    def __init__(self, api_key, model_name=None):
        genai.configure(api_key=api_key)
        if model_name is None:
            self.model_name = 'gemini-1.5-flash'
        else:
            self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)

    def analyze_route(self, data):
        # Determinar moneda y tipo de ruta para contexto correcto
        moneda = data.get('moneda', 'USD')
        tipo_ruta = data.get('tipo_ruta', 'Ruta General')
        tarifa = data.get('total_rate', 0)
        distancia_km = data.get('distancia_km', 0)
        
        # Verificar si es una ruta DAT con tarifa específica
        es_ruta_dat = data.get('dat_rate') is not None
        dat_rate = data.get('dat_rate', 0)
        dat_source = data.get('dat_source', '')
        dat_rate_per_mile = data.get('dat_rate_per_mile', 0)
        
        # 🚨 DETECTOR DE ANOMALÍAS DE TARIFA
        alertas_criticas = []
        
        # Si es ruta DAT, evaluar específicamente contra datos DAT
        if es_ruta_dat and dat_rate > 0:
            distancia_mi = data.get('distancia_mi', 0)
            # Calcular dat_rate_per_mile si no está disponible
            if distancia_mi > 0 and dat_rate_per_mile <= 0:
                dat_rate_per_mile = dat_rate / distancia_mi
            if distancia_mi > 0 and dat_rate_per_mile > 0:
                # Para rutas DAT, evaluar la tarifa real vs el rango DAT conocido
                if 'USA' in dat_source:
                    # Rangos DAT USA domésticas: $2.20-2.80 típicamente
                    if dat_rate_per_mile > 3.50:
                        alertas_criticas.append(f"🔴 TARIFA DAT ALTA: ${dat_rate_per_mile:.2f}/mi excede rangos típicos DAT USA ($2.20-2.80/mi)")
                    elif dat_rate_per_mile < 1.80:
                        alertas_criticas.append(f"🟡 TARIFA DAT BAJA: ${dat_rate_per_mile:.2f}/mi por debajo del mercado DAT USA")
                elif 'Internacional' in dat_source:
                    # Rangos DAT internacionales: $2.85-4.50 típicamente
                    if dat_rate_per_mile > 5.00:
                        alertas_criticas.append(f"🔴 TARIFA INTERNACIONAL ALTA: ${dat_rate_per_mile:.2f}/mi excede rangos DAT internacionales ($2.85-4.50/mi)")
                    elif dat_rate_per_mile < 2.50:
                        alertas_criticas.append(f"🟡 TARIFA INTERNACIONAL BAJA: ${dat_rate_per_mile:.2f}/mi por debajo del mercado DAT")
        else:
            # 🚨 ALERTA CRÍTICA: Sin datos DAT específicos para evaluar
            if tipo_ruta in ['Doméstica USA', 'Internacional USA-México'] and not es_ruta_dat:
                alertas_criticas.append("🚨 ALERTA CRÍTICA: No se proporciona la tarifa DAT específica para evaluar. Solo se puede ofrecer análisis genérico sin validación de mercado DAT.")
        
        # Verificar coherencia de monedas y valores (análisis adicional)
        if moneda == 'MXN' and distancia_km > 0:
            tarifa_por_km = tarifa / distancia_km
            if tarifa_por_km > 80:  # Límite más realista para FreightMetrics 2026
                alertas_criticas.append(f"⚠️ ALERTA: ${tarifa_por_km:.2f} MXN/km excede límites normales (máx $65 MXN/km)")
            elif tarifa_por_km < 25:
                alertas_criticas.append(f"🟡 TARIFA BAJA: ${tarifa_por_km:.2f} MXN/km por debajo del mercado (min $30 MXN/km)")
        elif moneda == 'USD' and distancia_km > 0:
            distancia_mi = distancia_km * 0.621371
            if distancia_mi > 0:
                tarifa_por_milla = tarifa / distancia_mi
                # Para rutas domésticas México mal etiquetadas
                if tarifa_por_milla > 10 and 'México' in tipo_ruta:
                    alertas_criticas.append(f"🚨 ERROR CRÍTICO: ${tarifa_por_milla:.2f} USD/mi sugiere conversión incorrecta - posible tarifa MXN etiquetada como USD")
        
        # Contexto específico según el tipo de ruta y fuente de datos
        if es_ruta_dat:
            if 'USA' in dat_source:
                contexto_ruta = "doméstica estadounidense (tarifas DAT)"
                referencia_mercado = f"Referencias DAT USA: ${dat_rate_per_mile:.2f}/mi actual vs rango típico $2.20-2.80/mi para van seco"
            elif 'Internacional' in dat_source:
                contexto_ruta = "internacional México-EEUU (tarifas DAT)"
                referencia_mercado = f"Referencias DAT Internacional: ${dat_rate_per_mile:.2f}/mi actual vs rango típico $2.85-4.50/mi + FSC 15-18%"
            else:
                contexto_ruta = "ruta DAT"
                referencia_mercado = f"Referencias DAT: ${dat_rate_per_mile:.2f}/mi actual"
        elif 'Doméstica México' in tipo_ruta:
            contexto_ruta = "doméstica mexicana (pesos MXN)"
            referencia_mercado = "Referencias: FreightMetrics $34.34-53.93 MXN/km según tipo equipo"
        elif 'Doméstica USA' in tipo_ruta:
            contexto_ruta = "doméstica estadounidense (dólares USD)"  
            referencia_mercado = "Referencias: DAT $2.20-2.45 USD/milla para van seco (sin datos DAT específicos)"
        elif 'Internacional USA-México' in tipo_ruta:
            contexto_ruta = "internacional México-EEUU (dólares USD)"
            referencia_mercado = "Referencias: $2.85-4.50 USD/milla + FSC 15-18% para internacionales (sin datos DAT específicos)"
        else:
            contexto_ruta = "ruta general"
            referencia_mercado = "Referencias: Consultar tarifas según mercado específico"
        
        # Construir información de tarifa para el prompt
        info_tarifa = f"💰 Tarifa Total: ${tarifa:,.2f} {moneda}"
        if es_ruta_dat:
            info_tarifa += f"\n💎 Tarifa DAT Específica: ${dat_rate:,.2f} USD (${dat_rate_per_mile:.2f}/mi)"
            info_tarifa += f"\n📋 Fuente: {dat_source}"
        
        # Construir prompt con alertas críticas si existen
        alertas_texto = "\n".join(alertas_criticas) if alertas_criticas else ""
        debug_texto = f"🔍 DEBUG: {data.get('debug_info', '')} | Tipo detectado: {tipo_ruta}"
        
        prompt = (
            f"Actúa como un Auditor Senior de Logística México-EEUU especializado en tarifas DAT.\n"
            f"Analiza estos datos de flete para ruta {contexto_ruta}:\n\n"
            f"📍 Ruta: {data['origin']} a {data['destination']}\n"  
            f"{info_tarifa}\n"
            f"📏 Distancia: {distancia_km} km / {data.get('distancia_mi', 0)} mi\n"
            f"🚛 Equipo: {data.get('tipo_equipo', 'N/A')}\n"
            f"📋 Tipo Ruta: {tipo_ruta}\n"
            f"⚠️ Riesgo País: {data.get('risk_level', data.get('riesgo_pais', 0))}/10\n"
            f"⛽ Diesel: ${data.get('precio_diesel', 0)}/L\n"
            f"{debug_texto}\n\n"
            f"{alertas_texto}\n\n" if alertas_criticas else ""
            f"{referencia_mercado}\n\n"
            f"🎯 ANÁLISIS REQUERIDO:\n"
            f"1. ¿La tarifa {'DAT específica' if es_ruta_dat else 'estimada'} está dentro del rango de mercado? (Sí/No + justificación)\n"
            f"2. Tres riesgos operativos específicos de esta ruta\n"  
            f"3. Dos recomendaciones de optimización inmediatas\n\n"
            f"{'PRIORIZA explicar alertas críticas detectadas. ' if alertas_criticas else ''}Máximo 150 palabras."
        )
        try:
            respuesta = self.model.generate_content(prompt)
            # Elimina bloques duplicados completos
            blocks = respuesta.text.strip().split('\n\n')
            seen_blocks = set()
            filtered_blocks = []
            for block in blocks:
                block_clean = block.strip()
                if block_clean and block_clean not in seen_blocks:
                    filtered_blocks.append(block_clean)
                    seen_blocks.add(block_clean)
            return '\n\n'.join(filtered_blocks)
        except Exception as e:
            return f"Error de conexión: {str(e)}"

    def analyze_route_custom(self, prompt_personalizado):
        """
        Analiza una ruta usando un prompt personalizado.
        Ideal para análisis precisos con requisitos específicos (ej: respuestas cortas, diesel).
        """
        try:
            respuesta = self.model.generate_content(prompt_personalizado)
            if respuesta and respuesta.text:
                return respuesta.text.strip()
            return None
        except Exception as e:
            print(f"[FreightAI Error] {str(e)}")
            return None
