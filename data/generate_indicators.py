"""
Genera data/indicators-usuarios.json y data/indicators-prestadores.json
a partir de info/indicadores.xlsx (hojas "Usuario" y "Prestadores de servicios ").

Cada indicador queda mapeado al campo equivalente en el schema del mock
(data/mock-{usuarios,prestadores}.json) por el ID Pregunta Nuevo (Usuario)
o ID pregunta (Prestadores), normalizado en mayúsculas.

Salida por indicador (Usuarios):
  {
    "id": "P16",
    "pilar": "Accesibilidad",
    "name": "Tiempo de espera para atención",
    "pregunta": "...",
    "objetivo": "...",
    "field": "p16",
    "type": "select_one p16_list",
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


def col_finder(header):
    norm = [str(h).strip().lower() if h else "" for h in header]
    def exact(name):
        n = name.strip().lower()
        for i, h in enumerate(norm):
            if h == n:
                return i
        return None
    def contains(substr):
        s = substr.strip().lower()
        for i, h in enumerate(norm):
            if s in h:
                return i
        return None
    return exact, contains


def normalize_id(raw) -> str:
    """P02.1 / p02.1 / p18 -> 'P02.1' / 'P18'."""
    return str(raw or "").strip().upper()


def load_indicators(sheet_name: str, id_col_label: str):
    wb = openpyxl.load_workbook(INFO / "indicadores.xlsx", data_only=True)
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    exact, contains = col_finder(header)

    i_pilar    = exact("Pilar")
    i_ind      = exact("Indicador")
    i_id       = exact(id_col_label) or contains(id_col_label)
    i_pregunta = exact("Pregunta") or contains("pregunta")
    i_tipo     = contains("tipo de respuesta")
    i_objetivo = contains("objetivo")
    i_estab    = contains("establecimiento")
    i_clasif   = contains("clasificación") or contains("clasificacion")

    indicators = []
    for r in rows[1:]:
        ind = r[i_ind] if i_ind is not None else None
        if not ind or str(ind).strip().lower() == "no aplica":
            continue
        indicators.append({
            "pilar":           str(r[i_pilar] or "").strip(),
            "name":            str(ind).strip(),
            "id":              normalize_id(r[i_id]),
            "pregunta":        str(r[i_pregunta] or "").strip()    if i_pregunta is not None else "",
            "respuestas":      str(r[i_tipo] or "").strip()        if i_tipo is not None else "",
            "objetivo":        str(r[i_objetivo] or "").strip()    if i_objetivo is not None else "",
            "establecimiento": str(r[i_estab] or "").strip()       if i_estab is not None else "",
            "clasificacion":   str(r[i_clasif] or "").strip()      if i_clasif is not None else "",
        })
    return indicators


def load_mock_schema(mock_filename: str):
    data = json.loads((OUT / mock_filename).read_text(encoding="utf-8"))
    schema = data["schema"]
    by_id = {}
    for q in schema:
        # Convierte 'p02_1' -> 'P02.1' y 'p18' -> 'P18' para empatar con IDs.
        name = str(q["name"])
        m_dot = re.match(r"^([Pp]\d+)(?:_(\d+))?(?:_.*)?$", name)
        if m_dot and m_dot.group(2):
            key = f"{m_dot.group(1).upper()}.{m_dot.group(2)}"
        else:
            m_simple = re.match(r"^([Pp]\d+)(_|$)", name)
            key = m_simple.group(1).upper() if m_simple else None
        if key and key not in by_id:
            by_id[key] = q
    return by_id


def enrich(indicators, schema_by_id):
    enriched = []
    for ind in indicators:
        meta = schema_by_id.get(ind["id"])
        ind["field"] = meta["name"] if meta else None
        ind["type"]  = meta["type"] if meta else None
        enriched.append(ind)
    return enriched


def report(label: str, enriched: list, out_path: Path):
    matched = sum(1 for i in enriched if i["field"])
    print(f"[ok] {out_path.relative_to(ROOT)} - {len(enriched)} indicadores ({matched} con field mapeado)")
    pilares = {}
    for i in enriched:
        pilares[i["pilar"]] = pilares.get(i["pilar"], 0) + 1
    for p, n in sorted(pilares.items()):
        print(f"  - {p}: {n}")


def main():
    # Usuarios
    u_indicators = load_indicators("Usuario", "ID Pregunta Nuevo")
    u_schema = load_mock_schema("mock-usuarios.json")
    u_enriched = enrich(u_indicators, u_schema)
    out_u = OUT / "indicators-usuarios.json"
    out_u.write_text(json.dumps(u_enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    report("Usuarios", u_enriched, out_u)

    # Prestadores
    # Nombre de hoja con espacio final (literal en el archivo).
    p_indicators = load_indicators("Prestadores de servicios ", "ID pregunta")
    p_schema = load_mock_schema("mock-prestadores.json")
    p_enriched = enrich(p_indicators, p_schema)
    out_p = OUT / "indicators-prestadores.json"
    out_p.write_text(json.dumps(p_enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    report("Prestadores", p_enriched, out_p)


if __name__ == "__main__":
    main()
