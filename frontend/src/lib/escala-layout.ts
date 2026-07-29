import type { Escala } from "@/types";

const LOCAIS_CELEBRACAO: Record<string, string> = {
  Santuario: "N. Sra. de Fátima",
  Comunidade: "Santo Antônio",
};

const ORDEM_SLOT_CRONO: Record<string, number> = {
  SextaAdoracao: 1,
  SabadoNoite: 2,
  DomingoManha: 3,
  ComunidadeDomingo: 4,
  DomingoNoite: 5,
  QuartaVoluntarios: 6,
  Dia13: 7,
  Outro: 8,
};

export const LEGENDA_CATEGORIAS_V6 = [
  "Grupo 1",
  "Grupo 2",
  "Grupo 3",
  "Grupo 4",
  "S. Antônio",
  "Solenidade",
  "Novena",
] as const;

export const ORIENTACOES_GERAIS_V6 = [
  "Chegada com 30 minutos de antecedência em todas as celebrações.",
  "Meninas: cabelos presos e trajes adequados ao ambiente da sacristia.",
  "Meninos: trajes adequados ao ambiente da sacristia.",
  "Sapatos preferencialmente pretos e vestes limpas e passadas.",
  "Em caso de impedimento, avisar com antecedência para reorganização.",
  "Dúvidas e trocas: falar com Igor ou Giaritssa.",
] as const;

/** Ordem das seções extras (fora do bloco sexta–domingo). */
export const SECOES_EXTRAS = [
  {
    id: "QuartaVoluntarios",
    titulo: "Quarta 19h",
    subtitulo: "Voluntários",
    tipoSlots: ["QuartaVoluntarios"],
  },
  {
    id: "Dia13",
    titulo: "Dia 13",
    subtitulo: "Missas da memória mensal (cadastro manual)",
    tipoSlots: ["Dia13"],
  },
  {
    id: "Outro",
    titulo: "Outras celebrações",
    subtitulo: "",
    tipoSlots: ["Outro"],
  },
] as const;

const SLOTS_FIM_DE_SEMANA = new Set([
  "SextaAdoracao",
  "SabadoNoite",
  "DomingoManha",
  "DomingoNoite",
  "ComunidadeDomingo",
]);

const ORDEM_SLOT_FDS: Record<string, number> = {
  SextaAdoracao: 1,
  SabadoNoite: 2,
  DomingoManha: 3,
  ComunidadeDomingo: 4,
  DomingoNoite: 5,
};

