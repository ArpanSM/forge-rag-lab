const baseUrl = (process.env.NEXT_PUBLIC_API_BASE ?? "").trim().replace(/\/+$/, "");

export const API_MODE: "live" | "mock" = baseUrl ? "live" : "mock";
export const API_BASE_URL = baseUrl;
