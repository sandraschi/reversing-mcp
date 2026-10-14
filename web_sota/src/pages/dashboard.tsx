import {
  Activity,
  Bot,
  CheckCircle,
  Cpu,
  Dumbbell,
  FlaskConical,
  Loader2,
  RefreshCw,
  Search,
  Terminal,
  Wrench,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type GhidraStatus = { installed?: boolean; bridge_running?: boolean };

interface HealthData {
  status: string;
  version?: string;
  tool_count?: number;
}

interface ToolboxData {
  ready?: number;
  total?: number;
}

interface GymRun {
  id: string;
  target: string;
  done: string[];
  running?: string | null;
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  kind: string;
  detail: string;
}

function fmtUptime(sec: number | undefined): string {
  if (sec == null) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m`;
  return `${sec}s`;
}

const LEVEL_DOT: Record<string, string> = {
  ERROR: "bg-red-500",
  WARNING: "bg-amber-500",
  INFO: "bg-emerald-500",
  DEBUG: "bg-slate-500",
};

export function Dashboard() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [uptime, setUptime] = useState<number | undefined>(undefined);
  const [ghidra, setGhidra] = useState<GhidraStatus | null>(null);
  const [toolbox, setToolbox] = useState<ToolboxData | null>(null);
  const [runs, setRuns] = useState<GymRun[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [onboard, setOnboard] = useState<{
    ready?: boolean;
    reason?: string;
    action?: string;
    action_label?: string;
    action_endpoint?: string;
    models?: string[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [onboardBusy, setOnboardBusy] = useState(false);

  const base = getApiBase();

  const fetchAll = useCallback(async () => {
    const [h, g, o, t, r, l, d] = await Promise.all([
      fetch(`${base}/health`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/ghidra/status`)
        .then((r) => r.json())
        .catch(() => null),
      fetch(`${base}/api/llm/onboarding`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/v1/toolbox`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/v1/gym/runs`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/logs?limit=8`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/v1/diagnostics`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
    ]);
    setBackendOk(h !== null);
    setHealth(h);
    setGhidra(g);
    setOnboard(o);
    setToolbox(t);
    if (Array.isArray(r?.runs)) setRuns(r.runs);
    if (Array.isArray(l?.entries)) setLogs(l.entries);
    setUptime(d?.uptime_seconds);
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

  const runOnboardAction = async () => {
    if (!onboard?.action_endpoint || onboardBusy) return;
    setOnboardBusy(true);
    try {
      const d = await fetch(`${base}${onboard.action_endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      }).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "Action failed");
      fetchAll();
    } catch {
      /* error surfaces via next poll's reason */
      fetchAll();
    } finally {
      setOnboardBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
      </div>
    );
  }

  const activeRuns = runs.filter((r) => r.running != null);
  const modelCount = onboard?.models?.length ?? 0;

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Hero: what this is + what to do next */}
      <div
        className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950/40 px-6 py-5"
        data-testid="hero"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="min-w-0">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Reversing MCP
            </h2>
            <p className="text-slate-300 mt-1 max-w-2xl">
              Agent-driven binary analysis: drop an .exe on Analyze and get
              strings, entropy, PE structure plus Ghidra / DiE / capa answers —
              or run a Gym cloning session and correlate the UI back to code.
              Every button below exists as an MCP tool, so AI agents drive the
              same workflows you click through here.
            </p>
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
            <span className="text-sm text-slate-300">
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
                <RefreshCw className="h-3 w-3 text-slate-300" />
              </button>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          <Link
            to="/analyze"
            data-testid="hero-cta-analyze"
            className="text-sm px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 font-medium"
          >
            Analyze a binary
          </Link>
          <Link
            to="/gym"
            data-testid="hero-cta-gym"
            className="text-sm px-4 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-700 border border-slate-700 font-medium"
          >
            New Gym run
          </Link>
          <Link
            to="/chat"
            data-testid="hero-cta-chat"
            className="text-sm px-4 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-700 border border-slate-700 font-medium"
          >
            Ask the AI
          </Link>
          <Link
            to="/status"
            data-testid="hero-cta-toolbox"
            className="text-sm px-4 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-700 border border-slate-700 font-medium"
          >
            Toolbox status
          </Link>
        </div>
      </div>

      {backendOk === true && onboard && onboard.ready === false && (
        <div
          className="rounded-lg border border-amber-800/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-200"
          data-testid="onboarding-cue"
        >
          <span className="font-medium">Get started with AI chat: </span>
          {onboard.reason}{" "}
          {onboard.action_endpoint && (
            <button
              type="button"
              onClick={runOnboardAction}
              disabled={onboardBusy}
              className="ml-1 px-3 py-1 rounded-md bg-amber-600 text-white hover:bg-amber-500 disabled:opacity-40 font-medium"
              data-testid="onboarding-action"
            >
              {onboardBusy ? "Working…" : (onboard.action_label ?? "Fix it")}
            </button>
          )}{" "}
          <a className="underline" href="#/settings">
            Open Settings
          </a>
        </div>
      )}

      <div
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6"
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
              <Loader2 className="h-4 w-4 animate-spin text-slate-300" />
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
            <p className="text-sm text-slate-300 font-mono truncate">
              {base} · up {fmtUptime(uptime)}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-tools"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              MCP Tools
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk ? (health?.tool_count ?? "—") : "—"}
            </div>
            <p className="text-sm text-slate-300">
              {backendOk ? (
                <Link to="/tools" className="text-blue-400 hover:underline">
                  Browse tools →
                </Link>
              ) : (
                "Offline"
              )}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-toolbox"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Toolbox
            </CardTitle>
            <Wrench className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {toolbox ? `${toolbox.ready}/${toolbox.total}` : "—"}
            </div>
            <p className="text-sm text-slate-300">
              <Link to="/status" className="text-blue-400 hover:underline">
                engines ready →
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-gym"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Gym Runs
            </CardTitle>
            <Dumbbell className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk ? runs.length : "—"}
            </div>
            <p className="text-sm text-slate-300">
              {activeRuns.length > 0 ? (
                <span className="text-emerald-400">
                  {activeRuns.length} active
                </span>
              ) : (
                <Link to="/gym" className="text-blue-400 hover:underline">
                  start one →
                </Link>
              )}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-models"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              AI Models
            </CardTitle>
            <Bot className="h-4 w-4 text-violet-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk ? modelCount : "—"}
            </div>
            <p className="text-sm text-slate-300">
              <Link to="/chat" className="text-blue-400 hover:underline">
                open chat →
              </Link>
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
            <p className="text-sm text-slate-300">
              Bridge: {ghidra?.bridge_running ? "Running" : "Stopped"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="active-ops"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-emerald-500" />
              Active operations
            </CardTitle>
            <Link to="/gym" className="text-sm text-blue-400 hover:underline">
              Gym →
            </Link>
          </CardHeader>
          <CardContent>
            {activeRuns.length === 0 ? (
              <p className="text-sm text-slate-300">
                Idle — nothing running.{" "}
                <Link to="/gym" className="text-blue-400 hover:underline">
                  Start a cloning run
                </Link>{" "}
                or{" "}
                <Link to="/analyze" className="text-blue-400 hover:underline">
                  analyze a binary
                </Link>
                .
              </p>
            ) : (
              <ul className="space-y-2">
                {activeRuns.map((r) => (
                  <li key={r.id} className="flex items-center gap-2 text-sm">
                    <Loader2 className="h-3 w-3 animate-spin text-emerald-400 shrink-0" />
                    <span className="text-slate-200 font-mono truncate">
                      {r.target}
                    </span>
                    <span className="text-slate-300 shrink-0">
                      · {r.running}
                    </span>
                    <Link
                      to="/gym"
                      className="text-blue-400 hover:underline shrink-0 ml-auto"
                    >
                      watch →
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="mini-log"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
              <Terminal className="h-4 w-4 text-slate-400" />
              Latest events
            </CardTitle>
            <Link to="/logs" className="text-sm text-blue-400 hover:underline">
              All logs →
            </Link>
          </CardHeader>
          <CardContent>
            {logs.length === 0 ? (
              <p className="text-sm text-slate-300">No events yet.</p>
            ) : (
              <ul className="space-y-1.5">
                {logs.map((e) => (
                  <li key={e.id} className="flex items-start gap-2 text-sm">
                    <span
                      className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                        LEVEL_DOT[e.level] ?? "bg-slate-500"
                      }`}
                      title={e.level}
                    />
                    <span className="text-slate-300 font-mono shrink-0">
                      {e.timestamp.slice(11, 19)}
                    </span>
                    <span className="text-slate-200 truncate" title={e.detail}>
                      {e.detail}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-sm text-slate-300 mt-3 flex items-center gap-1">
              <Cpu className="h-3 w-3" />
              <Link to="/tools" className="text-blue-400 hover:underline">
                <Search className="h-3 w-3 inline mr-1" />
                Browse tools →
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
