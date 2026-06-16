"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ClipboardList, LogIn, Sparkles } from "lucide-react";
import { fetchConfigPublica } from "@/lib/config-publica";

export function HomeHeroActions() {
  const [inscricoesAbertas, setInscricoesAbertas] = useState(false);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    fetchConfigPublica()
      .then((cfg) => setInscricoesAbertas(cfg.inscricoes_abertas))
      .finally(() => setCarregando(false));
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {!carregando && inscricoesAbertas && (
        <section
          aria-label="Inscrições abertas"
          className="relative overflow-hidden rounded-2xl border-2 border-gold/60 bg-gradient-to-br from-gold/25 via-gold/10 to-burgundy/20 p-6 sm:p-8 text-left shadow-gold"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-gold/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
          <div className="relative flex flex-col sm:flex-row sm:items-center gap-5">
            <div className="flex-1 space-y-2">
              <p className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-gold">
                <Sparkles className="size-4" aria-hidden />
                Inscrições abertas
              </p>
              <h2 className="font-display text-2xl sm:text-3xl font-semibold text-white leading-tight">
                Estamos recebendo novos coroinhas!
              </h2>
              <p className="text-white/85 text-sm sm:text-base max-w-md">
                Preencha a ficha online. A coordenação analisa cada inscrição e entra em contato com a família.
              </p>
            </div>
            <Link
              href="/inscricao"
              className="btn-primary shrink-0 text-base px-6 py-3 shadow-gold ring-2 ring-gold/30 hover:scale-[1.02] transition-transform"
            >
              <ClipboardList className="size-5" aria-hidden />
              Inscrever agora
            </Link>
          </div>
        </section>
      )}

      <div className="flex flex-wrap gap-3 justify-center pt-2">
        <Link href="/login" className="btn-primary">
          <LogIn className="size-4" aria-hidden />
          Entrar
        </Link>
        {!carregando && inscricoesAbertas && (
          <Link
            href="/inscricao"
            className="btn-outline border-white/25 bg-white/10 text-white hover:bg-white/15 sm:hidden"
          >
            <ClipboardList className="size-4" aria-hidden />
            Inscrição online
          </Link>
        )}
      </div>
    </div>
  );
}
