"use client";

import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Send, Trash2, UserCog, Users } from "lucide-react";
import { FuncoesEscalaForm } from "@/components/FuncoesEscalaForm";
import {
  LEGENDA_CATEGORIAS_V6,
  ORIENTACOES_GERAIS_V6,
  linhaTituloV6,
  linhasCoroinhasV6,
  nomeMes,
  type DiaEscalas,
} from "@/lib/escala-layout";
import { kanbanDragId, kanbanDropId, type KanbanDragItem } from "@/lib/escala-kanban";
import type { FuncaoEscala } from "@/lib/scheduling";
import type { Coroinha, Escala } from "@/types";

interface EscalaMesCronologicoProps {
  dias: DiaEscalas[];
  mes: number;
  ano: number;
  podeEditar: boolean;
  kanbanMode?: boolean;
  coroinhas: Coroinha[];
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

function BadgeTag({ escala }: { escala: Escala }) {
  if (escala.voluntarios) {
    return (
      <span className="inline-flex text-[10px] font-semibold uppercase tracking-wide rounded px-1.5 py-0.5 bg-amber-500/15 text-amber-800 dark:text-amber-300">
        Novena
      </span>
    );
  }
  if (escala.missa_tipo_slot === "ComunidadeDomingo") {
    return (
      <span className="inline-flex text-[10px] font-semibold uppercase tracking-wide rounded px-1.5 py-0.5 bg-emerald-500/15 text-emerald-800 dark:text-emerald-300">
        S. Antônio
      </span>
    );
  }
  if (escala.missa_tipo_slot === "Dia13") {
    return (
      <span className="inline-flex text-[10px] font-semibold uppercase tracking-wide rounded px-1.5 py-0.5 bg-violet-500/15 text-violet-800 dark:text-violet-300">
        Solenidade
      </span>
    );
  }
  if (escala.grupo_numero != null) {
    return (
      <span className="inline-flex text-[10px] font-semibold uppercase tracking-wide rounded px-1.5 py-0.5 bg-burgundy/10 text-burgundy">
        Grupo {escala.grupo_numero}
      </span>
    );
  }
  return null;
}

function DraggableCoroinhaLinha({
  escala,
  coroinhaId,
  coroinhaNome,
  linha,
}: {
  escala: Escala;
  coroinhaId: number;
  coroinhaNome: string;
  linha: string;
}) {
  const item: KanbanDragItem = {
    coroinhaId,
    coroinhaNome,
    source: { kind: "escala", escalaId: escala.id },
  };
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: kanbanDragId(item),
    data: item,
  });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), opacity: isDragging ? 0.5 : 1 }}
      className="text-sm text-foreground font-mono tabular-nums flex items-center gap-1.5"
    >
      <button
        type="button"
        className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-burgundy touch-none shrink-0"
        aria-label={`Arrastar ${coroinhaNome}`}
        {...listeners}
        {...attributes}
      >
        <GripVertical className="size-3.5" aria-hidden />
      </button>
      {linha}
    </li>
  );
}

function CelebracaoDropZone({
  escala,
  kanbanMode,
  children,
}: {
  escala: Escala;
  kanbanMode?: boolean;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: kanbanDropId({ kind: "escala", escalaId: escala.id }),
    disabled: !kanbanMode,
  });

  return (
    <div
      ref={kanbanMode ? setNodeRef : undefined}
      className={`min-w-0 flex-1 rounded-lg transition-colors ${
        kanbanMode && isOver ? "ring-2 ring-burgundy/30 bg-burgundy/5" : ""
      }`}
    >
      {children}
    </div>
  );
}

