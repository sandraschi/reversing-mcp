const TAURI_BACKEND_URL = "http://127.0.0.1:10750";
const STORAGE_KEY = "reversing_api_base";

function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(
    (window as unknown as { __TAURI__?: unknown }).__TAURI__ ||
      (window as unknown as { __TAURI_INTERNALS__?: unknown })
        .__TAURI_INTERNALS__,
  );
}

function getEnvApiBase(): string | undefined {
  if (typeof import.meta === "undefined") return undefined;
  const env = (import.meta as unknown as { env?: { VITE_API_URL?: string } })
    .env;
  return env?.VITE_API_URL;
}

/**
 * Backend API base (FastAPI, SOTA port 10750).
 * Order: VITE_API_URL env > localStorage (reversing_api_base) > Tauri check > same-origin relative ("").
 */
export function getApiBase(): string {
  const env = getEnvApiBase();
  if (env) return env;
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
  }
  if (isTauri()) {
    return TAURI_BACKEND_URL;
  }
  return "";
}

export function setApiBase(url: string): void {
  if (typeof localStorage !== "undefined")
    localStorage.setItem(STORAGE_KEY, url);
}

/** For components that need a stable ref; call getApiBase() when making requests. */
export const API_BASE = getApiBase();
