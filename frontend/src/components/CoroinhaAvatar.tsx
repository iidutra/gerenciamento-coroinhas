"use client";

import { useState } from "react";
import Image from "next/image";

export const AVATAR_PLACEHOLDER_SRC = "/avatar-placeholder.svg";

interface CoroinhaAvatarProps {
  nome: string;
  fotoUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = {
  sm: "size-8 text-xs",
  md: "size-10 text-sm",
  lg: "size-16 text-2xl",
};

const px = { sm: 32, md: 40, lg: 64 };

export function CoroinhaAvatar({ nome, fotoUrl, size = "md", className = "" }: CoroinhaAvatarProps) {
  const dim = px[size];
  const [fotoIndisponivel, setFotoIndisponivel] = useState(false);
  const src = fotoUrl && !fotoIndisponivel ? fotoUrl : AVATAR_PLACEHOLDER_SRC;

  return (
    <Image
      src={src}
      alt={fotoUrl && !fotoIndisponivel ? `Foto de ${nome}` : `Perfil de ${nome} (sem foto)`}
      width={dim}
      height={dim}
      className={`rounded-full object-cover shrink-0 bg-gold-soft ${sizes[size]} ${className}`}
      unoptimized
      onError={() => setFotoIndisponivel(true)}
    />
  );
}
