import type { ComunidadeFixa } from "@/types";

export const COMUNIDADE_FIXA_OPCOES: { value: ComunidadeFixa; label: string }[] = [
  { value: "", label: "Santuário (escala rotativa)" },
  { value: "SantaTerezinha", label: "Santa Terezinha" },
  { value: "NossaSenhoraAuxiliadora", label: "Nossa Senhora Auxiliadora" },
];

export function labelComunidadeFixa(valor?: ComunidadeFixa | null): string {
  if (!valor) return "Santuário";
  return COMUNIDADE_FIXA_OPCOES.find((o) => o.value === valor)?.label ?? valor;
}

export function participaEscalaRotativa(comunidadeFixa?: ComunidadeFixa | null): boolean {
  return !comunidadeFixa;
}