function EscalaCelebracaoCard({
  escala,
  mostrarDia,
  dia,
  diaSemana,
  kanbanMode,
  podeEditar,
  coroinhas,
  editandoMembros,
  editandoFuncoes,
  membrosEdicao,
  funcoesEdicao,
  notificandoId,
  excluindoEscalaId,
  onAbrirEdicaoMembros,
  onAbrirEdicaoFuncoes,
  onFecharEdicaoMembros,
  onFecharEdicaoFuncoes,
  onToggleMembro,
  onSalvarMembros,
  onSalvarFuncoes,
  onNotificar,
  onExcluir,
  onFuncoesChange,
}: {
  escala: Escala;
  mostrarDia: boolean;
  dia: string;
  diaSemana: string;
  kanbanMode?: boolean;
  editandoMembros: boolean;
  editandoFuncoes: boolean;
} & Omit<
  EscalaMesCronologicoProps,
  "dias" | "mes" | "ano" | "kanbanMode" | "editandoMembrosId" | "editandoFuncoesId"
>) {
  const nomes = linhasCoroinhasV6(escala);
  const itensArrastaveis = !escala.voluntarios && escala.itens.length > 0;

  return (
    <div className="flex gap-3 sm:gap-4 border-b border-border/60 last:border-b-0 py-4 first:pt-0">
      <div className="w-12 sm:w-14 shrink-0 text-center">
        {mostrarDia ? (
          <>
            <div className="font-display text-2xl sm:text-3xl font-bold text-burgundy leading-none">{dia}</div>
            <div className="text-[10px] sm:text-xs font-semibold text-muted-foreground mt-1 uppercase tracking-wide">
              {diaSemana}
            </div>
          </>
        ) : (
          <span className="sr-only">{escala.data}</span>
        )}
      </div>

      <CelebracaoDropZone escala={escala} kanbanMode={kanbanMode}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-display font-semibold text-burgundy text-sm sm:text-base leading-snug">
                {linhaTituloV6(escala)}
              </h4>
              <BadgeTag escala={escala} />
              {escala.notificacao_enviada && (
                <span className="inline-flex items-center gap-1 text-xs rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-2 py-0.5">
                  <Send className="size-3" aria-hidden />
                  Notificado
                </span>
              )}
            </div>
            {escala.observacao && (
              <p className="text-xs text-muted-foreground italic mt-1">{escala.observacao}</p>
            )}
          </div>

          {podeEditar && (
            <div className="flex items-center gap-1.5 shrink-0 self-start">
              <button
                type="button"
                onClick={() => (editandoMembros ? onFecharEdicaoMembros() : onAbrirEdicaoMembros(escala))}
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
                onClick={() => (editandoFuncoes ? onFecharEdicaoFuncoes() : onAbrirEdicaoFuncoes(escala))}
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
                onClick={() => onNotificar(escala.id)}
                disabled={notificandoId === escala.id}
                title="Notificar escalados"
                aria-label="Notificar escalados"
                className="p-2 rounded-lg border border-border text-muted-foreground hover:bg-muted hover:text-burgundy transition-colors disabled:opacity-50"
              >
                <Send className={`size-4 ${notificandoId === escala.id ? "animate-pulse" : ""}`} aria-hidden />
              </button>
              <button
                type="button"
                onClick={() => onExcluir(escala.id)}
                disabled={excluindoEscalaId === escala.id}
                title="Excluir escala"
                aria-label="Excluir escala"
                className="p-2 rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
              >
                <Trash2 className="size-4" aria-hidden />
              </button>
            </div>
          )}
        </div>

        <ul className="mt-2 space-y-0.5">
          {kanbanMode && itensArrastaveis
            ? escala.itens.map((item, idx) => (
                <DraggableCoroinhaLinha
                  key={item.id}
                  escala={escala}
                  coroinhaId={item.coroinha_id}
                  coroinhaNome={item.coroinha_nome}
                  linha={`${String(idx + 1).padStart(2, "0")} ${item.coroinha_nome}`}
                />
              ))
            : nomes.map((linha) => (
                <li key={linha} className="text-sm text-foreground font-mono tabular-nums">
                  {linha}
                </li>
              ))}
        </ul>

        {editandoMembros && (
          <div className="mt-4 rounded-lg border border-border bg-muted/20 p-4">
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
                    onChange={() => onToggleMembro(c.id)}
                  />
                  {c.nome}
                </label>
              ))}
            </div>
            <div className="flex gap-2 mt-3">
              <button type="button" onClick={() => onSalvarMembros(escala.id)} className="btn-primary text-sm">
                Salvar coroinhas
              </button>
              <button type="button" onClick={onFecharEdicaoMembros} className="btn-outline text-sm">
                Cancelar
              </button>
            </div>
          </div>
        )}

        {editandoFuncoes && (
          <div className="mt-4 rounded-lg border border-border bg-muted/20 p-4">
            <FuncoesEscalaForm
              coroinhas={coroinhas}
              valores={funcoesEdicao}
              onChange={onFuncoesChange}
              compact
            />
            <div className="flex gap-2 mt-3">
              <button type="button" onClick={() => onSalvarFuncoes(escala.id)} className="btn-primary text-sm">
                Salvar funções
              </button>
              <button type="button" onClick={onFecharEdicaoFuncoes} className="btn-outline text-sm">
                Cancelar
              </button>
            </div>
          </div>
        )}
      </CelebracaoDropZone>
    </div>
  );
}

export function EscalaMesCronologico(props: EscalaMesCronologicoProps) {
  const { dias, mes, ano } = props;

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="font-display text-xl sm:text-2xl font-bold text-burgundy">Escala de Coroinhas</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {nomeMes(mes)} de {ano} · Santuário de Fátima
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1 rounded-lg border border-border bg-muted/20 p-2">
        {LEGENDA_CATEGORIAS_V6.map((cat) => (
          <div
            key={cat}
            className="text-[10px] sm:text-xs text-center text-muted-foreground font-medium py-1 px-1"
          >
            {cat}
          </div>
        ))}
      </div>

      <div className="card-liturgical p-4 sm:p-6">
        {dias.map((dia) => (
          <div key={dia.id}>
            {dia.escalas.map((escala, idx) => (
              <EscalaCelebracaoCard
                key={escala.id}
                escala={escala}
                mostrarDia={idx === 0}
                dia={dia.dia}
                diaSemana={dia.diaSemana}
                kanbanMode={props.kanbanMode}
                {...props}
                editandoMembros={props.editandoMembrosId === escala.id}
                editandoFuncoes={props.editandoFuncoesId === escala.id}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="card-liturgical p-4 sm:p-5">
        <h3 className="font-display font-semibold text-burgundy mb-3">Orientações gerais</h3>
        <ul className="text-sm text-muted-foreground space-y-1.5 list-disc list-inside">
          {ORIENTACOES_GERAIS_V6.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
