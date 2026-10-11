/**
 * Global LLM selection store (fleet standard: Zustand, not page-local useState).
 *
 * Owns provider/model/running/models/detected. Persists selection to
 * localStorage (llm_provider/llm_model) and broadcasts same-tab so Chat and
 * Settings stay in sync; cross-tab sync arrives via the storage event.
 */
import { create } from "zustand";

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";
const SELECTION_EVENT = "llm-selection-changed";

export interface Selection {
  provider: string;
  model: string;
}

function readLS(key: string): string {
  try {
    return localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

interface LlmState extends Selection {
  running: string[];
  models: string[];
  detected: boolean | null;
  select: (provider: string, model: string) => void;
  applyDiscovery: (
    models: string[],
    running: string[],
    detected: boolean,
  ) => void;
}

function broadcast(sel: Selection) {
  try {
    localStorage.setItem(PROVIDER_KEY, sel.provider);
    localStorage.setItem(MODEL_KEY, sel.model);
  } catch {
    /* private mode */
  }
  try {
    window.dispatchEvent(
      new CustomEvent(SELECTION_EVENT, {
        detail: { provider: sel.provider, model: sel.model },
      }),
    );
  } catch {
    /* non-DOM */
  }
}

export const useLlmStore = create<LlmState>()((set) => ({
  provider: readLS(PROVIDER_KEY) || "ollama",
  model: readLS(MODEL_KEY),
  running: [],
  models: [],
  detected: null,
  select: (provider, model) =>
    set(() => {
      broadcast({ provider, model });
      return { provider, model };
    }),
  applyDiscovery: (models, running, detected) =>
    set((s) => ({
      models,
      running,
      detected,
      model:
        s.model && models.includes(s.model) ? s.model : (models[0] ?? s.model),
    })),
}));

/** Cross-tab sync: adopt selections saved by other tabs. */
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === PROVIDER_KEY || e.key === MODEL_KEY) {
      useLlmStore.setState({
        provider: readLS(PROVIDER_KEY) || "ollama",
        model: readLS(MODEL_KEY),
      });
    }
  });
  window.addEventListener(SELECTION_EVENT, (e) => {
    const d = (e as CustomEvent).detail as Selection | undefined;
    if (d && typeof d.provider === "string" && typeof d.model === "string") {
      useLlmStore.setState({ provider: d.provider, model: d.model });
    }
  });
}
