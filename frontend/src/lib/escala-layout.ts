import type { Escala } from "@/types";

const LOCAIS_CELEBRACAO: Record<string, string> = {
  Santuario: "N. Sra. de Fátima",
  Comunidade: "Santo Antônio",
};

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

export function formatarDataLegivelEscala(dataIso: string): string {
  const d = new Date(`${dataIso}T12:00:00`);
  const diaSemana = d.toLocaleDateString("pt-BR", { weekday: "long" });
  const capitalizado = diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
  const dia = d.getDate();
  const mes = d.toLocaleDateString("pt-BR", { month: "long" });
  return `${capitalizado}, ${dia} de ${mes}`;
}

/** Ex.: Domingo, 3 de agosto · Santo Antônio · 10h30 */
export function tituloCelebracaoEscala(escala: Escala): string {
  const partes = [formatarDataLegivelEscala(escala.data), localCelebracao(escala)];
  const horario = horarioCelebracao(escala);
  if (horario) partes.push(horario);
  if (escala.grupo_numero != null) {
    partes.push(`GRUPO ${escala.grupo_numero}`);
  }
  return partes.join(" · ");
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

/** @deprecated Use agruparEscalasPorSemana */
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
