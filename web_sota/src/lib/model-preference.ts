/**
 * Resident-first local LLM model selection for reversing-mcp webapp.
 *
 * VENDORED (subset) from mcp-central-docs/templates/llm-detect/model-preference.ts
 * (canonical source; Python twin: templates/llm-detect/detect.py pick_model).
 * Subset: preference list + pick/fit helpers. Probing lives server-side in
 * GET /api/llm/discover (running/models/default); fetchOllamaModels/fetchGpus/
 * pickTargetGpu/resolveDefaultModel were intentionally not carried over.
 * Pull updates from the template, then re-apply the subset.
 *
 * The rule: NEVER load a different model while a preferred one is resident in
 * Ollama. Loading a second big model evicts the first and forces a ~30s cold
 * reload for every client using it. So the chat/settings default must be
 * resolved resident-first:
 *
 *   1. Probe Ollama /api/ps (models loaded right now)
 *   2. Use the highest-preference model that is already loaded
 *   3. If nothing loaded, use the highest-preference INSTALLED model (/api/tags)
 *   4. Fall back to the old default only if the preference list is not installed
 */

export const FLEET_MODEL_PREFERENCE = [
  "qwen3.8:27b",
  "gemma4:12b",
  "qwen2.5-coder:32b-instruct-q4_K_M",
  "deepseek-r1:32b",
  "gemma4:26b",
  "qwen2.5-coder:14b",
  "llama3.1:8b",
  "qwen2.5-coder:7b",
  "mistral:7b",
  "llama3.2:3b",
] as const;

/** Approx. minimum VRAM (MB) per model tier - matches TIERS in detect.py. */
const MODEL_TIER_MIN_VRAM_MB: Record<string, number> = {
  "qwen3.8:27b": 20000,
  "gemma4:12b": 20000,
  "qwen2.5-coder:32b-instruct-q4_K_M": 32000,
  "deepseek-r1:32b": 32000,
  "gemma4:26b": 32000,
  "qwen2.5-coder:14b": 20000,
  "llama3.1:8b": 20000,
  "qwen2.5-coder:7b": 14000,
  "mistral:7b": 14000,
  "llama3.2:3b": 14000,
};

export interface GpuInfo {
  index: number;
  name: string;
  vramMb: number;
}

export interface OllamaModelsState {
  /** Models currently loaded in Ollama (from GET /api/ps). */
  loaded: string[];
  /** Models installed in Ollama (from GET /api/tags). */
  installed: string[];
}

/**
 * Pick the default chat model, resident-first AND target-GPU-aware.
 * Returns "" if none available. Models that do not fit the target card
 * (e.g. a 27B on a 16 GB secondary) are skipped entirely.
 */
export function pickPreferredModel(
  psModels: string[],
  tagsModels: string[],
  targetGpu?: GpuInfo | null,
): string {
  const installedOrder = FLEET_MODEL_PREFERENCE.filter(
    (m) => tagsModels.includes(m) && fitsTarget(m, targetGpu ?? null),
  );
  const loaded = new Set(psModels);
  for (const m of installedOrder) {
    if (loaded.has(m)) return m; // resident wins - never evict it
  }
  return installedOrder[0] ?? ""; // fallback: highest-preference installed that fits
}

/** True when a model's tier fits the target GPU's VRAM. */
export function fitsTarget(model: string, target: GpuInfo | null): boolean {
  if (!target?.vramMb) return true;
  const minVram = MODEL_TIER_MIN_VRAM_MB[model];
  if (minVram === undefined) return true;
  return target.vramMb >= minVram;
}
