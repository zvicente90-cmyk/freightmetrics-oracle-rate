#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para diagnosticar carga de datos"""

import json
import os
import pandas as pd

print("=" * 60)
print("🔍 DIAGNÓSTICO DE DATOS - Dashboard KPIs")
print("=" * 60)

# 1. Verificar matriz_comparativa_mx.json
matriz_path = "matriz_comparativa_mx.json"
print(f"\n1️⃣  Verificando: {matriz_path}")
print(f"   Existe: {os.path.exists(matriz_path)}")

if os.path.exists(matriz_path):
    try:
        with open(matriz_path, 'r', encoding='utf-8') as f:
            matriz_data = json.load(f)
        print("   ✅ JSON cargado correctamente")
        print(f"   Claves principales: {list(matriz_data.keys())}")
        
        if 'matriz' in matriz_data:
            print(f"   Años: {list(matriz_data['matriz'].keys())}")
            
            # Mostrar estructura de 1 período
            anio = list(matriz_data['matriz'].keys())[0]
            meses = matriz_data['matriz'][anio]
            mes = list(meses.keys())[0]
            
            print(f"\n   Ejemplo: Año {anio}, Mes {mes}")
            mes_data = meses[mes]
            
            for zona, zona_rows in mes_data.items():
                print(f"   - Zona: {zona}")
                if isinstance(zona_rows, list):
                    print(f"     Filas: {len(zona_rows)}")
                    # Buscar TARIFA SPOT FINAL
                    for row in zona_rows:
                        if row.get("Componente") == "TARIFA SPOT FINAL":
                            print(f"     ✅ Encontrado: TARIFA SPOT FINAL")
                            print(f"        Caja Seca: {row.get('Caja Seca (Dry Van)', 'N/A')}")
                            print(f"        Plataforma: {row.get('Plataforma (Flatbed)', 'N/A')}")
                            break
                break
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

# 2. Verificar freightmetrics_historical.json
print("\n" + "=" * 60)
hist_path = "freightmetrics_historical.json"
print(f"2️⃣  Verificando: {hist_path}")
print(f"   Existe: {os.path.exists(hist_path)}")

if os.path.exists(hist_path):
    try:
        with open(hist_path, 'r', encoding='utf-8') as f:
            hist_data = json.load(f)
        print("   ✅ JSON cargado correctamente")
        print(f"   Claves principales: {list(hist_data.keys())}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

# 3. Probar función de carga del dashboard
print("\n" + "=" * 60)
print("3️⃣  Probando función procesar_matriz_a_dataframe()")

try:
    # Copiar la función del dashboard
    datos = []
    meses_orden = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    for anio, anio_data in matriz_data.get("matriz", {}).items():
        for mes, mes_data in anio_data.items():
            for zona, zona_rows in mes_data.items():
                if isinstance(zona_rows, list):
                    for row in zona_rows:
                        if row.get("Componente") == "TARIFA SPOT FINAL":
                            datos.append({
                                'fecha': f"{anio}-{mes}",
                                'fecha_sort': f"{anio}-{meses_orden.index(mes)+1:02d}",
                                'zona': zona,
                                'caja_seca_mxn': float(row.get("Caja Seca (Dry Van)", 0)),
                                'plataforma_mxn': float(row.get("Plataforma (Flatbed)", 0)),
                                'refrigerado_mxn': float(row.get("Refrigerado (Reefer)", 0)),
                                'full_mxn': float(row.get("Full (Doble)", 0)),
                            })
                            break
    
    if datos:
        df = pd.DataFrame(datos)
        print(f"   ✅ DataFrame creado")
        print(f"   Filas: {len(df)}")
        print(f"   Columnas: {list(df.columns)}")
        print(f"\n   Primeras filas:")
        print(df.head())
        print(f"\n   Resumen de datos:")
        print(df.describe())
    else:
        print("   ❌ No se encontraron datos")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Diagnóstico completado")
print("=" * 60)
