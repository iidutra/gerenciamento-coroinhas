"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { ChevronDown, Filter, Pencil, Plus, Search, Trash2, Users, X } from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { EmptyState } from "@/components/EmptyState";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { StatusBadge } from "@/components/StatusBadge";
import { apiFetch, apiFetchForm, asList, mediaUrl } from "@/lib/api";
import { etapaCatequeseLabel, turmaLabel } from "@/lib/format";
import type { Coroinha, EtapaCatequese } from "@/types";

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

const ETAPAS_CATEQUESE: { value: Exclude<EtapaCatequese, "">; label: string }[] = [
  { value: "PreEucaristia", label: "Pré-Eucaristia" },
  { value: "PrimeiraEucaristia", label: "Primeira Eucaristia" },
  { value: "Crisma", label: "Crisma" },
];

type FormState = {
  nome: string;
  dataNascimento: string;
  enderecoTxt: string;
  nomePai: string;
  telefonePai: string;
  nomeMae: string;
  telefoneMae: string;
  fazCatequese: boolean;
  etapaCatequese: EtapaCatequese;
  fazIam: boolean;
  turma: string;
  status: string;
};

const FORM_VAZIO: FormState = {
  nome: "",
  dataNascimento: "",
  enderecoTxt: "",
  nomePai: "",
  telefonePai: "",
  nomeMae: "",
  telefoneMae: "",
  fazCatequese: false,
  etapaCatequese: "",
  fazIam: false,
  turma: "Iniciante",
  status: "EmFormacao",
};

function calcularIdade(iso: string): number | null {
  if (!iso) return null;
  const nasc = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(nasc.getTime())) return null;
  const hoje = new Date();
  let anos = hoje.getFullYear() - nasc.getFullYear();
  const m = hoje.getMonth() - nasc.getMonth();
  if (m < 0 || (m === 0 && hoje.getDate() < nasc.getDate())) anos -= 1;
  return anos >= 0 ? anos : null;
}

