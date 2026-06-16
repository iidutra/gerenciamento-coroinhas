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

/** Ordem cronológica: mais antigo → mais recente (data do evento ou publicação). */
export function compararNoticiasCronologicamente(a: Noticia, b: Noticia): number {
  const diff = noticiaTimestamp(a) - noticiaTimestamp(b);
  if (diff !== 0) return diff;
  return a.titulo.localeCompare(b.titulo, "pt-BR");
}

export function ordenarNoticias(noticias: Noticia[]): Noticia[] {
  return [...noticias].sort(compararNoticiasCronologicamente);
}

export function agruparNoticiasPorMes(noticias: Noticia[]): { mes: string; itens: Noticia[] }[] {
  const map = new Map<string, Noticia[]>();
  for (const n of noticias) {
    const chave = noticiaMesAnoLabel(n);
    const lista = map.get(chave) ?? [];
    lista.push(n);
    map.set(chave, lista);
  }
  return [...map.entries()]
    .map(([mes, itens]) => ({
      mes,
      itens: ordenarNoticias(itens),
    }))
    .sort((a, b) => compararNoticiasCronologicamente(a.itens[0], b.itens[0]));
}

export function noticiaNoMes(noticia: Noticia, referencia: Date = new Date()): boolean {
  const iso = noticia.data_evento ?? noticia.publicado_em.slice(0, 10);
  const d = new Date(`${iso}T12:00:00`);
  return d.getMonth() === referencia.getMonth() && d.getFullYear() === referencia.getFullYear();
}

/** Principal evento do mês: destaque do calendário ou próximo evento relevante. */
export function eventoDoMes(noticias: Noticia[], referencia: Date = new Date()): Noticia | undefined {
  const noMes = noticias.filter((n) => noticiaNoMes(n, referencia));
  if (noMes.length === 0) return undefined;

  const comDestaque = noMes.filter((n) => n.destaque);
  const pool = comDestaque.length > 0 ? comDestaque : noMes.filter((n) => n.data_evento);
  if (pool.length === 0) return undefined;

  const inicioHoje = new Date(referencia);
  inicioHoje.setHours(0, 0, 0, 0);
  const hoje = inicioHoje.getTime();

  const futuros = ordenarNoticias(pool.filter((n) => noticiaTimestamp(n) >= hoje));
  if (futuros.length > 0) return futuros[0];

  const passados = ordenarNoticias(pool);
  return passados.at(-1);
}
