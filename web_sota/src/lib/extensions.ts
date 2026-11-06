/** Ghidra community extensions: REST client for /api/v1/extensions/*. */
import { getApiBase } from "@/common/api";

export interface ExtensionEntry {
  name: string;
  repo: string;
  kind: string;
  targets: string[];
  description: string;
  install_kind: string;
  installed: boolean;
  enabled: boolean;
  installed_path: string | null;
}

export interface InstalledExtension {
  name: string;
  path: string;
  enabled: boolean;
  root: string;
  version?: string;
  description?: string;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${getApiBase()}${path}`, init);
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`);
  return (await r.json()) as T;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return getJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}

export const extensionsApi = {
  list: () =>
    getJson<{
      success: boolean;
      extensions: InstalledExtension[];
      count: number;
    }>("/api/v1/extensions"),
  catalog: () =>
    getJson<{ success: boolean; entries: ExtensionEntry[]; count: number }>(
      "/api/v1/extensions/catalog",
    ),
  install: (name: string, version?: string | null) =>
    postJson<{ success: boolean; message?: string; error?: string }>(
      "/api/v1/extensions/install",
      { name, version: version ?? null },
    ),
  remove: (name: string, confirm: boolean) =>
    postJson<{ success: boolean; message?: string; error?: string }>(
      "/api/v1/extensions/remove",
      { name, confirm },
    ),
  setEnabled: (name: string, enabled: boolean) =>
    postJson<{ success: boolean; message?: string; error?: string }>(
      "/api/v1/extensions/enabled",
      { name, enabled },
    ),
};
