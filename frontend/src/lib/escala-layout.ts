import type { Escala } from "@/types";

/** Ordem das seções conforme escala paroquial (PDF). */
export const SECOES_ESCALA = [
  {
    id: "SextaAdoracao",
    titulo: "Sexta 18h",
    subtitulo: "Adoração + Missa — 1 antigo e 1 novo (rotativo, equilibrado)",
    tipoSlots: ["SextaAdoracao"],
  },
  {
    id: "SabadoNoite",
    titulo: "Sábado 18h30",
    subtitulo: "Grupos 1–4 (rotativos)",
    tipoSlots: ["SabadoNoite"],
  },
  {
    id: "DomingoManha",
    titulo: "Domingo 08h",
    subtitulo: "Grupos 1–4 (rotativos)",
    tipoSlots: ["DomingoManha"],
  },
  {
    id: "DomingoNoite",
    titulo: "Domingo 18h30",
    subtitulo: "Grupos 1–4 (rotativos)",
    tipoSlots: ["DomingoNoite"],
  },
  {
    id: "QuartaVoluntarios",
    titulo: "Quarta 19h",
    subtitulo: "Voluntários",
    tipoSlots: ["QuartaVoluntarios"],
  },
  {
    id: "ComunidadeDomingo",
    titulo: "Comunidade — Domingo 10h30",
    subtitulo: "Comunidade Santo Antônio",
    tipoSlots: ["ComunidadeDomingo"],
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

export interface SecaoEscalas {
  id: string;
  titulo: string;
  subtitulo: string;
  escalas: Escala[];
}

export function agruparEscalasPorHorario(escalas: Escala[]): SecaoEscalas[] {
  const porSlot = new Map<string, Escala[]>();
  for (const escala of escalas) {
    const slot = slotDaEscala(escala);
    const lista = porSlot.get(slot) ?? [];
    lista.push(escala);
    porSlot.set(slot, lista);
  }

  for (const lista of porSlot.values()) {
    lista.sort((a, b) => a.data.localeCompare(b.data) || (a.missa_horario ?? "").localeCompare(b.missa_horario ?? ""));
  }

  const secoes: SecaoEscalas[] = [];
  for (const secao of SECOES_ESCALA) {
    const itens: Escala[] = [];
    for (const slot of secao.tipoSlots) {
      const lista = porSlot.get(slot);
      if (lista) itens.push(...lista);
    }
    if (itens.length > 0) {
      secoes.push({
        id: secao.id,
        titulo: secao.titulo,
        subtitulo: secao.subtitulo,
        escalas: itens,
      });
    }
  }
  return secoes;
}
