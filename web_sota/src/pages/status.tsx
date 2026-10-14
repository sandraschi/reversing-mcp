import { CheckCircle, Loader2, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getApiBase } from "@/common/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ToolsStatus = Record<string, { available?: boolean; version?: string }>;
type GhidraStatus = {
  installed?: boolean;
  bridge_running?: boolean;
  version?: string;
};
type ToolboxEntry = {
  name?: string;
  status?: string;
  path?: string | null;
  version?: string | null;
  install?: string | null;
  note?: string;
  pid?: number | null;
};
type ToolboxStatus = {
  success?: boolean;
  tools?: Record<string, ToolboxEntry>;
  ready?: number;
  total?: number;
  message?: string;
};
type RevaStatus = {
  success?: boolean;
  mcp_reva?: { available?: boolean; path?: string | null; install_hint?: string | null };
  ghidra?: { dir?: string | null; run_bat?: string | null; gui_available?: boolean };
  managed?: { running?: boolean; mode?: string | null; pid?: number | null };
  bridge?: { reachable?: boolean; url?: string };
  message?: string;
  error?: string;
};

export function Status() {
  const [tools, setTools] = useState<ToolsStatus | null>(null);
  const [ghidra, setGhidra] = useState<GhidraStatus | null>(null);
  const [reva, setReva] = useState<RevaStatus | null>(null);
  const [toolbox, setToolbox] = useState<ToolboxStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revaBusy, setRevaBusy] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);

  const fetchStatus = () => {
    setLoading(true);
    setError(null);
    const base = getApiBase();
    Promise.all([
      fetch(`${base}/tools/status`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/ghidra/status`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/v1/reva`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`${base}/api/v1/toolbox`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
    ])
      .then(([toolsRes, ghidraRes, revaRes, toolboxRes]) => {
        setTools(toolsRes?.tools ?? null);
        setGhidra(ghidraRes ?? null);
        setReva(revaRes ?? null);
        setToolbox(toolboxRes ?? null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  const toolboxInstall = async (name: string) => {
    setInstalling(name);
    setError(null);
    try {
      const d = await fetch(`${getApiBase()}/api/v1/toolbox/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? `Install ${name} failed`);
      fetchStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : `Install ${name} failed`);
    } finally {
      setInstalling(null);
    }
  };

  const revaStart = async (mode: string) => {
    setRevaBusy(true);
    setError(null);
    try {
      const d = await fetch(`${getApiBase()}/api/v1/reva/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, confirm: true }),
      }).then((r) => r.json());
      if (d.success === false) throw new Error(d.error ?? "ReVa start failed");
      fetchStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "ReVa start failed");
    } finally {
      setRevaBusy(false);
    }
  };

  const revaStop = async () => {
    setRevaBusy(true);
    setError(null);
    try {
      await fetch(`${getApiBase()}/api/v1/reva/stop`, { method: "POST" });
      fetchStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "ReVa stop failed");
    } finally {
      setRevaBusy(false);
    }
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: mount-once load; refresh is manual
  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading && !tools && !ghidra) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="status-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            System Status
          </h2>
          <p className="text-slate-300">
            Tools and Ghidra from backend ({getApiBase()})
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchStatus}
          disabled={loading}
          className="border-slate-700"
          data-testid="status-refresh"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      {error && (
        <Card
          className="border-red-900/50 bg-red-950/20"
          data-testid="status-error"
        >
          <CardContent className="pt-6 text-red-400">{error}</CardContent>
        </Card>
      )}

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="status-tools"
      >
        <CardHeader>
          <CardTitle className="text-white">Tools</CardTitle>
        </CardHeader>
        <CardContent>
          {tools ? (
            <div className="space-y-2">
              {Object.entries(tools).map(([name, info]) => (
                <div
                  key={name}
                  className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0"
                >
                  <span className="font-mono text-slate-300">{name}</span>
                  {info?.available ? (
                    <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                      <CheckCircle className="h-3 w-3 mr-1" /> OK
                      {info.version ? ` ${info.version}` : ""}
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Unavailable</Badge>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-300 text-sm">
              No tools data (backend down?)
            </p>
          )}
        </CardContent>
      </Card>

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="status-ghidra"
      >
        <CardHeader>
          <CardTitle className="text-white">Ghidra</CardTitle>
        </CardHeader>
        <CardContent>
          {ghidra !== null ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">
                  Installed (binary on disk)
                </span>
                {ghidra.installed ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">Bridge (ReVa/MCP)</span>
                {ghidra.bridge_running ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              {ghidra.version && (
                <p className="text-sm text-slate-300 mt-2">
                  Version: {ghidra.version}
                </p>
              )}
            </div>
          ) : (
            <p className="text-slate-300 text-sm">
              Could not load Ghidra status
            </p>
          )}
        </CardContent>
      </Card>

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="status-toolbox"
      >
        <CardHeader>
          <CardTitle className="text-white">
            Toolbox{" "}
            {toolbox && (
              <span className="text-sm font-normal text-slate-300">
                ({toolbox.ready}/{toolbox.total} ready — auto-discovered, no env edits)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {toolbox?.tools ? (
            <div className="space-y-1">
              {Object.entries(toolbox.tools).map(([name, t]) => (
                <div
                  key={name}
                  className="flex items-center justify-between py-1.5 border-b border-slate-800/50 last:border-0"
                  data-testid={`toolbox-row-${name}`}
                >
                  <div className="min-w-0">
                    <span className="text-slate-200 font-mono text-sm">{name}</span>
                    {t.version && (
                      <span className="text-slate-300 text-sm"> · {t.version}</span>
                    )}
                    {t.pid != null && (
                      <span className="text-slate-300 text-sm"> · pid {t.pid} (attached)</span>
                    )}
                    {t.note && (
                      <p className="text-slate-300 text-sm truncate" title={t.note}>
                        {t.note}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {t.status === "ready" ? (
                      <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                        <CheckCircle className="h-3 w-3 mr-1" /> Ready
                      </Badge>
                    ) : t.status === "platform_blocked" ? (
                      <Badge variant="secondary">N/A here</Badge>
                    ) : (
                      <>
                        <Badge variant="secondary">{t.status ?? "unknown"}</Badge>
                        {t.install &&
                          (t.install.startsWith("winget:") ||
                            t.install.startsWith("github:") ||
                            t.install.startsWith("pip:")) && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => toolboxInstall(name)}
                              disabled={installing !== null}
                              className="border-slate-700 disabled:opacity-40"
                              data-testid={`toolbox-install-${name}`}
                            >
                              {installing === name ? "Installing…" : "Install"}
                            </Button>
                          )}
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-300 text-sm">Could not load toolbox inventory</p>
          )}
        </CardContent>
      </Card>

      <Card
        className="border-slate-800 bg-slate-950/50"
        data-testid="status-reva"
      >
        <CardHeader>
          <CardTitle className="text-white">ReVa (Ghidra MCP server)</CardTitle>
        </CardHeader>
        <CardContent>
          {reva ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">mcp-reva on PATH</span>
                {reva.mcp_reva?.available ? (
                  <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                    <CheckCircle className="h-3 w-3 mr-1" /> OK
                  </Badge>
                ) : (
                  <Badge variant="secondary">Missing</Badge>
                )}
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">Managed process</span>
                {reva.managed?.running ? (
                  <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                    Running ({reva.managed.mode}, pid {reva.managed.pid})
                  </Badge>
                ) : (
                  <Badge variant="secondary">Stopped</Badge>
                )}
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">Bridge {reva.bridge?.url}</span>
                {reva.bridge?.reachable ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              {reva.mcp_reva?.install_hint && (
                <p className="text-sm text-amber-400">
                  {reva.mcp_reva.install_hint} — headless start unavailable;
                  GUI mode still works when Ghidra is installed.
                </p>
              )}
              <div className="flex gap-2 pt-2">
                {!reva.managed?.running && (
                  <>
                    <Button
                      size="sm"
                      onClick={() => revaStart("headless")}
                      disabled={revaBusy || !reva.mcp_reva?.available}
                      className="bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40"
                      data-testid="reva-start-headless"
                    >
                      Start ReVa headless
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => revaStart("gui")}
                      disabled={revaBusy || !reva.ghidra?.gui_available}
                      className="border-slate-700 disabled:opacity-40"
                      data-testid="reva-start-gui"
                    >
                      Start Ghidra GUI
                    </Button>
                  </>
                )}
                {reva.managed?.running && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={revaStop}
                    disabled={revaBusy}
                    className="border-amber-700 text-amber-400 disabled:opacity-40"
                    data-testid="reva-stop"
                  >
                    Stop ReVa (kills tree)
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <p className="text-slate-300 text-sm">
              Could not load ReVa status
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