export default function CoroinhasPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [coroinhas, setCoroinhas] = useState<Coroinha[]>([]);
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [feedback, setFeedback] = useState("");

  const [formAberto, setFormAberto] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(FORM_VAZIO);
  const [foto, setFoto] = useState<File | null>(null);
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);

  function setCampo<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

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

  function limparFoto() {
    setFoto(null);
    if (fotoPreview) URL.revokeObjectURL(fotoPreview);
    setFotoPreview(null);
  }

  function abrirNovo() {
    setEditId(null);
    setForm(FORM_VAZIO);
    limparFoto();
    setErro("");
    setFormAberto(true);
  }

  function abrirEdicao(c: Coroinha) {
    setEditId(c.id);
    setForm({
      nome: c.nome,
      dataNascimento: c.data_nascimento,
      enderecoTxt: c.endereco ?? "",
      nomePai: c.nome_pai ?? "",
      telefonePai: c.telefone_pai ?? "",
      nomeMae: c.nome_mae ?? "",
      telefoneMae: c.telefone_mae ?? "",
      fazCatequese: Boolean(c.faz_catequese),
      etapaCatequese: (c.etapa_catequese as EtapaCatequese) ?? "",
      fazIam: Boolean(c.faz_iam),
      turma: c.turma || "Iniciante",
      status: c.status || "EmFormacao",
    });
    limparFoto();
    setErro("");
    setFormAberto(true);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function fecharForm() {
    setFormAberto(false);
    setEditId(null);
    setForm(FORM_VAZIO);
    limparFoto();
  }

  function selecionarFoto(file: File | undefined) {
    if (!file) {
      limparFoto();
      return;
    }
    if (fotoPreview) URL.revokeObjectURL(fotoPreview);
    setFoto(file);
    setFotoPreview(URL.createObjectURL(file));
  }

  async function salvar(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    setSalvando(true);

    const dados: Record<string, unknown> = {
      nome: form.nome.trim(),
      data_nascimento: form.dataNascimento,
      endereco: form.enderecoTxt.trim(),
      nome_pai: form.nomePai.trim(),
      telefone_pai: form.telefonePai.trim(),
      nome_mae: form.nomeMae.trim(),
      telefone_mae: form.telefoneMae.trim(),
      faz_catequese: form.fazCatequese,
      etapa_catequese: form.fazCatequese ? form.etapaCatequese : "",
      faz_iam: form.fazIam,
    };
    if (editId) {
      dados.turma = form.turma;
      dados.status = form.status;
    }

    const path = editId ? `/coroinhas/${editId}/` : "/coroinhas/";
    const method = editId ? "PATCH" : "POST";

    try {
      if (foto) {
        const fd = new FormData();
        Object.entries(dados).forEach(([k, v]) => fd.append(k, String(v)));
        fd.append("foto", foto);
        await apiFetchForm(path, fd, { method });
      } else {
        await apiFetch(path, { method, body: JSON.stringify(dados) });
      }
      setFeedback(editId ? "Coroinha atualizado com sucesso." : "Coroinha cadastrado com sucesso.");
      fecharForm();
      await load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível salvar.");
    } finally {
      setSalvando(false);
    }
  }

  async function excluir(c: Coroinha) {
    if (!window.confirm(`Excluir ${c.nome}? Esta ação não pode ser desfeita.`)) return;
    setErro("");
    setExcluindoId(c.id);
    try {
      await apiFetch(`/coroinhas/${c.id}/`, { method: "DELETE" });
      if (editId === c.id) fecharForm();
      setFeedback("Coroinha excluído.");
      await load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível excluir.");
    } finally {
      setExcluindoId(null);
    }
  }

  const idadePreview = calcularIdade(form.dataNascimento);

  return (
    <StaffLayout loading={loading}>
      <StaffPage
        title="Coroinhas"
        description="Cadastro, edição e gestão do grupo paroquial."
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
              onClick={() => (formAberto ? fecharForm() : abrirNovo())}
              className="w-full flex items-center justify-between gap-3 p-4 sm:p-5 text-left hover:bg-muted/30 transition-colors"
            >
              <span className="inline-flex items-center gap-2 font-display font-semibold text-burgundy">
                {editId ? <Pencil className="size-5" aria-hidden /> : <Plus className="size-5" aria-hidden />}
                {editId ? "Editar coroinha" : "Cadastrar coroinha"}
              </span>
              <ChevronDown
                className={`size-5 text-muted-foreground transition-transform ${formAberto ? "rotate-180" : ""}`}
                aria-hidden
              />
            </button>
            {formAberto && (
              <form onSubmit={salvar} className="px-4 sm:px-5 pb-5 pt-0 border-t border-border space-y-5">
                <p className="text-sm text-muted-foreground pt-4">
                  {editId
                    ? "Atualize os dados do coroinha."
                    : "Cadastro direto pela coordenação. Inscrições online aparecem em Inscrições para aprovação."}
                </p>

                {/* Foto opcional */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <CoroinhaAvatar
                    nome={form.nome || "Coroinha"}
                    fotoUrl={
                      fotoPreview ??
                      (editId ? mediaUrl(coroinhas.find((c) => c.id === editId)?.foto_url) : null)
                    }
                    size="lg"
                  />
                  <div className="flex-1">
                    <label htmlFor="cad-foto" className="block text-sm font-medium mb-1.5">
                      Foto do coroinha (opcional)
                    </label>
                    <input
                      id="cad-foto"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={(e) => selecionarFoto(e.target.files?.[0])}
                      className="input-field file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-1.5 file:text-sm"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Usada como avatar nas escalas. Sem foto, mostramos um avatar padrão.
                    </p>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label htmlFor="cad-nome" className="block text-sm font-medium mb-1.5">
                      Nome completo *
                    </label>
                    <input
                      id="cad-nome"
                      value={form.nome}
                      onChange={(e) => setCampo("nome", e.target.value)}
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
                      value={form.dataNascimento}
                      onChange={(e) => setCampo("dataNascimento", e.target.value)}
                      className="input-field w-full"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-idade" className="block text-sm font-medium mb-1.5">
                      Idade
                    </label>
                    <input
                      id="cad-idade"
                      value={idadePreview != null ? `${idadePreview} anos` : ""}
                      readOnly
                      placeholder="Calculada pela data"
                      className="input-field w-full bg-muted/40 text-muted-foreground"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label htmlFor="cad-endereco" className="block text-sm font-medium mb-1.5">
                      Endereço
                    </label>
                    <input
                      id="cad-endereco"
                      value={form.enderecoTxt}
                      onChange={(e) => setCampo("enderecoTxt", e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-nome-pai" className="block text-sm font-medium mb-1.5">
                      Nome do pai
                    </label>
                    <input
                      id="cad-nome-pai"
                      value={form.nomePai}
                      onChange={(e) => setCampo("nomePai", e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-tel-pai" className="block text-sm font-medium mb-1.5">
                      Telefone do pai
                    </label>
                    <input
                      id="cad-tel-pai"
                      value={form.telefonePai}
                      onChange={(e) => setCampo("telefonePai", e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-nome-mae" className="block text-sm font-medium mb-1.5">
                      Nome da mãe
                    </label>
                    <input
                      id="cad-nome-mae"
                      value={form.nomeMae}
                      onChange={(e) => setCampo("nomeMae", e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="cad-tel-mae" className="block text-sm font-medium mb-1.5">
                      Telefone da mãe
                    </label>
                    <input
                      id="cad-tel-mae"
                      value={form.telefoneMae}
                      onChange={(e) => setCampo("telefoneMae", e.target.value)}
                      className="input-field w-full"
                    />
                  </div>
                </div>

                {/* Catequese */}
                <fieldset className="rounded-lg border border-border p-4">
                  <legend className="px-1 text-sm font-medium">Está fazendo catequese?</legend>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_catequese"
                        checked={form.fazCatequese}
                        onChange={() => setCampo("fazCatequese", true)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Sim
                    </label>
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_catequese"
                        checked={!form.fazCatequese}
                        onChange={() => {
                          setCampo("fazCatequese", false);
                          setCampo("etapaCatequese", "");
                        }}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Não
                    </label>
                  </div>
                  {form.fazCatequese && (
                    <div className="mt-3 flex flex-wrap gap-3 text-sm">
                      {ETAPAS_CATEQUESE.map((etapa) => (
                        <label
                          key={etapa.value}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-secondary cursor-pointer transition-colors"
                        >
                          <input
                            type="radio"
                            name="etapa_catequese"
                            checked={form.etapaCatequese === etapa.value}
                            onChange={() => setCampo("etapaCatequese", etapa.value)}
                            className="accent-[var(--burgundy)] size-4"
                          />
                          {etapa.label}
                        </label>
                      ))}
                    </div>
                  )}
                </fieldset>

                {/* IAM */}
                <fieldset className="rounded-lg border border-border p-4">
                  <legend className="px-1 text-sm font-medium">Faz parte da IAM?</legend>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_iam"
                        checked={form.fazIam}
                        onChange={() => setCampo("fazIam", true)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Sim
                    </label>
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_iam"
                        checked={!form.fazIam}
                        onChange={() => setCampo("fazIam", false)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Não
                    </label>
                  </div>
                </fieldset>

                {/* turma / status (apenas na edição) */}
                {editId && (
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="cad-turma" className="block text-sm font-medium mb-1.5">
                        Turma
                      </label>
                      <select
                        id="cad-turma"
                        value={form.turma}
                        onChange={(e) => setCampo("turma", e.target.value)}
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
                        value={form.status}
                        onChange={(e) => setCampo("status", e.target.value)}
                        className="input-field w-full"
                      >
                        {STATUS_OPCOES.map((s) => (
                          <option key={s.value} value={s.value}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                  <button type="submit" disabled={salvando} className="btn-primary">
                    {salvando ? "Salvando…" : editId ? "Salvar alterações" : "Salvar cadastro"}
                  </button>
                  <button type="button" onClick={fecharForm} className="btn-outline inline-flex gap-2">
                    <X className="size-4" aria-hidden />
                    Cancelar
                  </button>
                </div>
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
                  <th>Catequese</th>
                  <th>IAM</th>
                  <th>Turma</th>
                  <th>Status</th>
                  {podeEditar && <th className="text-right">Ações</th>}
                </tr>
              </thead>
              <tbody>
                {filtrados.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <CoroinhaAvatar nome={c.nome} fotoUrl={mediaUrl(c.foto_url)} size="sm" />
                    </td>
                    <td className="font-medium">{c.nome}</td>
                    <td>{c.idade}</td>
                    <td>
                      {c.faz_catequese
                        ? c.etapa_catequese
                          ? etapaCatequeseLabel(c.etapa_catequese)
                          : "Sim"
                        : "—"}
                    </td>
                    <td>{c.faz_iam ? "Sim" : "—"}</td>
                    <td>{turmaLabel(c.turma)}</td>
                    <td>
                      <StatusBadge status={c.status} />
                    </td>
                    {podeEditar && (
                      <td>
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => abrirEdicao(c)}
                            className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-burgundy transition-colors"
                            title="Editar"
                            aria-label={`Editar ${c.nome}`}
                          >
                            <Pencil className="size-4" aria-hidden />
                          </button>
                          <button
                            type="button"
                            onClick={() => excluir(c)}
                            disabled={excluindoId === c.id}
                            className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50"
                            title="Excluir"
                            aria-label={`Excluir ${c.nome}`}
                          >
                            <Trash2 className="size-4" aria-hidden />
                          </button>
                        </div>
                      </td>
                    )}
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
