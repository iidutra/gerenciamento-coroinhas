export const FUNCAO_ENTRE_OS_DOIS = "EntreOsDois" as const;
export const FUNCAO_ASSESSOR = "Assessor" as const;
export const MAX_COROINHAS_ENTRE_OS_DOIS = 2;

export const FUNCOES_ESCALA = [
  { value: "Cruz", label: "Cruz" },
  { value: "Vela1", label: "Vela 1" },
  { value: "Vela2", label: "Vela 2" },
  { value: "Turibulo", label: "Turíbulo" },
  { value: "Naveta", label: "Naveta" },
  { value: "Missal", label: "Missal" },
  { value: FUNCAO_ENTRE_OS_DOIS, label: "Altar", multi: true as const, max: 2 as const },
  { value: "Ofertorio", label: "Ofertório" },
  { value: FUNCAO_ASSESSOR, label: "Assessor", multi: true as const },
] as const;

export type FuncaoEscala = (typeof FUNCOES_ESCALA)[number]["value"];

/** Funções com lista de coroinhas (entre os dois, assessor, etc.). */
export type FuncoesEscalaState = Record<FuncaoEscala, number | ""> & {
  entreOsDoisIds: number[];
  assessorIds: number[];
};

export function funcaoEscalaLabel(funcao: string | null | undefined): string {
  if (!funcao) return "";
  if (funcao === "Velas") return "Vela 1";
  return FUNCOES_ESCALA.find((f) => f.value === funcao)?.label ?? funcao;
}

export function funcoesVazias(): FuncoesEscalaState {
  const slots = {} as Record<FuncaoEscala, number | "">;
  for (const f of FUNCOES_ESCALA) {
    slots[f.value] = "";
  }
  return { ...slots, entreOsDoisIds: [], assessorIds: [] };
}

export function funcoesFromItens(
  itens: { coroinha_id: number; funcao?: string | null }[],
): FuncoesEscalaState {
  const base = funcoesVazias();
  const entre: number[] = [];
  const assessores: number[] = [];
  for (const item of itens) {
    if (!item.funcao) continue;
    if (item.funcao === FUNCAO_ENTRE_OS_DOIS) {
      entre.push(item.coroinha_id);
      continue;
    }
    if (item.funcao === FUNCAO_ASSESSOR) {
      assessores.push(item.coroinha_id);
      continue;
    }
    if (item.funcao in base) {
      base[item.funcao as FuncaoEscala] = item.coroinha_id;
    }
  }
  base.entreOsDoisIds = entre.slice(0, MAX_COROINHAS_ENTRE_OS_DOIS);
  base.assessorIds = assessores;
  return base;
}

export type FuncoesEscalaPayload = Record<string, number | number[]>;

export function funcoesParaPayload(map: FuncoesEscalaState): FuncoesEscalaPayload {
  const out: FuncoesEscalaPayload = {};
  const assessorIds = map.assessorIds.filter((id) => id > 0);
  if (assessorIds.length) out[FUNCAO_ASSESSOR] = assessorIds;

  for (const f of FUNCOES_ESCALA) {
    if (f.value === FUNCAO_ENTRE_OS_DOIS) {
      const ids = map.entreOsDoisIds.filter((id) => id > 0);
      if (ids.length) out[FUNCAO_ENTRE_OS_DOIS] = ids;
      continue;
    }
    if (f.value === FUNCAO_ASSESSOR) continue;
    const id = map[f.value];
    if (id) out[f.value] = Number(id);
  }
  return out;
}