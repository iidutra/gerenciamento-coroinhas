"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2 } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { PainelCoroinhasRemanejamento } from "@/components/PainelCoroinhasRemanejamento";
import { EscalaMesCronologico } from "@/components/EscalaMesCronologico";
import { apiFetch } from "@/lib/api";
import { agruparEscalasPorDia, nomeMes } from "@/lib/escala-layout";
import {
  kanbanDragId,
  kanbanDropId,
  destinoAceitaTransferenciaDoGrupo,
  parseKanbanDragId,
  parseKanbanDropId,
  type KanbanDragItem,
  type KanbanDropTarget,
} from "@/lib/escala-kanban";
import type { FuncaoEscala } from "@/lib/scheduling";
import type { Coroinha, Escala, EscalaMensal } from "@/types";

function DraggableCoroinhaCard({ item, compact }: { item: KanbanDragItem; compact?: boolean }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: kanbanDragId(item),
    data: item,
  });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), opacity: isDragging ? 0.45 : 1 }}
      className={`flex items-center gap-2 rounded-lg border border-border bg-card px-2.5 py-2 text-sm shadow-sm ${
        compact ? "py-1.5" : ""
      }`}
    >
      <button
        type="button"
        className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-burgundy touch-none"
        aria-label={`Arrastar ${item.coroinhaNome}`}
        {...listeners}
        {...attributes}
      >
        <GripVertical className="size-4" aria-hidden />
      </button>
      <span className="truncate">{item.coroinhaNome}</span>
    </div>
  );
}

function GrupoColumn({
  numero,
  count,
  children,
}: {
  numero: number;
  count: number;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: kanbanDropId({ kind: "grupo", numero }) });

  return (
    <div
      ref={setNodeRef}
      className={`rounded-xl border min-h-[180px] flex flex-col ${
        isOver ? "border-burgundy bg-burgundy/5 ring-2 ring-burgundy/20" : "border-border bg-muted/10"
      }`}
    >
      <div className="px-3 py-2 border-b border-border bg-burgundy/5">
        <h3 className="font-display font-semibold text-burgundy text-sm uppercase tracking-wide">
          Grupo {numero}
        </h3>
        <p className="text-[10px] text-muted-foreground">{count} coroinhas</p>
      </div>
      <div className="p-2 space-y-2 flex-1">{children}</div>
    </div>
  );
}

function RemoverZone() {
  const { setNodeRef, isOver } = useDroppable({ id: kanbanDropId({ kind: "remover" }) });

  return (
    <div
      ref={setNodeRef}
      className={`rounded-xl border-2 border-dashed p-4 flex items-center justify-center gap-2 min-h-[72px] transition-colors ${
        isOver
          ? "border-destructive bg-destructive/10 text-destructive"
          : "border-border text-muted-foreground"
      }`}
    >
      <Trash2 className="size-4" aria-hidden />
      <span className="text-sm font-medium">Remover do grupo ou da celebração</span>
    </div>
  );
}

interface EscalaRemanejamentoKanbanProps {
  escalaMensal: EscalaMensal;
  escalas: Escala[];
  mes: number;
  ano: number;
  podeEditar: boolean;
  coroinhas: Coroinha[];
  onAtualizado: (escalaMensal: EscalaMensal, escalas: Escala[], substituirMes?: boolean) => void;
  editandoMembrosId: number | null;
  editandoFuncoesId: number | null;
  membrosEdicao: number[];
  funcoesEdicao: Record<FuncaoEscala, number | "">;
  notificandoId: number | null;
  excluindoEscalaId: number | null;
  onAbrirEdicaoMembros: (escala: Escala) => void;
  onAbrirEdicaoFuncoes: (escala: Escala) => void;
  onFecharEdicaoMembros: () => void;
  onFecharEdicaoFuncoes: () => void;
  onToggleMembro: (id: number) => void;
  onSalvarMembros: (escalaId: number) => void;
  onSalvarFuncoes: (escalaId: number) => void;
  onNotificar: (escalaId: number) => void;
  onExcluir: (escalaId: number) => void;
  onFuncoesChange: (valores: Record<FuncaoEscala, number | "">) => void;
}

