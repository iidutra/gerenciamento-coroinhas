"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Bell } from "lucide-react";
import { apiFetch, getUsuario } from "@/lib/api";
import type { Usuario } from "@/types";

// Perfis que aprovam pedidos de acesso (mesmo critério de podeGerenciarCoroinhas).
const GESTORES = ["Coordenador", "Secretario"];
const INTERVALO_MS = 60_000;

export function NotificationBell() {
  const pathname = usePathname();
  const [visivel, setVisivel] = useState(false);
  const [pendentes, setPendentes] = useState(0);

  const carregar = useCallback(async () => {
    try {
      const data = await apiFetch<{ pendentes: number }>(
        "/solicitacoes-acesso/pendentes-count/",
      );
      setPendentes(data.pendentes ?? 0);
    } catch {
      // Silencioso: o sino é apenas informativo.
    }
  }, []);

  useEffect(() => {
    const u = getUsuario<Usuario>();
    if (!u || !GESTORES.includes(u.tipo_perfil)) {
      setVisivel(false);
      return;
    }
    setVisivel(true);
    carregar();
    const id = setInterval(carregar, INTERVALO_MS);
    return () => clearInterval(id);
  }, [pathname, carregar]);

  if (!visivel) return null;

  const rotulo =
    pendentes > 0
      ? `${pendentes} cadastro${pendentes > 1 ? "s" : ""} esperando aprovação`
      : "Nenhum cadastro pendente";

  return (
    <Link
      href="/dashboard/acesso-pais"
      className="relative inline-flex items-center justify-center size-10 rounded-lg border border-border bg-card hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
      aria-label={rotulo}
      title={rotulo}
    >
      <Bell className="size-5" aria-hidden />
      {pendentes > 0 && (
        <span
          className="absolute -top-1.5 -right-1.5 min-w-[1.15rem] h-[1.15rem] px-1 rounded-full bg-destructive text-white text-[11px] font-semibold grid place-items-center leading-none"
          aria-hidden
        >
          {pendentes > 99 ? "99+" : pendentes}
        </span>
      )}
    </Link>
  );
}
