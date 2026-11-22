import { describe, expect, it } from "vitest";
import { formatarCpf, pareceEmail } from "./format";
import {
  funcaoEscalaLabel,
  funcoesEscalaCompletas,
  funcoesFromItens,
  funcoesParaPayload,
  funcoesVazias,
} from "./scheduling";
import {
  escalaTodosDestaqueVermelho,
  exibirObservacaoOfertorioAssessor,
  limparObservacaoEscala,
  linhaTituloV6,
  observacaoCelebracao,
  TITULO_NATAL,
} from "./escala-layout";
import type { Escala } from "@/types";

describe("formatarCpf", () => {
  it("aplica máscara progressiva", () => {
    expect(formatarCpf("11144477735")).toBe("111.444.777-35");
    expect(formatarCpf("111.444.777-35")).toBe("111.444.777-35");
  });
});

describe("pareceEmail", () => {
  it("detecta letras ou @", () => {
    expect(pareceEmail("coord@paroquia.org")).toBe(true);
    expect(pareceEmail("c")).toBe(true);
    expect(pareceEmail("11144477735")).toBe(false);
  });
});

describe("scheduling helpers", () => {
  it("funcoesVazias retorna todas as funções", () => {
    const vazias = funcoesVazias();
    expect(vazias.Vela1).toBe("");
    expect(vazias.Vela2).toBe("");
    expect(vazias.entreOsDoisIds).toEqual([]);
    expect(vazias.assessorIds).toEqual([]);
  });

  it("funcoesFromItens mapeia funções dos itens", () => {
    const map = funcoesFromItens([
      { coroinha_id: 1, funcao: "Vela1" },
      { coroinha_id: 2, funcao: "Cruz" },
    ]);
    expect(map.Vela1).toBe(1);
    expect(map.Cruz).toBe(2);
  });

  it("funcoesFromItens mapeia até dois no Altar", () => {
    const map = funcoesFromItens([
      { coroinha_id: 10, funcao: "EntreOsDois" },
      { coroinha_id: 11, funcao: "EntreOsDois" },
    ]);
    expect(map.entreOsDoisIds).toEqual([10, 11]);
    expect(funcoesParaPayload(map)).toEqual({ EntreOsDois: [10, 11] });
  });

  it("funcoesFromItens mapeia vários assessores", () => {
    const map = funcoesFromItens([
      { coroinha_id: 20, funcao: "Assessor" },
      { coroinha_id: 21, funcao: "Assessor" },
    ]);
    expect(map.assessorIds).toEqual([20, 21]);
    expect(funcoesParaPayload(map)).toEqual({ Assessor: [20, 21] });
  });

  it("funcoesFromItens aceita duas funções no mesmo coroinha", () => {
    const map = funcoesFromItens([{ coroinha_id: 5, funcoes: ["Cruz", "Assessor"] }]);
    expect(map.Cruz).toBe(5);
    expect(map.assessorIds).toEqual([5]);
    expect(funcoesParaPayload(map)).toEqual({ Cruz: 5, Assessor: [5] });
  });

  it("funcoesParaPayload ignora vazios", () => {
    const base = funcoesVazias();
    base.Vela1 = 5;
    base.Cruz = 3;
    expect(funcoesParaPayload(base)).toEqual({ Vela1: 5, Cruz: 3 });
  });

  it("funcoesEscalaCompletas exige todos os papéis principais", () => {
    const parcial = funcoesVazias();
    parcial.Cruz = 1;
    expect(funcoesEscalaCompletas(parcial)).toBe(false);
    const completa = funcoesFromItens([
      { coroinha_id: 1, funcao: "Cruz" },
      { coroinha_id: 2, funcao: "Vela1" },
      { coroinha_id: 3, funcao: "Vela2" },
      { coroinha_id: 4, funcao: "Turibulo" },
      { coroinha_id: 5, funcao: "Naveta" },
      { coroinha_id: 6, funcao: "Missal" },
      { coroinha_id: 7, funcao: "EntreOsDois" },
      { coroinha_id: 8, funcao: "Assessor" },
    ]);
    expect(funcoesEscalaCompletas(completa)).toBe(true);
  });

  it("linhaTituloV6 usa Missa do Natal em 25/12", () => {
    const escala = {
      data: "2026-12-25",
      missa_horario: "18:30",
      missa_tipo_slot: "DomingoNoite",
      grupo_numero: 2,
      itens: [],
    } as Escala;
    expect(linhaTituloV6(escala)).toBe(`19h ${TITULO_NATAL}`);
  });

  it("quarta e sexta: ofertório sim, texto extra da escala não", () => {
    const sexta = {
      missa_tipo_slot: "SextaAdoracao",
      observacao: "Adoração ao Santíssimo seguida de Missa",
      itens: [],
    } as Escala;
    const quarta = {
      missa_tipo_slot: "QuartaVoluntarios",
      observacao: "Voluntários",
      itens: [],
    } as Escala;
    const comunidade = {
      missa_tipo_slot: "ComunidadeDomingo",
      missa_local: "Comunidade",
      itens: [],
    } as Escala;
    const domingo = { missa_tipo_slot: "DomingoManha", itens: [] } as Escala;
    expect(exibirObservacaoOfertorioAssessor(sexta)).toBe(true);
    expect(exibirObservacaoOfertorioAssessor(quarta)).toBe(true);
    expect(exibirObservacaoOfertorioAssessor(comunidade)).toBe(false);
    expect(observacaoCelebracao(sexta)).toBeNull();
    expect(observacaoCelebracao(quarta)).toBeNull();
    expect(exibirObservacaoOfertorioAssessor(domingo)).toBe(true);
  });

  it("limparObservacaoEscala remove frase descontinuada", () => {
    const texto =
      "Adoração ao Santíssimo seguida de Missa Após a adoração teremos um momento especial.";
    expect(limparObservacaoEscala(texto)).toBe("Adoração ao Santíssimo seguida de Missa");
    const escala = {
      observacao: texto,
      itens: [],
    } as Escala;
    expect(observacaoCelebracao(escala)).toBe("Adoração ao Santíssimo seguida de Missa");
  });

  it("escalaTodosDestaqueVermelho quando todos sem funções completas", () => {
    const escala = {
      todos_coroinhas: true,
      itens: [{ coroinha_id: 1, coroinha_nome: "João", id: 1, ordem: 1 }],
    } as Escala;
    expect(escalaTodosDestaqueVermelho(escala)).toBe(true);
  });

  it("funcaoEscalaLabel traduz valores", () => {
    expect(funcaoEscalaLabel("Vela1")).toBe("Vela 1");
    expect(funcaoEscalaLabel("Velas")).toBe("Vela 1");
    expect(funcaoEscalaLabel("EntreOsDois")).toBe("Altar");
    expect(funcaoEscalaLabel(null)).toBe("");
  });
});
