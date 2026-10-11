import { Activity, CheckCircle, Loader2, Search, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type GhidraStatus = { installed?: boolean; bridge_running?: boolean };

interface HealthData {
  status: string;
  version?: string;
  tool_count?: number;
  uptime_seconds?: number;
}

export function Dashboard() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [ghidra, setGhidra] = useState<GhidraStatus | null>(null);
  const [onboard, setOnboard] = useState<{
    ready?: boolean;
    reason?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  const base = getApiBase();

  const fetchAll = useCallback(async () => {
    const [h, g, o] = await Promise.all([
      fetch(`${base}/health`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/ghidra/status`)
        .then((r) => r.json())
        .catch(() => null),
      fetch(`${base}/api/llm/onboarding`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
    ]);
    setBackendOk(h !== null);
    setHealth(h);
    setGhidra(g);
    setOnboard(o);
    setLoading(false);
  }, [base]);

  // Tauri backend-status events when wrapped; HTTP polling above is the fallback.
  useEffect(() => {
    let unlisten: (() => void) | null = null;
    (async () => {
      try {
        const mod = await import("@tauri-apps/api/event");
        const { listen } = mod as unknown as {
          listen: (ev: string, cb: () => void) => Promise<() => void>;
        };
        unlisten = await listen("backend-status", () => fetchAll());
      } catch {
        /* browser dev: polling covers it */
      }
    })();
    return () => {
      if (unlisten) unlisten();
    };
  }, [fetchAll]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Exponential backoff retry when backend is down
  useEffect(() => {
    if (backendOk === false) {
      const delays = [1000, 2000, 4000, 8000, 16000, 30000];
      const delay = delays[Math.min(retryCount, delays.length - 1)];
      const timer = setTimeout(() => {
        setRetryCount((c) => c + 1);
        fetchAll();
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [backendOk, retryCount, fetchAll]);

  // No self-restart endpoint exists on the backend (POST /api/shutdown stops
  // without relaunch). Restart via the launcher: repo-root start.ps1 / start.bat.
  const handleRestart = async () => {
    setRetryCount((c) => c + 1);
    fetchAll();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Reversing MCP Dashboard
          </h2>
          <p className="text-slate-400">System overview and status</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2" data-testid="backend-dot">
            {backendOk === true ? (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            ) : null}
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                backendOk === true
                  ? "bg-emerald-500"
                  : backendOk === false
                    ? "bg-red-500"
                    : "bg-gray-500"
              }`}
            ></span>
          </span>
          <span className="text-xs text-slate-400">
            {backendOk === true
              ? "Live"
              : backendOk === false
                ? "Offline"
                : "Connecting..."}
          </span>
          {backendOk === false && (
            <button
              type="button"
              onClick={handleRestart}
              className="ml-2 p-1 rounded hover:bg-slate-800 transition-colors"
              title="Retry connection (restart the backend via start.ps1 if it stays down)"
            >
              <RefreshCw className="h-3 w-3 text-slate-400" />
            </button>
          )}
        </div>
      </div>

      {backendOk === true && onboard && onboard.ready === false && (
        <div
          className="rounded-lg border border-amber-800/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-200"
          data-testid="onboarding-cue"
        >
          <span className="font-medium">Get started with AI chat: </span>
          {onboard.reason}{" "}
          <a className="underline" href="#/settings">
            Open Settings
          </a>
        </div>
      )}

      <div
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        data-testid="kpi-grid"
      >
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-server"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Backend
            </CardTitle>
            {backendOk === true ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : backendOk === false ? (
              <XCircle className="h-4 w-4 text-red-500" />
            ) : (
              <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk === true
                ? "Connected"
                : backendOk === false
                  ? "Not reachable"
                  : "Loading"}
            </div>
            <p className="text-xs text-slate-400 font-mono truncate">{base}</p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-tools"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Registered Tools
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk ? (health?.tool_count ?? "—") : "—"}
            </div>
            <p className="text-xs text-slate-400">
              {backendOk ? `v${health?.version ?? "?"}` : "Offline"}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-ghidra"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Ghidra
            </CardTitle>
            {ghidra?.installed ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : (
              <XCircle className="h-4 w-4 text-slate-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {ghidra ? (ghidra.installed ? "Installed" : "Not found") : "—"}
            </div>
            <p className="text-xs text-slate-400">
              Bridge: {ghidra?.bridge_running ? "Running" : "Stopped"}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-status"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Analysis
            </CardTitle>
            <Search className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk ? "Ready" : "Offline"}
            </div>
            <p className="text-xs text-slate-400">
              <Link to="/tools" className="text-blue-400 hover:underline">
                Browse tools →
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