const MESES = [
  "",
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export function nomeMes(mes: number): string {
  return MESES[mes] ?? String(mes);
}

export function formatarHorarioCurto(horario: string): string {
  const [hRaw, mRaw] = horario.slice(0, 5).split(":");
  const h = parseInt(hRaw, 10);
  const m = parseInt(mRaw, 10);
  if (m === 0) return `${h}h`;
  return `${h}h${String(m).padStart(2, "0")}`;
}

function localCelebracao(escala: Escala): string {
  if (escala.missa_tipo_slot === "ComunidadeDomingo" || escala.missa_local === "Comunidade") {
    return "Santo Antônio";
  }
  if (escala.missa_local) {
    return LOCAIS_CELEBRACAO[escala.missa_local] ?? escala.missa_local;
  }
  return "N. Sra. de Fátima";
}

function horarioCelebracao(escala: Escala): string {
  if (escala.missa_horario) return formatarHorarioCurto(escala.missa_horario);
  if (escala.missa_tipo_slot === "ComunidadeDomingo") return "10h30";
  return "";
}

export function formatarDataLegivelEscala(dataIso: string): string {
  const d = new Date(`${dataIso}T12:00:00`);
  const diaSemana = d.toLocaleDateString("pt-BR", { weekday: "long" });
  const capitalizado = diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
  const dia = d.getDate();
  const mes = d.toLocaleDateString("pt-BR", { month: "long" });
  return `${capitalizado}, ${dia} de ${mes}`;
}

/** @deprecated Prefer linhaTituloV6 */
export function tituloCelebracaoEscala(escala: Escala): string {
  return linhaTituloV6(escala);
}

export function filtrarEscalasDoMes(escalas: Escala[], ano: number, mes: number): Escala[] {
  return escalas.filter((e) => {
    const [y, m] = e.data.split("-").map(Number);
    return y === ano && m === mes;
  });
}

function slotDaEscala(escala: Escala): string {
  if (escala.missa_tipo_slot) return escala.missa_tipo_slot;
  return "Outro";
}

function chaveOrdemEscala(escala: Escala): [string, number, string] {
  const slot = slotDaEscala(escala);
  return [escala.data, ORDEM_SLOT_CRONO[slot] ?? 99, escala.missa_horario ?? ""];
}

export function rotuloDiaSemanaCurto(dataIso: string): string {
  const d = new Date(`${dataIso}T12:00:00`);
  const label = d.toLocaleDateString("pt-BR", { weekday: "long" }).toUpperCase();
  return label.replace("-FEIRA", "");
}

export function tagCelebracao(escala: Escala): string {
  const slot = slotDaEscala(escala);
  if (slot === "ComunidadeDomingo") return "Santo Antônio";
  if (slot === "QuartaVoluntarios") return "Novena";
  if (slot === "Dia13") return "Solenidade";
  if (escala.grupo_numero != null) return `Grupo ${escala.grupo_numero}`;
  return "";
}

export function tituloCelebracaoV6(escala: Escala): string {
  const slot = slotDaEscala(escala);
  const horario = horarioCelebracao(escala);
  if (slot === "SabadoNoite") return `${horario} Missa`;
  if (slot === "DomingoManha") return `${horario} Missa da Manhã`;
  if (slot === "DomingoNoite") return `${horario} Missa da Noite`;
  if (slot === "ComunidadeDomingo") return `${horario} Comunidade`;
  if (slot === "SextaAdoracao") return `${horario} Adoração + Missa`;
  if (slot === "QuartaVoluntarios") return "Noite Novena";
  if (slot === "Dia13") {
    const hora = parseInt(escala.missa_horario?.slice(0, 2) ?? "0", 10);
    if (hora === 6) return "Missa das 6h";
    if (hora === 9) return "Missa das 9h";
    if (hora === 12) return "Missa das 12h";
    return "Missa das 18h";
  }
  return `${horario} ${escala.missa_nome ?? "Celebração"}`;
}

export function linhaTituloV6(escala: Escala): string {
  const titulo = tituloCelebracaoV6(escala);
  const slot = slotDaEscala(escala);
  const tag = tagCelebracao(escala);
  if (slot === "QuartaVoluntarios") {
    return tag ? `${titulo} ${tag}` : titulo;
  }
  if (slot === "Dia13") return titulo;
  if (escala.grupo_numero != null) {
    return `${titulo} Grupo ${escala.grupo_numero}`;
  }
  if (tag) return `${titulo} ${tag}`;
  return titulo;
}

export const TITULO_SOLENIDADE_DIA_13 = "Solenidade de Nossa Senhora de Fátima";

export function diaTemSolenidade(escalas: Escala[]): boolean {
  return escalas.some((e) => slotDaEscala(e) === "Dia13");
}

export function linhasCoroinhasV6(escala: Escala): string[] {
  if (escala.voluntarios) return ["01 Participação aberta — Voluntários"];
  if (escala.itens.length === 0) return ["—"];
  return escala.itens.map((item, idx) => `${String(idx + 1).padStart(2, "0")} ${item.coroinha_nome}`);
}

export interface DiaEscalas {
  id: string;
  data: string;
  dia: string;
  diaSemana: string;
  escalas: Escala[];
}

export function agruparEscalasPorDia(escalas: Escala[]): DiaEscalas[] {
  const porDia = new Map<string, Escala[]>();
  for (const escala of escalas) {
    const lista = porDia.get(escala.data) ?? [];
    lista.push(escala);
    porDia.set(escala.data, lista);
  }

  return Array.from(porDia.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([data, lista]) => {
      lista.sort((a, b) => {
        const [, ordemA, horaA] = chaveOrdemEscala(a);
        const [, ordemB, horaB] = chaveOrdemEscala(b);
        if (ordemA !== ordemB) return ordemA - ordemB;
        return horaA.localeCompare(horaB);
      });
      const d = new Date(`${data}T12:00:00`);
      return {
        id: data,
        data,
        dia: String(d.getDate()).padStart(2, "0"),
        diaSemana: rotuloDiaSemanaCurto(data),
        escalas: lista,
      };
    });
}

/** Sábado de referência do bloco sexta–sábado–domingo. */
export function chaveFimDeSemana(dataIso: string): string {
  const d = new Date(`${dataIso}T12:00:00`);
  const wd = d.getDay();
  const sab = new Date(d);
  if (wd === 5) sab.setDate(sab.getDate() + 1);
  else if (wd === 0) sab.setDate(sab.getDate() - 1);
  return sab.toISOString().slice(0, 10);
}

function ordenarEscalasFds(a: Escala, b: Escala): number {
  const ordemA = ORDEM_SLOT_FDS[slotDaEscala(a)] ?? 99;
  const ordemB = ORDEM_SLOT_FDS[slotDaEscala(b)] ?? 99;
  if (ordemA !== ordemB) return ordemA - ordemB;
  return a.data.localeCompare(b.data) || (a.missa_horario ?? "").localeCompare(b.missa_horario ?? "");
}

export function rotuloSemana(chaveSabado: string): string {
  const sab = new Date(`${chaveSabado}T12:00:00`);
  const sex = new Date(sab);
  sex.setDate(sex.getDate() - 1);
  const dom = new Date(sab);
  dom.setDate(dom.getDate() + 1);

  const fmt = (d: Date) =>
    d.toLocaleDateString("pt-BR", { day: "numeric", month: "long" });

  const mesSex = sex.getMonth();
  const mesDom = dom.getMonth();
  if (mesSex === mesDom) {
    return `${sex.getDate()} a ${dom.getDate()} de ${fmt(dom).split(" de ")[1]}`;
  }
  return `${fmt(sex)} a ${fmt(dom)}`;
}

export interface SecaoEscalas {
  id: string;
  titulo: string;
  subtitulo: string;
  escalas: Escala[];
}

export interface SemanaEscalas {
  id: string;
  titulo: string;
  escalas: Escala[];
}

export interface EscalasAgrupadas {
  semanas: SemanaEscalas[];
  extras: SecaoEscalas[];
}

/** @deprecated Prefer agruparEscalasPorDia (template v6) */
export function agruparEscalasPorSemana(escalas: Escala[]): EscalasAgrupadas {
  const porSemana = new Map<string, Escala[]>();
  const extrasPorSlot = new Map<string, Escala[]>();

  for (const escala of escalas) {
    const slot = slotDaEscala(escala);
    if (SLOTS_FIM_DE_SEMANA.has(slot)) {
      const chave = chaveFimDeSemana(escala.data);
      const lista = porSemana.get(chave) ?? [];
      lista.push(escala);
      porSemana.set(chave, lista);
    } else {
      const lista = extrasPorSlot.get(slot) ?? [];
      lista.push(escala);
      extrasPorSlot.set(slot, lista);
    }
  }

  const semanas: SemanaEscalas[] = Array.from(porSemana.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([chave, lista], idx) => {
      lista.sort(ordenarEscalasFds);
      return {
        id: chave,
        titulo: `Semana ${idx + 1} · ${rotuloSemana(chave)}`,
        escalas: lista,
      };
    });

  for (const lista of extrasPorSlot.values()) {
    lista.sort((a, b) => a.data.localeCompare(b.data) || (a.missa_horario ?? "").localeCompare(b.missa_horario ?? ""));
  }

  const extras: SecaoEscalas[] = [];
  for (const secao of SECOES_EXTRAS) {
    const itens: Escala[] = [];
    for (const slot of secao.tipoSlots) {
      const lista = extrasPorSlot.get(slot);
      if (lista) itens.push(...lista);
    }
    if (itens.length > 0) {
      extras.push({
        id: secao.id,
        titulo: secao.titulo,
        subtitulo: secao.subtitulo,
        escalas: itens,
      });
    }
  }

  return { semanas, extras };
}

/** @deprecated Use agruparEscalasPorDia */
export function agruparEscalasPorHorario(escalas: Escala[]): SecaoEscalas[] {
  const { semanas, extras } = agruparEscalasPorSemana(escalas);
  const resultado: SecaoEscalas[] = semanas.map((s) => ({
    id: s.id,
    titulo: s.titulo,
    subtitulo: "Sexta, sábado e domingo",
    escalas: s.escalas,
  }));
  return [...resultado, ...extras];
}
