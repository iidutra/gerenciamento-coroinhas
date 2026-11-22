import { describe, expect, it } from "vitest";
import { formatarCpf, pareceEmail } from "./format";
import {
  funcaoEscalaLabel,
  funcoesFromItens,
  funcoesParaPayload,
  funcoesVazias,
} from "./scheduling";

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

  it("funcoesFromItens mapeia até dois Entre os dois", () => {
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

  it("funcoesParaPayload ignora vazios", () => {
    const base = funcoesVazias();
    base.Vela1 = 5;
    base.Cruz = 3;
    expect(funcoesParaPayload(base)).toEqual({ Vela1: 5, Cruz: 3 });
  });

  it("funcaoEscalaLabel traduz valores", () => {
    expect(funcaoEscalaLabel("Vela1")).toBe("Vela 1");
    expect(funcaoEscalaLabel("Velas")).toBe("Vela 1");
    expect(funcaoEscalaLabel(null)).toBe("");
  });
});
