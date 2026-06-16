export function formatarCpf(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
}

/** Detecta digitação de e-mail antes do @ (evita máscara de CPF comer as letras). */
export function pareceEmail(value: string): boolean {
  return /[a-zA-Z@]/.test(value);
}

export function turmaLabel(turma: string): string {
  const map: Record<string, string> = {
    Iniciante: "Iniciante",
    Intermediario: "Intermediário",
    Avancado: "Avançado",
  };
  return map[turma] || turma;
}

export function categoriaDocumentoLabel(categoria: string): string {
  const map: Record<string, string> = {
    Liturgia: "Liturgia",
    Formacao: "Formação",
    Ritual: "Ritual",
    Outro: "Outro",
  };
  return map[categoria] || categoria;
}

function formatarDataIso(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("pt-BR");
}

/** Texto legível da data do evento (ou publicação). */
export function noticiaDataLabel(noticia: {
  data_evento?: string | null;
  data_evento_fim?: string | null;
  publicado_em: string;
}): string {
  if (noticia.data_evento) {
    const inicio = formatarDataIso(noticia.data_evento);
    if (noticia.data_evento_fim && noticia.data_evento_fim !== noticia.data_evento) {
      return `${inicio} a ${formatarDataIso(noticia.data_evento_fim)}`;
    }
    return inicio;
  }
  return new Date(noticia.publicado_em).toLocaleDateString("pt-BR");
}

/** Remove metadados legados da importação do calendário. */
export function noticiaConteudoLegivel(conteudo: string): string {
  return conteudo
    .split("\n")
    .filter((linha) => {
      const t = linha.trim();
      if (!t) return true;
      if (t.startsWith("[calendario-paroquial]")) return false;
      if (t.startsWith("Fonte:")) return false;
      if (t.startsWith("Data:")) return false;
      if (t.startsWith("Local:")) return false;
      if (t.startsWith("Horário:")) return false;
      return true;
    })
    .join("\n")
    .trim();
}
