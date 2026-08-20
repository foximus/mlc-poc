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
    // Escala observacional 1-5 del formulario de prestadores
    "optimo", "adecuado",
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
  /** Respuestas desfavorables explícitas (para colorear en rojo). */
  negativas: new Set([
    "no", "nunca", "detectable", "malo", "muy_malo",
    "deficiente", "muy_deficiente", "hubo_desabastecimiento",
    "mas_de_1_hora", "no_se_realiza", "no_lo_sistematiza",
    "insuficiente", "muy_insuficiente", "inseguras", "muy_inseguras",
    "sin_privacidad", "se_escucha_facilmente", "sin_separacion",
    "no_hay_senalizacion", "no_visible", "no_hay_letreros",
    "malos", "50porcentaje"
  ]),
  noSabe: new Set([
    "no_se", "no_recuerda", "no_se_no_recuerda", "no_sabe",
    "prefiero_no_responder", "no_aplica", null, undefined, ""
  ]),

  /**
   * Preguntas donde "Sí" es la respuesta DESFAVORABLE. Su puntaje se invierte
   * (1 − valor) antes de entrar al pilar. Los campos de usuarios van en
   * minúscula y los de prestadores en mayúscula, así que no colisionan.
   */
  sentidoInverso: new Set([
    "p18",  // ¿dejó de asistir a una cita por falta de permiso laboral?
    "p23",  // ¿ha tenido que pagar medicamentos o pruebas fuera de la unidad?
    "p25",  // ¿dejó de asistir a una cita por falta de dinero?
    "p26",  // ¿hoy perdió ingresos o dejó de trabajar por asistir a su consulta?
    "p36",  // ¿le dieron receta para comprarlo? (en vez de entregar el medicamento)
    "p45",  // ¿ha sido discriminado por ser una persona con VIH en este servicio?
  ]),

  /** Preguntas que no miden calidad del servicio y quedan fuera del puntaje. */
  sinPuntaje: new Set([
    "p34",  // ¿ha consultado por alguna ITS? — tamizaje, no evalúa al servicio
  ]),

  /** Mínimo de respuestas en toda la encuesta para que una pregunta puntúe. */
  minRespuestasPregunta: 3,

  /** Etiquetas legibles para códigos cuyo slug pierde tildes o mayúsculas. */
  labels: {
    si: "Sí", no: "No", no_se: "No sé", no_recuerda: "No recuerda",
    no_se_no_recuerda: "No sé / No recuerda",
    prefiero_no_responder: "Prefiero no responder", no_aplica: "No aplica",
    a_veces: "A veces", siempre: "Siempre", nunca: "Nunca",
    si_para_todos: "Sí, para todos", si_periodicamente: "Sí, periódicamente",
    si_de_forma_sistematizada: "Sí, de forma sistematizada",
    si_pero_sin_sistematizacion: "Sí, pero sin sistematización",
    si_sistematicamente: "Sí, sistemáticamente",
    si_consiento_participar: "Sí, consiento participar",
    hubo_desabastecimiento: "No, hubo desabastecimiento",
    optimo: "Óptimo", adecuado: "Adecuado", regular: "Regular",
    deficiente: "Deficiente", muy_deficiente: "Muy deficiente",
    muy_bueno: "Muy bueno", bueno: "Bueno", malo: "Malo", muy_malo: "Muy malo",
    menos_de_30_minutos: "Menos de 30 minutos",
    entre_30_y_60_minutos: "Entre 30 y 60 minutos",
    mas_de_1_hora: "Más de 1 hora",
    "90porcentaje": "≥ 90 %", "75_89porcentaje": "75-89 %",
    "50_74porcentaje": "50-74 %", "50porcentaje": "< 50 %",
    "30_dias": "30 días", "60_dias": "60 días", "90_dias": "90 días",
    mensual: "Mensual", trimestral: "Trimestral", semestral: "Semestral",
    no_se_realiza: "No se realiza", no_lo_sistematiza: "No lo sistematiza",
    sigsa: "SIGSA", excel: "Excel", sistema_interno: "Sistema interno",
    detectable: "Detectable", indetectable: "Indetectable",
    // Áreas, cargos y poblaciones
    clinicas: "Clínicas", laboratorio: "Laboratorio", farmacia: "Farmacia",
    otros: "Otros", medico: "Médico", enfermera: "Enfermera",
    consejeria: "Consejería", trabajo_social: "Trabajo social",
    navegador_o_par: "Navegador o par", psicologo: "Psicólogo",
    nutricion: "Nutrición", personal_de_laboratorio: "Personal de laboratorio",
    administrativo: "Administrativo",
    mts: "MTS", hsh: "HSH", mt: "MT", ht: "HT", pv: "PV", ppl: "PPL",
    poblacion_general: "Población general", mujer_embarazada: "Mujer embarazada",
    usuarios_de_drogas: "Usuarios de drogas", mujeres_trans: "Mujeres trans",
    trabajadoras_sexuales: "Trabajadoras sexuales",
    personas_que_se_inyectan_drogas: "Personas que se inyectan drogas",
    ninguna: "Ninguna",
    // Caracterización
    hombre: "Hombre", mujer: "Mujer", intersex: "Intersex",
    cis_genero: "Cis género", no_binario: "No binario",
    mujer_trans: "Mujer trans", hombre_trans: "Hombre trans",
    gay: "Gay", lesbiana: "Lesbiana", bisexual: "Bisexual",
    heterosexual: "Heterosexual",
    ladino_o_mestizo: "Ladino o mestizo", maya: "Maya", xinka: "Xinka",
    garifuna: "Garífuna", espanol: "Español", kiche: "K'iche'",
    kaqchikel: "Kaqchikel", mam: "Mam", qeqchi: "Q'eqchi'",
    v_18_a_24: "18 a 24 años", v_25_a_34: "25 a 34 años",
    v_35_a_44: "35 a 44 años", v_45_a_54: "45 a 54 años",
    v_55_a_64: "55 a 64 años", v_65_o_mas: "65 años o más",
    menor_de_18: "Menor de 18 años",
    // Tipo de establecimiento
    uai: "UAI", vicits: "VICITS", cap: "CAP", caimi: "CAIMI",
    centro_de_salud: "Centro de salud", puesto_de_salud: "Puesto de salud",
    centro_comunitario: "Centro comunitario", hospital: "Hospital",
  },

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
   * Valor 0..1 de una respuesta suelta: 1 favorable, 0.5 parcial, 0 desfavorable.
   * Devuelve null cuando la respuesta no debe entrar al denominador
   * (NS / PNR / sin respuesta, o un select_multiple, que no se puntúa).
   */
  valorRespuesta(v) {
    if (Array.isArray(v)) return null;
    if (this.noSabe.has(v)) return null;
    if (this.positivas.has(v)) return 1;
    if (this.parciales.has(v)) return 0.5;
    return 0;
  },

  /** Preguntas elegibles por pilar, cacheadas por initPuntaje(). */
  _elegibles: null,

  /**
   * Define, una sola vez sobre el universo completo de respuestas, qué preguntas
   * puntúan en cada pilar: select_one, no excluida y contestada por al menos
   * `minRespuestasPregunta` personas. El set se fija aquí —y no por
   * establecimiento ni por filtro— para que los puntajes sigan siendo
   * comparables cuando el usuario filtra o cambia de pestaña.
   */
  initPuntaje(schema, universo) {
    this._elegibles = this._calcularElegibles(schema, universo);
    return this._elegibles;
  },

  _calcularElegibles(schema, universo) {
    const out = new Map();
    for (const q of schema) {
      if (typeof q.type !== "string" || !q.type.startsWith("select_one")) continue;
      if (this.sinPuntaje.has(q.name)) continue;
      let n = 0;
      for (const r of universo) {
        if (this.valorRespuesta(r[q.name]) !== null) n += 1;
      }
      if (n < this.minRespuestasPregunta) continue;
      if (!out.has(q.pilar)) out.set(q.pilar, []);
      out.get(q.pilar).push(q.name);
    }
    return out;
  },

  /**
   * Puntaje 0-100 de un pilar para un conjunto de respuestas.
   *
   * Cada pregunta elegible se promedia primero entre quienes la contestaron y
   * después se promedian las preguntas entre sí, de modo que todas pesen igual:
   * con el conteo plano anterior, una pregunta que el formulario le mostró a
   * más gente dominaba el pilar sin que eso fuera una decisión metodológica.
   * Las preguntas de `sentidoInverso` se invierten antes de promediar.
   *
   * Devuelve null (no 0) cuando ninguna pregunta del pilar tiene respuestas,
   * para poder distinguir "sin dato" de "puntaje cero".
   */
  pillarScore(schema, responses, pilarName) {
    const elegibles = this._elegibles || this._calcularElegibles(schema, responses);
    const nombres = elegibles.get(pilarName) || [];
    if (!nombres.length || !responses.length) return null;

    const porPregunta = [];
    for (const name of nombres) {
      let suma = 0, n = 0;
      for (const r of responses) {
        const v = this.valorRespuesta(r[name]);
        if (v === null) continue;
        suma += this.sentidoInverso.has(name) ? 1 - v : v;
        n += 1;
      }
      if (n > 0) porPregunta.push(suma / n);
    }
    if (!porPregunta.length) return null;
    const media = porPregunta.reduce((a, b) => a + b, 0) / porPregunta.length;
    return Math.round(media * 100);
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
    // Las preguntas con lógica de salto llegan vacías cuando no aplicaban.
    if (s === "" || s === null || s === undefined) return "Sin respuesta";
    if (!s) return s;
    const str = String(s);
    // Se usa `MLC.labels` (no `this`) porque prettyLabel suele pasarse
    // desligada del objeto, p. ej. `keys.map(MLC.prettyLabel)`.
    if (Object.prototype.hasOwnProperty.call(MLC.labels, str)) return MLC.labels[str];
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
