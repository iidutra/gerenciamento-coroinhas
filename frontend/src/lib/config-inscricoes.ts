import { apiFetch } from "@/lib/api";

export interface ConfigInscricoes {
  inscricoes_abertas: boolean;
  controlado_por_env?: boolean;
  atualizado_em?: string;
  atualizado_por_nome?: string | null;
}

export async function fetchConfigInscricoes(): Promise<ConfigInscricoes> {
  return apiFetch<ConfigInscricoes>("/config/inscricoes");
}

export async function definirInscricoesAbertas(aberto: boolean): Promise<ConfigInscricoes & { detail?: string }> {
  return apiFetch<ConfigInscricoes & { detail?: string }>("/config/inscricoes", {
    method: "PATCH",
    body: JSON.stringify({ inscricoes_abertas: aberto }),
  });
}
