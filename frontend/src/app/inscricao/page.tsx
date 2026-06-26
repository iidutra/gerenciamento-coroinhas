"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Church,
  Camera,
  Cross,
  Loader2,
  Send,
  User,
  Users,
} from "lucide-react";
import { CoroinhaAvatar } from "@/components/CoroinhaAvatar";
import { FormSection } from "@/components/FormField";
import { apiFetchForm } from "@/lib/api";
import { fetchConfigPublica } from "@/lib/config-publica";
import type { EtapaCatequese } from "@/types";

const ETAPAS_CATEQUESE: { value: Exclude<EtapaCatequese, "">; label: string }[] = [
  { value: "PreEucaristia", label: "Pré-Eucaristia" },
  { value: "PrimeiraEucaristia", label: "Primeira Eucaristia" },
  { value: "Crisma", label: "Crisma" },
];

function calcularIdade(iso: string): number | null {
  if (!iso) return null;
  const nasc = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(nasc.getTime())) return null;
  const hoje = new Date();
  let anos = hoje.getFullYear() - nasc.getFullYear();
  const m = hoje.getMonth() - nasc.getMonth();
  if (m < 0 || (m === 0 && hoje.getDate() < nasc.getDate())) anos -= 1;
  return anos >= 0 ? anos : null;
}

