export const FUNCAO_ENTRE_OS_DOIS = "EntreOsDois" as const;
export const MAX_COROINHAS_ENTRE_OS_DOIS = 2;

export const FUNCOES_ESCALA = [
  { value: "Cruz", label: "Cruz" },
  { value: "Vela1", label: "Vela 1" },
  { value: "Vela2", label: "Vela 2" },
  { value: "Turibulo", label: "Turíbulo" },
  { value: "Naveta", label: "Naveta" },
  { value: "Missal", label: "Missal" },
  { value: FUNCAO_ENTRE_OS_DOIS, label: "Entre os dois", multi: true as const },
  { value: "Ofertorio", label: "Ofertório" },
  { value: "Assessor", label: "Assessor" },
] as const;

export type FuncaoEscala = (typeof FUNCOES_ESCALA)[number]["value"];

/** Valor por função: id único ou, em EntreOsDois, até dois ids. */
export type FuncoesEscalaState = Record<FuncaoEscala, number | ""> & {
  EntreOsDois2?: number | "";
};

export function funcaoEscalaLabel(funcao: string | null | undefined): string {
  if (!funcao) return "";
  if (funcao === "Velas") return "Vela 1";
  return FUNCOES_ESCALA.find((f) => f.value === funcao)?.label ?? funcao;
}

export function funcoesVazias(): FuncoesEscalaState {
  return FUNCOES_ESCALA.reduce(
    (acc, f) => {
      acc[f.value] = "";
      return acc;
    },
    { EntreOsDois2: "" } as FuncoesEscalaState,
  );
}

export function funcoesFromItens(
  itens: { coroinha_id: number; funcao?: string | null }[],
): FuncoesEscalaState {
  const base = funcoesVazias();
  const entre: number[] = [];
  for (const item of itens) {
    if (!item.funcao) continue;
    if (item.funcao === FUNCAO_ENTRE_OS_DOIS) {
      entre.push(item.coroinha_id);
      continue;
    }
    if (item.funcao in base) {
      base[item.funcao as FuncaoEscala] = item.coroinha_id;
    }
  }
  if (entre[0]) base.EntreOsDois = entre[0];
  if (entre[1]) base.EntreOsDois2 = entre[1];
  return base;
}

export type FuncoesEscalaPayload = Record<string, number | number[]>;

export function funcoesParaPayload(map: FuncoesEscalaState): FuncoesEscalaPayload {
  const out: FuncoesEscalaPayload = {};
  for (const f of FUNCOES_ESCALA) {
    if (f.value === FUNCAO_ENTRE_OS_DOIS) {
      const ids = [map.EntreOsDois, map.EntreOsDois2].filter((id): id is number => Boolean(id));
      if (ids.length) out[FUNCAO_ENTRE_OS_DOIS] = ids;
      continue;
    }
    const id = map[f.value];
    if (id) out[f.value] = Number(id);
  }
  return out;
}