"use client";

import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { normalizarBusca } from "@/lib/format";
import type { Coroinha } from "@/types";

interface CoroinhaSelecaoListaProps {
  coroinhas: Coroinha[];
  selecionados: number[];
  onToggle: (id: number) => void;
  maxSelecionados?: number;
  className?: string;
}

export function CoroinhaSelecaoLista({
  coroinhas,
  selecionados,
  onToggle,
  maxSelecionados,
  className = "",
}: CoroinhaSelecaoListaProps) {
  const [busca, setBusca] = useState("");
  const filtrados = useMemo(() => {
    const termo = normalizarBusca(busca);
    if (!termo) return coroinhas;
    return coroinhas.filter((c) => normalizarBusca(c.nome).includes(termo));
  }, [coroinhas, busca]);

  return (
    <div className={className}>
      <div className="relative mb-2">
        <Search
          className="absolute left-3 top-1/2 z-10 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
          aria-hidden
        />
        <input
          type="search"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar coroinha..."
          className="input-field input-field--icon-left text-sm"
        />
      </div>
      {maxSelecionados != null && (
        <p className="text-xs text-muted-foreground mb-2">
          {selecionados.length} de {maxSelecionados} selecionado(s)
        </p>
      )}
      <div className="max-h-56 overflow-y-auto border border-border rounded-lg bg-card p-2 grid sm:grid-cols-2 gap-1">
        {filtrados.length === 0 ? (
          <p className="text-sm text-muted-foreground col-span-full py-3 text-center">Nenhum nome encontrado.</p>
        ) : (
          filtrados.map((c) => {
            const checked = selecionados.includes(c.id);
            const bloqueado =
              maxSelecionados != null && !checked && selecionados.length >= maxSelecionados;
            return (
              <label
                key={c.id}
                className={`flex items-center gap-2 text-sm px-2 py-1.5 rounded ${
                  bloqueado ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:bg-muted/50"
                }`}
              >
                <input
                  type="checkbox"
                  className="accent-[var(--burgundy)] size-4"
                  checked={checked}
                  disabled={bloqueado}
                  onChange={() => onToggle(c.id)}
                />
                {c.nome}
              </label>
            );
          })
        )}
      </div>
    </div>
  );
}