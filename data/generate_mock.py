"""
Generador de datos mock para los dashboards MLC.

Lee la estructura de las encuestas en `info/kobo_prestadores.xlsx` y
`info/kobo_usuarios.xlsx`, genera 50 respuestas simuladas por encuesta
y guarda los resultados como JSON consumible por los dashboards.

Salidas:
    data/mock-prestadores.json
    data/mock-usuarios.json
"""

from __future__ import annotations
import json
import random
from datetime import date, timedelta
from pathlib import Path

import openpyxl

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
INFO = ROOT / "info"
OUT = ROOT / "data"

UNIDADES = [
    "Centro de Salud Roosevelt",
    "Centro de Salud San Juan de Dios",
    "Puesto de Salud Esquintla",
    "Puesto de Salud Quetzaltenango",
    "Puesto de Salud Izabal",
]

ETNIAS = ["maya", "ladino_o_mestizo", "xinka", "garifuna", "otro"]


# ---------------------------------------------------------------------------
# Carga de la estructura de la encuesta desde un xlsx KoboToolbox
# ---------------------------------------------------------------------------
def load_kobo(path: Path):
    wb = openpyxl.load_workbook(path, data_only=True)
    sheet = wb["survey"]
    header = [c.value for c in sheet[1]]
    i_type = header.index("type")
    i_name = header.index("name")
    i_label = next(i for i, h in enumerate(header) if h and "label" in str(h))
    i_pilar = next((i for i, h in enumerate(header) if h and "pilar" in str(h).lower()), None)

    questions = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or not row[i_type]:
            continue
        t = str(row[i_type]).strip()
        if t.startswith(("begin", "end")) or t in ("note", "calculate"):
            continue
        questions.append(
            {
                "type": t,
                "name": row[i_name],
                "label": row[i_label],
                "pilar": (row[i_pilar] if i_pilar is not None else None),
            }
        )

    sheet = wb["choices"]
    header = [c.value for c in sheet[1]]
    i_list = header.index("list_name")
    i_name = header.index("name")
    i_label = next(i for i, h in enumerate(header) if h and "label" in str(h))
    choices: dict[str, list[dict]] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or not row[i_list]:
            continue
        ln = str(row[i_list]).strip()
        choices.setdefault(ln, []).append({"name": row[i_name], "label": row[i_label]})

    return questions, choices


# ---------------------------------------------------------------------------
# Generación de respuestas
# ---------------------------------------------------------------------------
def list_name(q_type: str) -> str | None:
    """Extrae el nombre de la lista de un tipo `select_one X` / `select_multiple X`."""
    parts = q_type.split()
    if parts[0] in ("select_one", "select_multiple") and len(parts) >= 2:
        return parts[1]
    return None


def weighted_choice(options: list[str], biases: dict[str, float] | None = None) -> str:
    """Devuelve una opción con pesos (default cae en favor de respuestas positivas)."""
    if biases is None:
        biases = {}
    weights = []
    for opt in options:
        if opt in biases:
            weights.append(biases[opt])
        elif opt in ("si", "siempre", "si_para_todos", "si_periodicamente",
                     "si_de_forma_sistematizada", "si_sistematicamente"):
            weights.append(0.55)
        elif opt in ("a_veces", "ocasionalmente", "parcialmente",
                     "si_pero_sin_sistematizacion", "solo_ocasional"):
            weights.append(0.18)
        elif opt in ("no",):
            weights.append(0.18)
        elif opt in ("no_se", "no_se_no_recuerda", "prefiero_no_responder"):
            weights.append(0.05)
        else:
            weights.append(0.1)
    return random.choices(options, weights=weights, k=1)[0]


def random_date(days_back: int = 365) -> str:
    delta = timedelta(days=random.randint(0, days_back))
    return (date.today() - delta).isoformat()


SI_NO_NS = ["si", "no", "no_se"]


