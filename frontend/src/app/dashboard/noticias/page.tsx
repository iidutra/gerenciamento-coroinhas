"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Cake,
  ChevronDown,
  Loader2,
  Megaphone,
  Newspaper,
  Plus,
  Search,
  Star,
  Trash2,
} from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { EmptyState } from "@/components/EmptyState";
import { NoticiaCard } from "@/components/NoticiaCard";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiFetch, asList } from "@/lib/api";
import { turmaLabel } from "@/lib/format";
import { agruparNoticiasPorMes, ordenarNoticias } from "@/lib/noticias";
import type { Aniversariante, Noticia } from "@/types";

type FiltroNoticia = "todas" | "destaques" | "eventos";

export default function NoticiasPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [noticias, setNoticias] = useState<Noticia[]>([]);
  const [aniversariantes, setAniversariantes] = useState<Aniversariante[]>([]);
  const [titulo, setTitulo] = useState("");
  const [conteudo, setConteudo] = useState("");
  const [destaque, setDestaque] = useState(false);
  const [loading, setLoading] = useState(true);
  const [publicando, setPublicando] = useState(false);
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState<FiltroNoticia>("todas");
  const [formAberto, setFormAberto] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [removendoId, setRemovendoId] = useState<number | null>(null);

  function load() {
    Promise.all([
      apiFetch<{ results?: Noticia[] } | Noticia[]>("/noticias/"),
      apiFetch<Aniversariante[] | { results?: Aniversariante[] }>("/coroinhas/aniversariantes/"),
    ])
      .then(([n, a]) => {
        setNoticias(asList(n));
        setAniversariantes(asList(a));
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  useEffect(() => {
    if (!feedback) return;
    const t = setTimeout(() => setFeedback(""), 3500);
    return () => clearTimeout(t);
  }, [feedback]);

  const ativas = useMemo(() => noticias.filter((n) => n.ativo), [noticias]);

  const filtradas = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return ordenarNoticias(
      ativas.filter((n) => {
        if (filtro === "destaques" && !n.destaque) return false;
        if (filtro === "eventos" && !n.data_evento) return false;
        if (!q) return true;
        return (
          n.titulo.toLowerCase().includes(q) ||
          n.conteudo.toLowerCase().includes(q) ||
          (n.local_evento?.toLowerCase().includes(q) ?? false)
        );
      }),
    );
  }, [ativas, busca, filtro]);

  const grupos = useMemo(() => agruparNoticiasPorMes(filtradas), [filtradas]);

  const destaquePrincipal = filtro === "todas" && !busca ? filtradas.find((n) => n.destaque) : undefined;
  const listaGrupos = useMemo(() => {
    if (!destaquePrincipal) return grupos;
    return grupos
      .map((g) => ({
        ...g,
        itens: g.itens.filter((n) => n.id !== destaquePrincipal.id),
      }))
      .filter((g) => g.itens.length > 0);
  }, [grupos, destaquePrincipal]);

  const stats = useMemo(
    () => ({
      total: ativas.length,
      destaques: ativas.filter((n) => n.destaque).length,
      eventos: ativas.filter((n) => n.data_evento).length,
    }),
    [ativas],
  );

  async function publicar(ev: FormEvent) {
    ev.preventDefault();
    setPublicando(true);
    try {
      await apiFetch("/noticias/", {
        method: "POST",
        body: JSON.stringify({ titulo, conteudo, destaque, ativo: true }),
      });
      setTitulo("");
      setConteudo("");
      setDestaque(false);
      setFormAberto(false);
      setFeedback("Notícia publicada com sucesso.");
      load();
    } catch {
      setFeedback("Não foi possível publicar. Tente novamente.");
    } finally {
      setPublicando(false);
    }
  }

  async function remover(id: number) {
    if (!window.confirm("Remover esta notícia? Ela deixará de aparecer no portal.")) return;
    setRemovendoId(id);
    try {
      await apiFetch(`/noticias/${id}/`, { method: "PATCH", body: JSON.stringify({ ativo: false }) });
      setFeedback("Notícia removida.");
      load();
    } finally {
      setRemovendoId(null);
    }
  }

  const filtros: { id: FiltroNoticia; label: string; count: number }[] = [
    { id: "todas", label: "Todas", count: stats.total },
    { id: "destaques", label: "Destaques", count: stats.destaques },
    { id: "eventos", label: "Eventos", count: stats.eventos },
  ];

  return (
    <StaffLayout loading={loading}>
      <StaffPage title="Canal de Notícias" description="Comunicados para coroinhas e famílias." onLogout={sair}>
        <ReadOnlyGestorBanner tipoPerfil={usuario?.tipo_perfil} />

        {feedback && (
          <p
            className="mb-4 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200/80 rounded-lg px-4 py-3"
            role="status"
          >
            {feedback}
          </p>
        )}

        <div className="grid grid-cols-3 gap-2 sm:gap-3 mb-6">
          {[
            { label: "Comunicados", value: stats.total, icon: Newspaper },
            { label: "Destaques", value: stats.destaques, icon: Star },
            { label: "Eventos", value: stats.eventos, icon: Megaphone },
          ].map((s) => (
            <div key={s.label} className="card-liturgical p-3 sm:p-4 text-center">
              <s.icon className="size-4 sm:size-5 mx-auto mb-1.5 sm:mb-2 text-burgundy/70" aria-hidden />
              <p className="stat-value text-xl sm:text-2xl">{s.value}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5 leading-tight">{s.label}</p>
            </div>
          ))}
        </div>

        {aniversariantes.length > 0 && (
          <details className="card-liturgical mb-6 border-l-4 border-l-gold group">
            <summary className="flex cursor-pointer list-none items-center gap-2 p-5 font-display text-lg font-semibold [&::-webkit-details-marker]:hidden">
              <Cake className="size-5 text-gold shrink-0" aria-hidden />
              Aniversariantes do mês
              <span className="ml-auto text-xs font-sans font-normal text-muted-foreground">
                {aniversariantes.length} coroinha{aniversariantes.length !== 1 ? "s" : ""}
              </span>
              <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" aria-hidden />
            </summary>
            <ul className="grid sm:grid-cols-2 gap-3 px-5 pb-5 pt-0 border-t border-border/60">
              {aniversariantes.map((a) => (
                <li key={a.id} className="flex items-center gap-3 text-sm pt-4">
                  <CoroinhaAvatar nome={a.nome} fotoUrl={a.foto_url} size="md" />
                  <div>
                    <p className="font-medium">{a.nome}</p>
                    <p className="text-muted-foreground text-xs">
                      {String(a.dia).padStart(2, "0")}/{String(new Date().getMonth() + 1).padStart(2, "0")} ·{" "}
                      {a.idade} anos · {turmaLabel(a.turma)}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </details>
        )}

        <div className="flex flex-col gap-3 mb-4">
          <div className="relative w-full">
            <Search
              className="absolute left-3 top-1/2 z-10 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
              aria-hidden
            />
            <input
              type="search"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar título, texto ou local..."
              className="input-field input-field--icon-left w-full"
              aria-label="Buscar notícias"
            />
          </div>
          <div className="-mx-1 px-1 overflow-x-auto scrollbar-none">
            <div className="inline-flex min-w-full sm:min-w-0 rounded-lg border border-border p-1 bg-muted/30">
              {filtros.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFiltro(f.id)}
                  className={`px-3 py-2 sm:py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                    filtro === f.id
                      ? "bg-card text-burgundy shadow-soft"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {f.label}
                  <span className="ml-1 opacity-60">({f.count})</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {podeEditar && (
          <div className="card-liturgical mb-8 overflow-hidden">
            <button
              type="button"
              onClick={() => setFormAberto((v) => !v)}
              className="w-full flex items-center justify-between gap-3 p-5 text-left hover:bg-muted/30 transition-colors"
            >
              <span className="flex items-center gap-2 font-display text-lg font-semibold">
                <Plus className="size-5 text-gold" aria-hidden />
                Nova notícia
              </span>
              <ChevronDown
                className={`size-5 text-muted-foreground transition-transform ${formAberto ? "rotate-180" : ""}`}
                aria-hidden
              />
            </button>
            {formAberto && (
              <form onSubmit={publicar} className="px-5 pb-5 pt-0 space-y-4 border-t border-border">
                <div className="pt-4 space-y-4">
                  <div>
                    <label htmlFor="noticia-titulo" className="block text-sm font-medium mb-1.5">
                      Título
                    </label>
                    <input
                      id="noticia-titulo"
                      placeholder="Ex.: Retiro dos coroinhas — março"
                      value={titulo}
                      onChange={(e) => setTitulo(e.target.value)}
                      className="input-field w-full"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="noticia-conteudo" className="block text-sm font-medium mb-1.5">
                      Conteúdo
                    </label>
                    <textarea
                      id="noticia-conteudo"
                      placeholder="Descreva o comunicado para famílias e coroinhas..."
                      value={conteudo}
                      onChange={(e) => setConteudo(e.target.value)}
                      className="input-field w-full min-h-[120px] resize-y"
                      required
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={destaque}
                      onChange={(e) => setDestaque(e.target.checked)}
                      className="size-4 accent-[var(--burgundy)] rounded"
                    />
                    <Star className="size-4 text-gold" aria-hidden />
                    Destacar no topo do portal
                  </label>
                  <button type="submit" disabled={publicando} className="btn-primary w-fit gap-2">
                    {publicando ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
                    Publicar
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {filtradas.length === 0 ? (
          <div className="card-liturgical">
            <EmptyState
              icon={Newspaper}
              title={busca || filtro !== "todas" ? "Nenhum resultado" : "Nenhuma notícia ainda"}
              description={
                busca || filtro !== "todas"
                  ? "Tente outro termo ou limpe os filtros."
                  : "Publique o primeiro comunicado para as famílias."
              }
            />
          </div>
        ) : (
          <div className="space-y-8">
            {destaquePrincipal && (
              <section aria-label="Comunicado em destaque">
                <NoticiaCard
                  noticia={destaquePrincipal}
                  featured
                  actions={
                    podeEditar ? (
                      <button
                        type="button"
                        onClick={() => remover(destaquePrincipal.id)}
                        disabled={removendoId === destaquePrincipal.id}
                        className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
                        aria-label="Remover notícia"
                      >
                        {removendoId === destaquePrincipal.id ? (
                          <Loader2 className="size-4 animate-spin" aria-hidden />
                        ) : (
                          <Trash2 className="size-4" />
                        )}
                      </button>
                    ) : undefined
                  }
                />
              </section>
            )}

            {listaGrupos.map(({ mes, itens }) => (
              <section key={mes}>
                <h2 className="font-display text-base font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                  <span className="h-px flex-1 bg-border" aria-hidden />
                  {mes}
                  <span className="h-px flex-1 bg-border" aria-hidden />
                </h2>
                <ul className="space-y-3">
                  {itens.map((n) => (
                    <li key={n.id} className="card-liturgical p-1">
                      <NoticiaCard
                        noticia={n}
                        actions={
                          podeEditar ? (
                            <button
                              type="button"
                              onClick={() => remover(n.id)}
                              disabled={removendoId === n.id}
                              className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
                              aria-label="Remover notícia"
                            >
                              {removendoId === n.id ? (
                                <Loader2 className="size-4 animate-spin" aria-hidden />
                              ) : (
                                <Trash2 className="size-4" />
                              )}
                            </button>
                          ) : undefined
                        }
                      />
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}
      </StaffPage>
    </StaffLayout>
  );
}
