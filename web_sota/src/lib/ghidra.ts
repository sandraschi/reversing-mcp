/**
 * Ghidra forwarding session: REST client, types and stores.
 *
 * Backend: /api/v1/ghidra/* (ghidra_bridge.py). The same bridge backs the
 * `ghidra` MCP tool, but the webapp backend is its own process, so a session
 * started from a chat client over stdio is not visible here (gui mode lets
 * both attach to one running Ghidra).
 */
import { getApiBase } from "@/common/api";
import { create } from "zustand";
import {
  createJSONStorage,
  persist,
  type StateStorage,
} from "zustand/middleware";

export type SessionState = "stopped" | "starting" | "ready" | "error";

export interface GhidraSession {
  success: boolean;
  state: SessionState;
  mode: "headless" | "watch" | null;
  target: string | null;
  tool_count: number;
  error: string | null;
  log_file: string | null;
  gui_window?: boolean;
  elapsed_s?: number;
  startup_s?: number;
  hint?: string;
}

export interface ToolSummary {
  name: string;
  summary: string;
}

export interface ToolPage {
  success: boolean;
  total: number;
  offset: number;
  next_offset: number | null;
  tools: ToolSummary[];
  error?: string;
}

export interface JsonSchema {
  type?: string | string[];
  description?: string;
  properties?: Record<string, JsonSchema>;
  required?: string[];
  default?: unknown;
  enum?: unknown[];
  items?: JsonSchema;
}

export interface ToolDetail {
  success: boolean;
  name: string;
  description: string;
  input_schema: JsonSchema;
  error?: string;
  did_you_mean?: string[];
}

export interface ContentBlock {
  type: string;
  text?: string | null;
  uri?: string;
  mime_type?: string | null;
  truncated_from?: number;
}

export interface CallResult {
  success: boolean;
  tool: string;
  elapsed_s?: number;
  content?: ContentBlock[];
  structured?: unknown;
  note?: string;
  error?: string;
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

export const ghidraApi = {
  session: () => getJson<GhidraSession>("/api/v1/ghidra/session"),
  start: (mode: "headless" | "watch") =>
    postJson<GhidraSession & { message?: string; busy?: boolean }>(
      "/api/v1/ghidra/session/start",
      { mode, confirm: true },
    ),
  stop: () =>
    postJson<{ success: boolean; message: string }>(
      "/api/v1/ghidra/session/stop",
      {},
    ),
  /** Whole catalogue: the bridge pages at 100, so loop until done. */
  allTools: async (): Promise<ToolSummary[]> => {
    const out: ToolSummary[] = [];
    let offset: number | null = 0;
    while (offset !== null) {
      const page: ToolPage = await getJson<ToolPage>(
        `/api/v1/ghidra/tools?offset=${offset}&limit=100`,
      );
      if (!page.success) throw new Error(page.error ?? "Tool listing failed");
      out.push(...page.tools);
      offset = page.next_offset;
    }
    return out;
  },
  describe: (name: string) =>
    getJson<ToolDetail>(`/api/v1/ghidra/tools/${encodeURIComponent(name)}`),
  call: (tool: string, args: Record<string, unknown>, timeout_s?: number) =>
    postJson<CallResult>("/api/v1/ghidra/call", {
      tool,
      arguments: args,
      timeout_s: timeout_s ?? null,
    }),
};

/** ReVa tool names are verb-noun (get-functions, find-cross-references, ...). */
export function toolCategory(name: string): string {
  const head = name.split(/[-_]/)[0]?.toLowerCase() ?? "";
  const known: Record<string, string> = {
    get: "Read",
    list: "Read",
    read: "Read",
    search: "Search",
    find: "Search",
    trace: "Search",
    set: "Edit",
    rename: "Edit",
    create: "Edit",
    apply: "Edit",
    change: "Edit",
    remove: "Edit",
    delete: "Edit",
    edit: "Edit",
    write: "Edit",
    parse: "Types",
    validate: "Types",
    diff: "Diff",
    analyze: "Analysis",
    analysis: "Analysis",
    import: "Project",
    checkin: "Project",
    run: "Scripts",
  };
  return known[head] ?? "Other";
}

/** Skeleton arguments from a JSON schema: defaults where given, else typed blanks. */
export function skeletonArgs(
  schema: JsonSchema | undefined,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, prop] of Object.entries(schema?.properties ?? {})) {
    if (prop.default !== undefined) {
      out[key] = prop.default;
      continue;
    }
    const t = Array.isArray(prop.type) ? prop.type[0] : prop.type;
    out[key] =
      t === "integer" || t === "number"
        ? 0
        : t === "boolean"
          ? false
          : t === "array"
            ? []
            : t === "object"
              ? {}
              : "";
  }
  return out;
}

/* ------------------------------------------------------------------ stores */

/** localStorage that never throws (private windows, blocked storage). */
const safeStorage: StateStorage = {
  getItem: (k) => {
    try {
      return localStorage.getItem(k);
    } catch {
      return null;
    }
  },
  setItem: (k, v) => {
    try {
      localStorage.setItem(k, v);
    } catch {
      /* storage unavailable: history stays in memory */
    }
  },
  removeItem: (k) => {
    try {
      localStorage.removeItem(k);
    } catch {
      /* ignore */
    }
  },
};

export interface HistoryEntry {
  id: string;
  at: string;
  tool: string;
  args: Record<string, unknown>;
  ok: boolean;
  elapsed_s: number | null;
  preview: string;
}

interface HistoryStore {
  entries: HistoryEntry[];
  add: (e: Omit<HistoryEntry, "id" | "at">) => void;
  remove: (id: string) => void;
  clear: () => void;
}

const HISTORY_CAP = 500;

export const useGhidraHistory = create<HistoryStore>()(
  persist(
    (set) => ({
      entries: [],
      add: (e) =>
        set((s) => ({
          entries: [
            {
              ...e,
              id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
              at: new Date().toISOString(),
            },
            ...s.entries,
          ].slice(0, HISTORY_CAP),
        })),
      remove: (id) =>
        set((s) => ({ entries: s.entries.filter((x) => x.id !== id) })),
      clear: () => set({ entries: [] }),
    }),
    {
      name: "ghidra_call_history",
      storage: createJSONStorage(() => safeStorage),
    },
  ),
);

interface SessionStore {
  session: GhidraSession | null;
  reachable: boolean | null;
  refresh: () => Promise<void>;
}

export const useGhidraSession = create<SessionStore>()((set) => ({
  session: null,
  reachable: null,
  refresh: async () => {
    try {
      const s = await ghidraApi.session();
      set({ session: s, reachable: true });
    } catch {
      set({ reachable: false });
    }
  },
}));

export function previewOf(res: CallResult): string {
  if (!res.success && res.error) return res.error.slice(0, 200);
  const text = res.content?.find((b) => b.type === "text")?.text ?? "";
  return (text || JSON.stringify(res.structured ?? "")).slice(0, 200);
}
