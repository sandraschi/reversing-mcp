/**
 * Local-first LLM abstraction for the reversing-mcp webapp.
 *
 * Local = Ollama via the FastAPI backend (no direct browser-to-Ollama calls,
 * so no CORS wrestling). Cloud providers are an extension point: keys live in
 * Settings only and travel in POST bodies, never persisted server-side
 * (backend is Ollama-only today - cloud send is phase 2).
 *
 * Selection sync: llm_provider/llm_model in localStorage, broadcast
 * same-tab via CustomEvent and cross-tab via the storage event.
 */
import { getApiBase } from "@/common/api";

export interface LlmDiscovery {
  provider: string;
  detected: boolean;
  base_url: string;
  default_model: string | null;
  running: string[];
  models: string[];
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";
const SELECTION_EVENT = "llm-selection-changed";

export type Selection = { provider: string; model: string };

function storageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function storageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* quota */
  }
}

export function loadSelection(): Selection {
  return {
    provider: storageGet(PROVIDER_KEY) || "ollama",
    model: storageGet(MODEL_KEY) || "",
  };
}

export function saveSelection(provider: string, model: string) {
  storageSet(PROVIDER_KEY, provider);
  storageSet(MODEL_KEY, model);
  try {
    window.dispatchEvent(
      new CustomEvent(SELECTION_EVENT, { detail: { provider, model } }),
    );
  } catch {
    /* non-DOM */
  }
}

export function subscribeSelection(cb: (sel: Selection) => void): () => void {
  const onStorage = (e: StorageEvent) => {
    if (e.key === PROVIDER_KEY || e.key === MODEL_KEY) cb(loadSelection());
  };
  const onCustom = (e: Event) => {
    const d = (e as CustomEvent).detail as Selection | undefined;
    if (d && typeof d.provider === "string" && typeof d.model === "string")
      cb({ provider: d.provider, model: d.model });
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(SELECTION_EVENT, onCustom);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(SELECTION_EVENT, onCustom);
  };
}

/** Backend truth: Ollama presence, resident-first default, installed list. */
export async function fetchDiscovery(): Promise<LlmDiscovery> {
  const r = await fetch(`${getApiBase()}/api/llm/providers`);
  if (!r.ok) throw new Error(`discover failed: ${r.status}`);
  return (await r.json()) as LlmDiscovery;
}

/** Persist a model choice server-side (drives /api/v1/chat default) + locally. */
export async function selectModel(model: string): Promise<void> {
  const sel = loadSelection();
  saveSelection(sel.provider, model);
  await fetch(`${getApiBase()}/llm/select_model`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider: sel.provider, model }),
  }).catch(() => {
    /* backend down - local selection still applies on reconnect */
  });
}

/** Fetch the skill-first preprompt: skill list, then raw SKILL.md content. */
export async function fetchSkillPreprompt(
  skill = "primary",
): Promise<{ name: string; content: string }> {
  const list = await fetch(`${getApiBase()}/api/skills`).then((r) => r.json());
  const names: string[] = Array.isArray(list.skills) ? list.skills : [];
  const pick = names.includes(skill) ? skill : (names[0] ?? skill);
  const content = await fetch(
    `${getApiBase()}/skill/${encodeURIComponent(pick)}`,
  ).then((r) => r.text());
  return { name: pick, content };
}

/** Standard §1.2 composition: skill content + --- + role instructions. */
export function buildSystemPrompt(
  skillContent: string,
  personalityId: string,
  personalityPrompt: string,
  customPrompt: string,
): string {
  if (personalityId === "custom") return customPrompt || skillContent;
  return `${skillContent}\n\n---\n\n## Role\n${personalityPrompt}`;
}

export interface SendChatArgs {
  message: string;
  history: ChatMessage[];
  system?: string;
  model?: string;
}

/** POST /api/v1/chat. Throws with a readable message on failure. */
export async function sendChat(args: SendChatArgs): Promise<{
  reply: string;
  model: string;
}> {
  const r = await fetch(`${getApiBase()}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  if (r.status === 409) {
    const d = await r.json().catch(() => ({}));
    throw new Error(
      (d.detail as string) ||
        "No Ollama model available. Pull one, then retry.",
    );
  }
  if (!r.ok) throw new Error(`chat failed: ${r.status}`);
  return (await r.json()) as { reply: string; model: string };
}
