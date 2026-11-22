"use client";

import { useMemo, useState } from "react";
import { normalizarBusca } from "@/lib/format";
import type { Coroinha } from "@/types";

interface CoroinhaSearchSelectProps {
  coroinhas: Coroinha[];
  value: number | "";
  onChange: (id: number | "") => void;
  id?: string;
  placeholder?: string;
  excluirIds?: number[];
}

export function CoroinhaSearchSelect({
  coroinhas,
  value,
  onChange,
  id,
  placeholder = "—",
  excluirIds = [],
}: CoroinhaSearchSelectProps) {
  const [busca, setBusca] = useState("");

  const opcoes = useMemo(() => {
    const termo = normalizarBusca(busca);
    return coroinhas.filter((c) => {
      if (excluirIds.includes(c.id)) return false;
      if (!termo) return true;
      return normalizarBusca(c.nome).includes(termo);
    });
  }, [coroinhas, busca, excluirIds]);

  const valorVisivel =
    value !== "" && opcoes.some((c) => c.id === value)
      ? value
      : value !== "" && coroinhas.some((c) => c.id === value)
        ? value
        : "";

  return (
    <div className="space-y-1">
      <input
        type="search"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
        placeholder="Buscar nome..."
        className="input-field text-xs py-1.5"
        aria-label="Buscar coroinha"
      />
      <select
        id={id}
        value={valorVisivel === "" ? "" : String(valorVisivel)}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
        className="input-field text-sm"
      >
        <option value="">{placeholder}</option>
        {valorVisivel !== "" &&
          !opcoes.some((c) => c.id === valorVisivel) &&
          coroinhas
            .filter((c) => c.id === valorVisivel)
            .map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
        {opcoes.map((c) => (
          <option key={c.id} value={c.id}>
            {c.nome}
          </option>
        ))}
      </select>
    </div>
  );
}