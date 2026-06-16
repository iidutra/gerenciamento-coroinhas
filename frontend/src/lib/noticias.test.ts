import { describe, expect, it } from "vitest";
import type { Noticia } from "@/types";
import { agruparNoticiasPorMes, noticiaMesAnoLabel, ordenarNoticias } from "./noticias";

function noticia(partial: Partial<Noticia> & Pick<Noticia, "id" | "titulo">): Noticia {
  return {
    conteudo: "",
    destaque: false,
    publicado_em: "2026-03-01T12:00:00Z",
    ativo: true,
    ...partial,
  };
}

describe("ordenarNoticias", () => {
  it("prioriza destaques e depois data do evento", () => {
    const lista = ordenarNoticias([
      noticia({ id: 1, titulo: "Normal", data_evento: "2026-05-01" }),
      noticia({ id: 2, titulo: "Destaque", destaque: true, data_evento: "2026-03-01" }),
      noticia({ id: 3, titulo: "Recente", data_evento: "2026-06-01" }),
    ]);
    expect(lista[0].id).toBe(2);
    expect(lista[1].id).toBe(3);
  });
});

describe("agruparNoticiasPorMes", () => {
  it("agrupa por mês/ano", () => {
    const grupos = agruparNoticiasPorMes([
      noticia({ id: 1, titulo: "A", data_evento: "2026-03-13" }),
      noticia({ id: 2, titulo: "B", data_evento: "2026-03-21" }),
      noticia({ id: 3, titulo: "C", data_evento: "2026-04-19" }),
    ]);
    expect(grupos).toHaveLength(2);
    expect(grupos[0].itens).toHaveLength(2);
    expect(noticiaMesAnoLabel(grupos[0].itens[0])).toMatch(/março/i);
  });
});
