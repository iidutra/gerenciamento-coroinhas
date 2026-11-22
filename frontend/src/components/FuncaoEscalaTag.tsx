import { funcaoEscalaLabel } from "@/lib/scheduling";

const TAG_FUNC_CLASS =
  "inline-flex text-[10px] font-semibold uppercase tracking-wide rounded px-1.5 py-0.5 bg-blue-500/15 text-blue-800 dark:text-blue-300 shrink-0";

export function FuncaoEscalaTag({ funcao }: { funcao?: string | null }) {
  if (!funcao) return null;
  const label = funcaoEscalaLabel(funcao);
  if (!label) return null;
  return <span className={TAG_FUNC_CLASS}>{label}</span>;
}

export function FuncaoEscalaTags({
  funcao,
  funcoes,
}: {
  funcao?: string | null;
  funcoes?: string[] | null;
}) {
  const lista =
    funcoes?.length ? funcoes : funcao ? [funcao] : [];
  if (!lista.length) return null;
  return (
    <span className="inline-flex flex-wrap items-center gap-1">
      {lista.map((f) => (
        <FuncaoEscalaTag key={f} funcao={f} />
      ))}
    </span>
  );
}