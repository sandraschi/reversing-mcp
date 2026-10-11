/**
 * useZoom — fleet Tauri zoom hook (Ctrl+Scroll, Ctrl+0 reset).
 *
 * Levels {0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0}, persisted to
 * localStorage "tauri-zoom", applied on mount. CSS `zoom` fallback covers the
 * dev browser; Tauri WebView honors the same property.
 */
import { useCallback, useEffect, useState } from "react";

const LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];
const LS_KEY = "tauri-zoom";

function loadZoom(): number {
  try {
    const v = Number(localStorage.getItem(LS_KEY));
    if (LEVELS.includes(v)) return v;
  } catch {
    /* private mode */
  }
  return 1.0;
}

export function useZoom() {
  const [zoom, setZoom] = useState(loadZoom);

  useEffect(() => {
    try {
      (document.documentElement.style as CSSStyleDeclaration & { zoom?: string }).zoom =
        String(zoom);
      localStorage.setItem(LS_KEY, String(zoom));
    } catch {
      /* non-DOM */
    }
  }, [zoom]);

  const step = useCallback((dir: 1 | -1) => {
    setZoom((z) => {
      const i = LEVELS.indexOf(z);
      const n = Math.min(LEVELS.length - 1, Math.max(0, (i < 0 ? 4 : i) + dir));
      return LEVELS[n];
    });
  }, []);

  useEffect(() => {
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      step(e.deltaY < 0 ? 1 : -1);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "0") {
        e.preventDefault();
        setZoom(1.0);
      }
    };
    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKey);
    };
  }, [step]);

  return { zoom, setZoom, reset: () => setZoom(1.0) };
}
