"use client";

import { CoroinhaSearchSelect } from "@/components/CoroinhaSearchSelect";
import { CoroinhaSelecaoLista } from "@/components/CoroinhaSelecaoLista";
import type { Coroinha } from "@/types";
import {
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

function toggleEntreOsDois(valores: FuncoesEscalaState, id: number, onChange: (v: FuncoesEscalaState) => void) {
  const atual = valores.entreOsDoisIds ?? [];
  if (atual.includes(id)) {
    onChange({ ...valores, entreOsDoisIds: atual.filter((x) => x !== id) });
    return;
  }
  if (atual.length >= MAX_COROINHAS_ENTRE_OS_DOIS) return;
  onChange({ ...valores, entreOsDoisIds: [...atual, id] });
}

export function FuncoesEscalaForm({ coroinhas, valores, onChange, compact }: FuncoesEscalaFormProps) {
  return (
    <div className={`space-y-2 ${compact ? "" : "p-3 rounded-lg border border-border bg-muted/30"}`}>
      {!compact && (
        <p className="text-xs text-muted-foreground">
          Funções litúrgicas (opcional). Em &quot;Entre os dois&quot;, marque até 2 coroinhas na lista.
        </p>
      )}
      <div className="grid sm:grid-cols-2 gap-3">
        {FUNCOES_ESCALA.map((f) => {
          if (f.value === FUNCAO_ENTRE_OS_DOIS) {
            return (
              <div key={f.value} className="sm:col-span-2 space-y-2 rounded-lg border border-border/60 p-3">
                <span className="text-muted-foreground text-xs font-medium block">{f.label}</span>
                <p className="text-xs text-muted-foreground">
                  Selecione 1 ou 2 coroinhas (marque na lista abaixo).
                </p>
                <CoroinhaSelecaoLista
                  coroinhas={coroinhas}
                  selecionados={valores.entreOsDoisIds ?? []}
                  maxSelecionados={MAX_COROINHAS_ENTRE_OS_DOIS}
                  onToggle={(id) => toggleEntreOsDois(valores, id, onChange)}
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