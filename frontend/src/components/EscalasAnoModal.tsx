"use client";

import { useEffect, useState } from "react";
import { ChevronDown, Loader2, X } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { CoroinhaEscalasAno } from "@/types";

interface EscalasAnoModalProps {
  coroinhaId: number;
  nome: string;
  onClose: () => void;
}

export function EscalasAnoModal({ coroinhaId, nome, onClose }: EscalasAnoModalProps) {
  const [dados, setDados] = useState<CoroinhaEscalasAno | null>(null);
  const [ano, setAno] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErro("");
      try {
        const query = ano ? `?ano=${ano}` : "";
        const r = await apiFetch<CoroinhaEscalasAno>(
          `/portal/coroinhas/${coroinhaId}/escalas${query}`,
        );
        setDados(r);
        setAno(r.ano);
      } catch {
        setErro("Erro ao carregar escalas.");
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coroinhaId, ano]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center p-4 bg-black/45 backdrop-blur-[2px]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="escalas-ano-title"
      onClick={onClose}
    >
      <div
        className="card-liturgical w-full max-w-lg p-6 shadow-elegant max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h2 id="escalas-ano-title" className="font-display text-lg font-semibold text-burgundy">
              Escalas de {nome}
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">Histórico do ano</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Fechar"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>

        {dados && dados.anos_disponiveis.length > 0 && (
          <div className="relative max-w-[160px] mb-4">
            <select
              value={ano ?? ""}
              onChange={(e) => setAno(Number(e.target.value))}
              className="input-field input-field--icon-right appearance-none cursor-pointer"
            >
              {dados.anos_disponiveis.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
              aria-hidden
            />
          </div>
        )}

        <div className="overflow-y-auto -mx-1 px-1">
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="size-5 animate-spin" aria-hidden />
            </div>
          ) : erro ? (
            <p className="text-destructive text-sm">{erro}</p>
          ) : dados && dados.escalas.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {dados.escalas.map((e, i) => (
                <li key={i} className="flex justify-between border-b border-border pb-2">
                  <span>
                    {new Date(e.data + "T12:00:00").toLocaleDateString("pt-BR")} · {e.missa}
                  </span>
                  <span
                    className={
                      e.presenca === "Presente"
                        ? "text-emerald-700"
                        : e.presenca === "Ausente"
                          ? "text-destructive"
                          : "text-muted-foreground"
                    }
                  >
                    {e.presenca ?? "—"}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-6">
              Nenhuma escala neste ano.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
