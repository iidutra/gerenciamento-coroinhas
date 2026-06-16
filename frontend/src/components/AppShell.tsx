"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import { Sidebar, type NavGroup } from "@/components/Sidebar";

interface AppShellProps {
  groups: NavGroup[];
  subtitle?: string;
  tipoPerfil?: string;
  children: ReactNode;
}

export function AppShell({ groups, subtitle, tipoPerfil, children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <div className="flex min-h-screen text-foreground">
      <header className="app-mobile-header lg:hidden">
        <button
          type="button"
          onClick={() => setMenuOpen(true)}
          className="inline-flex items-center justify-center size-10 -ml-1 rounded-lg hover:bg-muted active:bg-muted/80 transition-colors"
          aria-label="Abrir menu"
          aria-expanded={menuOpen}
        >
          <Menu className="size-5 text-burgundy" aria-hidden />
        </button>
        <span className="font-display text-base font-semibold text-burgundy truncate min-w-0">
          Pastoral dos Coroinhas
        </span>
      </header>

      {menuOpen && (
        <button
          type="button"
          className="lg:hidden fixed inset-0 z-40 bg-black/45 backdrop-blur-[2px]"
          aria-label="Fechar menu"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <div
        className={`lg:static lg:translate-x-0 fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-out ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar
          groups={groups}
          subtitle={subtitle}
          tipoPerfil={tipoPerfil}
          onNavigate={() => setMenuOpen(false)}
          showCloseButton={menuOpen}
          onClose={() => setMenuOpen(false)}
        />
      </div>

      <main className="app-main">{children}</main>
    </div>
  );
}
