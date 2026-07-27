"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Calendar, CalendarRange, Clock, Pencil, Plus, Send, Shuffle, Trash2, UserCog, Users } from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { FuncoesEscalaForm } from "@/components/FuncoesEscalaForm";
import { GruposMensaisPanel } from "@/components/GruposMensaisPanel";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiFetch, apiFetchAll, mediaUrl } from "@/lib/api";
import {
  funcoesFromItens,
  funcoesParaPayload,
  funcoesVazias,
} from "@/lib/scheduling";
import {
  agruparEscalasPorHorario,
  filtrarEscalasDoMes,
  nomeMes,
} from "@/lib/escala-layout";
import type { Coroinha, Escala, EscalaMensal, Missa } from "@/types";

const DIAS_SEMANA = [
  "Domingo", "Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado",
];

type TipoRecorrencia = "semanal" | "mensal";

function formatarHorario(horario: string) {
  return horario?.slice(0, 5) ?? "";
}

function labelRecorrencia(m: Missa) {
  if (m.recorrencia) return m.recorrencia;
  if (m.dia_mes) return `Dia ${m.dia_mes} do mês`;
  return m.dia_semana ?? "";
}

function partesData(iso: string) {
  const d = new Date(iso + "T12:00:00");
  return {
    dia: d.getDate(),
    mes: d.toLocaleDateString("pt-BR", { month: "short" }).replace(".", "").toUpperCase(),
    semana: d.toLocaleDateString("pt-BR", { weekday: "long" }),
  };
}

