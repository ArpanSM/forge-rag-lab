/**
 * The demo ships as a fully static export so it can be served from Cloudflare
 * Pages, GitHub Pages or any object store. Set NEXT_PUBLIC_BASE_PATH when the
 * site lives under a sub-path (for example a GitHub Pages project site).
 */
const rawBasePath = process.env.NEXT_PUBLIC_BASE_PATH?.trim() ?? "";
const basePath = rawBasePath.replace(/\/+$/, "") || undefined;

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  basePath,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