export function EscalaRemanejamentoKanban({
  escalaMensal,
  escalas,
  mes,
  ano,
  podeEditar,
  coroinhas,
  onAtualizado,
  ...cronologicoProps
}: EscalaRemanejamentoKanbanProps) {
  const [activeItem, setActiveItem] = useState<KanbanDragItem | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const gruposOrdenados = useMemo(
    () => escalaMensal.grupos.slice().sort((a, b) => a.numero - b.numero),
    [escalaMensal.grupos],
  );

  const diasAgrupados = useMemo(() => agruparEscalasPorDia(escalas), [escalas]);

  const itensGrupo = useCallback(
    (numero: number): KanbanDragItem[] => {
      const grupo = gruposOrdenados.find((g) => g.numero === numero);
      if (!grupo) return [];
      return grupo.membros
        .slice()
        .sort((a, b) => a.ordem - b.ordem)
        .map((m) => ({
          coroinhaId: m.coroinha_id,
          coroinhaNome: m.coroinha_nome,
          source: { kind: "grupo" as const, numero },
        }));
    },
    [gruposOrdenados],
  );

  async function executarDrop(item: KanbanDragItem, alvo: KanbanDropTarget) {
    setErro("");
    setSalvando(true);
    try {
      if (alvo.kind === "grupo") {
        const res = await apiFetch<{ escala_mensal: EscalaMensal; escalas: Escala[] }>(
          "/escalas/mensal/remanejar-grupo/",
          {
            method: "PATCH",
            body: JSON.stringify({
              ano,
              mes,
              coroinha_id: item.coroinhaId,
              grupo_destino: alvo.numero,
            }),
          },
        );
        onAtualizado(res.escala_mensal, res.escalas, true);
        return;
      }

      if (alvo.kind === "remover") {
        if (item.source.kind === "grupo") {
          const res = await apiFetch<{ escala_mensal: EscalaMensal; escalas: Escala[] }>(
            "/escalas/mensal/remover-grupo/",
            {
              method: "PATCH",
              body: JSON.stringify({
                ano,
                mes,
                coroinha_id: item.coroinhaId,
              }),
            },
          );
          onAtualizado(res.escala_mensal, res.escalas, true);
          return;
        }

        const origemId = item.source.kind === "escala" ? item.source.escalaId : null;
        if (!origemId) {
          throw new Error("Não foi possível identificar a celebração de origem.");
        }
        const res = await apiFetch<{ origem: Escala }>(`/escalas/${origemId}/mover-coroinha/`, {
          method: "PATCH",
          body: JSON.stringify({ coroinha_id: item.coroinhaId, escala_destino_id: null }),
        });
        onAtualizado(escalaMensal, [res.origem]);
        return;
      }

      const origemId = item.source.kind === "escala" ? item.source.escalaId : null;

      if (!origemId && item.source.kind === "grupo" && alvo.kind === "escala") {
        const destino = escalas.find((e) => e.id === alvo.escalaId);
        if (!destino) return;

        if (destinoAceitaTransferenciaDoGrupo(destino.missa_tipo_slot)) {
          const res = await apiFetch<{ origem: Escala; destino: Escala }>(
            "/escalas/mensal/transferir-celebracao/",
            {
              method: "PATCH",
              body: JSON.stringify({
                ano,
                mes,
                coroinha_id: item.coroinhaId,
                escala_destino_id: destino.id,
                grupo_numero: item.source.numero,
              }),
            },
          );
          onAtualizado(escalaMensal, [res.origem, res.destino]);
          return;
        }

        const ids = [...destino.itens.map((i) => i.coroinha_id), item.coroinhaId];
        const atualizada = await apiFetch<Escala>(`/escalas/${destino.id}/membros/`, {
          method: "PATCH",
          body: JSON.stringify({ coroinha_ids: ids }),
        });
        onAtualizado(escalaMensal, [atualizada]);
        return;
      }

      if (!origemId) {
        throw new Error("Não foi possível identificar a celebração de origem.");
      }

      const res = await apiFetch<{ origem: Escala; destino?: Escala }>(
        `/escalas/${origemId}/mover-coroinha/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            coroinha_id: item.coroinhaId,
            escala_destino_id: alvo.escalaId,
          }),
        },
      );
      onAtualizado(escalaMensal, res.destino ? [res.origem, res.destino] : [res.origem]);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao remanejar");
    } finally {
      setSalvando(false);
    }
  }

  function handleDragStart(event: DragStartEvent) {
    const parsed = parseKanbanDragId(String(event.active.id), escalaMensal.grupos, escalas);
    if (parsed) setActiveItem(parsed);
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveItem(null);
    const alvo = event.over ? parseKanbanDropId(String(event.over.id)) : null;
    const item =
      (event.active.data.current as KanbanDragItem | undefined) ??
      parseKanbanDragId(String(event.active.id), escalaMensal.grupos, escalas);
    if (!item || !alvo || !podeEditar) return;

    if (item.source.kind === "grupo" && alvo.kind === "grupo" && item.source.numero === alvo.numero) {
      return;
    }
    if (
      item.source.kind === "escala" &&
      alvo.kind === "escala" &&
      item.source.escalaId === alvo.escalaId
    ) {
      return;
    }

    await executarDrop(item, alvo);
  }

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="space-y-6">
        <div className="card-liturgical p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
            <div>
              <h2 className="font-display text-lg font-semibold text-burgundy">
                Remanejamento — {nomeMes(mes)} {ano}
              </h2>
              <p className="text-xs text-muted-foreground">
                Arraste do grupo para Comunidade (domingo) ou Adoração (sexta): o cronograma atualiza
                (ex.: 9 → 7 na missa da manhã). Irmãos/gêmeos movem juntos nos grupos.
              </p>
            </div>
            {salvando && (
              <span className="text-xs text-muted-foreground animate-pulse">Salvando…</span>
            )}
          </div>

          {erro && (
            <p className="text-sm text-destructive mb-3" role="alert">
              {erro}
            </p>
          )}

          <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3 mb-4">
            {gruposOrdenados.map((grupo) => {
              const itens = itensGrupo(grupo.numero);
              return (
                <GrupoColumn key={grupo.numero} numero={grupo.numero} count={itens.length}>
                  {itens.map((item) => (
                    <DraggableCoroinhaCard key={kanbanDragId(item)} item={item} compact />
                  ))}
                </GrupoColumn>
              );
            })}
          </div>

          <RemoverZone />

          <div className="mt-4">
            <PainelCoroinhasRemanejamento
              coroinhas={coroinhas}
              escalaMensal={escalaMensal}
              ano={ano}
              mes={mes}
              podeEditar={podeEditar}
              onAtualizado={(em, esc) => onAtualizado(em, esc, true)}
            />
          </div>
        </div>

        <EscalaMesCronologico
          {...cronologicoProps}
          coroinhas={coroinhas}
          dias={diasAgrupados}
          mes={mes}
          ano={ano}
          podeEditar={podeEditar}
          kanbanMode
        />
      </div>

      <DragOverlay>
        {activeItem ? (
          <div className="rounded-lg border border-burgundy bg-card px-3 py-2 text-sm shadow-lg">
            {activeItem.coroinhaNome}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
