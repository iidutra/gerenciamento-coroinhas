"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { portalNav } from "@/components/Sidebar";
import { PageHeader } from "@/components/PageHeader";
import { PortalCorpo } from "@/components/PortalCorpo";
import { LoadingScreen } from "@/components/LoadingScreen";
import { clearTokens, getUsuario } from "@/lib/api";
import type { Usuario } from "@/types";

export default function PortalPage() {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  useEffect(() => {
    const u = getUsuario<Usuario>();
    if (!u) {
      router.push("/login");
      return;
    }
    if (u.tipo_perfil !== "Pai" && u.tipo_perfil !== "Coroinha") {
      router.push("/dashboard/portal");
      return;
    }
    setUsuario(u);
  }, [router]);

  function sair() {
    clearTokens();
    router.push("/login");
  }

  if (!usuario) return <LoadingScreen />;

  return (
    <AppShell groups={portalNav} subtitle={usuario.nome} onLogout={sair}>
      <PageHeader
        title="Portal dos Pais"
        description="Acompanhe a vida do seu filho na pastoral."
        onLogout={sair}
      />
      <PortalCorpo usuario={usuario} />
    </AppShell>
  );
}