export default function EscalasPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [missas, setMissas] = useState<Missa[]>([]);
  const [escalas, setEscalas] = useState<Escala[]>([]);
  const [coroinhas, setCoroinhas] = useState<Coroinha[]>([]);
  const [data, setData] = useState("");
  const [missaId, setMissaId] = useState("");
  const [modo, setModo] = useState<"SorteioAutomatico" | "SelecaoManual">("SorteioAutomatico");
  const [quantidade, setQuantidade] = useState(3);
  const [selecionados, setSelecionados] = useState<number[]>([]);
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(true);
  const [mostrarFormMissa, setMostrarFormMissa] = useState(false);
  const [editandoMissaId, setEditandoMissaId] = useState<number | null>(null);
  const [nomeMissa, setNomeMissa] = useState("");
  const [tipoRecorrencia, setTipoRecorrencia] = useState<TipoRecorrencia>("semanal");
  const [diaMissa, setDiaMissa] = useState("Domingo");
  const [diaMesMissa, setDiaMesMissa] = useState(13);
  const [horarioMissa, setHorarioMissa] = useState("18:30");
  const [funcoesMontar, setFuncoesMontar] = useState(funcoesVazias);
  const [editandoFuncoesId, setEditandoFuncoesId] = useState<number | null>(null);
  const [funcoesEdicao, setFuncoesEdicao] = useState(funcoesVazias);
  const [editandoMembrosId, setEditandoMembrosId] = useState<number | null>(null);
  const [membrosEdicao, setMembrosEdicao] = useState<number[]>([]);
  const [notificarEscalados, setNotificarEscalados] = useState(true);
  const [notificandoId, setNotificandoId] = useState<number | null>(null);
  const [excluindoEscalaId, setExcluindoEscalaId] = useState<number | null>(null);
  const [mostrarGerarMes, setMostrarGerarMes] = useState(false);
  const [mesGerar, setMesGerar] = useState(new Date().getMonth() + 1);
  const [anoGerar, setAnoGerar] = useState(new Date().getFullYear());
  const [tamanhoGrupo, setTamanhoGrupo] = useState(9);
  const [quantidadeSexta, setQuantidadeSexta] = useState(2);
  const [quantidadeComunidade, setQuantidadeComunidade] = useState(2);
  const [substituirMes, setSubstituirMes] = useState(false);
  const [gerandoMes, setGerandoMes] = useState(false);
  const [ultimaEscalaMensal, setUltimaEscalaMensal] = useState<EscalaMensal | null>(null);
  const [mesVisualizar, setMesVisualizar] = useState(new Date().getMonth() + 1);
  const [anoVisualizar, setAnoVisualizar] = useState(new Date().getFullYear());
  const [escalaMensalView, setEscalaMensalView] = useState<EscalaMensal | null>(null);

  function carregarEscalaMensal(ano: number, mes: number) {
    apiFetch<EscalaMensal>(`/escalas/mensal/?ano=${ano}&mes=${mes}`)
      .then(setEscalaMensalView)
      .catch(() => setEscalaMensalView(null));
  }

  const escalasDoMes = useMemo(
    () => filtrarEscalasDoMes(escalas, anoVisualizar, mesVisualizar),
    [escalas, anoVisualizar, mesVisualizar],
  );

  const secoesEscalas = useMemo(
    () => agruparEscalasPorHorario(escalasDoMes),
    [escalasDoMes],
  );

  const escalaMensalExibir = escalaMensalView ?? (
    ultimaEscalaMensal?.ano === anoVisualizar && ultimaEscalaMensal?.mes === mesVisualizar
      ? ultimaEscalaMensal
      : null
  );

  function load() {
    Promise.all([
      apiFetchAll<Missa>("/missas/"),
      apiFetchAll<Escala>("/escalas/"),
      apiFetchAll<Coroinha>("/coroinhas/"),
    ])
      .then(([m, e, c]) => {
        setMissas(m);
        setEscalas(e);
        setCoroinhas(c);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  useEffect(() => {
    if (ready) carregarEscalaMensal(anoVisualizar, mesVisualizar);
  }, [ready, anoVisualizar, mesVisualizar]);

  function resetFormMissa() {
    setNomeMissa("");
    setTipoRecorrencia("semanal");
    setDiaMissa("Domingo");
    setDiaMesMissa(13);
    setHorarioMissa("18:30");
    setEditandoMissaId(null);
    setMostrarFormMissa(false);
  }

  function abrirEdicao(m: Missa) {
    setEditandoMissaId(m.id);
    setNomeMissa(m.nome);
    setTipoRecorrencia(m.dia_mes ? "mensal" : "semanal");
    setDiaMissa(m.dia_semana ?? "Domingo");
    setDiaMesMissa(m.dia_mes ?? 13);
    setHorarioMissa(formatarHorario(m.horario));
    setMostrarFormMissa(true);
  }

  function payloadMissa() {
    return {
      nome: nomeMissa,
      dia_semana: tipoRecorrencia === "semanal" ? diaMissa : null,
      dia_mes: tipoRecorrencia === "mensal" ? diaMesMissa : null,
      horario: horarioMissa,
      ativa: true,
    };
  }

  async function salvarMissa(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    try {
      if (editandoMissaId) {
        await apiFetch(`/missas/${editandoMissaId}/`, {
          method: "PATCH",
          body: JSON.stringify(payloadMissa()),
        });
      } else {
        await apiFetch("/missas/", {
          method: "POST",
          body: JSON.stringify(payloadMissa()),
        });
      }
      resetFormMissa();
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao salvar missa");
    }
  }

  async function removerMissa(id: number) {
    if (!confirm("Desativar esta missa?")) return;
    setErro("");
    try {
      await apiFetch(`/missas/${id}/`, { method: "PATCH", body: JSON.stringify({ ativa: false }) });
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao remover missa");
    }
  }

  async function montarEscala(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    try {
      await apiFetch("/escalas/montar/", {
        method: "POST",
        body: JSON.stringify({
          data,
          missa_id: Number(missaId),
          modo,
          quantidade,
          coroinha_ids: modo === "SelecaoManual" ? selecionados : undefined,
          funcoes: funcoesParaPayload(funcoesMontar),
          notificar: notificarEscalados,
        }),
      });
      setFuncoesMontar(funcoesVazias());
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao montar escala");
    }
  }

  function toggleCoroinha(id: number) {
    setSelecionados((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  function abrirEdicaoFuncoes(escala: Escala) {
    setEditandoMembrosId(null);
    setEditandoFuncoesId(escala.id);
    setFuncoesEdicao(funcoesFromItens(escala.itens));
  }

  async function salvarFuncoes(escalaId: number) {
    setErro("");
    try {
      await apiFetch(`/escalas/${escalaId}/funcoes/`, {
        method: "PATCH",
        body: JSON.stringify({ funcoes: funcoesParaPayload(funcoesEdicao) }),
      });
      setEditandoFuncoesId(null);
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao salvar funções");
    }
  }

  async function notificarEscala(escalaId: number) {
    setErro("");
    setNotificandoId(escalaId);
    try {
      await apiFetch(`/escalas/${escalaId}/notificar/`, { method: "POST", body: "{}" });
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao notificar escalados");
    } finally {
      setNotificandoId(null);
    }
  }

  function abrirEdicaoMembros(escala: Escala) {
    setEditandoFuncoesId(null);
    setEditandoMembrosId(escala.id);
    setMembrosEdicao(escala.itens.map((i) => i.coroinha_id));
  }

  function toggleMembro(id: number) {
    setMembrosEdicao((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function salvarMembros(escalaId: number) {
    setErro("");
    try {
      await apiFetch(`/escalas/${escalaId}/membros/`, {
        method: "PATCH",
        body: JSON.stringify({ coroinha_ids: membrosEdicao }),
      });
      setEditandoMembrosId(null);
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao salvar coroinhas");
    }
  }

  async function gerarEscalaMes(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    setGerandoMes(true);
    try {
      const resultado = await apiFetch<EscalaMensal>("/escalas/gerar-mes/", {
        method: "POST",
        body: JSON.stringify({
          ano: anoGerar,
          mes: mesGerar,
          tamanho_grupo: tamanhoGrupo,
          quantidade_sexta: quantidadeSexta,
          quantidade_comunidade: quantidadeComunidade,
          substituir: substituirMes,
        }),
      });
      setUltimaEscalaMensal(resultado);
      setMesVisualizar(resultado.mes);
      setAnoVisualizar(resultado.ano);
      setEscalaMensalView(resultado);
      setMostrarGerarMes(false);
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao gerar escala do mês");
    } finally {
      setGerandoMes(false);
    }
  }

  async function excluirEscala(escalaId: number) {
    if (!confirm("Excluir esta escala? Esta ação não pode ser desfeita.")) return;
    setErro("");
    setExcluindoEscalaId(escalaId);
    try {
      await apiFetch(`/escalas/${escalaId}/`, { method: "DELETE" });
      if (editandoFuncoesId === escalaId) setEditandoFuncoesId(null);
      if (editandoMembrosId === escalaId) setEditandoMembrosId(null);
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao excluir escala");
    } finally {
      setExcluindoEscalaId(null);
    }
  }

  const missasAtivas = missas.filter((m) => m.ativa);

  return (
    <StaffLayout loading={loading}>
      <StaffPage title="Escalas" description="Cadastro de missas e montagem das escalas." onLogout={sair}>
        {!podeEditar && <ReadOnlyGestorBanner tipoPerfil={usuario?.tipo_perfil} />}
        {erro && (
          <p className="mb-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3" role="alert">
            {erro}
          </p>
        )}

        {ultimaEscalaMensal && (
          <div className="mb-6 card-liturgical p-4 border border-emerald-500/30 bg-emerald-500/5">
            <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
              Escala de {ultimaEscalaMensal.mes.toString().padStart(2, "0")}/{ultimaEscalaMensal.ano} gerada
              — {ultimaEscalaMensal.total_escalas} celebrações, 4 grupos de {ultimaEscalaMensal.tamanho_grupo} coroinhas.
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Quarta: voluntários (sem nomes). Dia 13: cadastre manualmente quando receber a lista.
            </p>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <div className="card-liturgical p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold flex items-center gap-2">
                <Calendar className="size-5 text-gold" aria-hidden /> Missas cadastradas
              </h2>
              {podeEditar && (
                <button
                  type="button"
                  onClick={() => {
                    if (mostrarFormMissa && !editandoMissaId) {
                      resetFormMissa();
                    } else {
                      resetFormMissa();
                      setMostrarFormMissa(true);
                    }
                  }}
                  className="btn-outline text-sm flex items-center gap-1"
                >
                  <Plus className="size-4" aria-hidden />
                  Adicionar
                </button>
              )}
            </div>

            {podeEditar && mostrarFormMissa && (
              <form onSubmit={salvarMissa} className="mb-4 p-4 rounded-lg border border-border space-y-3">
                <input
                  placeholder="Nome (ex: Domingo 18h30)"
                  value={nomeMissa}
                  onChange={(e) => setNomeMissa(e.target.value)}
                  className="input-field"
                  required
                />
                <select
                  value={tipoRecorrencia}
                  onChange={(e) => setTipoRecorrencia(e.target.value as TipoRecorrencia)}
                  className="input-field"
                >
                  <option value="semanal">Toda semana (dia fixo)</option>
                  <option value="mensal">Todo mês (dia fixo)</option>
                </select>
                {tipoRecorrencia === "semanal" ? (
                  <select value={diaMissa} onChange={(e) => setDiaMissa(e.target.value)} className="input-field">
                    {DIAS_SEMANA.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    min={1}
                    max={31}
                    value={diaMesMissa}
                    onChange={(e) => setDiaMesMissa(Number(e.target.value))}
                    className="input-field"
                    placeholder="Dia do mês (ex: 13)"
                    required
                  />
                )}
                <input
                  type="time"
                  value={horarioMissa}
                  onChange={(e) => setHorarioMissa(e.target.value)}
                  className="input-field"
                  required
                />
                <div className="flex gap-2">
                  <button type="submit" className="btn-primary text-sm">
                    {editandoMissaId ? "Atualizar missa" : "Salvar missa"}
                  </button>
                  <button type="button" onClick={resetFormMissa} className="btn-outline text-sm">
                    Cancelar
                  </button>
                </div>
              </form>
            )}

            <ul className="space-y-2 text-sm">
              {missasAtivas.map((m) => (
                <li key={m.id} className="flex items-center justify-between gap-2 border-b border-border pb-2">
                  <div>
                    <span className="font-medium">{m.nome}</span>
                    <span className="text-muted-foreground block text-xs">
                      {labelRecorrencia(m)} · {formatarHorario(m.horario)}
                    </span>
                  </div>
                  {podeEditar && (
                    <div className="flex gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => abrirEdicao(m)}
                        className="p-1.5 rounded hover:bg-muted text-muted-foreground"
                        title="Editar"
                      >
                        <Pencil className="size-4" aria-hidden />
                      </button>
                      <button
                        type="button"
                        onClick={() => removerMissa(m.id)}
                        className="p-1.5 rounded hover:bg-destructive/10 text-destructive"
                        title="Desativar"
                      >
                        <Trash2 className="size-4" aria-hidden />
                      </button>
                    </div>
                  )}
                </li>
              ))}
              {missasAtivas.length === 0 && (
                <li className="text-muted-foreground py-4 text-center">Nenhuma missa cadastrada.</li>
              )}
            </ul>
          </div>

          {podeEditar ? (
            <div className="space-y-6">
              <form onSubmit={montarEscala} className="card-liturgical p-6 space-y-4">
                <h2 className="font-display text-lg font-semibold flex items-center gap-2">
                  <Shuffle className="size-5 text-gold" aria-hidden /> Nova escala (avulsa)
                </h2>
              <input type="date" value={data} onChange={(e) => setData(e.target.value)} className="input-field" required />
              <select value={missaId} onChange={(e) => setMissaId(e.target.value)} className="input-field" required>
                <option value="">Selecione a missa...</option>
                {missasAtivas.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome} ({labelRecorrencia(m)} · {formatarHorario(m.horario)})
                  </option>
                ))}
              </select>
              <select value={modo} onChange={(e) => setModo(e.target.value as typeof modo)} className="input-field">
                <option value="SorteioAutomatico">Sorteio automático</option>
                <option value="SelecaoManual">Seleção manual</option>
              </select>
              <input
                type="number"
                min={1}
                max={20}
                value={quantidade}
                onChange={(e) => setQuantidade(Number(e.target.value))}
                className="input-field"
                placeholder="Quantidade de coroinhas"
              />
              {modo === "SorteioAutomatico" && (
                <p className="text-xs text-muted-foreground">
                  O sistema distribui de forma equilibrada, evitando repetir o mesmo coroinha.
                </p>
              )}
              {modo === "SelecaoManual" && (
                <div className="max-h-40 overflow-y-auto border border-border rounded-lg p-2 space-y-1">
                  {coroinhas.map((c) => (
                    <label key={c.id} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selecionados.includes(c.id)}
                        onChange={() => toggleCoroinha(c.id)}
                      />
                      {c.nome}
                    </label>
                  ))}
                </div>
              )}
              <FuncoesEscalaForm
                coroinhas={coroinhas}
                valores={funcoesMontar}
                onChange={setFuncoesMontar}
              />
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={notificarEscalados}
                  onChange={(e) => setNotificarEscalados(e.target.checked)}
                />
                Notificar escalados automaticamente (WhatsApp/e-mail)
              </label>
              <button type="submit" className="btn-primary w-full">Sortear coroinhas</button>
              </form>

              <div className="card-liturgical p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-display text-lg font-semibold flex items-center gap-2">
                    <CalendarRange className="size-5 text-gold" aria-hidden /> Gerar escala do mês
                  </h2>
                  <button
                    type="button"
                    onClick={() => setMostrarGerarMes((v) => !v)}
                    className="btn-outline text-sm"
                  >
                    {mostrarGerarMes ? "Fechar" : "Abrir"}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Monta sábado/domingo (grupos rotativos), sextas (1 antigo + 1 novo, sem repetir quem já serve no fim de semana), comunidade e quartas (voluntários).
                  O dia 13 fica de fora — você cadastra depois com a lista manual.
                </p>
                {mostrarGerarMes && (
                  <form onSubmit={gerarEscalaMes} className="space-y-3 border-t border-border pt-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Mês</label>
                        <select
                          value={mesGerar}
                          onChange={(e) => setMesGerar(Number(e.target.value))}
                          className="input-field"
                        >
                          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                            <option key={m} value={m}>
                              {new Date(2000, m - 1, 1).toLocaleDateString("pt-BR", { month: "long" })}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Ano</label>
                        <input
                          type="number"
                          min={2020}
                          max={2100}
                          value={anoGerar}
                          onChange={(e) => setAnoGerar(Number(e.target.value))}
                          className="input-field"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground block mb-1">
                        Tamanho de cada grupo (fim de semana)
                      </label>
                      <input
                        type="number"
                        min={4}
                        max={15}
                        value={tamanhoGrupo}
                        onChange={(e) => setTamanhoGrupo(Number(e.target.value))}
                        className="input-field"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Coroinhas por sexta</label>
                        <input
                          type="number"
                          min={1}
                          max={6}
                          value={quantidadeSexta}
                          onChange={(e) => setQuantidadeSexta(Number(e.target.value))}
                          className="input-field"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Coroinhas comunidade (dom.)</label>
                        <input
                          type="number"
                          min={1}
                          max={6}
                          value={quantidadeComunidade}
                          onChange={(e) => setQuantidadeComunidade(Number(e.target.value))}
                          className="input-field"
                        />
                      </div>
                    </div>
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={substituirMes}
                        onChange={(e) => setSubstituirMes(e.target.checked)}
                      />
                      Substituir escala deste mês se já existir
                    </label>
                    <button type="submit" disabled={gerandoMes} className="btn-primary w-full">
                      {gerandoMes ? "Gerando…" : "Gerar escala do mês"}
                    </button>
                  </form>
                )}
              </div>
            </div>
          ) : (
            <div className="card-liturgical p-6 text-sm text-muted-foreground">
              A montagem de escalas é feita pelo coordenador ou secretário.
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="font-display text-xl font-semibold flex items-center gap-2">
            <Calendar className="size-5 text-gold" aria-hidden />
            Escalas montadas
          </h2>
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={mesVisualizar}
              onChange={(e) => setMesVisualizar(Number(e.target.value))}
              className="input-field text-sm py-1.5 w-auto min-w-[8rem]"
              aria-label="Mês"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>{nomeMes(m)}</option>
              ))}
            </select>
            <input
              type="number"
              min={2020}
              max={2100}
              value={anoVisualizar}
              onChange={(e) => setAnoVisualizar(Number(e.target.value))}
              className="input-field text-sm py-1.5 w-24"
              aria-label="Ano"
            />
            {escalasDoMes.length > 0 && (
              <span className="text-sm text-muted-foreground">
                {escalasDoMes.length} {escalasDoMes.length === 1 ? "celebração" : "celebrações"}
              </span>
            )}
          </div>
        </div>

        {escalaMensalExibir && <GruposMensaisPanel escalaMensal={escalaMensalExibir} />}

        {escalasDoMes.length === 0 ? (
          <div className="card-liturgical p-10 text-center">
            <Calendar className="size-10 text-muted-foreground/40 mx-auto mb-3" aria-hidden />
            <p className="text-muted-foreground">
              Nenhuma escala em {nomeMes(mesVisualizar)} de {anoVisualizar}.
            </p>
            {podeEditar && (
              <p className="text-sm text-muted-foreground/80 mt-1">
                Use “Gerar escala do mês” ou “Nova escala (avulsa)” acima.
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-8">
            {secoesEscalas.map((secao) => (
              <section key={secao.id}>
                <div className="flex items-start gap-2 mb-3 pb-2 border-b border-border">
                  <Clock className="size-4 text-gold mt-0.5 shrink-0" aria-hidden />
                  <div>
                    <h3 className="font-display font-semibold text-burgundy">{secao.titulo}</h3>
                    {secao.subtitulo && (
                      <p className="text-xs text-muted-foreground">{secao.subtitulo}</p>
                    )}
                  </div>
                </div>
                <div className="space-y-3">
                  {secao.escalas.map((e) => {
                    const { dia, mes, semana } = partesData(e.data);
                    const editandoMembros = editandoMembrosId === e.id;
                    const editandoFuncoes = editandoFuncoesId === e.id;
                    const listaNumerada = e.grupo_numero != null && e.itens.length > 0;
                    return (
                      <div key={e.id} className="card-liturgical overflow-hidden">
                        <div className="flex flex-col gap-4 p-4 sm:p-5 sm:flex-row sm:items-start sm:justify-between">
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="shrink-0 w-14 overflow-hidden rounded-xl border border-border bg-card text-center">
                              <div className="bg-card text-burgundy text-[10px] font-semibold leading-none tracking-wide py-1 border-b border-border">
                                {mes}
                              </div>
                              <div className="bg-gradient-gold text-burgundy-deep font-display text-xl font-bold leading-none py-1.5">
                                {dia}
                              </div>
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-display font-semibold text-burgundy capitalize">
                                  {semana}
                                  {e.missa_horario && (
                                    <span className="text-muted-foreground font-normal"> · {formatarHorario(e.missa_horario)}</span>
                                  )}
                                </h4>
                                {e.grupo_numero != null && (
                                  <span className="text-xs rounded-full bg-burgundy/10 text-burgundy px-2 py-0.5 font-semibold">
                                    GRUPO {e.grupo_numero}
                                  </span>
                                )}
                                {e.notificacao_enviada && (
                                  <span className="inline-flex items-center gap-1 text-xs rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-2 py-0.5">
                                    <Send className="size-3" aria-hidden />
                                    Notificado
                                  </span>
                                )}
                                {e.voluntarios && (
                                  <span className="inline-flex items-center gap-1 text-xs rounded-full bg-amber-500/10 text-amber-800 dark:text-amber-300 px-2 py-0.5">
                                    Voluntários
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {e.missa_nome}
                                {e.voluntarios ? " · sem escala fixa" : ` · ${e.itens.length} ${e.itens.length === 1 ? "coroinha" : "coroinhas"}`}
                              </p>
                              {e.observacao && (
                                <p className="text-xs text-muted-foreground italic mt-0.5">{e.observacao}</p>
                              )}
                            </div>
                          </div>

                          {podeEditar && (
                            <div className="flex items-center gap-1.5 shrink-0 self-start">
                              <button
                                type="button"
                                onClick={() => (editandoMembros ? setEditandoMembrosId(null) : abrirEdicaoMembros(e))}
                                aria-pressed={editandoMembros}
                                title="Editar coroinhas"
                                aria-label="Editar coroinhas"
                                className={`p-2 rounded-lg border transition-colors ${
                                  editandoMembros
                                    ? "border-burgundy/40 bg-burgundy/5 text-burgundy"
                                    : "border-border text-muted-foreground hover:bg-muted hover:text-burgundy"
                                }`}
                              >
                                <Users className="size-4" aria-hidden />
                              </button>
                              <button
                                type="button"
                                onClick={() => (editandoFuncoes ? setEditandoFuncoesId(null) : abrirEdicaoFuncoes(e))}
                                aria-pressed={editandoFuncoes}
                                title="Editar funções"
                                aria-label="Editar funções"
                                className={`p-2 rounded-lg border transition-colors ${
                                  editandoFuncoes
                                    ? "border-burgundy/40 bg-burgundy/5 text-burgundy"
                                    : "border-border text-muted-foreground hover:bg-muted hover:text-burgundy"
                                }`}
                              >
                                <UserCog className="size-4" aria-hidden />
                              </button>
                              <button
                                type="button"
                                onClick={() => notificarEscala(e.id)}
                                disabled={notificandoId === e.id}
                                title="Notificar escalados"
                                aria-label="Notificar escalados"
                                className="p-2 rounded-lg border border-border text-muted-foreground hover:bg-muted hover:text-burgundy transition-colors disabled:opacity-50"
                              >
                                <Send className={`size-4 ${notificandoId === e.id ? "animate-pulse" : ""}`} aria-hidden />
                              </button>
                              <button
                                type="button"
                                onClick={() => excluirEscala(e.id)}
                                disabled={excluindoEscalaId === e.id}
                                title="Excluir escala"
                                aria-label="Excluir escala"
                                className="p-2 rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
                              >
                                <Trash2 className="size-4" aria-hidden />
                              </button>
                            </div>
                          )}
                        </div>

                        <div className="px-4 sm:px-5 pb-4">
                          {e.itens.length === 0 ? (
                            <p className="text-sm text-muted-foreground italic">
                              {e.voluntarios ? "Voluntários — nenhum nome na escala automática." : "Nenhum coroinha nesta escala."}
                            </p>
                          ) : listaNumerada ? (
                            <ol className="text-sm space-y-1 list-decimal list-inside columns-1 sm:columns-2">
                              {e.itens.map((i) => (
                                <li key={i.id} className="break-inside-avoid">
                                  {i.coroinha_nome}
                                  {i.funcao_label && (
                                    <span className="text-xs text-gold ml-1">({i.funcao_label})</span>
                                  )}
                                </li>
                              ))}
                            </ol>
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {e.itens.map((i) => (
                                <div
                                  key={i.id}
                                  className="flex items-center gap-2 rounded-full border border-border bg-muted/30 pl-1 pr-3 py-1"
                                  title={i.funcao_label ? `${i.funcao_label}: ${i.coroinha_nome}` : i.coroinha_nome}
                                >
                                  <CoroinhaAvatar
                                    nome={i.coroinha_nome}
                                    fotoUrl={mediaUrl(i.coroinha_foto_url)}
                                    size="sm"
                                  />
                                  <span className="text-sm leading-tight">
                                    {i.funcao_label && (
                                      <span className="block text-[11px] font-semibold text-gold uppercase tracking-wide">
                                        {i.funcao_label}
                                      </span>
                                    )}
                                    <span>{i.coroinha_nome}</span>
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {editandoMembros && (
                          <div className="border-t border-border bg-muted/20 p-4 sm:p-5">
                            <p className="text-sm font-medium mb-2">Selecione os coroinhas desta escala</p>
                            <div className="max-h-56 overflow-y-auto border border-border rounded-lg bg-card p-2 grid sm:grid-cols-2 gap-1">
                              {coroinhas.map((c) => (
                                <label
                                  key={c.id}
                                  className="flex items-center gap-2 text-sm cursor-pointer px-2 py-1.5 rounded hover:bg-muted/50"
                                >
                                  <input
                                    type="checkbox"
                                    className="accent-[var(--burgundy)] size-4"
                                    checked={membrosEdicao.includes(c.id)}
                                    onChange={() => toggleMembro(c.id)}
                                  />
                                  {c.nome}
                                </label>
                              ))}
                            </div>
                            <div className="flex gap-2 mt-3">
                              <button type="button" onClick={() => salvarMembros(e.id)} className="btn-primary text-sm">
                                Salvar coroinhas
                              </button>
                              <button type="button" onClick={() => setEditandoMembrosId(null)} className="btn-outline text-sm">
                                Cancelar
                              </button>
                            </div>
                          </div>
                        )}

                        {editandoFuncoes && (
                          <div className="border-t border-border bg-muted/20 p-4 sm:p-5">
                            <FuncoesEscalaForm
                              coroinhas={coroinhas}
                              valores={funcoesEdicao}
                              onChange={setFuncoesEdicao}
                              compact
                            />
                            <div className="flex gap-2 mt-3">
                              <button type="button" onClick={() => salvarFuncoes(e.id)} className="btn-primary text-sm">
                                Salvar funções
                              </button>
                              <button type="button" onClick={() => setEditandoFuncoesId(null)} className="btn-outline text-sm">
                                Cancelar
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        )}
      </StaffPage>
    </StaffLayout>
  );
}
