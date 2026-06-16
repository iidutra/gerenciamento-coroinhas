"use client";

import { useEffect, useState } from "react";
import { Check, ClipboardList, Loader2, MessageSquare, Megaphone, X } from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { EmptyState } from "@/components/EmptyState";
import { StaffLayout, useStaffAuth, podeGerenciarCoroinhas, ReadOnlyGestorBanner } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiFetch, asList, mediaUrl } from "@/lib/api";
import { definirInscricoesAbertas, fetchConfigInscricoes } from "@/lib/config-inscricoes";
import type { Inscricao } from "@/types";

type AcaoInscricao = "aprovar" | "rejeitar";

export default function InscricoesPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [inscricoes, setInscricoes] = useState<Inscricao[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState("");
  const [erro, setErro] = useState("");
  const [processandoId, setProcessandoId] = useState<number | null>(null);
  const [modal, setModal] = useState<{ inscricao: Inscricao; acao: AcaoInscricao } | null>(null);
  const [mensagem, setMensagem] = useState("");
  const [notificar, setNotificar] = useState(true);
  const [inscricoesAbertas, setInscricoesAbertas] = useState(false);
  const [controladoPorEnv, setControladoPorEnv] = useState(false);
  const [alternandoInscricoes, setAlternandoInscricoes] = useState(false);

  function loadInscricoes() {
    return apiFetch<{ results?: Inscricao[] } | Inscricao[]>("/inscricoes/?status=Pendente").then((d) =>
      setInscricoes(asList(d)),
    );
  }

  function loadConfig() {
    return fetchConfigInscricoes().then((cfg) => {
      setInscricoesAbertas(cfg.inscricoes_abertas);
      setControladoPorEnv(Boolean(cfg.controlado_por_env));
    });
  }

  function load() {
    setLoading(true);
    Promise.all([loadInscricoes(), loadConfig()]).finally(() => setLoading(false));
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  useEffect(() => {
    if (!feedback) return;
    const t = setTimeout(() => setFeedback(""), 4000);
    return () => clearTimeout(t);
  }, [feedback]);

  function abrirModal(inscricao: Inscricao, acao: AcaoInscricao) {
    setModal({ inscricao, acao });
    setMensagem("");
    setNotificar(true);
  }

  function fecharModal() {
    if (processandoId) return;
    setModal(null);
  }

  async function alternarInscricoes() {
    setErro("");
    setAlternandoInscricoes(true);
    try {
      const cfg = await definirInscricoesAbertas(!inscricoesAbertas);
      setInscricoesAbertas(cfg.inscricoes_abertas);
      setControladoPorEnv(Boolean(cfg.controlado_por_env));
      setFeedback(cfg.detail ?? (cfg.inscricoes_abertas ? "Inscrições abertas na home." : "Inscrições fechadas."));
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível alterar o status.");
    } finally {
      setAlternandoInscricoes(false);
    }
  }

  async function confirmarAcao() {
    if (!modal) return;
    setErro("");
    setProcessandoId(modal.inscricao.id);
    const path =
      modal.acao === "aprovar"
        ? `/inscricoes/${modal.inscricao.id}/aprovar/`
        : `/inscricoes/${modal.inscricao.id}/rejeitar/`;
    try {
      await apiFetch(path, {
        method: "POST",
        body: JSON.stringify({ mensagem, notificar }),
      });
      setFeedback(
        modal.acao === "aprovar"
          ? "Inscrição aprovada. O responsável será avisado."
          : "Inscrição rejeitada. O responsável será avisado.",
      );
      setModal(null);
      load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível concluir a ação.");
    } finally {
      setProcessandoId(null);
    }
  }

  return (
    <StaffLayout loading={loading}>
      <StaffPage
        title="Inscrições pendentes"
        description="Avalie fichas enviadas online, aprove ou rejeite e avise a família."
        onLogout={sair}
      >
        <ReadOnlyGestorBanner tipoPerfil={usuario?.tipo_perfil} />

        {podeEditar && (
          <div
            className={`card-liturgical mb-6 p-5 border-l-4 ${
              inscricoesAbertas ? "border-l-gold bg-gold/5" : "border-l-muted-foreground/30"
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Megaphone className={`size-5 ${inscricoesAbertas ? "text-gold" : "text-muted-foreground"}`} aria-hidden />
                  <h2 className="font-display text-lg font-semibold">Inscrições online</h2>
                  {inscricoesAbertas && (
                    <span className="rounded-full bg-gold/15 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-burgundy">
                      Abertas
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {inscricoesAbertas
                    ? "A página inicial exibe um aviso em destaque e famílias podem enviar a ficha online."
                    : "Ative quando for época de inscrições. A home mostrará o aviso e o formulário público."}
                </p>
                {controladoPorEnv && (
                  <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200/80 rounded-lg px-3 py-2 mt-2">
                    A variável <code className="text-[11px]">INSCRICOES_ABERTAS</code> no servidor também está
                    forçando inscrições abertas.
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={alternarInscricoes}
                disabled={alternandoInscricoes || controladoPorEnv}
                className={inscricoesAbertas ? "btn-outline" : "btn-primary"}
                title={controladoPorEnv ? "Desative INSCRICOES_ABERTAS no servidor para controlar pelo painel" : undefined}
              >
                {alternandoInscricoes ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                ) : inscricoesAbertas ? (
                  "Fechar inscrições"
                ) : (
                  "Abrir inscrições"
                )}
              </button>
            </div>
          </div>
        )}

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

        {inscricoes.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="Nenhuma inscrição pendente"
            description="Quando as inscrições online estiverem abertas, novas fichas aparecerão aqui para avaliação."
          />
        ) : (
          <div className="space-y-4">
            {inscricoes.map((i) => {
              const coroinha = i.dados.coroinha;
              const resp = i.dados.responsavel;
              return (
                <div key={i.id} className="card-liturgical p-5">
                  <div className="flex flex-col lg:flex-row gap-4">
                    <CoroinhaAvatar
                      nome={coroinha?.nome ?? "?"}
                      fotoUrl={mediaUrl(i.foto_url)}
                      size="lg"
                      className="shrink-0"
                    />
                    <div className="flex-1 min-w-0 space-y-2">
                      <p className="font-display text-lg font-semibold">{coroinha?.nome ?? "Sem nome"}</p>
                      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1 text-sm text-muted-foreground">
                        <p>Nasc.: {coroinha?.data_nascimento ?? "—"}</p>
                        <p>Escola: {coroinha?.escola || "—"}</p>
                        <p>Responsável (CPF): {resp?.cpf ?? "—"}</p>
                        <p>Mãe: {resp?.nome_mae || "—"}</p>
                        <p>WhatsApp: {resp?.whatsapp || resp?.telefone_principal || "—"}</p>
                        <p>E-mail: {resp?.email || "—"}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Enviada em {new Date(i.criado_em).toLocaleDateString("pt-BR")}
                      </p>
                    </div>
                    {podeEditar && (
                      <div className="flex flex-col sm:flex-row lg:flex-col gap-2 shrink-0">
                        <button
                          type="button"
                          onClick={() => abrirModal(i, "aprovar")}
                          className="btn-primary text-sm"
                          disabled={processandoId === i.id}
                        >
                          <Check className="size-4" aria-hidden /> Aprovar
                        </button>
                        <button
                          type="button"
                          onClick={() => abrirModal(i, "rejeitar")}
                          className="btn-outline text-sm text-destructive"
                          disabled={processandoId === i.id}
                        >
                          <X className="size-4" aria-hidden /> Rejeitar
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {modal && (
          <div
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-inscricao-titulo"
          >
            <div className="card-liturgical w-full max-w-lg p-6 shadow-elegant">
              <h2 id="modal-inscricao-titulo" className="font-display text-xl font-semibold text-burgundy mb-1">
                {modal.acao === "aprovar" ? "Aprovar inscrição" : "Rejeitar inscrição"}
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                {modal.inscricao.dados.coroinha?.nome ?? "Coroinha"}
              </p>

              <label className="flex items-start gap-2 text-sm mb-4 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={notificar}
                  onChange={(e) => setNotificar(e.target.checked)}
                  className="size-4 mt-0.5 accent-[var(--burgundy)] rounded"
                />
                <span className="inline-flex items-start gap-1.5">
                  <MessageSquare className="size-4 shrink-0 text-burgundy/70 mt-0.5" aria-hidden />
                  Enviar mensagem ao responsável (WhatsApp/e-mail, conforme configurado)
                </span>
              </label>

              <label htmlFor="msg-inscricao" className="block text-sm font-medium mb-1.5">
                Mensagem adicional (opcional)
              </label>
              <textarea
                id="msg-inscricao"
                value={mensagem}
                onChange={(e) => setMensagem(e.target.value)}
                placeholder={
                  modal.acao === "aprovar"
                    ? "Ex.: Bem-vindo! A primeira formação será no dia..."
                    : "Ex.: Neste momento estamos com vagas limitadas..."
                }
                className="input-field w-full min-h-[100px] resize-y mb-4"
              />

              <div className="flex flex-wrap gap-2 justify-end">
                <button type="button" onClick={fecharModal} className="btn-outline" disabled={!!processandoId}>
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={confirmarAcao}
                  disabled={!!processandoId}
                  className={modal.acao === "aprovar" ? "btn-primary" : "btn-primary bg-destructive hover:bg-destructive/90"}
                >
                  {processandoId ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                  ) : modal.acao === "aprovar" ? (
                    "Confirmar aprovação"
                  ) : (
                    "Confirmar rejeição"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </StaffPage>
    </StaffLayout>
  );
}
