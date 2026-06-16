import type { NextConfig } from "next";

function mediaRemotePatterns() {
  const patterns: NonNullable<NextConfig["images"]>["remotePatterns"] = [
    { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
    { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
    { protocol: "https", hostname: "*.up.railway.app", pathname: "/media/**" },
  ];
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (apiUrl) {
    try {
      const { protocol, hostname } = new URL(apiUrl);
      if (hostname && !patterns.some((p) => p.hostname === hostname)) {
        patterns.push({
          protocol: protocol.replace(":", "") as "http" | "https",
          hostname,
          pathname: "/media/**",
        });
      }
    } catch {
      /* ignore invalid URL at build time */
    }
  }
  return patterns;
}

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: mediaRemotePatterns(),
  },
};

export default nextConfig;