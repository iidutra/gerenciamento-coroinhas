"use client";

import { ChevronDown, Search, UserMinus, UserPlus } from "lucide-react";
import { useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  labelComunidadeFixa,
  participaEscalaRotativa,
} from "@/lib/comunidade-fixa";
import { normalizarBusca } from "@/lib/format";
import type { Coroinha, Escala, EscalaMensal } from "@/types";

interface PainelCoroinhasRemanejamentoProps {
  coroinhas: Coroinha[];
  escalaMensal: EscalaMensal;
  ano: number;
  mes: number;
  podeEditar: boolean;
  onAtualizado: (escalaMensal: EscalaMensal, escalas: Escala[]) => void;
}

export function PainelCoroinhasRemanejamento({
  coroinhas,
  escalaMensal,
  ano,
  mes,
  podeEditar,
  onAtualizado,
}: PainelCoroinhasRemanejamentoProps) {
  const [aberto, setAberto] = useState(false);
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState<"todos" | "grupo" | "fora" | "comunidade">("todos");
  const [acaoId, setAcaoId] = useState<number | null>(null);
  const [erro, setErro] = useState("");

  const grupoPorCoroinha = useMemo(() => {
    const map = new Map<number, number>();
    for (const grupo of escalaMensal.grupos) {
      for (const membro of grupo.membros) {
        map.set(membro.coroinha_id, grupo.numero);
      }
    }
    return map;
  }, [escalaMensal.grupos]);

  const lista = useMemo(() => {
    const termo = normalizarBusca(busca);
    return coroinhas
      .filter((c) => normalizarBusca(c.nome).includes(termo))
      .filter((c) => {
        const grupo = grupoPorCoroinha.get(c.id);
        const fixa = Boolean(c.comunidade_fixa);
        if (filtro === "grupo") return grupo !== undefined;
        if (filtro === "fora") return grupo === undefined && !fixa;
        if (filtro === "comunidade") return fixa;
        return true;
      })
      .slice()
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  }, [coroinhas, busca, filtro, grupoPorCoroinha]);

  async function adicionarAoGrupo(coroinhaId: number, grupoDestino: number) {
    setErro("");
    setAcaoId(coroinhaId);
    try {
      const res = await apiFetch<{ escala_mensal: EscalaMensal; escalas: Escala[] }>(
        "/escalas/mensal/remanejar-grupo/",
        {
          method: "PATCH",
          body: JSON.stringify({
            ano,
            mes,
            coroinha_id: coroinhaId,
            grupo_destino: grupoDestino,
          }),
        },
      );
      onAtualizado(res.escala_mensal, res.escalas);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao adicionar ao grupo");
    } finally {
      setAcaoId(null);
    }
  }

  async function removerDoGrupo(coroinhaId: number) {
    setErro("");
    setAcaoId(coroinhaId);
    try {
      const res = await apiFetch<{ escala_mensal: EscalaMensal; escalas: Escala[] }>(
        "/escalas/mensal/remover-grupo/",
        {
          method: "PATCH",
          body: JSON.stringify({ ano, mes, coroinha_id: coroinhaId }),
        },
      );
      onAtualizado(res.escala_mensal, res.escalas);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao remover do grupo");
    } finally {
      setAcaoId(null);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-muted/5 overflow-hidden">
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-muted/20 transition-colors"
      >
        <span className="text-sm font-medium text-burgundy">
          Todos os coroinhas — adicionar ou remover dos grupos
        </span>
        <ChevronDown
          className={`size-4 text-muted-foreground transition-transform ${aberto ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>

      {aberto && (
        <div className="px-4 pb-4 border-t border-border space-y-3">
          <p className="text-xs text-muted-foreground pt-3">
            Coroinhas de comunidade fixa (Santa Terezinha / N. Sra. Auxiliadora) não entram na
            geração automática da paróquia. Coroinhas da paróquia aparecem nos grupos rotativos.
            Ao remover alguém do remanejamento, ele sai de todas as celebrações do mês abaixo.
          </p>

          {erro && (
            <p className="text-sm text-destructive" role="alert">
              {erro}
            </p>
          )}

          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
                aria-hidden
              />
              <input
                type="search"
                placeholder="Buscar coroinha…"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="input-field input-field--icon-left w-full"
              />
            </div>
            <select
              value={filtro}
              onChange={(e) => setFiltro(e.target.value as typeof filtro)}
              className="input-field sm:w-48"
            >
              <option value="todos">Todos</option>
              <option value="grupo">Nos grupos</option>
              <option value="fora">Fora dos grupos</option>
              <option value="comunidade">Comunidade fixa</option>
            </select>
          </div>

          <div className="max-h-72 overflow-y-auto rounded-lg border border-border divide-y divide-border bg-card">
            {lista.length === 0 ? (
              <p className="text-sm text-muted-foreground p-4 text-center">Nenhum coroinha encontrado.</p>
            ) : (
              lista.map((c) => {
                const grupo = grupoPorCoroinha.get(c.id);
                const rotativo = participaEscalaRotativa(c.comunidade_fixa);
                const processando = acaoId === c.id;

                return (
                  <div
                    key={c.id}
                    className="flex flex-col sm:flex-row sm:items-center gap-2 px-3 py-2.5 text-sm"
                  >
                    <div className="flex-1 min-w-0">
                      <span className="font-medium truncate block">{c.nome}</span>
                      <span className="text-xs text-muted-foreground">
                        {grupo !== undefined ? `Grupo ${grupo}` : "Fora dos grupos"}
                        {c.comunidade_fixa
                          ? ` · ${labelComunidadeFixa(c.comunidade_fixa)}`
                          : ""}
                      </span>
                    </div>

                    {podeEditar && (
                      <div className="flex flex-wrap items-center gap-2 shrink-0">
                        {grupo !== undefined ? (
                          <button
                            type="button"
                            disabled={processando}
                            onClick={() => removerDoGrupo(c.id)}
                            className="btn-outline text-xs py-1.5 px-2.5 inline-flex items-center gap-1.5 text-destructive border-destructive/30 hover:bg-destructive/10"
                          >
                            <UserMinus className="size-3.5" aria-hidden />
                            Remover
                          </button>
                        ) : rotativo ? (
                          <div className="inline-flex items-center gap-1">
                            <UserPlus className="size-3.5 text-muted-foreground" aria-hidden />
                            {[1, 2, 3, 4].map((num) => (
                              <button
                                key={num}
                                type="button"
                                disabled={processando}
                                onClick={() => adicionarAoGrupo(c.id, num)}
                                className="btn-outline text-xs py-1 px-2 min-w-[2rem]"
                              >
                                G{num}
                              </button>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">Escala fixa</span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
