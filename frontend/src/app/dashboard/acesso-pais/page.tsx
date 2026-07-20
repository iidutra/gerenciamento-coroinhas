"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, ShieldQuestion, UserRound, X } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import {
  StaffLayout,
  useStaffAuth,
  podeGerenciarCoroinhas,
  ReadOnlyGestorBanner,
} from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiFetch, asList } from "@/lib/api";
import type { SolicitacaoAcesso } from "@/types";

function formatarData(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("pt-BR");
}

export default function AcessoPaisPage() {
  const { ready, sair, usuario } = useStaffAuth();
  const podeEditar = usuario ? podeGerenciarCoroinhas(usuario.tipo_perfil) : false;
  const [solicitacoes, setSolicitacoes] = useState<SolicitacaoAcesso[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState("");
  const [erro, setErro] = useState("");
  const [processandoId, setProcessandoId] = useState<number | null>(null);
  const [confirmandoRejeicao, setConfirmandoRejeicao] = useState<number | null>(null);

  function load() {
    setLoading(true);
    apiFetch<{ results?: SolicitacaoAcesso[] } | SolicitacaoAcesso[]>(
      "/solicitacoes-acesso/?status=Pendente",
    )
      .then((d) => setSolicitacoes(asList(d)))
      .catch((err) => setErro(err instanceof Error ? err.message : "Erro ao carregar solicitações."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  useEffect(() => {
    if (!feedback) return;
    const t = setTimeout(() => setFeedback(""), 4000);
    return () => clearTimeout(t);
  }, [feedback]);

  async function agir(id: number, acao: "aprovar" | "rejeitar") {
    setErro("");
    setProcessandoId(id);
    try {
      await apiFetch(`/solicitacoes-acesso/${id}/${acao}/`, { method: "POST" });
      setFeedback(
        acao === "aprovar"
          ? "Acesso liberado. O responsável já pode entrar com CPF e senha."
          : "Solicitação recusada.",
      );
      setConfirmandoRejeicao(null);
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
        title="Acesso dos pais"
        description="Pedidos de acesso ao Portal dos Pais feitos pelas famílias. Aprove para liberar a conta."
        onLogout={sair}
      >
        <ReadOnlyGestorBanner tipoPerfil={usuario?.tipo_perfil} />

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

        {solicitacoes.length === 0 ? (
          <EmptyState
            icon={ShieldQuestion}
            title="Nenhuma solicitação pendente"
            description="Quando um pai ou mãe pedir acesso pelo portal, o pedido aparecerá aqui para aprovação."
          />
        ) : (
          <div className="space-y-4">
            {solicitacoes.map((s) => (
              <div key={s.id} className="card-liturgical p-5">
                <div className="flex flex-col lg:flex-row gap-4">
                  <div className="size-12 rounded-full bg-gold/15 grid place-items-center text-burgundy shrink-0">
                    <UserRound className="size-6" aria-hidden />
                  </div>
                  <div className="flex-1 min-w-0 space-y-2">
                    <p className="font-display text-lg font-semibold">{s.nome_responsavel}</p>
                    <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1 text-sm text-muted-foreground">
                      <p>CPF: {s.cpf_mascarado ?? "—"}</p>
                      <p>WhatsApp: {s.whatsapp || "—"}</p>
                      <p>
                        Coroinha: <span className="text-foreground font-medium">{s.coroinha_nome}</span>
                      </p>
                      <p>Nasc. coroinha: {formatarData(s.coroinha_data_nascimento)}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Pedido em {new Date(s.criado_em).toLocaleDateString("pt-BR")}
                    </p>
                  </div>

                  {podeEditar && (
                    <div className="flex flex-col sm:flex-row lg:flex-col gap-2 shrink-0">
                      {confirmandoRejeicao === s.id ? (
                        <>
                          <button
                            type="button"
                            onClick={() => agir(s.id, "rejeitar")}
                            className="btn-primary bg-destructive hover:bg-destructive/90 text-sm"
                            disabled={processandoId === s.id}
                          >
                            {processandoId === s.id ? (
                              <Loader2 className="size-4 animate-spin" aria-hidden />
                            ) : (
                              "Confirmar recusa"
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => setConfirmandoRejeicao(null)}
                            className="btn-outline text-sm"
                            disabled={processandoId === s.id}
                          >
                            Cancelar
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => agir(s.id, "aprovar")}
                            className="btn-primary text-sm"
                            disabled={processandoId === s.id}
                          >
                            {processandoId === s.id ? (
                              <Loader2 className="size-4 animate-spin" aria-hidden />
                            ) : (
                              <>
                                <Check className="size-4" aria-hidden /> Aprovar
                              </>
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => setConfirmandoRejeicao(s.id)}
                            className="btn-outline text-sm text-destructive"
                            disabled={processandoId === s.id}
                          >
                            <X className="size-4" aria-hidden /> Recusar
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </StaffPage>
    </StaffLayout>
  );
}
