const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ConfigPublica {
  inscricoes_abertas: boolean;
}

export async function fetchConfigPublica(): Promise<ConfigPublica> {
  const res = await fetch(`${API_URL}/config/publica`, { next: { revalidate: 60 } });
  if (!res.ok) {
    return { inscricoes_abertas: false };
  }
  return res.json() as Promise<ConfigPublica>;
}
