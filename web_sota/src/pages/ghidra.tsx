import { GhidraHeader } from "@/components/ghidra/GhidraHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type CallResult,
  type ToolDetail,
  ghidraApi,
  previewOf,
  skeletonArgs,
  useGhidraHistory,
  useGhidraSession,
} from "@/lib/ghidra";
import {
  AlertTriangle,
  Loader2,
  Play,
  Power,
  Square,
  Terminal,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";

function StartPanel({ onStarted }: { onStarted: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [guiUrl, setGuiUrl] = useState("");

  const start = async (mode: "headless" | "gui") => {
    setBusy(true);
    setErr(null);
    try {
      const d = await ghidraApi.start(
        mode,
        mode === "gui" ? guiUrl : undefined,
      );
      if (d.success === false)
        throw new Error(d.error ?? `Start (${mode}) failed`);
      onStarted();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Start failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      className="border-slate-800 bg-slate-950/50"
      data-testid="ghidra-start"
    >
      <CardHeader>
        <CardTitle className="text-white">Start a Ghidra session</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-800 p-4 space-y-2">
            <h4 className="text-sm font-semibold text-white">Headless</h4>
            <p className="text-sm text-slate-300">
              Boots <code className="font-mono text-xs">mcp-reva</code> with its
              own Ghidra JVM. No window; ~1-2 min cold start, ~1-2 GB RAM. Best
              for batch work and when you do not need to watch.
            </p>
            <Button
              onClick={() => start("headless")}
              disabled={busy}
              className="bg-red-700 text-white hover:bg-red-600 disabled:opacity-40"
              data-testid="ghidra-start-headless"
            >
              {busy ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Power className="h-4 w-4 mr-2" />
              )}
              Start headless
            </Button>
          </div>
          <div className="rounded-lg border border-slate-800 p-4 space-y-2">
            <h4 className="text-sm font-semibold text-white">Attach to GUI</h4>
            <p className="text-sm text-slate-300">
              Connect to a running Ghidra with the ReVa plugin server enabled
              (Edit &gt; Tool Options &gt; ReVa). You watch every rename and
              comment land in the window.
            </p>
            <input
              value={guiUrl}
              onChange={(e) => setGuiUrl(e.target.value)}
              placeholder="http://127.0.0.1:8080/mcp/message (default)"
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-white placeholder:text-slate-500 outline-none focus:border-red-500"
              data-testid="ghidra-gui-url"
            />
            <Button
              onClick={() => start("gui")}
              disabled={busy}
              variant="outline"
              className="border-slate-700 disabled:opacity-40"
              data-testid="ghidra-start-gui"
            >
              {busy ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Attach to GUI
            </Button>
          </div>
        </div>
        {err && (
          <p
            className="text-sm text-red-400 flex items-start gap-2"
            data-testid="ghidra-start-error"
          >
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            {err}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function CallPanel({ initialTool }: { initialTool: string | null }) {
  const [toolName, setToolName] = useState(initialTool ?? "");
  const [detail, setDetail] = useState<ToolDetail | null>(null);
  const [argsText, setArgsText] = useState("{}");
  const [result, setResult] = useState<CallResult | null>(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const addHistory = useGhidraHistory((s) => s.add);

  const load = useCallback(async (name: string) => {
    setErr(null);
    setDetail(null);
    try {
      const d = await ghidraApi.describe(name);
      if (!d.success) {
        setErr(
          d.error +
            (d.did_you_mean?.length
              ? ` Try: ${d.did_you_mean.join(", ")}`
              : ""),
        );
        return;
      }
      setDetail(d);
      setArgsText(JSON.stringify(skeletonArgs(d.input_schema), null, 2));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "describe failed");
    }
  }, []);

  useEffect(() => {
    if (initialTool) {
      setToolName(initialTool);
      load(initialTool);
    }
  }, [initialTool, load]);

  const run = async () => {
    let args: Record<string, unknown>;
    try {
      args = JSON.parse(argsText || "{}");
    } catch {
      setErr("Arguments are not valid JSON.");
      return;
    }
    setRunning(true);
    setErr(null);
    try {
      const d = await ghidraApi.call(toolName, args);
      setResult(d);
      addHistory({
        tool: toolName,
        args,
        ok: d.success,
        elapsed_s: d.elapsed_s ?? null,
        preview: previewOf(d),
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "call failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <Card
      className="border-slate-800 bg-slate-950/50"
      data-testid="ghidra-call"
    >
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Terminal className="h-4 w-4 text-red-400" />
          Call a tool
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <input
            value={toolName}
            onChange={(e) => setToolName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && toolName && load(toolName)}
            placeholder="tool name (e.g. get-functions)"
            className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-sm text-white placeholder:text-slate-500 outline-none focus:border-red-500"
            data-testid="ghidra-call-tool"
          />
          <Button
            variant="outline"
            onClick={() => toolName && load(toolName)}
            className="border-slate-700"
            data-testid="ghidra-call-load"
          >
            Load schema
          </Button>
        </div>
        {detail && (
          <p className="text-sm text-slate-300">
            {detail.description.split("\n")[0]}
          </p>
        )}
        <div>
          <label className="text-xs text-slate-400" htmlFor="ghidra-args">
            Arguments (JSON)
          </label>
          <textarea
            id="ghidra-args"
            value={argsText}
            onChange={(e) => setArgsText(e.target.value)}
            spellCheck={false}
            rows={Math.min(14, Math.max(4, argsText.split("\n").length))}
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-xs text-white outline-none focus:border-red-500"
            data-testid="ghidra-call-args"
          />
        </div>
        <Button
          onClick={run}
          disabled={running || !toolName}
          className="bg-red-700 text-white hover:bg-red-600 disabled:opacity-40"
          data-testid="ghidra-call-run"
        >
          {running ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          Run
        </Button>
        {err && <p className="text-sm text-red-400">{err}</p>}
        {result && (
          <div
            className="rounded-lg border border-slate-800 bg-slate-900/60 p-3"
            data-testid="ghidra-call-result"
          >
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>
                {result.success ? "OK" : "Error"}
                {result.elapsed_s != null ? ` · ${result.elapsed_s}s` : ""}
              </span>
              {result.note && (
                <span className="text-amber-400">{result.note}</span>
              )}
            </div>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-slate-200">
              {result.content?.map((b) => b.text ?? `[${b.type}]`).join("\n") ??
                JSON.stringify(result.structured ?? result, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Ghidra() {
  const { session, reachable, refresh } = useGhidraSession();
  const [stopping, setStopping] = useState(false);
  const location = useLocation();
  const initialTool = useMemo(
    () => new URLSearchParams(location.search).get("tool"),
    [location.search],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  const stop = async () => {
    setStopping(true);
    try {
      await ghidraApi.stop();
      refresh();
    } finally {
      setStopping(false);
    }
  };

  const ready = session?.state === "ready";
  const starting = session?.state === "starting";

  return (
    <div className="space-y-5" data-testid="ghidra-page">
      <GhidraHeader
        title="Ghidra Workbench"
        blurb="Decompile, trace cross-references, rename and retype through ReVa, behind one session. Start headless for batch work or attach to a live Ghidra to watch it happen."
      />

      {reachable === false && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-400">
            Backend not reachable. Start it with start.ps1, then refresh.
          </CardContent>
        </Card>
      )}

      {session && session.state === "stopped" && (
        <StartPanel onStarted={refresh} />
      )}

      {starting && (
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="ghidra-starting"
        >
          <CardContent className="pt-6 flex items-center gap-3 text-slate-200">
            <Loader2 className="h-5 w-5 animate-spin text-amber-400" />
            <div>
              <p>
                Starting {session.mode} session
                {session.elapsed_s != null
                  ? ` · ${session.elapsed_s}s elapsed`
                  : ""}
                .
              </p>
              {session.hint && (
                <p className="text-sm text-slate-400">{session.hint}</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {session?.state === "error" && (
        <Card
          className="border-red-900/50 bg-red-950/20"
          data-testid="ghidra-error"
        >
          <CardContent className="pt-6 space-y-3">
            <p className="text-red-400">{session.error}</p>
            <Button
              onClick={stop}
              variant="outline"
              className="border-slate-700"
            >
              Reset session
            </Button>
          </CardContent>
        </Card>
      )}

      {ready && (
        <>
          <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3">
            <p className="text-sm text-slate-300">
              {session.mode} session ready · {session.tool_count} tools
              {session.startup_s != null
                ? ` · booted in ${session.startup_s}s`
                : ""}
              {session.log_file ? (
                <span className="text-slate-500 font-mono">
                  {" "}
                  · {session.log_file}
                </span>
              ) : null}
            </p>
            <Button
              onClick={stop}
              disabled={stopping}
              variant="outline"
              className="border-amber-700 text-amber-400 disabled:opacity-40"
              data-testid="ghidra-stop"
            >
              {stopping ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Square className="h-4 w-4 mr-2" />
              )}
              Stop session
            </Button>
          </div>
          <CallPanel initialTool={initialTool} />
        </>
      )}
    </div>
  );
}