export default function InscricaoPage() {
  const [loading, setLoading] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [erro, setErro] = useState("");
  const [nomeCoroinha, setNomeCoroinha] = useState("");
  const [dataNascimento, setDataNascimento] = useState("");
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);
  const [fazCatequese, setFazCatequese] = useState(false);
  const [etapaCatequese, setEtapaCatequese] = useState<EtapaCatequese>("");
  const [fazIam, setFazIam] = useState(false);
  const [verificando, setVerificando] = useState(true);
  const [inscricoesAbertas, setInscricoesAbertas] = useState(false);

  useEffect(() => {
    fetchConfigPublica()
      .then((cfg) => setInscricoesAbertas(cfg.inscricoes_abertas))
      .finally(() => setVerificando(false));
  }, []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErro("");
    setLoading(true);

    const formEl = new FormData(e.currentTarget);
    const telMae = String(formEl.get("telefone_mae") || "").trim();
    const telPai = String(formEl.get("telefone_pai") || "").trim();
    const payload = {
      coroinha: {
        nome: formEl.get("nome_coroinha"),
        data_nascimento: dataNascimento,
        endereco: formEl.get("endereco"),
        faz_catequese: fazCatequese,
        etapa_catequese: fazCatequese ? etapaCatequese : "",
        faz_iam: fazIam,
      },
      responsavel: {
        nome_pai: formEl.get("nome_pai"),
        telefone_pai: telPai,
        nome_mae: formEl.get("nome_mae"),
        telefone_mae: telMae,
        // usado para notificação opcional na aprovação
        telefone_principal: telMae || telPai,
      },
    };

    const body = new FormData();
    body.append("dados", JSON.stringify(payload));
    const foto = formEl.get("foto") as File | null;
    if (foto && foto.size > 0) {
      body.append("foto", foto);
    }

    try {
      await apiFetchForm("/inscricoes/publica", body, { auth: false });
      setSucesso(true);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao enviar inscrição");
    } finally {
      setLoading(false);
    }
  }

  if (verificando) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <Loader2 className="size-8 animate-spin text-burgundy" aria-label="Carregando" />
      </main>
    );
  }

  if (!inscricoesAbertas) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md text-center card-liturgical shadow-elegant p-8">
          <Church className="size-14 text-gold mx-auto mb-4" aria-hidden />
          <h1 className="font-display text-2xl font-semibold text-burgundy">Inscrições fechadas</h1>
          <p className="text-muted-foreground mt-2">
            As inscrições online ainda não estão abertas. Aguarde o comunicado da pastoral ou fale com a
            coordenação.
          </p>
          <Link href="/" className="btn-outline mt-6 inline-flex gap-2">
            <ArrowLeft className="size-4" aria-hidden />
            Voltar ao início
          </Link>
        </div>
      </main>
    );
  }

  if (sucesso) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md text-center card-liturgical shadow-elegant p-8">
          <CheckCircle2 className="size-14 text-emerald-600 mx-auto mb-4" aria-hidden />
          <h1 className="font-display text-2xl font-semibold text-burgundy">Inscrição enviada!</h1>
          <p className="text-muted-foreground mt-2">Aguarde a aprovação da coordenação.</p>
          <Link href="/" className="btn-outline mt-6 inline-flex gap-2">
            <ArrowLeft className="size-4" aria-hidden />
            Voltar ao início
          </Link>
        </div>
      </main>
    );
  }

  const idade = calcularIdade(dataNascimento);

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-burgundy mb-4"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Voltar
        </Link>

        <div className="card-liturgical shadow-elegant p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="size-11 rounded-full bg-gradient-gold grid place-items-center text-burgundy-deep">
              <Church className="size-5" aria-hidden />
            </div>
            <div>
              <h1 className="font-display text-3xl font-semibold text-burgundy">Inscrição Online</h1>
              <p className="text-muted-foreground text-sm">Substitui a ficha de papel.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            <FormSection title="Dados do coroinha" icon={User}>
              <div className="grid gap-4">
                <input
                  name="nome_coroinha"
                  placeholder="Nome completo *"
                  required
                  className="input-field"
                  value={nomeCoroinha}
                  onChange={(e) => setNomeCoroinha(e.target.value)}
                />
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="insc-nasc" className="block text-sm font-medium mb-1.5">
                      Data de nascimento *
                    </label>
                    <input
                      id="insc-nasc"
                      name="data_nascimento"
                      type="date"
                      required
                      className="input-field w-full"
                      value={dataNascimento}
                      onChange={(e) => setDataNascimento(e.target.value)}
                    />
                  </div>
                  <div>
                    <label htmlFor="insc-idade" className="block text-sm font-medium mb-1.5">
                      Idade
                    </label>
                    <input
                      id="insc-idade"
                      readOnly
                      value={idade != null ? `${idade} anos` : ""}
                      placeholder="Calculada pela data"
                      className="input-field w-full bg-muted/40 text-muted-foreground"
                    />
                  </div>
                </div>
                <input name="endereco" placeholder="Endereço" className="input-field" />
              </div>
            </FormSection>

            <FormSection title="Responsáveis" icon={Users}>
              <div className="grid gap-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <input name="nome_pai" placeholder="Nome do pai" className="input-field" />
                  <input name="telefone_pai" placeholder="Telefone do pai" className="input-field" />
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  <input name="nome_mae" placeholder="Nome da mãe" className="input-field" />
                  <input name="telefone_mae" placeholder="Telefone da mãe" className="input-field" />
                </div>
              </div>
            </FormSection>

            <FormSection title="Catequese e IAM" icon={Cross}>
              <div className="space-y-4">
                <fieldset className="rounded-lg border border-border p-4">
                  <legend className="px-1 text-sm font-medium">Está fazendo catequese?</legend>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_catequese"
                        checked={fazCatequese}
                        onChange={() => setFazCatequese(true)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Sim
                    </label>
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_catequese"
                        checked={!fazCatequese}
                        onChange={() => {
                          setFazCatequese(false);
                          setEtapaCatequese("");
                        }}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Não
                    </label>
                  </div>
                  {fazCatequese && (
                    <div className="mt-3 flex flex-wrap gap-3 text-sm">
                      {ETAPAS_CATEQUESE.map((etapa) => (
                        <label
                          key={etapa.value}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-secondary cursor-pointer transition-colors"
                        >
                          <input
                            type="radio"
                            name="etapa_catequese"
                            checked={etapaCatequese === etapa.value}
                            onChange={() => setEtapaCatequese(etapa.value)}
                            className="accent-[var(--burgundy)] size-4"
                          />
                          {etapa.label}
                        </label>
                      ))}
                    </div>
                  )}
                </fieldset>

                <fieldset className="rounded-lg border border-border p-4">
                  <legend className="px-1 text-sm font-medium">Faz parte da IAM?</legend>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_iam"
                        checked={fazIam}
                        onChange={() => setFazIam(true)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Sim
                    </label>
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="faz_iam"
                        checked={!fazIam}
                        onChange={() => setFazIam(false)}
                        className="accent-[var(--burgundy)] size-4"
                      />
                      Não
                    </label>
                  </div>
                </fieldset>
              </div>
            </FormSection>

            <FormSection title="Foto do coroinha" icon={Camera}>
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-3">
                <CoroinhaAvatar nome={nomeCoroinha || "Coroinha"} fotoUrl={fotoPreview} size="lg" />
                <p className="text-sm text-muted-foreground flex-1">
                  Foto de rosto para identificação nas escalas (opcional). Se não enviar, aparecerá o
                  avatar padrão até a coordenação ou família anexar a foto.
                </p>
              </div>
              <input
                name="foto"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="input-field file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-1.5 file:text-sm"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) {
                    setFotoPreview(null);
                    return;
                  }
                  setFotoPreview(URL.createObjectURL(file));
                }}
              />
            </FormSection>

            {erro && (
              <p className="text-destructive text-sm bg-destructive/10 px-3 py-2 rounded-lg" role="alert">
                {erro}
              </p>
            )}

            <div className="flex flex-wrap gap-3 pt-2">
              <Link href="/" className="btn-outline">
                Cancelar
              </Link>
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Send className="size-4" aria-hidden />
                    Enviar inscrição
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
