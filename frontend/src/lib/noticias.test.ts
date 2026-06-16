import { describe, expect, it } from "vitest";
import type { Noticia } from "@/types";
import { agruparNoticiasPorMes, eventoDoMes, noticiaMesAnoLabel, ordenarNoticias } from "./noticias";

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
  it("ordena por cronologia crescente (data do evento)", () => {
    const lista = ordenarNoticias([
      noticia({ id: 1, titulo: "Maio", data_evento: "2026-05-01" }),
      noticia({ id: 2, titulo: "Março", destaque: true, data_evento: "2026-03-01" }),
      noticia({ id: 3, titulo: "Junho", data_evento: "2026-06-01" }),
    ]);
    expect(lista.map((n) => n.id)).toEqual([2, 1, 3]);
  });
});

describe("agruparNoticiasPorMes", () => {
  it("agrupa por mês/ano em ordem cronológica", () => {
    const grupos = agruparNoticiasPorMes([
      noticia({ id: 1, titulo: "A", data_evento: "2026-04-19" }),
      noticia({ id: 2, titulo: "B", data_evento: "2026-03-21" }),
      noticia({ id: 3, titulo: "C", data_evento: "2026-03-13" }),
    ]);
    expect(grupos).toHaveLength(2);
    expect(noticiaMesAnoLabel(grupos[0].itens[0])).toMatch(/março/i);
    expect(grupos[0].itens.map((n) => n.id)).toEqual([3, 2]);
    expect(grupos[1].itens[0].id).toBe(1);
  });
});

describe("eventoDoMes", () => {
  it("prioriza destaque do mês corrente", () => {
    const ref = new Date("2026-05-10T12:00:00");
    const escolhido = eventoDoMes(
      [
        noticia({ id: 1, titulo: "Fátima", data_evento: "2026-05-13", destaque: true }),
        noticia({ id: 2, titulo: "Outro", data_evento: "2026-05-20" }),
        noticia({ id: 3, titulo: "Abril", data_evento: "2026-04-19", destaque: true }),
      ],
      ref,
    );
    expect(escolhido?.id).toBe(1);
  });

  it("escolhe o próximo evento futuro quando não há destaque", () => {
    const ref = new Date("2026-06-01T12:00:00");
    const escolhido = eventoDoMes(
      [
        noticia({ id: 1, titulo: "Corpus Christi", data_evento: "2026-06-04" }),
        noticia({ id: 2, titulo: "Fátima", data_evento: "2026-06-13" }),
      ],
      ref,
    );
    expect(escolhido?.id).toBe(1);
  });

  it("retorna o mais recente quando todos os eventos do mês já passaram", () => {
    const ref = new Date("2026-06-16T12:00:00");
    const escolhido = eventoDoMes(
      [
        noticia({ id: 1, titulo: "Corpus Christi", data_evento: "2026-06-04" }),
        noticia({ id: 2, titulo: "Fátima", data_evento: "2026-06-13" }),
      ],
      ref,
    );
    expect(escolhido?.id).toBe(2);
  });
});
