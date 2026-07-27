import type { EscalaMensal } from "@/types";
import { nomeMes } from "@/lib/escala-layout";

interface GruposMensaisPanelProps {
  escalaMensal: EscalaMensal;
}

export function GruposMensaisPanel({ escalaMensal }: GruposMensaisPanelProps) {
  return (
    <div className="card-liturgical p-5 mb-6">
      <h2 className="font-display text-lg font-semibold text-burgundy mb-1">
        Grupos — {nomeMes(escalaMensal.mes)} {escalaMensal.ano}
      </h2>
      <p className="text-xs text-muted-foreground mb-4">
        Composição mensal dos grupos rotativos (Sábado 18h30 · Domingo 08h · Domingo 18h30)
      </p>
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {escalaMensal.grupos
          .slice()
          .sort((a, b) => a.numero - b.numero)
          .map((grupo) => (
            <div key={grupo.numero} className="rounded-lg border border-border bg-muted/20 p-3">
              <h3 className="font-display font-semibold text-burgundy text-sm mb-2 uppercase tracking-wide">
                Grupo {grupo.numero}
              </h3>
              <ol className="text-sm space-y-0.5 list-decimal list-inside">
                {grupo.membros
                  .slice()
                  .sort((a, b) => a.ordem - b.ordem)
                  .map((m) => (
                    <li key={m.coroinha_id} className="text-foreground">
                      {m.coroinha_nome}
                    </li>
                  ))}
              </ol>
            </div>
          ))}
      </div>
    </div>
  );
}
