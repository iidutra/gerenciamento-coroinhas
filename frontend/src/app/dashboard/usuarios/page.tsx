"use client";

import { FormEvent, useEffect, useState } from "react";
import { StaffLayout, useStaffAuth } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { apiFetch, asList } from "@/lib/api";
import type { UsuarioStaff } from "@/types";

export default function UsuariosPage() {
  const { usuario, ready, sair } = useStaffAuth();
  const [lista, setLista] = useState<UsuarioStaff[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [tipoPerfil, setTipoPerfil] = useState<"Secretario" | "Padre">("Secretario");
  const [senha, setSenha] = useState("");

  const isCoordenador = usuario?.tipo_perfil === "Coordenador";

  function load() {
    setLoading(true);
    apiFetch<UsuarioStaff[] | { results?: UsuarioStaff[] }>("/usuarios-staff/")
      .then((data) => setLista(asList(data)))
      .catch(() => setErro("Erro ao carregar usuários."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (ready && isCoordenador) load();
    else if (ready) setLoading(false);
  }, [ready, isCoordenador]);

  async function criar(ev: FormEvent) {
    ev.preventDefault();
    setErro("");
    try {
      await apiFetch("/usuarios-staff/", {
        method: "POST",
        body: JSON.stringify({ nome, email, tipo_perfil: tipoPerfil, senha }),
      });
      setNome("");
      setEmail("");
      setSenha("");
      load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao criar usuário.");
    }
  }

  async function alternarAtivo(u: UsuarioStaff) {
    try {
      await apiFetch(`/usuarios-staff/${u.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !u.is_active }),
      });
      load();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao atualizar.");
    }
  }

  return (
    <StaffLayout loading={loading}>
      <StaffPage
        title="Usuários da pastoral"
        description="Gerencie contas de secretário e padre."
        onLogout={sair}
      >
        {!isCoordenador ? (
          <p className="text-muted-foreground">Apenas o coordenador pode gerenciar usuários.</p>
        ) : (
          <>
            {erro && (
              <p className="text-destructive bg-destructive/10 px-4 py-3 rounded-lg mb-4" role="alert">
                {erro}
              </p>
            )}

            <form onSubmit={criar} className="card-liturgical p-6 mb-8 space-y-4">
              <h2 className="font-display text-lg font-semibold">Novo usuário staff</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <input
                  placeholder="Nome"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="input-field"
                  required
                />
                <input
                  type="email"
                  placeholder="E-mail"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  required
                />
                <select
                  value={tipoPerfil}
                  onChange={(e) => setTipoPerfil(e.target.value as "Secretario" | "Padre")}
                  className="input-field"
                >
                  <option value="Secretario">Secretário</option>
                  <option value="Padre">Padre</option>
                </select>
                <input
                  type="password"
                  placeholder="Senha inicial"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  className="input-field"
                  minLength={6}
                  required
                />
              </div>
              <button type="submit" className="btn-primary w-fit">
                Criar usuário
              </button>
            </form>

            <div className="space-y-3">
              {lista.map((u) => (
                <div key={u.id} className="card-liturgical p-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium">{u.nome}</p>
                    <p className="text-sm text-muted-foreground">
                      {u.email} · {u.tipo_perfil}
                      {!u.is_active && " · Inativo"}
                    </p>
                  </div>
                  {u.tipo_perfil !== "Coordenador" && (
                    <button
                      type="button"
                      onClick={() => alternarAtivo(u)}
                      className="btn-outline text-sm"
                    >
                      {u.is_active ? "Desativar" : "Reativar"}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </StaffPage>
    </StaffLayout>
  );
}
