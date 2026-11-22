"use client";

import { CoroinhaSearchSelect } from "@/components/CoroinhaSearchSelect";
import type { Coroinha } from "@/types";
import { FUNCAO_ENTRE_OS_DOIS, FUNCOES_ESCALA, type FuncoesEscalaState } from "@/lib/scheduling";

interface FuncoesEscalaFormProps {
  coroinhas: Coroinha[];
  valores: FuncoesEscalaState;
  onChange: (valores: FuncoesEscalaState) => void;
  compact?: boolean;
}

export function FuncoesEscalaForm({ coroinhas, valores, onChange, compact }: FuncoesEscalaFormProps) {
  return (
    <div className={`space-y-2 ${compact ? "" : "p-3 rounded-lg border border-border bg-muted/30"}`}>
      {!compact && (
        <p className="text-xs text-muted-foreground">
          Funções litúrgicas (opcional) — busque o nome e selecione. &quot;Entre os dois&quot; aceita até 2
          coroinhas.
        </p>
      )}
      <div className="grid sm:grid-cols-2 gap-3">
        {FUNCOES_ESCALA.map((f) => {
          if (f.value === FUNCAO_ENTRE_OS_DOIS) {
            const primeiro = valores.EntreOsDois;
            const segundo = valores.EntreOsDois2 ?? "";
            return (
              <div key={f.value} className="sm:col-span-2 space-y-2 rounded-lg border border-border/60 p-2">
                <span className="text-muted-foreground text-xs font-medium block">{f.label}</span>
                <div className="grid sm:grid-cols-2 gap-2">
                  <CoroinhaSearchSelect
                    coroinhas={coroinhas}
                    value={primeiro}
                    excluirIds={segundo ? [Number(segundo)] : []}
                    onChange={(id) => onChange({ ...valores, EntreOsDois: id })}
                    placeholder="1º coroinha"
                  />
                  <CoroinhaSearchSelect
                    coroinhas={coroinhas}
                    value={segundo}
                    excluirIds={primeiro ? [Number(primeiro)] : []}
                    onChange={(id) => onChange({ ...valores, EntreOsDois2: id })}
                    placeholder="2º coroinha (opcional)"
                  />
                </div>
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