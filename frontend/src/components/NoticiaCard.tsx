"use client";

import { useState } from "react";
import { Calendar, ChevronDown, Clock, MapPin, Sparkles, Star } from "lucide-react";
import { noticiaConteudoLegivel, noticiaDataLabel } from "@/lib/format";
import type { Noticia } from "@/types";

interface NoticiaCardProps {
  noticia: Noticia;
  compact?: boolean;
  actions?: React.ReactNode;
  featured?: boolean;
}

const LIMITE_COMPACTO = 140;
const LIMITE_COMPLETO = 220;

export function NoticiaCard({ noticia, compact = false, actions, featured = false }: NoticiaCardProps) {
  const [expandido, setExpandido] = useState(false);
  const conteudo = noticiaConteudoLegivel(noticia.conteudo);
  const limite = compact ? LIMITE_COMPACTO : LIMITE_COMPLETO;
  const conteudoLongo = conteudo.length > limite;
  const conteudoVisivel =
    expandido || !conteudoLongo ? conteudo : `${conteudo.slice(0, limite).trim()}…`;

  const ehEvento = Boolean(noticia.data_evento);

  return (
    <article
      className={`relative overflow-hidden rounded-xl transition-shadow ${
        featured || noticia.destaque
          ? "ring-1 ring-gold/40 shadow-gold bg-gradient-to-br from-gold/8 via-card to-card"
          : "bg-card"
      }`}
    >
      {(featured || noticia.destaque) && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-gold" aria-hidden />
      )}

      <div className="p-4 sm:p-5 md:p-6">
        <div className="flex justify-between gap-4">
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              {noticia.destaque && (
                <span className="inline-flex items-center gap-1 rounded-full bg-gold/15 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-burgundy">
                  <Star className="size-3 text-gold" aria-hidden />
                  Destaque
                </span>
              )}
              {ehEvento && (
                <span className="inline-flex items-center gap-1 rounded-full bg-burgundy/8 px-2.5 py-0.5 text-[11px] font-medium text-burgundy">
                  <Calendar className="size-3 opacity-70" aria-hidden />
                  Evento
                </span>
              )}
              {featured && (
                <span className="inline-flex items-center gap-1 rounded-full bg-burgundy/10 px-2.5 py-0.5 text-[11px] font-medium text-burgundy">
                  <Sparkles className="size-3" aria-hidden />
                  Em evidência
                </span>
              )}
            </div>

            <h3
              className={`font-display font-semibold text-foreground leading-snug ${
                featured ? "text-xl sm:text-2xl" : compact ? "text-base" : "text-lg"
              }`}
            >
              {noticia.titulo}
            </h3>

            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 px-2.5 py-1 text-xs text-foreground">
                <Calendar className="size-3.5 shrink-0 text-burgundy/70" aria-hidden />
                {noticiaDataLabel(noticia)}
              </span>
              {noticia.local_evento && (
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 px-2.5 py-1 text-xs text-foreground">
                  <MapPin className="size-3.5 shrink-0 text-burgundy/70" aria-hidden />
                  {noticia.local_evento}
                </span>
              )}
              {noticia.horario_evento && (
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 px-2.5 py-1 text-xs text-foreground">
                  <Clock className="size-3.5 shrink-0 text-burgundy/70" aria-hidden />
                  {noticia.horario_evento}
                </span>
              )}
            </div>

            {conteudo && (
              <div className="space-y-2">
                <p
                  className={`text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap ${
                    compact && !expandido && conteudoLongo ? "line-clamp-3" : ""
                  }`}
                >
                  {conteudoVisivel}
                </p>
                {conteudoLongo && (
                  <button
                    type="button"
                    onClick={() => setExpandido((v) => !v)}
                    className="inline-flex items-center gap-1 text-xs font-medium text-burgundy hover:underline"
                  >
                    {expandido ? "Ver menos" : "Ler mais"}
                    <ChevronDown
                      className={`size-3.5 transition-transform ${expandido ? "rotate-180" : ""}`}
                      aria-hidden
                    />
                  </button>
                )}
              </div>
            )}

            {noticia.autor_nome && (
              <p className="text-[11px] text-muted-foreground/80 pt-1 border-t border-border/60">
                Publicado por {noticia.autor_nome}
              </p>
            )}
          </div>

          {actions && <div className="shrink-0 pt-1">{actions}</div>}
        </div>
      </div>
    </article>
  );
}
