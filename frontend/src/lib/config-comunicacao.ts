import { apiFetch } from "@/lib/api";

export interface ConfigComunicacao {
  email_configurado: boolean;
  whatsapp_configurado: boolean;
  whatsapp_provider: string;
  whatsapp_simulacao: boolean;
}

export async function fetchConfigComunicacao(): Promise<ConfigComunicacao> {
  return apiFetch<ConfigComunicacao>("/config/comunicacao");
}
