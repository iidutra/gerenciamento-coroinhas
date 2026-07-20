"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Church,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Phone,
  Search,
  User,
  UserRound,
} from "lucide-react";
import { InputField } from "@/components/FormField";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { apiFetch, normalizarCpf } from "@/lib/api";
import { formatarCpf } from "@/lib/format";
import type { CoroinhaVerificada } from "@/types";

type Etapa = "verificar" | "escolher" | "cadastrar" | "sucesso";

export default function AcessoPage() {
  const [etapa, setEtapa] = useState<Etapa>("verificar");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  // Passo 1 — identificação do coroinha
  const [nomeCoroinha, setNomeCoroinha] = useState("");
  const [dataNascimento, setDataNascimento] = useState("");
  const [coroinhas, setCoroinhas] = useState<CoroinhaVerificada[]>([]);
  const [selecionado, setSelecionado] = useState<CoroinhaVerificada | null>(null);

  // Passo 2 — dados do responsável
  const [nomeResponsavel, setNomeResponsavel] = useState("");
  const [cpf, setCpf] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [senha, setSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  async function handleVerificar(e: FormEvent) {
    e.preventDefault();
    setErro("");
    setLoading(true);
    try {
      const data = await apiFetch<{ coroinhas: CoroinhaVerificada[] }>(
        "/portal/acesso/verificar",
        {
          method: "POST",
          auth: false,
          body: JSON.stringify({ nome: nomeCoroinha, data_nascimento: dataNascimento }),
        },
      );
      const lista = data.coroinhas ?? [];
      setCoroinhas(lista);
      if (lista.length === 1) {
        setSelecionado(lista[0]);
        setEtapa("cadastrar");
      } else {
        setSelecionado(null);
        setEtapa("escolher");
      }
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível localizar o coroinha.");
    } finally {
      setLoading(false);
    }
  }

  function escolher(c: CoroinhaVerificada) {
    setSelecionado(c);
    setErro("");
    setEtapa("cadastrar");
  }

  async function handleSolicitar(e: FormEvent) {
    e.preventDefault();
    if (!selecionado) return;
    setErro("");
    if (senha !== confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }
    setLoading(true);
    try {
      await apiFetch("/portal/acesso/solicitar", {
        method: "POST",
        auth: false,
        body: JSON.stringify({
          coroinha_id: selecionado.id,
          nome: selecionado.nome,
          data_nascimento: dataNascimento,
          nome_responsavel: nomeResponsavel,
          cpf: normalizarCpf(cpf),
          whatsapp,
          senha,
          confirmar_senha: confirmarSenha,
        }),
      });
      setEtapa("sucesso");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não foi possível enviar o pedido.");
    } finally {
      setLoading(false);
    }
  }

  function voltarParaBusca() {
    setEtapa("verificar");
    setErro("");
    setSelecionado(null);
    setCoroinhas([]);
  }

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="w-full max-w-md mx-auto">
        <Link
          href="/login"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-burgundy mb-4"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Voltar ao login
        </Link>

        <div className="card-liturgical shadow-elegant p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="size-11 rounded-full bg-gradient-gold grid place-items-center text-burgundy-deep shadow-gold">
              <Church className="size-5" aria-hidden />
            </div>
            <div>
              <h1 className="font-display text-2xl font-semibold text-burgundy">Acesso dos Pais</h1>
              <p className="text-sm text-muted-foreground">Acompanhe seu filho na pastoral.</p>
            </div>
          </div>

          {/* Indicador de etapas */}
          {etapa !== "sucesso" && (
            <div className="flex items-center gap-2 mb-6 text-xs">
              <span
                className={`flex-1 h-1.5 rounded-full ${
                  etapa === "verificar" || etapa === "escolher" ? "bg-gold" : "bg-emerald-500"
                }`}
              />
              <span
                className={`flex-1 h-1.5 rounded-full ${etapa === "cadastrar" ? "bg-gold" : "bg-border"}`}
              />
            </div>
          )}

          {erro && (
            <p className="mb-4 text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg" role="alert">
              {erro}
            </p>
          )}

          {etapa === "verificar" && (
            <form onSubmit={handleVerificar} className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Informe o <strong>nome</strong> e a <strong>data de nascimento</strong> do coroinha
                para localizá-lo.
              </p>
              <InputField
                label="Nome completo do coroinha"
                icon={User}
                type="text"
                value={nomeCoroinha}
                onChange={(e) => setNomeCoroinha(e.target.value)}
                placeholder="Ex.: João da Silva"
                required
              />
              <InputField
                label="Data de nascimento"
                icon={CalendarDays}
                type="date"
                value={dataNascimento}
                onChange={(e) => setDataNascimento(e.target.value)}
                required
              />
              <button type="submit" disabled={loading} className="btn-primary w-full gap-2">
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    Procurando...
                  </>
                ) : (
                  <>
                    <Search className="size-4" aria-hidden />
                    Localizar coroinha
                  </>
                )}
              </button>
            </form>
          )}

          {etapa === "escolher" && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Encontramos mais de um coroinha com esses dados. Selecione o correto:
              </p>
              {coroinhas.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => escolher(c)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg border border-border hover:border-gold hover:bg-gold/5 transition-colors text-left"
                >
                  <CoroinhaAvatar nome={c.nome} fotoUrl={null} size="md" />
                  <div className="flex-1">
                    <p className="font-medium">{c.nome}</p>
                    <p className="text-xs text-muted-foreground">{c.idade} anos</p>
                  </div>
                  <ArrowRight className="size-4 text-muted-foreground" aria-hidden />
                </button>
              ))}
              <button type="button" onClick={voltarParaBusca} className="btn-outline w-full">
                Buscar novamente
              </button>
            </div>
          )}

          {etapa === "cadastrar" && selecionado && (
            <form onSubmit={handleSolicitar} className="space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-gold/5 border border-gold/30">
                <CoroinhaAvatar nome={selecionado.nome} fotoUrl={null} size="md" />
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground">Coroinha encontrado</p>
                  <p className="font-medium">{selecionado.nome}</p>
                  <p className="text-xs text-muted-foreground">{selecionado.idade} anos</p>
                </div>
                <button
                  type="button"
                  onClick={voltarParaBusca}
                  className="text-xs text-burgundy hover:underline"
                >
                  Trocar
                </button>
              </div>

              <p className="text-sm text-muted-foreground">
                Agora crie seu acesso. A coordenação vai revisar e liberar.
              </p>

              <InputField
                label="Seu nome completo (pai/mãe/responsável)"
                icon={UserRound}
                type="text"
                value={nomeResponsavel}
                onChange={(e) => setNomeResponsavel(e.target.value)}
                placeholder="Ex.: Maria da Silva"
                required
              />
              <InputField
                label="Seu CPF"
                icon={UserRound}
                type="text"
                inputMode="numeric"
                value={cpf}
                onChange={(e) => setCpf(formatarCpf(e.target.value))}
                placeholder="000.000.000-00"
                autoComplete="username"
                required
              />
              <InputField
                label="WhatsApp (opcional)"
                icon={Phone}
                type="tel"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                placeholder="(69) 99999-0000"
              />

              <div>
                <label htmlFor="senha" className="block text-sm font-medium mb-1.5">
                  Crie uma senha
                </label>
                <div className="relative">
                  <KeyRound
                    className="absolute left-3 top-1/2 z-10 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none"
                    aria-hidden
                  />
                  <input
                    id="senha"
                    type={mostrarSenha ? "text" : "password"}
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    className="input-field input-field--icon-left input-field--icon-right"
                    placeholder="Mínimo 6 caracteres"
                    minLength={6}
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setMostrarSenha(!mostrarSenha)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {mostrarSenha ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>

              <InputField
                label="Confirme a senha"
                icon={KeyRound}
                type={mostrarSenha ? "text" : "password"}
                value={confirmarSenha}
                onChange={(e) => setConfirmarSenha(e.target.value)}
                minLength={6}
                autoComplete="new-password"
                required
              />

              <button type="submit" disabled={loading} className="btn-primary w-full gap-2">
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    Enviando...
                  </>
                ) : (
                  <>
                    <ArrowRight className="size-4" aria-hidden />
                    Enviar pedido de acesso
                  </>
                )}
              </button>
            </form>
          )}

          {etapa === "sucesso" && (
            <div className="text-center py-4">
              <CheckCircle2 className="size-14 text-emerald-600 mx-auto mb-4" aria-hidden />
              <h2 className="font-display text-xl font-semibold text-burgundy">Pedido enviado!</h2>
              <p className="text-muted-foreground mt-2 text-sm">
                Assim que a coordenação aprovar, você poderá entrar com seu <strong>CPF</strong> e a
                senha que criou.
              </p>
              <Link href="/login" className="btn-primary mt-6 inline-flex gap-2">
                <ArrowLeft className="size-4" aria-hidden />
                Ir para o login
              </Link>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
