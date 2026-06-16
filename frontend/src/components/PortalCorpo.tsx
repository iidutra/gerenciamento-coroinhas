"use client";

import { useEffect, useState } from "react";
import {
  BookOpen,
  Cake,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ExternalLink,
  FileText,
  GraduationCap,
  Newspaper,
  User,
  XCircle,
} from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { LoadingScreen } from "@/components/LoadingScreen";
import { NoticiaCard } from "@/components/NoticiaCard";
import { StatusBadge } from "@/components/StatusBadge";
import { apiFetch, asList, mediaUrl } from "@/lib/api";
import { categoriaDocumentoLabel, turmaLabel } from "@/lib/format";
import { ordenarNoticias } from "@/lib/noticias";
import type { Aniversariante, Coroinha, CoroinhaResumo, Documento, Noticia, Usuario } from "@/types";

interface PortalCorpoProps {
  usuario: Usuario;
  modoPreview?: boolean;
}

export function PortalCorpo({ usuario, modoPreview = false }: PortalCorpoProps) {
  const [filhos, setFilhos] = useState<Coroinha[]>([]);
  const [selecionado, setSelecionado] = useState<number | null>(null);
  const [resumo, setResumo] = useState<CoroinhaResumo | null>(null);
  const [erro, setErro] = useState("");
  const [noticias, setNoticias] = useState<Noticia[]>([]);
  const [aniversariantes, setAniversariantes] = useState<Aniversariante[]>([]);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [loading, setLoading] = useState(true);

  const precisaSeletor =
    modoPreview || (usuario.tipo_perfil === "Pai" && filhos.length > 1);

  useEffect(() => {
    async function load() {
      try {
        if (usuario.tipo_perfil === "Coroinha" && usuario.coroinha_id) {
          setSelecionado(usuario.coroinha_id);
          const r = await apiFetch<CoroinhaResumo>(
            `/portal/coroinhas/${usuario.coroinha_id}/resumo`,
          );
          setResumo(r);
        } else {
          const lista = await apiFetch<Coroinha[]>("/portal/filhos");
          setFilhos(lista);
          if (lista.length === 1) {
            setSelecionado(lista[0].id);
            const r = await apiFetch<CoroinhaResumo>(`/portal/coroinhas/${lista[0].id}/resumo`);
            setResumo(r);
          }
        }
        const n = await apiFetch<{ results?: Noticia[] } | Noticia[]>("/noticias/");
        setNoticias(asList(n));
        const aniv = await apiFetch<Aniversariante[] | { results?: Aniversariante[] }>(
          "/coroinhas/aniversariantes/",
        );
        setAniversariantes(asList(aniv));
        const d = await apiFetch<{ results?: Documento[] } | Documento[]>("/documentos/");
        setDocumentos(asList(d));
      } catch {
        setErro("Erro ao carregar portal.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [usuario]);

  async function selecionarFilho(id: number) {
    setSelecionado(id);
    setLoading(true);
    setErro("");
    try {
      const r = await apiFetch<CoroinhaResumo>(`/portal/coroinhas/${id}/resumo`);
      setResumo(r);
    } catch {
      setErro("Erro ao carregar dados do coroinha.");
      setResumo(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {modoPreview && (
        <p className="mb-4 text-sm text-muted-foreground bg-amber-50 border border-amber-200/80 rounded-lg px-4 py-3">
          Visualização da equipe pastoral — mesma tela que pais e coroinhas veem. Somente leitura.
        </p>
      )}

      {erro && (
        <p className="text-destructive bg-destructive/10 px-4 py-3 rounded-lg mb-4" role="alert">
          {erro}
        </p>
      )}

      {precisaSeletor && (
        <div className="mb-6 card-liturgical p-4">
          <label htmlFor="filho" className="flex items-center gap-2 text-sm font-medium mb-2">
            <User className="size-4 text-gold" aria-hidden />
            {modoPreview ? "Visualizar como família do coroinha" : "Selecione o coroinha"}
          </label>
          <div className="relative max-w-sm">
            <select
              id="filho"
              value={selecionado ?? ""}
              onChange={(e) => selecionarFilho(Number(e.target.value))}
              className="input-field input-field--icon-right appearance-none cursor-pointer"
            >
              <option value="">Selecione...</option>
              {filhos.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.nome}
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
              aria-hidden
            />
          </div>
        </div>
      )}

      {loading && !resumo ? (
        <LoadingScreen message="Carregando dados..." />
      ) : resumo ? (
        <div className="space-y-6">
          <div className="card-liturgical p-6 flex flex-col sm:flex-row sm:items-center gap-4">
            <CoroinhaAvatar nome={resumo.nome} fotoUrl={mediaUrl(resumo.foto_url)} size="lg" />
            <div>
              <h2 className="font-display text-2xl font-semibold">{resumo.nome}</h2>
              <p className="text-muted-foreground mt-1">
                {resumo.idade} anos
                {resumo.escola ? ` · ${resumo.escola}` : ""}
                {resumo.serie ? ` · ${resumo.serie}` : ""}
              </p>
              <div className="mt-2">
                <StatusBadge status={resumo.status} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Escalas", value: resumo.escalas_total, icon: Calendar, accent: "text-burgundy" },
              { label: "Presenças", value: resumo.presencas_total, icon: CheckCircle2, accent: "text-emerald-700" },
              { label: "Faltas", value: resumo.faltas_total, icon: XCircle, accent: "text-destructive" },
              { label: "Formações", value: resumo.formacoes_concluidas, icon: GraduationCap, accent: "text-amber-700" },
            ].map((item) => (
              <div key={item.label} className="card-liturgical p-4 text-center">
                <item.icon className={`size-5 mx-auto mb-2 ${item.accent}`} aria-hidden />
                <p className="stat-value">{item.value}</p>
                <p className="text-sm text-muted-foreground mt-1">{item.label}</p>
              </div>
            ))}
          </div>

          <div className="card-liturgical p-6">
            <div className="flex items-center gap-2 mb-3">
              <Calendar className="size-5 text-gold" aria-hidden />
              <h3 className="font-display text-lg font-semibold">Próxima escala</h3>
            </div>
            <p className="text-muted-foreground text-sm">
              {resumo.proxima_escala
                ? `${new Date(resumo.proxima_escala.data + "T12:00:00").toLocaleDateString("pt-BR")} · ${resumo.proxima_escala.missa}`
                : "Sem escalas futuras no momento."}
            </p>
          </div>

          {resumo.escalas.length > 0 && (
            <div className="card-liturgical p-6">
              <h3 className="font-display text-lg font-semibold mb-3">Minhas escalas</h3>
              <ul className="space-y-2 text-sm">
                {resumo.escalas.map((e, i) => (
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
            </div>
          )}

          {resumo.formacoes.length > 0 && (
            <div className="card-liturgical p-6">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen className="size-5 text-gold" aria-hidden />
                <h3 className="font-display text-lg font-semibold">Formações concluídas</h3>
              </div>
              <ul className="space-y-3">
                {resumo.formacoes.map((f, i) => (
                  <li key={i}>
                    <p className="font-medium">{f.titulo}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(f.data + "T12:00:00").toLocaleDateString("pt-BR")}
                    </p>
                    {f.descricao && <p className="text-sm text-muted-foreground mt-1">{f.descricao}</p>}
                  </li>
                ))}
              </ul>
              {resumo.formacoes_total != null && (
                <p className="text-xs text-muted-foreground mt-4">
                  Total disponíveis: {resumo.formacoes_total} · Concluídas: {resumo.formacoes_concluidas}
                </p>
              )}
            </div>
          )}

          {aniversariantes.length > 0 && (
            <div className="card-liturgical p-6 border-l-4 border-l-gold">
              <div className="flex items-center gap-2 mb-4">
                <Cake className="size-5 text-gold" aria-hidden />
                <h3 className="font-display text-lg font-semibold">Aniversariantes do mês</h3>
              </div>
              <ul className="grid sm:grid-cols-2 gap-3">
                {aniversariantes.map((a) => (
                  <li key={a.id} className="flex items-center gap-3 text-sm">
                    <CoroinhaAvatar nome={a.nome} fotoUrl={mediaUrl(a.foto_url)} size="md" />
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
            </div>
          )}

          {noticias.length > 0 && (
            <div className="card-liturgical p-6">
              <div className="flex items-center gap-2 mb-3">
                <Newspaper className="size-5 text-gold" aria-hidden />
                <h3 className="font-display text-lg font-semibold">Notícias</h3>
              </div>
              <ul className="space-y-3">
                {ordenarNoticias(noticias)
                  .slice(-5)
                  .map((n) => (
                    <li key={n.id}>
                      <NoticiaCard noticia={n} compact />
                    </li>
                  ))}
              </ul>
            </div>
          )}

          {documentos.length > 0 && (
            <div className="card-liturgical p-6">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="size-5 text-gold" aria-hidden />
                <h3 className="font-display text-lg font-semibold">Documentos</h3>
              </div>
              <ul className="space-y-3">
                {documentos.slice(0, 6).map((doc) => (
                  <li key={doc.id}>
                    <p className="text-xs text-muted-foreground">{categoriaDocumentoLabel(doc.categoria)}</p>
                    <p className="font-medium">{doc.titulo}</p>
                    {doc.url && (
                      <a
                        href={doc.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-burgundy mt-1 hover:underline"
                      >
                        Ler conteúdo <ExternalLink className="size-3.5" aria-hidden />
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        !erro &&
        precisaSeletor && (
          <p className="text-muted-foreground text-center py-12">
            Selecione um coroinha acima para ver os detalhes.
          </p>
        )
      )}
    </>
  );
}
