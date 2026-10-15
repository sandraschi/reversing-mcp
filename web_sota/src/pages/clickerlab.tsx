import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCallback, useEffect, useState } from "react";

interface RunSummary {
  id: string;
  target: string;
  created: string;
  done: string[];
  running?: string | null;
  gate: string | null;
}

interface Engines {
  drive_ready: boolean;
  elicitation_ready: boolean;
  engines: Record<string, { available: boolean; install_hint?: string }>;
  message: string;
}

interface Elicitation {
  success: boolean;
  strings_scanned?: number;
  format_candidates?: number;
  features?: number;
  priority1?: number;
  message?: string;
  error?: string;
}

interface Session {
  success: boolean;
  session_id?: string;
  status?: string;
  mode?: string;
  coverage?: Record<string, number>;
  message?: string;
  error?: string;
}

const COV_LABEL: Record<string, string> = {
  nodes_seen: "nodes seen",
  nodes_visited: "nodes visited",
  menus_seen: "menus seen",
  menus_opened: "menus opened",
  dialogs_reached: "dialogs reached",
  steps: "steps",
};

export function ClickerLab() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [engines, setEngines] = useState<Engines | null>(null);
  const [elic, setElic] = useState<Elicitation | null>(null);
  const [features, setFeatures] = useState<string | null>(null);
  const [tour, setTour] = useState<string | null>(null);
  const [mode, setMode] = useState("rip");
  const [tourRel, setTourRel] = useState("elicitation/tour-draft.yaml");
  const [confirm, setConfirm] = useState(false);
  const [acceptLocal, setAcceptLocal] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [mapMd, setMapMd] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = useCallback(async () => {
    try {
      const d = await fetch(`${getApiBase()}/api/v1/gym/runs`).then((r) =>
        r.json(),
      );
      if (Array.isArray(d.runs)) setRuns(d.runs);
    } catch {
      /* backend down */
    }
  }, []);

  const refreshEngines = useCallback(async () => {
    try {
      const d = await fetch(`${getApiBase()}/api/v1/clicker/engines`).then(
        (r) => r.json(),
      );
      setEngines(d);
    } catch {
      /* backend down */
    }
  }, []);

  useEffect(() => {
    refreshRuns();
    refreshEngines();
    const iv = setInterval(refreshRuns, 10000);
    return () => clearInterval(iv);
  }, [refreshRuns, refreshEngines]);

  const loadElicitation = useCallback(async (id: string) => {
    try {
      const f = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${id}/artifacts/elicitation/features.json`,
      ).then((r) => r.json());
      setFeatures(f.success ? f.content : null);
      const t = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${id}/artifacts/elicitation/tour-draft.yaml`,
      ).then((r) => r.json());
      setTour(t.success ? t.content : null);
      const s = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${id}/artifacts/elicitation/elicitation.json`,
      ).then((r) => r.json());
      if (s.success) {
        const parsed = JSON.parse(s.content) as Omit<Elicitation, "success">;
        setElic({ success: true, ...parsed });
      }
    } catch {
      /* no elicitation yet */
    }
  }, []);

  useEffect(() => {
    if (!selected) return;
    setElic(null);
    setFeatures(null);
    setTour(null);
    setSession(null);
    setMapMd(null);
    loadElicitation(selected);
  }, [selected, loadElicitation]);

  const refreshSession = useCallback(
    async (sid: string) => {
      if (!selected) return;
      try {
        const d = await fetch(
          `${getApiBase()}/api/v1/gym/runs/${selected}/clicker/sessions/${sid}`,
        ).then((r) => r.json());
        setSession(d);
      } catch {
        /* backend down */
      }
    },
    [selected],
  );

  useEffect(() => {
    const sid = session?.session_id;
    if (!sid) return;
    if (session?.status !== "running") return;
    const iv = setInterval(() => refreshSession(sid), 3000);
    return () => clearInterval(iv);
  }, [session, refreshSession]);

  const runElicitation = async () => {
    if (!selected || busy) return;
    setBusy(true);
    setError(null);
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/elicitation`,
        { method: "POST" },
      ).then((r) => r.json());
      setElic(d);
      if (d.success === false) throw new Error(d.error ?? "Elicitation failed");
      loadElicitation(selected);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Elicitation failed");
    } finally {
      setBusy(false);
    }
  };

  const startSession = async () => {
    if (!selected || busy) return;
    setBusy(true);
    setError(null);
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/clicker/sessions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mode,
            tour_rel: mode === "tour" ? tourRel : null,
            step_cap: 200,
            time_cap_s: 600,
            confirm,
            accept_local: acceptLocal,
          }),
        },
      ).then((r) => r.json());
      setSession(d);
      if (d.success === false)
        throw new Error(d.error ?? "Session start failed");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Session start failed");
    } finally {
      setBusy(false);
    }
  };

  const stopSession = async () => {
    if (!selected || !session?.session_id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/clicker/sessions/${session.session_id}/stop`,
        { method: "POST" },
      ).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "Stop failed");
      refreshSession(session.session_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    } finally {
      setBusy(false);
    }
  };

  const correlate = async () => {
    if (!selected || !session?.session_id || busy) return;
    setBusy(true);
    setError(null);
    setMapMd(null);
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/clicker/sessions/${session.session_id}/correlate`,
        { method: "POST" },
      ).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "Correlate failed");
      const m = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/artifacts/clicker/sessions/${session.session_id}/map.md`,
      ).then((r) => r.json());
      if (m.success) setMapMd(m.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Correlate failed");
    } finally {
      setBusy(false);
    }
  };

  const sessionRunning = session?.status === "running";

  return (
    <div className="space-y-6" data-testid="clickerlab-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          ClickerLab
        </h2>
        <p className="text-slate-300">
          Stage 1b elicitation (static, safe) + stage 3 clicker sessions
          (execute the target — VM preferred, desktop only on explicit opt-out).
        </p>
      </div>

      {engines && (
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="clickerlab-engines"
        >
          <CardHeader>
            <CardTitle className="text-white text-base">Driver stack</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300">{engines.message}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(engines.engines).map(([name, info]) => (
                <span
                  key={name}
                  title={info.install_hint ?? name}
                  className={`text-sm px-2 py-0.5 rounded border ${
                    info.available
                      ? "text-emerald-400 bg-emerald-900/30 border-emerald-800/50"
                      : "text-amber-400 bg-amber-900/30 border-amber-800/50"
                  }`}
                >
                  {name}: {info.available ? "ready" : "missing"}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="clickerlab-runs"
      >
        <CardHeader>
          <CardTitle className="text-white text-base">
            Run ({runs.length}) — pick one, then elicit below
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {runs.length === 0 && (
            <p className="text-sm text-slate-300">
              No runs yet. Start one on the Gym page first.
            </p>
          )}
          {runs.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => setSelected(r.id)}
              className={`w-full text-left text-sm font-mono px-2 py-1.5 rounded border transition-colors ${
                r.id === selected
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800"
              }`}
            >
              {r.id} · {r.target}
            </button>
          ))}
        </CardContent>
      </Card>

      {selected && (
        <>
          <Card
            className="border-slate-800 bg-slate-950/50"
            data-testid="clickerlab-elicit"
          >
            <CardHeader>
              <CardTitle className="text-white text-base">
                Stage 1b: elicitation (static — never executes)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <button
                type="button"
                onClick={runElicitation}
                disabled={busy}
                className="text-sm px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40"
                data-testid="clickerlab-elicit-run"
              >
                {busy ? "Working…" : "Build elicitation"}
              </button>
              {elic?.success && (
                <p
                  className="text-sm text-slate-300"
                  data-testid="clickerlab-elicit-summary"
                >
                  {elic.message ??
                    `${elic.format_candidates} format(s), ${elic.features} feature(s) (${elic.priority1} file-I/O).`}
                </p>
              )}
              {features && (
                <details data-testid="clickerlab-features">
                  <summary className="text-sm text-slate-200 cursor-pointer">
                    features.json ({JSON.parse(features).length} rows)
                  </summary>
                  <pre className="mt-2 text-sm text-slate-300 bg-slate-900 rounded-lg p-4 overflow-y-auto max-h-72 whitespace-pre-wrap font-mono">
                    {features}
                  </pre>
                </details>
              )}
              {tour && (
                <details data-testid="clickerlab-tour">
                  <summary className="text-sm text-slate-200 cursor-pointer">
                    tour-draft.yaml (driver input — paths resolved live)
                  </summary>
                  <pre className="mt-2 text-sm text-slate-300 bg-slate-900 rounded-lg p-4 overflow-y-auto max-h-72 whitespace-pre-wrap font-mono">
                    {tour}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>

          <Card
            className="border-slate-800 bg-slate-950/50"
            data-testid="clickerlab-session"
          >
            <CardHeader>
              <CardTitle className="text-white text-base">
                Stage 3: clicker session (executes the target)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                {(["rip", "tour"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    className={`text-sm px-3 py-1.5 rounded border ${
                      mode === m
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800"
                    }`}
                    data-testid={`clickerlab-mode-${m}`}
                  >
                    {m === "rip" ? "Rip (B1 BFS)" : "Tour (B2 draft)"}
                  </button>
                ))}
                {mode === "tour" && (
                  <input
                    value={tourRel}
                    onChange={(e) => setTourRel(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                    data-testid="clickerlab-tour-rel"
                  />
                )}
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={confirm}
                  onChange={(e) => setConfirm(e.target.checked)}
                  data-testid="clickerlab-confirm"
                />
                I understand this executes the target binary (confirm)
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={acceptLocal}
                  onChange={(e) => setAcceptLocal(e.target.checked)}
                  data-testid="clickerlab-accept-local"
                />
                Run on this desktop — logged opt-out from VM isolation (spec §1)
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={startSession}
                  disabled={busy || sessionRunning || !confirm || !acceptLocal}
                  className="text-sm px-4 py-2 rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40"
                  data-testid="clickerlab-start"
                >
                  {sessionRunning ? "Running…" : "Start session"}
                </button>
                {sessionRunning && (
                  <button
                    type="button"
                    onClick={stopSession}
                    disabled={busy}
                    className="text-sm px-4 py-2 rounded-md bg-amber-700 text-white hover:bg-amber-600 disabled:opacity-40"
                    data-testid="clickerlab-stop"
                  >
                    Stop (kills target tree)
                  </button>
                )}
              </div>
              {session && (
                <div data-testid="clickerlab-status">
                  <p className="text-sm text-slate-200">
                    Session{" "}
                    <span className="font-mono">{session.session_id}</span> —{" "}
                    {session.status ?? session.error}
                  </p>
                  {session.coverage &&
                    Object.keys(session.coverage).length > 0 && (
                      <ul className="mt-1 space-y-1">
                        {Object.entries(session.coverage).map(([k, v]) => (
                          <li key={k} className="text-sm text-slate-300">
                            {COV_LABEL[k] ?? k}:{" "}
                            <span className="text-white">{v}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  {session.message && (
                    <p className="text-sm text-slate-300">{session.message}</p>
                  )}
                  {session.status !== "running" && (
                    <button
                      type="button"
                      onClick={correlate}
                      disabled={busy}
                      className="mt-2 text-sm px-4 py-2 rounded-md bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-40"
                      data-testid="clickerlab-correlate"
                    >
                      {busy ? "Correlating…" : "Correlate (§5 map)"}
                    </button>
                  )}
                  {mapMd && (
                    <details data-testid="clickerlab-map" open>
                      <summary className="text-sm text-slate-200 cursor-pointer mt-2">
                        map.md (feature → code rows + stated limits)
                      </summary>
                      <pre className="mt-2 text-sm text-slate-300 bg-slate-900 rounded-lg p-4 overflow-y-auto max-h-96 whitespace-pre-wrap font-mono">
                        {mapMd}
                      </pre>
                    </details>
                  )}
                </div>
              )}
              {error && (
                <p
                  className="text-sm text-red-400"
                  data-testid="clickerlab-error"
                >
                  {error}
                </p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
