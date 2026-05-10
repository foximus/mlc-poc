// js/dashboard-data.js
// Helpers compartidos por los dashboards: carga JSON mock y agregaciones por pilar.

const MLC = {
  positivas: new Set([
    "si", "siempre", "si_para_todos", "si_periodicamente",
    "si_de_forma_sistematizada", "si_sistematicamente",
    "claramente_visible", "muy_clara", "clara",
    "total_privacidad_no_se_escucha", "buena_privacidad",
    "areas_muy_seguras", "seguras", "muy_seguras",
    "separacion_total", "buena_separacion",
    "excelente_capacidad", "buena", "suficiente",
    "excelentes", "muy_buenos", "buenos",
    "no_hubo_desabastecimiento",
    "indetectable",
    "menos_de_30_minutos",
    "muy_bueno", "bueno",
    "90porcentaje", "mensual"
  ]),
  parciales: new Set([
    "a_veces", "ocasionalmente", "parcialmente",
    "si_pero_sin_sistematizacion", "solo_ocasional",
    "visible", "apenas_visible",
    "parcial_se_escucha_algo", "parcialmente_seguras",
    "parcial_biombo_parcial", "regular",
    "regularmente_seguras", "entre_30_y_60_minutos",
    "75_89porcentaje", "50_74porcentaje", "trimestral", "semestral",
    "30_dias", "60_dias", "90_dias"
  ]),
  noSabe: new Set([
    "no_se", "no_se_no_recuerda", "prefiero_no_responder", null, undefined, ""
  ]),

  /** Cargar el JSON mock por rol */
  async loadMock(role) {
    const url = `data/mock-${role}.json`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`No se pudo cargar ${url}`);
    return res.json();
  },

  /**
   * Filtra respuestas según un diccionario {fieldName: value}.
   * - El valor "" / null / undefined se ignora (= sin filtro en ese campo).
   * - Si el campo en la respuesta es array (select_multiple), matchea por inclusión.
   * - Caso contrario, igualdad estricta.
   */
  filterResponses(responses, filters = {}) {
    const entries = Object.entries(filters).filter(
      ([, v]) => v !== null && v !== undefined && v !== ""
    );
    if (!entries.length) return responses.slice();
    return responses.filter(r => {
      for (const [field, value] of entries) {
        const v = r[field];
        if (Array.isArray(v)) {
          if (!v.includes(value)) return false;
        } else if (v !== value) {
          return false;
        }
      }
      return true;
    });
  },

  /**
   * Calcula el % de respuestas "positivas" para un pilar dado.
   * Considera sólo preguntas select_one con respuestas en la lista positiva o parcial.
   * Una respuesta cuenta como 1.0 si está en `positivas`, 0.5 si en `parciales`, 0 si negativa.
   * Las respuestas no_se / pnr no entran en el denominador.
   */
  pillarScore(schema, responses, pilarName) {
    const qs = schema.filter(q =>
      q.pilar === pilarName &&
      typeof q.type === "string" &&
      q.type.startsWith("select_one")
    );
    if (qs.length === 0 || responses.length === 0) return 0;

    let num = 0, den = 0;
    for (const r of responses) {
      for (const q of qs) {
        const v = r[q.name];
        if (this.noSabe.has(v)) continue;
        if (this.positivas.has(v))      { num += 1; den += 1; }
        else if (this.parciales.has(v)) { num += 0.5; den += 1; }
        else                            {            den += 1; }
      }
    }
    return den === 0 ? 0 : Math.round((num / den) * 100);
  },

  /** Cuenta valores de una pregunta puntual (clave -> conteo). */
  countValues(responses, name) {
    const out = {};
    for (const r of responses) {
      const v = r[name];
      if (Array.isArray(v)) v.forEach(x => out[x] = (out[x] || 0) + 1);
      else out[v] = (out[v] || 0) + 1;
    }
    return out;
  },

  /** Calcula % "Sí" sobre una pregunta de tipo select_one Sí/No (descontando NS/PNR). */
  yesPct(responses, name, yesValues = ["si", "siempre", "claramente_visible"]) {
    let yes = 0, total = 0;
    for (const r of responses) {
      const v = r[name];
      if (v == null || this.noSabe.has(v)) continue;
      total += 1;
      if (yesValues.includes(v)) yes += 1;
    }
    return total === 0 ? 0 : Math.round((yes / total) * 100);
  },

  /** Etiqueta legible para una opción (snake_case → Capitalizado).
   *  Si el string ya viene formateado (contiene mayúsculas y minúsculas o tildes),
   *  se devuelve tal cual para no romper nombres como "Petén" o "Suchitepéquez". */
  prettyLabel(s) {
    if (!s) return s;
    const str = String(s);
    if (/[A-ZÁÉÍÓÚÑ]/.test(str) && /[a-záéíóúñ]/.test(str)) return str;
    return str.replace(/_/g, " ").replace(/(^|\s)(\p{L})/gu, (_, sp, c) => sp + c.toUpperCase());
  },

  /** Promedio numérico ignorando null/no_se */
  avgNumeric(responses, name) {
    const vals = responses
      .map(r => r[name])
      .filter(v => typeof v === "number");
    if (!vals.length) return 0;
    return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  },
};

window.MLC = MLC;
