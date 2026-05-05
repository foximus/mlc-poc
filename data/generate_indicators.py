"""
Genera data/indicators-usuarios.json a partir de info/indicadores.xlsx (hoja "Usuarios").

Cada indicador queda mapeado al campo equivalente en el schema del mock
(data/mock-usuarios.json) por prefijo de ID (P16 -> p16_*).

Salida por indicador:
  {
    "id": "P16",
    "pilar": "Accesibilidad",
    "name": "Tiempo de espera para atención",
    "pregunta": "...",
    "objetivo": "...",
    "field": "p16_tiempo_espera",
    "type": "select_one tiempo_espera",     # del schema
    "respuestas": "Menos de 30 minutos, ...",
    "establecimiento": "UAI",
    "clasificacion": "Universal"
  }
"""

from __future__ import annotations
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
INFO = ROOT / "info"
OUT  = ROOT / "data"


def load_indicators():
    wb = openpyxl.load_workbook(INFO / "indicadores.xlsx", data_only=True)
    ws = wb["Usuarios"]
    rows = list(ws.iter_rows(values_only=True))
    header = [h.strip() if isinstance(h, str) else h for h in rows[0]]

    def col_exact(name):
        for i, h in enumerate(header):
            if h and str(h).strip().lower() == name.lower():
                return i
        return None

    def col(name_substr):
        for i, h in enumerate(header):
            if h and name_substr.lower() in str(h).lower():
                return i
        return None

    i_pilar       = col_exact("Pilar")
    i_indicador   = col_exact("Indicador")
    i_id_nuevo    = col_exact("ID Pregunta Nuevo")
    i_pregunta    = col_exact("Pregunta")
    i_tipo        = col("Tipo de respuesta")
    i_objetivo    = col("Objetivo")
    i_estab       = col("establecimiento")
    i_clasif      = col("Clasificación")

    indicators = []
    for r in rows[1:]:
        ind = r[i_indicador] if i_indicador is not None else None
        if not ind or str(ind).strip().lower() == "no aplica":
            continue
        indicators.append({
            "pilar":          str(r[i_pilar] or "").strip(),
            "name":           str(ind).strip(),
            "id":             str(r[i_id_nuevo] or "").strip(),
            "pregunta":       str(r[i_pregunta] or "").strip(),
            "respuestas":     str(r[i_tipo] or "").strip(),
            "objetivo":       str(r[i_objetivo] or "").strip(),
            "establecimiento":str(r[i_estab] or "").strip(),
            "clasificacion":  str(r[i_clasif] or "").strip(),
        })
    return indicators


def load_mock_schema():
    data = json.loads((OUT / "mock-usuarios.json").read_text(encoding="utf-8"))
    schema = data["schema"]
    # build index: prefix "pNN" -> field meta
    by_prefix = {}
    for q in schema:
        m = re.match(r"^(p\d+)(_|$)", q["name"])
        if m:
            by_prefix[m.group(1)] = q
    return by_prefix


def main():
    indicators = load_indicators()
    schema_by_prefix = load_mock_schema()

    enriched = []
    for ind in indicators:
        pid = ind["id"].lower()  # "P16" -> "p16"
        meta = schema_by_prefix.get(pid)
        ind["field"] = meta["name"] if meta else None
        ind["type"]  = meta["type"] if meta else None
        enriched.append(ind)

    out = OUT / "indicators-usuarios.json"
    out.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    # Reporte resumido
    matched = sum(1 for i in enriched if i["field"])
    print(f"[ok] {out} - {len(enriched)} indicadores ({matched} con field mapeado)")
    pilares = {}
    for i in enriched:
        pilares.setdefault(i["pilar"], 0)
        pilares[i["pilar"]] += 1
    for p, n in pilares.items():
        print(f"  - {p}: {n}")


if __name__ == "__main__":
    main()
