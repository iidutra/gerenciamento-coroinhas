"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Calendar, CalendarRange, Download, Pencil, Plus, Shuffle, Trash2 } from "lucide-react";
import { EscalaMesCronologico } from "@/components/EscalaMesCronologico";
import { EscalaRemanejamentoKanban } from "@/components/EscalaRemanejamentoKanban";
import { FuncoesEscalaForm } from "@/components/FuncoesEscalaForm";
import { GruposMensaisPanel } from "@/components/GruposMensaisPanel";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiDownload, apiFetch, apiFetchAll } from "@/lib/api";
import {
  funcoesFromItens,
  funcoesParaPayload,
  funcoesVazias,
} from "@/lib/scheduling";
import {
  agruparEscalasPorDia,
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
  const [exportandoPdf, setExportandoPdf] = useState(false);
  const [excluindoMes, setExcluindoMes] = useState(false);

  function carregarEscalaMensal(ano: number, mes: number) {
    apiFetch<EscalaMensal>(`/escalas/mensal/?ano=${ano}&mes=${mes}`)
      .then(setEscalaMensalView)
      .catch(() => setEscalaMensalView(null));
  }

  const escalasDoMes = useMemo(
    () => filtrarEscalasDoMes(escalas, anoVisualizar, mesVisualizar),
    [escalas, anoVisualizar, mesVisualizar],
  );

  const diasAgrupados = useMemo(
    () => agruparEscalasPorDia(escalasDoMes),
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

  async function exportarPdfMes() {
    setErro("");
    setExportandoPdf(true);
    try {
      await apiDownload(
        `/relatorios/escala-mes?ano=${anoVisualizar}&mes=${mesVisualizar}&formato=pdf`,
        `escala-${anoVisualizar}-${String(mesVisualizar).padStart(2, "0")}.pdf`,
      );
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao exportar PDF");
    } finally {
      setExportandoPdf(false);
    }
  }

  function handleKanbanAtualizado(
    escalaMensal: EscalaMensal,
    escalasAtualizadas: Escala[],
    substituirMes = false,
  ) {
    setEscalaMensalView(escalaMensal);
    setEscalas((prev) => {
      if (substituirMes) {
        const foraMes = prev.filter((e) => {
          const [y, m] = e.data.split("-").map(Number);
          return y !== anoVisualizar || m !== mesVisualizar;
        });
        return [...foraMes, ...escalasAtualizadas];
      }
      const map = new Map(prev.map((e) => [e.id, e]));
      for (const e of escalasAtualizadas) map.set(e.id, e);
      return Array.from(map.values());
    });
  }

  async function excluirEscalaMensal() {
    if (
      !confirm(
        `Excluir toda a escala de ${nomeMes(mesVisualizar)}/${anoVisualizar}? Você poderá gerar uma nova em seguida.`,
      )
    ) {
      return;
    }
    setErro("");
    setExcluindoMes(true);
    try {
      await apiFetch(`/escalas/mensal/?ano=${anoVisualizar}&mes=${mesVisualizar}`, {
        method: "DELETE",
      });
      setEscalaMensalView(null);
      setUltimaEscalaMensal(null);
      load();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao excluir escala do mês");
    } finally {
      setExcluindoMes(false);
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
            {escalaMensalExibir && podeEditar && (
              <button
                type="button"
                onClick={excluirEscalaMensal}
                disabled={excluindoMes}
                className="btn-outline text-sm flex items-center gap-1.5 text-destructive border-destructive/40 hover:bg-destructive/10"
              >
                <Trash2 className="size-4" aria-hidden />
                {excluindoMes ? "Excluindo…" : "Excluir mês"}
              </button>
            )}
            {escalasDoMes.length > 0 && podeEditar && (
              <button
                type="button"
                onClick={exportarPdfMes}
                disabled={exportandoPdf}
                className="btn-outline text-sm flex items-center gap-1.5"
              >
                <Download className="size-4" aria-hidden />
                {exportandoPdf ? "Exportando…" : "PDF do mês"}
              </button>
            )}
            {escalasDoMes.length > 0 && (
              <span className="text-sm text-muted-foreground">
                {escalasDoMes.length} {escalasDoMes.length === 1 ? "celebração" : "celebrações"}
              </span>
            )}
          </div>
        </div>

        {escalaMensalExibir && !podeEditar && (
          <GruposMensaisPanel escalaMensal={escalaMensalExibir} />
        )}

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
        ) : escalaMensalExibir && podeEditar ? (
          <EscalaRemanejamentoKanban
            escalaMensal={escalaMensalExibir}
            escalas={escalasDoMes}
            mes={mesVisualizar}
            ano={anoVisualizar}
            podeEditar={podeEditar}
            coroinhas={coroinhas}
            onAtualizado={handleKanbanAtualizado}
            editandoMembrosId={editandoMembrosId}
            editandoFuncoesId={editandoFuncoesId}
            membrosEdicao={membrosEdicao}
            funcoesEdicao={funcoesEdicao}
            notificandoId={notificandoId}
            excluindoEscalaId={excluindoEscalaId}
            onAbrirEdicaoMembros={abrirEdicaoMembros}
            onAbrirEdicaoFuncoes={abrirEdicaoFuncoes}
            onFecharEdicaoMembros={() => setEditandoMembrosId(null)}
            onFecharEdicaoFuncoes={() => setEditandoFuncoesId(null)}
            onToggleMembro={toggleMembro}
            onSalvarMembros={salvarMembros}
            onSalvarFuncoes={salvarFuncoes}
            onNotificar={notificarEscala}
            onExcluir={excluirEscala}
            onFuncoesChange={setFuncoesEdicao}
          />
        ) : (
          <EscalaMesCronologico
            dias={diasAgrupados}
            mes={mesVisualizar}
            ano={anoVisualizar}
            podeEditar={podeEditar}
            coroinhas={coroinhas}
            editandoMembrosId={editandoMembrosId}
            editandoFuncoesId={editandoFuncoesId}
            membrosEdicao={membrosEdicao}
            funcoesEdicao={funcoesEdicao}
            notificandoId={notificandoId}
            excluindoEscalaId={excluindoEscalaId}
            onAbrirEdicaoMembros={abrirEdicaoMembros}
            onAbrirEdicaoFuncoes={abrirEdicaoFuncoes}
            onFecharEdicaoMembros={() => setEditandoMembrosId(null)}
            onFecharEdicaoFuncoes={() => setEditandoFuncoesId(null)}
            onToggleMembro={toggleMembro}
            onSalvarMembros={salvarMembros}
            onSalvarFuncoes={salvarFuncoes}
            onNotificar={notificarEscala}
            onExcluir={excluirEscala}
            onFuncoesChange={setFuncoesEdicao}
          />
        )}
      </StaffPage>
    </StaffLayout>
  );
}
