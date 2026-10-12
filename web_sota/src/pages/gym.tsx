import { useCallback, useEffect, useState } from "react";
import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STAGES = [
  "intake",
  "triage",
  "oracle_capture",
  "clicker_tour",
  "assessment",
  "recovery",
  "ui_build",
  "round_trip",
  "compare",
];

interface RunSummary {
  id: string;
  target: string;
  created: string;
  done: string[];
  gate: string | null;
}

interface RunDetail extends Omit<RunSummary, "gate"> {
  sha256: string;
  size: number;
  test_files: string[];
  notes: string;
  stages: Record<
    string,
    {
      status: string;
      started: string | null;
      ended: string | null;
      error: string | null;
    }
  >;
  gate: { stage: string; decision: string | null; at: string | null } | null;
  message?: string;
}

const DIM_LABEL: Record<string, string> = {
  green: "text-emerald-400",
  amber: "text-amber-400",
  red: "text-red-400",
  unknown: "text-slate-500",
};

export function Gym() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [assessment, setAssessment] = useState<{
    dimensions: { dimension: string; status: string; reason: string }[];
    verdict: string;
  } | null>(null);
  const [target, setTarget] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [artifactPath, setArtifactPath] = useState(
    "assessment/assessment.json",
  );
  const [artifact, setArtifact] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    try {
      const d = await fetch(`${getApiBase()}/api/v1/gym/runs`).then((r) =>
        r.json(),
      );
      if (Array.isArray(d.runs)) setRuns(d.runs);
    } catch {
      /* backend down */
    }
  }, []);

  const refreshDetail = useCallback(async (id: string) => {
    try {
      const d = await fetch(`${getApiBase()}/api/v1/gym/runs/${id}`).then((r) =>
        r.json(),
      );
      if (d.success === false) {
        setError(d.error ?? "Run not found");
        return;
      }
      setDetail(d);
      try {
        const a = await fetch(
          `${getApiBase()}/api/v1/gym/runs/${id}/artifacts/assessment/assessment.json`,
        ).then((r) => r.json());
        if (a.success) setAssessment(JSON.parse(a.content));
        else setAssessment(null);
      } catch {
        setAssessment(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    }
  }, []);

  useEffect(() => {
    refreshList();
    const iv = setInterval(refreshList, 10000);
    return () => clearInterval(iv);
  }, [refreshList]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    refreshDetail(selected);
    const iv = setInterval(() => refreshDetail(selected), 5000);
    return () => clearInterval(iv);
  }, [selected, refreshDetail]);

  const start = async () => {
    if (!target.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const d = await fetch(`${getApiBase()}/api/v1/gym/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target.trim(), test_files: [], notes }),
      }).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "Start failed");
      setTarget("");
      setNotes("");
      setSelected(d.run_id);
      refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    } finally {
      setBusy(false);
    }
  };

  const advance = async (decision?: string) => {
    if (!selected || busy) return;
    setBusy(true);
    setError(null);
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/advance`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision: decision ?? null }),
        },
      ).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "Advance failed");
      refreshDetail(selected);
      refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Advance failed");
    } finally {
      setBusy(false);
    }
  };

  const loadArtifact = async () => {
    if (!selected) return;
    try {
      const d = await fetch(
        `${getApiBase()}/api/v1/gym/runs/${selected}/artifacts/${artifactPath}`,
      ).then((r) => r.json());
      setArtifact(d.success ? d.content : `Error: ${d.error}`);
    } catch (e) {
      setArtifact(`Error: ${e instanceof Error ? e.message : e}`);
    }
  };

  const awaitingGate =
    detail !== null &&
    detail.stages.assessment?.status === "done" &&
    detail.gate?.decision === null;

  return (
    <div className="space-y-6" data-testid="gym-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Reversing Gym
        </h2>
        <p className="text-slate-300">
          Clone assessment: intake, triage, gate. The original is the oracle.
        </p>
      </div>

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="gym-intake"
      >
        <CardHeader>
          <CardTitle className="text-white text-base">
            New run (stage 0: intake)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Local target path, e.g. D:/apps/prog.exe"
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            data-testid="gym-target"
          />
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Operator notes (entitlement, context)"
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            data-testid="gym-notes"
          />
          <button
            type="button"
            onClick={start}
            disabled={busy || !target.trim()}
            className="text-sm px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40"
            data-testid="gym-start"
          >
            {busy ? "Working…" : "Start run"}
          </button>
          {error && (
            <p className="text-sm text-red-400" data-testid="gym-error">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="gym-runs"
        >
          <CardHeader>
            <CardTitle className="text-white text-base">
              Runs ({runs.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {runs.length === 0 && (
              <p className="text-sm text-slate-300">
                No runs yet. Start one above.
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

        <Card
          className="border-slate-800 bg-slate-950/50 md:col-span-2"
          data-testid="gym-detail"
        >
          <CardHeader>
            <CardTitle className="text-white text-base">
              {detail ? `${detail.id} · ${detail.target}` : "Select a run"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {detail && (
              <>
                <div className="flex flex-wrap gap-1" data-testid="gym-stepper">
                  {STAGES.map((s) => {
                    const st = detail.stages[s]?.status ?? "pending";
                    return (
                      <span
                        key={s}
                        title={`${s}: ${st}`}
                        className={`text-sm px-2 py-0.5 rounded border ${
                          st === "done"
                            ? "text-emerald-400 bg-emerald-900/30 border-emerald-800/50"
                            : st === "running"
                              ? "text-blue-400 bg-blue-900/30 border-blue-800/50"
                              : st === "failed"
                                ? "text-red-400 bg-red-900/30 border-red-800/50"
                                : "text-slate-300 bg-slate-900 border-slate-800"
                        }`}
                      >
                        {s}
                      </span>
                    );
                  })}
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => advance()}
                    disabled={busy}
                    className="text-sm px-4 py-2 rounded-md bg-slate-800 text-slate-200 hover:bg-slate-700 disabled:opacity-40"
                    data-testid="gym-advance"
                  >
                    Advance
                  </button>
                  {awaitingGate && (
                    <>
                      <button
                        type="button"
                        onClick={() => advance("go")}
                        disabled={busy}
                        className="text-sm px-4 py-2 rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40"
                        data-testid="gym-gate-go"
                      >
                        Gate: go
                      </button>
                      <button
                        type="button"
                        onClick={() => advance("no-go")}
                        disabled={busy}
                        className="text-sm px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-40"
                        data-testid="gym-gate-nogo"
                      >
                        Gate: no-go
                      </button>
                    </>
                  )}
                </div>

                {assessment && (
                  <div data-testid="gym-assessment">
                    <p className="text-sm font-medium text-slate-200">
                      Verdict:{" "}
                      <span className={DIM_LABEL[assessment.verdict] ?? ""}>
                        {assessment.verdict.toUpperCase()}
                      </span>
                    </p>
                    <ul className="mt-1 space-y-1">
                      {assessment.dimensions.map((d) => (
                        <li key={d.dimension} className="text-sm">
                          <span className={DIM_LABEL[d.status] ?? ""}>
                            {d.dimension}: {d.status}
                          </span>{" "}
                          <span className="text-slate-300">— {d.reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-2">
                  <input
                    value={artifactPath}
                    onChange={(e) => setArtifactPath(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                    data-testid="gym-artifact-path"
                  />
                  <button
                    type="button"
                    onClick={loadArtifact}
                    className="text-sm px-4 py-2 rounded-md bg-slate-800 text-slate-200 hover:bg-slate-700"
                    data-testid="gym-artifact-load"
                  >
                    Load
                  </button>
                </div>
                {artifact !== null && (
                  <pre
                    className="text-sm text-slate-300 bg-slate-900 rounded-lg p-4 overflow-y-auto max-h-96 whitespace-pre-wrap font-mono"
                    data-testid="gym-artifact"
                  >
                    {artifact}
                  </pre>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
