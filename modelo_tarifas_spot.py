"""
Modelo simple de Tarifas Spot - FreightMetrics

Este módulo define los componentes por tipo de equipo según la tabla
proporcionada y permite calcular la tarifa spot final (por km) y
exportar un archivo JSON con el modelo base.

Uso rápido:
    python modelo_tarifas_spot.py --export

Funciones principales:
 - get_components(equipo)
 - compute_spot_rate(equipo, overrides=None)
 - export_model_json(path)

"""
from __future__ import annotations
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Datos base extraídos de la tabla proporcionada (valores en $/km)
BASE_MODEL = {
    "sencillo": {
        "label": "Sencillo (Caja Seca)",
        "consumo_diesel": 11.40,
        "inflacion": 2.40,
        "casetas": 5.40,
        "sueldo_viaticos": 4.50,
        "riesgo_seguro": 2.20,
        "manto_accesorios": 3.20,
        "costo_operativo": 29.10,
        "utilidad_pct": 0.18,
        "tarifa_final": 34.34,
    },
    "plataforma": {
        "label": "Plataforma (Flatbed)",
        "consumo_diesel": 12.10,
        "inflacion": 2.80,
        "casetas": 5.40,
        "sueldo_viaticos": 5.10,
        "riesgo_seguro": 3.40,
        "manto_accesorios": 3.90,
        "costo_operativo": 32.70,
        "utilidad_pct": 0.18,
        "tarifa_final": 38.58,
    },
    "refrigerado": {
        "label": "Refrigerado (Termo)",
        "consumo_diesel": 15.20,
        "inflacion": 3.10,
        "casetas": 5.40,
        "sueldo_viaticos": 5.20,
        "riesgo_seguro": 3.60,
        "manto_accesorios": 4.10,
        "costo_operativo": 36.60,
        "utilidad_pct": 0.18,
        "tarifa_final": 43.19,
    },
    "full": {
        "label": "Full (Doble Remolque)",
        "consumo_diesel": 16.70,
        "inflacion": 3.80,
        "casetas": 9.80,
        "sueldo_viaticos": 6.80,
        "riesgo_seguro": 3.10,
        "manto_accesorios": 5.50,
        "costo_operativo": 45.70,
        "utilidad_pct": 0.18,
        "tarifa_final": 53.93,
    },
}


def get_components(equipo: str) -> Dict[str, Any]:
    """Devuelve los componentes base para un `equipo`.

    equipo: uno de 'sencillo', 'plataforma', 'refrigerado', 'full'.
    """
    key = equipo.lower()
    if key not in BASE_MODEL:
        raise KeyError(f"Equipo desconocido: {equipo}")
    return dict(BASE_MODEL[key])


def compute_spot_rate(equipo: str, overrides: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Calcula la tarifa spot final por km para el `equipo`.

    - `overrides` puede contener valores para cualquiera de los componentes
      (por ejemplo 'consumo_diesel', 'casetas', 'inflacion', etc.).

    Devuelve un dict con los componentes usados, `costo_operativo` calculado,
    `utilidad` y `tarifa_spot`.
    """
    data = get_components(equipo)
    if overrides:
        for k, v in overrides.items():
            if k in data:
                data[k] = float(v)

    # Recalcular costo operativo si alguno de los subcomponentes cambió
    costo_operativo = round(
        data.get("consumo_diesel", 0)
        + data.get("inflacion", 0)
        + data.get("casetas", 0)
        + data.get("sueldo_viaticos", 0)
        + data.get("riesgo_seguro", 0)
        + data.get("manto_accesorios", 0),
        2,
    )

    utilidad = round(costo_operativo * data.get("utilidad_pct", 0.18), 2)
    tarifa_spot = round(costo_operativo + utilidad, 2)

    result = {
        "equipo": equipo,
        "label": data.get("label"),
        "costo_operativo": costo_operativo,
        "utilidad": utilidad,
        "tarifa_spot": tarifa_spot,
        "componentes": {
            "consumo_diesel": data.get("consumo_diesel"),
            "inflacion": data.get("inflacion"),
            "casetas": data.get("casetas"),
            "sueldo_viaticos": data.get("sueldo_viaticos"),
            "riesgo_seguro": data.get("riesgo_seguro"),
            "manto_accesorios": data.get("manto_accesorios"),
            "utilidad_pct": data.get("utilidad_pct"),
        },
    }
    return result


def export_model_json(path: str | Path = "modelo_tarifas_spot.json") -> Path:
    """Exporta el modelo base (`BASE_MODEL`) a un archivo JSON y devuelve la ruta."""
    p = Path(path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(BASE_MODEL, f, ensure_ascii=False, indent=2)
    return p


def export_to_excel(path: str | Path = "modelo_tarifas_spot.xlsx") -> Path:
    """Exporta el modelo base a una hoja Excel (una fila por equipo)."""
    try:
        import pandas as pd
    except Exception:
        raise RuntimeError("Pandas no está disponible. Instala 'pandas' y 'openpyxl' para exportar Excel.")

    rows = []
    for key, v in BASE_MODEL.items():
        row = {
            "equipo_key": key,
            "equipo": v.get("label"),
            "consumo_diesel": v.get("consumo_diesel"),
            "inflacion": v.get("inflacion"),
            "casetas": v.get("casetas"),
            "sueldo_viaticos": v.get("sueldo_viaticos"),
            "riesgo_seguro": v.get("riesgo_seguro"),
            "manto_accesorios": v.get("manto_accesorios"),
            "costo_operativo": v.get("costo_operativo"),
            "utilidad_pct": v.get("utilidad_pct"),
            "tarifa_final": v.get("tarifa_final"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    p = Path(path)
    df.to_excel(p, index=False)
    return p


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generador del modelo de Tarifas Spot")
    parser.add_argument("--export", action="store_true", help="Exportar modelo a modelo_tarifas_spot.json")
    parser.add_argument("--export-excel", action="store_true", help="Exportar modelo a modelo_tarifas_spot.xlsx")
    parser.add_argument("--equipo", type=str, help="Calcular tarifa para un equipo específico")
    parser.add_argument("--override", action="append", help="Override componente en formato clave=valor (puede repetirse)")

    args = parser.parse_args()

    if args.export:
        out = export_model_json()
        print(f"Modelo exportado a: {out}")

    if args.export_excel:
        out_x = export_to_excel()
        print(f"Modelo exportado a Excel: {out_x}")

    if args.equipo:
        overrides = {}
        if args.override:
            for o in args.override:
                if "=" in o:
                    k, v = o.split("=", 1)
                    try:
                        overrides[k.strip()] = float(v)
                    except ValueError:
                        print(f"Ignorando override no numérico: {o}")

        res = compute_spot_rate(args.equipo, overrides=overrides if overrides else None)
        print(json.dumps(res, ensure_ascii=False, indent=2))
