export type KanbanDropTarget =
  | { kind: "grupo"; numero: number }
  | { kind: "escala"; escalaId: number }
  | { kind: "remover" };

export type KanbanDragItem = {
  coroinhaId: number;
  coroinhaNome: string;
  source:
    | { kind: "grupo"; numero: number }
    | { kind: "escala"; escalaId: number };
};

export function kanbanDropId(target: KanbanDropTarget): string {
  if (target.kind === "grupo") return `grupo-${target.numero}`;
  if (target.kind === "escala") return `escala-${target.escalaId}`;
  return "remover";
}

export function parseKanbanDropId(id: string): KanbanDropTarget | null {
  if (id.startsWith("grupo-")) return { kind: "grupo", numero: Number(id.slice(6)) };
  if (id.startsWith("escala-")) return { kind: "escala", escalaId: Number(id.slice(7)) };
  if (id === "remover") return { kind: "remover" };
  return null;
}

export function kanbanDragId(item: KanbanDragItem): string {
  const origem =
    item.source.kind === "grupo" ? `grupo-${item.source.numero}` : `escala-${item.source.escalaId}`;
  return `coroinha-${item.coroinhaId}-${origem}`;
}

export function parseKanbanDragId(
  id: string,
  grupos: { numero: number; membros: { coroinha_id: number; coroinha_nome: string }[] }[],
  escalas: { id: number; itens: { coroinha_id: number; coroinha_nome: string }[] }[],
): KanbanDragItem | null {
  const match = id.match(/^coroinha-(\d+)-/);
  if (!match) return null;
  const coroinhaId = Number(match[1]);

  if (id.includes("-grupo-")) {
    const numero = Number(id.split("-grupo-")[1]);
    const membro = grupos
      .find((g) => g.numero === numero)
      ?.membros.find((m) => m.coroinha_id === coroinhaId);
    return {
      coroinhaId,
      coroinhaNome: membro?.coroinha_nome ?? `Coroinha ${coroinhaId}`,
      source: { kind: "grupo", numero },
    };
  }

  if (id.includes("-escala-")) {
    const escalaId = Number(id.split("-escala-")[1]);
    const item = escalas
      .find((e) => e.id === escalaId)
      ?.itens.find((i) => i.coroinha_id === coroinhaId);
    return {
      coroinhaId,
      coroinhaNome: item?.coroinha_nome ?? `Coroinha ${coroinhaId}`,
      source: { kind: "escala", escalaId },
    };
  }

  return null;
}

export function destinoAceitaTransferenciaDoGrupo(missaTipoSlot?: string): boolean {
  return missaTipoSlot === "ComunidadeDomingo" || missaTipoSlot === "SextaAdoracao";
}
