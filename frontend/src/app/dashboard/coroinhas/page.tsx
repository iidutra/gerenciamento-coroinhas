"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { ChevronDown, Filter, Plus, Search, Upload, Users } from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { EmptyState } from "@/components/EmptyState";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { StatusBadge } from "@/components/StatusBadge";
import { apiFetch, apiFetchForm, asList, mediaUrl } from "@/lib/api";
import { turmaLabel } from "@/lib/format";
import type { Coroinha } from "@/types";

const TURMAS = [
  { value: "Iniciante", label: "Iniciante" },
  { value: "Intermediario", label: "Intermediário" },
  { value: "Avancado", label: "Avançado" },
];

const STATUS_OPCOES = [
  { value: "EmFormacao", label: "Em formação" },
  { value: "Ativo", label: "Ativo" },
  { value: "Inativo", label: "Inativo" },
];

export default function CoroinhasPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [coroinhas, setCoroinhas] = useState<Coroinha[]>([]);
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [feedback, setFeedback] = useState("");
  const [enviandoFotoId, setEnviandoFotoId] = useState<number | null>(null);
  const [formAberto, setFormAberto] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [nome, setNome] = useState("");
  const [dataNascimento, setDataNascimento] = useState("");
  const [turma, setTurma] = useState("Iniciante");
  const [status, setStatus] = useState("EmFormacao");
  const [escola, setEscola] = useState("");
  const [serie, setSerie] = useState("");
  const [telefone, setTelefone] = useState("");

  function load() {
    return apiFetch<{ results?: Coroinha[] } | Coroinha[]>("/coroinhas/").then((c) =>
      setCoroinhas(asList(c)),
    );
  }

  useEffect(() => {
    if (!ready) return;
    load().finally(() => setLoading(false));
  }, [ready]);

  useEffect(() => {
    if (!feedback) return;
    const t = setTimeout(() => setFeedback(""), 3500);
    return () => clearTimeout(t);
  }, [feedback]);

  const filtrados = useMemo(() => {
    return coroinhas.filter((c) => {
      const matchBusca = c.nome.toLowerCase().includes(busca.toLowerCase());
      const matchStatus = !statusFiltro || c.status === statusFiltro;
      return matchBusca && matchStatus;
    });
  }, [coroinhas, busca, statusFiltro]);

  async function enviarFoto(id: number, file: File) {
    setErro("");
    setEnviandoFotoId(id);
    try {
      const fd = new FormData();
      fd.append("foto", file);
      await apiFetchForm(`/coroinhas/${id}/foto/`, fd);
      await load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao enviar foto.");
    } finally {
      setEnviandoFotoId(null);
    }
  }

  async function cadastrar(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    setSalvando(true);
    try {
      await apiFetch("/coroinhas/", {
        method: "POST",
        body: JSON.stringify({
          nome: nome.trim(),
          data_nascimento: dataNascimento,
          turma,
          status,
          escola: escola.trim(),
          serie: serie.trim(),
          telefone: telefone.trim(),
          batizado: false,
          primeira_eucaristia: false,
          crisma: false,
        }),
      });
      setFeedback("Coroinha cadastrado com sucesso.");
      setNome("");
      setDataNascimento("");
      setTurma("Iniciante");
      setStatus("EmFormacao");
      setEscola("");
      setSerie("");
      setTelefone("");
      setFormAberto(false);
      await load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível cadastrar.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <StaffLayout loading={loading}>
      <StaffPage
        title="Coroinhas"
        description="Cadastro manual e gestão do grupo paroquial."
        onLogout={sair}
      >
        {feedback && (
          <p
            className="mb-4 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200/80 rounded-lg px-4 py-3"
            role="status"
          >
            {feedback}
          </p>
        )}
        {erro && (
          <p
            className="mb-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3"
            role="alert"
          >
            {erro}
          </p>
        )}
        {!podeEditar && <ReadOnlyGestorBanner tipoPerfil={usuario?.tipo_perfil} />}

        {podeEditar && (
          <div className="card-liturgical mb-6 overflow-hidden">
            <button
              type="button"
              onClick={() => setFormAberto((v) => !v)}
              className="w-full flex items-center justify-between gap-3 p-4 sm:p-5 text-left hover:bg-muted/30 transition-colors"
            >
              <span className="inline-flex items-center gap-2 font-display font-semibold text-burgundy">
                <Plus className="size-5" aria-hidden />
                Cadastrar coroinha
              </span>
              <ChevronDown
                className={`size-5 text-muted-foreground transition-transform ${formAberto ? "rotate-180" : ""}`}
                aria-hidden
              />
            </button>
            {formAberto && (
              <form onSubmit={cadastrar} className="px-4 sm:px-5 pb-5 pt-0 border-t border-border space-y-4">
                <p className="text-sm text-muted-foreground pt-4">
                  Cadastro direto pela coordenação. Inscrições online aparecem em{" "}
                  <strong className="font-medium text-foreground">Inscrições</strong> para aprovação.
                </p>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="cad-nome" className="block text-sm font-medium mb-1.5">
                      Nome completo *
                    </label>
                    <input
                      id="cad-nome"
                      value={nome}
                      onChange={(e) => setNome(e.target.value)}
                      className="input-field w-full"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-nasc" className="block text-sm font-medium mb-1.5">
                      Data de nascimento *
                    </label>
                    <input
                      id="cad-nasc"
                      type="date"
                      value={dataNascimento}
                      onChange={(e) => setDataNascimento(e.target.value)}
                      className="input-field w-full"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-turma" className="block text-sm font-medium mb-1.5">
                      Turma
                    </label>
                    <select
                      id="cad-turma"
                      value={turma}
                      onChange={(e) => setTurma(e.target.value)}
                      className="input-field w-full"
                    >
                      {TURMAS.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="cad-status" className="block text-sm font-medium mb-1.5">
                      Status
                    </label>
                    <select
                      id="cad-status"
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      className="input-field w-full"
                    >
                      {STATUS_OPCOES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="cad-escola" className="block text-sm font-medium mb-1.5">
                      Escola
                    </label>
                    <input
                      id="cad-escola"
                      value={escola}
                      onChange={(e) => setEscola(e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-serie" className="block text-sm font-medium mb-1.5">
                      Série
                    </label>
                    <input
                      id="cad-serie"
                      value={serie}
                      onChange={(e) => setSerie(e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label htmlFor="cad-tel" className="block text-sm font-medium mb-1.5">
                      Telefone / WhatsApp
                    </label>
                    <input
                      id="cad-tel"
                      value={telefone}
                      onChange={(e) => setTelefone(e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                </div>
                <button type="submit" disabled={salvando} className="btn-primary">
                  {salvando ? "Salvando…" : "Salvar cadastro"}
                </button>
              </form>
            )}
          </div>
        )}

        <div className="card-liturgical overflow-hidden">
          <div className="px-4 md:px-6 py-4 border-b border-border flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search
                className="absolute left-3 top-1/2 z-10 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
                aria-hidden
              />
              <input
                type="search"
                placeholder="Buscar por nome..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="input-field input-field--icon-left"
              />
            </div>
            <div className="relative sm:w-48">
              <Filter
                className="absolute left-3 top-1/2 z-10 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
                aria-hidden
              />
              <select
                value={statusFiltro}
                onChange={(e) => setStatusFiltro(e.target.value)}
                className="input-field input-field--icon-left appearance-none"
              >
                <option value="">Todos os status</option>
                <option value="Ativo">Ativo</option>
                <option value="EmFormacao">Em formação</option>
                <option value="Inativo">Inativo</option>
              </select>
            </div>
          </div>
          {filtrados.length === 0 ? (
            <EmptyState
              icon={Users}
              title={coroinhas.length === 0 ? "Nenhum coroinha cadastrado" : "Nenhum resultado"}
              description={
                podeEditar
                  ? "Use o formulário acima para cadastrar ou aguarde inscrições online."
                  : "Nenhum coroinha corresponde à busca."
              }
            />
          ) : (
            <table className="table-liturgical">
              <thead>
                <tr>
                  <th>Foto</th>
                  <th>Nome</th>
                  <th>Idade</th>
                  <th>Turma</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((c) => (
                  <tr key={c.id}>
                    <td>
                      {podeEditar ? (
                        <label
                          className={`cursor-pointer inline-flex items-center gap-2 ${enviandoFotoId === c.id ? "opacity-60 pointer-events-none" : ""}`}
                          title="Enviar foto"
                        >
                          <CoroinhaAvatar nome={c.nome} fotoUrl={mediaUrl(c.foto_url)} size="sm" />
                          <Upload className="size-4 text-muted-foreground" aria-hidden />
                          <input
                            type="file"
                            accept="image/*"
                            className="sr-only"
                            disabled={enviandoFotoId === c.id}
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f) enviarFoto(c.id, f);
                              e.target.value = "";
                            }}
                          />
                        </label>
                      ) : (
                        <CoroinhaAvatar nome={c.nome} fotoUrl={mediaUrl(c.foto_url)} size="sm" />
                      )}
                    </td>
                    <td className="font-medium">{c.nome}</td>
                    <td>{c.idade}</td>
                    <td>{turmaLabel(c.turma)}</td>
                    <td>
                      <StatusBadge status={c.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </StaffPage>
    </StaffLayout>
  );
}
