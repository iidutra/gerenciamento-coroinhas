"use client";

import { CoroinhaSearchSelect } from "@/components/CoroinhaSearchSelect";
import { CoroinhaSelecaoLista } from "@/components/CoroinhaSelecaoLista";
import type { Coroinha } from "@/types";
import {
  FUNCAO_ASSESSOR,
  FUNCAO_ENTRE_OS_DOIS,
  FUNCOES_ESCALA,
  MAX_COROINHAS_ENTRE_OS_DOIS,
  type FuncoesEscalaState,
} from "@/lib/scheduling";

interface FuncoesEscalaFormProps {
  coroinhas: Coroinha[];
  valores: FuncoesEscalaState;
  onChange: (valores: FuncoesEscalaState) => void;
  compact?: boolean;
}

function toggleLista(
  chave: "entreOsDoisIds" | "assessorIds",
  valores: FuncoesEscalaState,
  id: number,
  onChange: (v: FuncoesEscalaState) => void,
  max?: number,
) {
  const atual = valores[chave] ?? [];
  if (atual.includes(id)) {
    onChange({ ...valores, [chave]: atual.filter((x) => x !== id) });
    return;
  }
  if (max != null && atual.length >= max) return;
  onChange({ ...valores, [chave]: [...atual, id] });
}

export function FuncoesEscalaForm({ coroinhas, valores, onChange, compact }: FuncoesEscalaFormProps) {
  return (
    <div className={`space-y-2 ${compact ? "" : "p-3 rounded-lg border border-border bg-muted/30"}`}>
      {!compact && (
        <p className="text-xs text-muted-foreground">
          Funções litúrgicas (opcional). &quot;Entre os dois&quot; (até 2) e &quot;Assessor&quot; (um ou mais) usam
          lista com busca.
        </p>
      )}
      <div className="grid sm:grid-cols-2 gap-3">
        {FUNCOES_ESCALA.map((f) => {
          if (f.value === FUNCAO_ENTRE_OS_DOIS) {
            return (
              <div key={f.value} className="sm:col-span-2 space-y-2 rounded-lg border border-border/60 p-3">
                <span className="text-muted-foreground text-xs font-medium block">{f.label}</span>
                <p className="text-xs text-muted-foreground">Até 2 coroinhas.</p>
                <CoroinhaSelecaoLista
                  coroinhas={coroinhas}
                  selecionados={valores.entreOsDoisIds ?? []}
                  maxSelecionados={MAX_COROINHAS_ENTRE_OS_DOIS}
                  onToggle={(id) => toggleLista("entreOsDoisIds", valores, id, onChange, MAX_COROINHAS_ENTRE_OS_DOIS)}
                />
              </div>
            );
          }
          if (f.value === FUNCAO_ASSESSOR) {
            return (
              <div key={f.value} className="sm:col-span-2 space-y-2 rounded-lg border border-border/60 p-3">
                <span className="text-muted-foreground text-xs font-medium block">{f.label}</span>
                <p className="text-xs text-muted-foreground">Um ou mais coroinhas assessores nesta missa.</p>
                <CoroinhaSelecaoLista
                  coroinhas={coroinhas}
                  selecionados={valores.assessorIds ?? []}
                  onToggle={(id) => toggleLista("assessorIds", valores, id, onChange)}
                />
              </div>
            );
          }
          return (
            <label key={f.value} className="text-sm block">
              <span className="text-muted-foreground text-xs block mb-1">{f.label}</span>
              <CoroinhaSearchSelect
                coroinhas={coroinhas}
                value={valores[f.value]}
                onChange={(id) => onChange({ ...valores, [f.value]: id })}
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}