"""
Convierte las exportaciones "labels" de KoboToolbox en los JSON que consumen
los dashboards del sitio MLC. Acepta el export en CSV (separador ';') o el
libro .xlsx ya depurado; si existen ambos para un formulario, gana el .xlsx.

Entradas
    data/kobo/kobo-prestadores.[xlsx|csv]
    data/kobo/kobo-usuarios.[xlsx|csv]
    data/unidades-catalog.json   (catálogo de establecimientos, para canonizar nombres)

Salidas
    data/mock-prestadores.json   { schema: [...], responses: [...] }
    data/mock-usuarios.json      { schema: [...], responses: [...] }

El schema (nombre de campo, tipo y pilar) se conserva del proyecto: sólo se
actualizan las etiquetas con el texto real del formulario y los tipos que
cambiaron de select_one a select_multiple en la versión vigente de la encuesta.

Uso:  python data/build_from_kobo.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from datetime import date, datetime, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
KOBO = BASE / "kobo"


# ---------------------------------------------------------------- utilidades

def norm(s: str) -> str:
    """Minúsculas, sin tildes ni puntuación, espacios colapsados."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def slug(s: str) -> str:
    return re.sub(r"_+", "_", norm(s).replace(" ", "_")).strip("_")


def _cell(value) -> str:
    """Normaliza una celda de xlsx al mismo texto que produciría el CSV."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        # La fecha de recolección viene sin hora; _submission_time sí la trae.
        fmt = "%Y-%m-%d" if value.time() == time(0, 0) else "%Y-%m-%d %H:%M:%S"
        return value.strftime(fmt)
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


# Qué hacer con filas que repiten el `_uuid` (identificador único por envío
# de KoboToolbox). "renumerar" las conserva como respuestas independientes
# asignándoles un id propio; "descartar" se queda sólo con la primera.
DUPLICADOS = "renumerar"

# Marca que separa el uuid original del número de repetición.
DUP_SEP = "-dup"


def read_table(name: str):
    """Lee el export de Kobo en CSV (labels, separador ';') o en xlsx.

    Devuelve (header, rows) con todas las celdas ya como texto. Las filas que
    repiten `_uuid` se tratan según `DUPLICADOS`: al renumerar se les añade el
    sufijo `-dupN` al `_uuid` y al `_id` para que no colisionen entre sí.
    """
    xlsx, csv_path = KOBO / f"{name}.xlsx", KOBO / f"{name}.csv"
    if xlsx.exists():
        import openpyxl
        ws = openpyxl.load_workbook(xlsx, data_only=True).worksheets[0]
        raw = [[_cell(c) for c in row] for row in ws.iter_rows(values_only=True)]
        header, body = raw[0], raw[1:]
    elif csv_path.exists():
        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            rd = csv.reader(fh, delimiter=";")
            header = next(rd)
            body = list(rd)
    else:
        raise SystemExit(f"No se encontró data/kobo/{name}.[xlsx|csv]")

    header = [h.strip() for h in header]
    col = {c: header.index(c) for c in ("_uuid", "_id") if c in header}
    uuid_col = col.get("_uuid")

    rows, vistos, dupes = [], {}, 0
    for r in body:
        if not any(str(c).strip() for c in r):
            continue
        if uuid_col is not None:
            uid = str(r[uuid_col]).strip()
            if uid:
                n = vistos.get(uid, 0) + 1
                vistos[uid] = n
                if n > 1:
                    dupes += 1
                    if DUPLICADOS == "descartar":
                        continue
                    # Id propio para cada repetición, conservando el original.
                    r = list(r)
                    r[uuid_col] = f"{uid}{DUP_SEP}{n}"
                    if "_id" in col:
                        r[col["_id"]] = f"{str(r[col['_id']]).strip()}{DUP_SEP}{n}"
        rows.append(r)
    if dupes:
        accion = ("descartada(s)" if DUPLICADOS == "descartar"
                  else "conservada(s) con id propio")
        print(f"[aviso] {name}: {dupes} fila(s) con _uuid repetido — {accion}")
    return header, rows


def split_dup(uid: str):
    """'<uuid>-dup2' -> ('<uuid>-dup2', '<uuid>'); si no es repetición, ('<uuid>', '')."""
    uid = str(uid).strip()
    if DUP_SEP in uid:
        return uid, uid.rsplit(DUP_SEP, 1)[0]
    return uid, ""


def as_number(raw: str):
    """Devuelve int/float si la celda es un número puro; si no, None."""
    if raw is None:
        return None
    t = str(raw).strip().replace(",", ".")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    n = float(t)
    return int(n) if n.is_integer() else n


# ------------------------------------------------- diccionarios de respuestas

# Valores comunes a ambos formularios. Los slugs coinciden con los conjuntos
# `positivas` / `parciales` / `noSabe` de js/dashboard-data.js.
COMMON = {
    "sí": "si",
    "si": "si",
    "no": "no",
    "a veces": "a_veces",
    "siempre": "siempre",
    "nunca": "nunca",
    "parcialmente": "parcialmente",
    "ocasionalmente": "ocasionalmente",
    "no sé": "no_se",
    "no se": "no_se",
    "no sabe": "no_se",
    "no recuerda": "no_recuerda",
    "no sé / no recuerda": "no_se_no_recuerda",
    "prefiero no responder": "prefiero_no_responder",
    "no aplica": "no_aplica",
    "sí, consiento participar": "si_consiento_participar",
    "no, declino participar": "no_declino_participar",
    "sí, para todos": "si_para_todos",
    "sí, sólo para algunos": "si_solo_para_algunos",
    "sí, períodicamente": "si_periodicamente",
    "sí, periódicamente": "si_periodicamente",
    "sí, de forma sistematizada": "si_de_forma_sistematizada",
    "sí, pero sin sistematización": "si_pero_sin_sistematizacion",
    "sí, sistemáticamente": "si_sistematicamente",
    "solo ocasional": "solo_ocasional",
    "en desarrollo": "en_desarrollo",
    # Disponibilidad de TAR: la etiqueta "No, hubo desabastecimiento" es una
    # respuesta desfavorable; se codifica sin el "no" inicial para que no se
    # confunda con "no hubo desabastecimiento".
    "no, hubo desabastecimiento": "hubo_desabastecimiento",
    # Escala observacional 1–5 (sección de instalaciones, prestadores)
    "5 óptimo": "optimo",
    "4 adecuado": "adecuado",
    "3 regular": "regular",
    "2 deficiente": "deficiente",
    "1 muy deficiente": "muy_deficiente",
    # Escalas de trato / confidencialidad (usuarios)
    "muy bueno": "muy_bueno",
    "bueno": "bueno",
    "regular": "regular",
    "malo": "malo",
    "muy malo": "muy_malo",
    # Tiempos (usuarios)
    "menos de 30 minutos": "menos_de_30_minutos",
    "entre 30 y 60 minutos": "entre_30_y_60_minutos",
    "más de 1 hora": "mas_de_1_hora",
    # Carga viral
    "detectable": "detectable",
    "indetectable": "indetectable",
    # Frecuencias / periodos
    "mensual": "mensual",
    "trimestral": "trimestral",
    "semestral": "semestral",
    "anual": "anual",
    "no se realiza": "no_se_realiza",
    "30 días": "30_dias",
    "60 días": "60_dias",
    "90 días": "90_dias",
    "otro": "otro",
    "otros": "otros",
    # Porcentaje de vinculación ≤7 días
    "_≥90%": "90porcentaje",
    "≥90%": "90porcentaje",
    "75-89%": "75_89porcentaje",
    "50-74%": "50_74porcentaje",
    "<50%": "50porcentaje",
    # Caracterización (usuarios)
    "hombre": "hombre",
    "mujer": "mujer",
    "intersex": "intersex",
    "cis género": "cis_genero",
    "no binario": "no_binario",
    "mujer trans": "mujer_trans",
    "hombre trans": "hombre_trans",
    "gay": "gay",
    "lesbiana": "lesbiana",
    "bisexual": "bisexual",
    "heterosexual": "heterosexual",
    "ladino o mestizo": "ladino_o_mestizo",
    "maya": "maya",
    "xinka": "xinka",
    "garífuna": "garifuna",
    "español": "espanol",
    "k'iche'": "kiche",
    "q'eqchi'": "qeqchi",
    "q'anjob'al": "qanjobal",
    "achi'": "achi",
    "ch'orti'": "chorti",
    "poqomchi'": "poqomchi",
    "tz'utujil": "tzutujil",
    "médico": "medico",
    "enfermera": "enfermera",
    # Ámbito de monitoreo (primera columna del formulario)
    "unidad de atención integral -uai-": "uai",
    "vicits, puesto de salud, centro de salud u otros.": "otros_servicios",
}

# Tipo de establecimiento -> slug corto (campo p02_3)
TIPO_SLUG = {
    "uai": "uai",
    "vicits": "vicits",
    "caimi": "caimi",
    "cae": "cae",
    "centro de salud": "centro_de_salud",
    "puesto de salud": "puesto_de_salud",
    "centro comunitario": "centro_comunitario",
    "centro de atencion permanente cap": "cap",
    "clinica familiar": "clinica_familiar",
}


def code(raw: str, extra: dict | None = None) -> str:
    """Traduce una etiqueta de Kobo a su código interno."""
    if raw is None:
        return ""
    t = str(raw).strip()
    if not t:
        return ""
    key = t.lower()
    if extra and key in extra:
        return extra[key]
    if key in COMMON:
        return COMMON[key]
    return slug(t)


def multi(row, cols: dict) -> list:
    """Reconstruye un select_multiple a partir de las columnas binarias."""
    out = []
    for idx, value in cols.items():
        if str(row[idx]).strip() == "1":
            out.append(value)
    return out


# --------------------------------------------------- catálogo de unidades

CATALOG = json.loads((BASE / "unidades-catalog.json").read_text(encoding="utf-8"))

TIPO_PREFIXES = [
    "centro de atencion permanente cap",
    "centro de atencion permanente",
    "centro comunitario",
    "centro de salud",
    "puesto de salud",
    "clinica familiar",
    "hospital nacional",
    "hospital regional",
    "hospital",
    "caimi",
    "vicits",
    "uai",
    "cap",
    "cae",
]


def core_name(name: str) -> str:
    """Nombre sin el prefijo del tipo de establecimiento."""
    n = norm(name)
    for p in TIPO_PREFIXES:
        if n.startswith(p + " "):
            return n[len(p) + 1:].strip()
        if n == p:
            return ""
    return n


CATALOG_INDEX = {}
for entry in CATALOG:
    CATALOG_INDEX.setdefault((norm(entry["_departamento"]), norm(entry["_unidad"])), entry)

CATALOG_BY_DEP = {}
for entry in CATALOG:
    CATALOG_BY_DEP.setdefault(norm(entry["_departamento"]), []).append(entry)

_unmatched: set = set()


def resolve_unidad(departamento: str, municipio: str, tipo: str, nombre: str) -> dict:
    """Devuelve los valores canónicos (_departamento/_municipio/_tipo/_unidad).

    Se busca el establecimiento en el catálogo oficial para que los filtros en
    cascada del dashboard (que se alimentan del catálogo) encuentren la unidad.
    Si no hay coincidencia se conservan los valores tal cual vienen del CSV.
    """
    dep_n = norm(departamento)
    hit = CATALOG_INDEX.get((dep_n, norm(nombre)))
    if hit:
        return dict(hit)

    pool = CATALOG_BY_DEP.get(dep_n, [])
    mun_n = norm(municipio)
    core = core_name(nombre)

    # 1) mismo municipio + mismo núcleo de nombre
    for entry in pool:
        if norm(entry["_municipio"]) == mun_n and core_name(entry["_unidad"]) == core:
            return dict(entry)
    # 2) mismo municipio + mismo tipo (cubre "VICITS Escuintla" -> "VICITS")
    tipo_n = norm(tipo)
    same_mun_tipo = [
        e for e in pool
        if norm(e["_municipio"]) == mun_n and norm(e["_tipo"]).startswith(tipo_n)
    ]
    if len(same_mun_tipo) == 1:
        return dict(same_mun_tipo[0])
    # 3) núcleo de nombre único en el departamento
    by_core = [e for e in pool if core_name(e["_unidad"]) == core and core]
    if len(by_core) == 1:
        return dict(by_core[0])

    _unmatched.add(f"{departamento} / {municipio} / {tipo} / {nombre}")
    return {
        "_departamento": departamento.strip(),
        "_municipio": municipio.strip(),
        "_tipo": tipo.strip(),
        "_unidad": nombre.strip(),
    }


# ------------------------------------------------------------------ schema

def load_schema(filename: str) -> list:
    return json.loads((BASE / filename).read_text(encoding="utf-8"))["schema"]


def apply_schema_updates(schema: list, labels: dict, types: dict) -> list:
    out = []
    for q in schema:
        q = dict(q)
        if q["name"] in labels:
            q["label"] = labels[q["name"]]
        if q["name"] in types:
            q["type"] = types[q["name"]]
        out.append(q)
    return out


# ------------------------------------------------------------- prestadores

def build_prestadores() -> dict:
    header, rows = read_table("kobo-prestadores")

    # columna del CSV -> campo del schema
    COL = {
        4: "P01", 8: "P02", 15: "P04", 28: "P06", 29: "P07", 30: "P08",
        31: "P09", 32: "P51", 33: "P10", 34: "P11", 35: "P12", 36: "P13",
        37: "P14", 38: "P15", 39: "P16", 40: "P17", 41: "P18", 42: "P19",
        43: "P20", 44: "P21", 45: "P22", 52: "P24", 53: "P25", 55: "P26",
        56: "P27", 57: "P28", 58: "P29", 59: "P30", 60: "P31", 61: "P32",
        62: "P33", 63: "P34", 64: "P35", 65: "P36", 66: "P37", 67: "P38",
        68: "P39", 69: "P40", 70: "P41", 72: "P42", 73: "P43", 74: "P44",
        75: "P45", 76: "P46", 77: "P47", 78: "P48", 79: "P49",
    }
    # campos que se conservan como texto libre (el dashboard extrae el número)
    TEXT_FIELDS = {"P01", "P02", "P06", "P15", "P16", "P17", "P22", "P24",
                   "P29", "P35", "P37", "P41"}
    NUM_FIELDS = {"P51"}

    AREAS = {10: "laboratorio", 11: "clinicas", 12: "farmacia", 13: "otros"}
    POBLACIONES = {
        18: "mts", 19: "hsh", 20: "mt", 21: "ht", 22: "pv", 23: "no_se",
        24: "mujer_embarazada", 25: "poblacion_general", 26: "ppl",
        27: "usuarios_de_drogas",
    }
    SISTEMAS = {
        47: "excel", 48: "sigsa", 49: "sistema_interno",
        50: "no_lo_sistematiza", 51: "no_se",
    }

    responses = []
    for i, row in enumerate(rows, start=1):
        loc = resolve_unidad(row[5], row[6], row[7], row[8])
        _uuid, _orig = split_dup(row[84])
        r = {
            "_id": f"P{i:03d}",
            **loc,
            "_fecha": row[4].strip(),
            "_kobo_id": row[83].strip(),
            "_uuid": _uuid,
            "_duplicado_de": _orig,
            "_ambito": code(row[0]),
            "_consentimiento": code(row[3]),
            "_area_otros": row[14].strip(),
            "_cargo_otros": row[16].strip(),
            "_perdida_seguimiento_otro": row[54].strip(),
            "_recomendacion": row[80].strip(),
            "_comentario": row[81].strip(),
        }
        for col, field in COL.items():
            raw = row[col].strip()
            if field in TEXT_FIELDS:
                r[field] = raw
            elif field in NUM_FIELDS:
                n = as_number(raw)
                r[field] = n if n is not None else raw
            else:
                r[field] = code(raw)
        r["P03"] = multi(row, AREAS)
        r["P05"] = multi(row, POBLACIONES)
        r["P23"] = multi(row, SISTEMAS)
        r["P50"] = ""  # sin equivalente en la versión vigente del formulario
        responses.append(r)

    labels = {COL[c]: header[c].strip() for c in COL}
    labels.update({
        "P03": header[9].strip(),
        "P05": header[17].strip(),
        "P23": header[46].strip(),
    })
    types = {
        # select_multiple en el formulario vigente: quedan fuera del promedio
        # por pilar (pillarScore sólo considera select_one).
        "P03": "select_multiple list_P03",
        "P05": "select_multiple list_P05",
        "P23": "select_multiple list_P23",
        # respuestas numéricas abiertas
        "P37": "integer",
        "P51": "integer",
    }
    schema = apply_schema_updates(load_schema("mock-prestadores.json"), labels, types)
    return {"schema": schema, "responses": responses}


# ---------------------------------------------------------------- usuarios

EDAD_BUCKETS = [
    (0, 17, "menor_de_18"),
    (18, 24, "v_18_a_24"),
    (25, 34, "v_25_a_34"),
    (35, 44, "v_35_a_44"),
    (45, 54, "v_45_a_54"),
    (55, 64, "v_55_a_64"),
    (65, 200, "v_65_o_mas"),
]


def edad_bucket(raw: str) -> str:
    n = as_number(raw)
    if n is None:
        return code(raw)
    for lo, hi, key in EDAD_BUCKETS:
        if lo <= n <= hi:
            return key
    return ""


def build_usuarios() -> dict:
    header, rows = read_table("kobo-usuarios")

    COL = {
        3: "p00", 4: "p01", 5: "p02_1", 6: "p02_2", 7: "p02_3", 8: "p03",
        10: "p05", 11: "p06", 13: "p08", 14: "p09", 28: "p10", 30: "p11",
        31: "p12", 16: "p13", 32: "p15", 33: "p16", 34: "p17", 35: "p18",
        36: "p19", 37: "p20", 38: "p21", 39: "p22", 40: "p23", 41: "p24",
        42: "p25", 43: "p26", 44: "p27", 45: "p28", 46: "p29", 47: "p30",
        48: "p31", 49: "p32", 50: "p33", 51: "p34", 52: "p35", 53: "p36",
        54: "p37", 55: "p38", 56: "p39", 57: "p40", 58: "p41", 59: "p42",
        60: "p43", 61: "p44", 62: "p45", 64: "p46", 65: "p47", 66: "p48",
        82: "p50", 83: "p51", 84: "p52", 85: "p53", 86: "p54", 87: "p55",
        88: "p56", 89: "p57",
    }
    TEXT_FIELDS = {"p01", "p02_1", "p02_2", "p03", "p05", "p06", "p20", "p24",
                   "p39", "p53", "p55", "p56", "p57"}
    NUM_FIELDS = {"p21", "p22", "p29", "p41", "p42"}

    POB_CLAVE = {
        19: "hsh", 20: "mujeres_trans", 21: "trabajadoras_sexuales",
        22: "personas_que_se_inyectan_drogas", 23: "ppl", 24: "ninguna",
        25: "no_se", 26: "prefiero_no_responder", 27: "pv",
    }
    PERSONAL = {
        68: "medico", 69: "administrativo", 70: "consejeria",
        71: "trabajo_social", 72: "navegador_o_par", 73: "no_se",
        74: "prefiero_no_responder", 75: "enfermera",
        76: "personal_de_laboratorio", 77: "nutricion", 78: "psicologo",
        79: "farmacia", 80: "otros",
    }

    responses = []
    for i, row in enumerate(rows, start=1):
        loc = resolve_unidad(row[5], row[6], row[7], row[8])
        _uuid, _orig = split_dup(row[92])
        r = {
            "_id": f"U{i:03d}",
            **loc,
            "_fecha": row[4].strip(),
            "_kobo_id": row[91].strip(),
            "_uuid": _uuid,
            "_duplicado_de": _orig,
            "_ambito": code(row[0]),
            "_etnia": code(row[28]),
            "_edad": as_number(row[12]),
            "_identidad_otro": row[15].strip(),
            "_orientacion_otro": row[17].strip(),
            "_discriminacion_detalle": row[63].strip(),
            "_personal_otros": row[81].strip(),
        }
        for col, field in COL.items():
            raw = row[col].strip()
            if field in TEXT_FIELDS:
                r[field] = raw
            elif field in NUM_FIELDS:
                n = as_number(raw)
                r[field] = n if n is not None else ""
            else:
                r[field] = code(raw)
        # p02_3: tipo de establecimiento, alineado con el catálogo
        tipo_n = norm(loc["_tipo"])
        r["p02_3"] = TIPO_SLUG.get(tipo_n, slug(loc["_tipo"]))
        if tipo_n.startswith("hospital"):
            r["p02_3"] = "hospital"
        # p04 (Código Construido) se omite: es un pseudoidentificador de la
        # persona encuestada y ningún indicador del dashboard lo utiliza.
        r["p04"] = ""
        r["p07"] = edad_bucket(row[12])
        r["p14"] = multi(row, POB_CLAVE)
        r["p49"] = multi(row, PERSONAL)
        responses.append(r)

    labels = {COL[c]: header[c].strip() for c in COL}
    labels.update({
        "p07": header[12].strip(),
        "p14": header[18].strip(),
        "p49": header[67].strip(),
    })
    types = {
        "p14": "select_multiple p14_list",
        "p49": "select_multiple p49_list",
    }
    schema = apply_schema_updates(load_schema("mock-usuarios.json"), labels, types)
    return {"schema": schema, "responses": responses}


# -------------------------------------------------------------------- main

def write(name: str, payload: dict):
    path = BASE / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] data/{name} — {len(payload['responses'])} respuestas")


def main():
    prest = build_prestadores()
    usua = build_usuarios()
    write("mock-prestadores.json", prest)
    write("mock-usuarios.json", usua)

    for label, payload in (("prestadores", prest), ("usuarios", usua)):
        unidades = sorted({r["_unidad"] for r in payload["responses"]})
        print(f"     {label}: {len(unidades)} establecimientos, "
              f"{len({r['_departamento'] for r in payload['responses']})} departamentos")

    if _unmatched:
        print("\n[aviso] establecimientos sin coincidencia en unidades-catalog.json:")
        for u in sorted(_unmatched):
            print("   -", u)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
