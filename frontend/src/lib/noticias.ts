import type { Noticia } from "@/types";

/** Data usada para ordenação e agrupamento (evento ou publicação). */
export function noticiaTimestamp(noticia: Noticia): number {
  const iso = noticia.data_evento ?? noticia.publicado_em.slice(0, 10);
  return new Date(`${iso}T12:00:00`).getTime();
}

export function noticiaMesAnoLabel(noticia: Noticia): string {
  const iso = noticia.data_evento ?? noticia.publicado_em.slice(0, 10);
  const d = new Date(`${iso}T12:00:00`);
  const label = d.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function agruparNoticiasPorMes(noticias: Noticia[]): { mes: string; itens: Noticia[] }[] {
  const map = new Map<string, Noticia[]>();
  for (const n of noticias) {
    const chave = noticiaMesAnoLabel(n);
    const lista = map.get(chave) ?? [];
    lista.push(n);
    map.set(chave, lista);
  }
  return [...map.entries()].map(([mes, itens]) => ({ mes, itens }));
}

export function ordenarNoticias(noticias: Noticia[]): Noticia[] {
  return [...noticias].sort((a, b) => {
    if (a.destaque !== b.destaque) return Number(b.destaque) - Number(a.destaque);
    return noticiaTimestamp(b) - noticiaTimestamp(a);
  });
}
