export function formatarCpf(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
}

/**
 * Máscara de telefone para exibição/digitação no formato 99 9 9999 9999.
 * Apenas visual — sempre envie os dígitos puros (telefoneDigits) ao backend.
 */
export function formatarTelefone(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 11);
  const partes: string[] = [];
  if (d.length > 0) partes.push(d.slice(0, 2)); // DDD
  if (d.length > 2) partes.push(d.slice(2, 3)); // 9
  if (d.length > 3) partes.push(d.slice(3, 7)); // 9999
  if (d.length > 7) partes.push(d.slice(7, 11)); // 9999
  return partes.join(" ");
}

/** Só os dígitos do telefone — o que deve ser persistido/enviado. */
export function telefoneDigits(value: string): string {
  return value.replace(/\D/g, "").slice(0, 11);
}

/** Normaliza texto para busca: minúsculas e sem acentos (Júlia == Julia). */
export function normalizarBusca(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
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

export function etapaCatequeseLabel(etapa: string): string {
  const map: Record<string, string> = {
    PreEucaristia: "Pré-Eucaristia",
    PrimeiraEucaristia: "Primeira Eucaristia",
    Crisma: "Crisma",
  };
  return map[etapa] || etapa;
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