def looks_like_yes_no(label: str) -> bool:
    """Heurística para detectar preguntas que son sí/no aunque el list_name esté mal mapeado."""
    if not label:
        return False
    s = label.strip().lower()
    return s.startswith(("¿", "se ", "el ", "la ", "los ", "las ", "existe", "cuenta", "ofertan",
                         "cuenta con", "se realiza", "se asigna", "se entrega"))


def gen_response(q: dict, choices: dict[str, list[dict]]):
    t = q["type"]

    if t == "date":
        return random_date()

    if t == "integer":
        label = (q["label"] or "").lower()
        if "minuto" in label or ("tiempo" in label and "promedio" in label):
            return random.randint(15, 90)
        if "hora" in label:
            return random.choice([1, 2, 3, 4])
        if "cantidad" in label or "cuánt" in label or "cuant" in label:
            return random.randint(0, 30)
        return random.randint(0, 100)

    if t == "decimal":
        return round(random.uniform(0, 100), 1)

    if t == "text":
        return ""

    if t.startswith("select_one"):
        lname = list_name(t)
        opts = [c["name"] for c in choices.get(lname, [])]
        # Si la lista parece estar mal mapeada (valores de tipo establecimiento)
        # pero la pregunta es claramente sí/no, sustituye por sí/no/no_se.
        establishment_like = {"uai", "vicits", "cap", "caimi",
                               "puesto_de_salud", "centro_de_salud", "hospital"}
        if opts and set(opts).issubset(establishment_like) and looks_like_yes_no(q["label"]):
            return weighted_choice(SI_NO_NS)
        if not opts:
            return None
        return weighted_choice(opts)

    if t.startswith("select_multiple"):
        lname = list_name(t)
        opts = [c["name"] for c in choices.get(lname, [])]
        if not opts:
            return []
        k = random.randint(1, min(3, len(opts)))
        return random.sample(opts, k)

    return None


def gen_prestador_response(idx: int, questions, choices):
    answers = {}
    for q in questions:
        answers[q["name"]] = gen_response(q, choices)
    # Sustituciones específicas para que el mock parezca coherente
    answers["p01"] = random_date(180)
    answers["p02"] = random.choice(UNIDADES)
    return {
        "_id": f"P{idx:03d}",
        "_unidad": answers["p02"],
        "_fecha": answers["p01"],
        **answers,
    }


def gen_usuario_response(idx: int, questions, choices):
    answers = {}
    for q in questions:
        answers[q["name"]] = gen_response(q, choices)
    answers["p01"] = random_date(180)
    answers["p03"] = random.choice(UNIDADES)
    answers["p10"] = random.choice(ETNIAS)
    return {
        "_id": f"U{idx:03d}",
        "_unidad": answers["p03"],
        "_fecha": answers["p01"],
        "_etnia": answers["p10"],
        **answers,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # Prestadores
    p_q, p_c = load_kobo(INFO / "kobo_prestadores.xlsx")
    prestadores = [gen_prestador_response(i + 1, p_q, p_c) for i in range(50)]
    schema_p = [{"name": q["name"], "label": q["label"], "type": q["type"], "pilar": q["pilar"]} for q in p_q]
    (OUT / "mock-prestadores.json").write_text(
        json.dumps({"schema": schema_p, "responses": prestadores}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] data/mock-prestadores.json — {len(prestadores)} respuestas")

    # Usuarios
    u_q, u_c = load_kobo(INFO / "kobo_usuarios.xlsx")
    usuarios = [gen_usuario_response(i + 1, u_q, u_c) for i in range(50)]
    schema_u = [{"name": q["name"], "label": q["label"], "type": q["type"], "pilar": q["pilar"]} for q in u_q]
    (OUT / "mock-usuarios.json").write_text(
        json.dumps({"schema": schema_u, "responses": usuarios}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] data/mock-usuarios.json — {len(usuarios)} respuestas")


if __name__ == "__main__":
    main()
