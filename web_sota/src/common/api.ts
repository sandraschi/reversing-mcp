const DEFAULT_API_BASE = "http://localhost:10750";
const STORAGE_KEY = "reversing_api_base";

function getEnvApiBase(): string | undefined {
  if (typeof import.meta === "undefined") return undefined;
  const env = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env;
  return env?.VITE_API_URL;
}

/**
 * Backend API base (FastAPI, SOTA port 10750).
 * Order: VITE_API_URL env > localStorage (reversing_api_base) > default.
 */
export function getApiBase(): string {
  const env = getEnvApiBase();
  if (env) return env;
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
  }
  return DEFAULT_API_BASE;
}

export function setApiBase(url: string): void {
  if (typeof localStorage !== "undefined") localStorage.setItem(STORAGE_KEY, url);
}

/** For components that need a stable ref; call getApiBase() when making requests. */
export const API_BASE = DEFAULT_API_BASE;
