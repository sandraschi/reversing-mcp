import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, CheckCircle, XCircle, Loader2, RefreshCw } from "lucide-react";
import { getApiBase } from "@/common/api";

type ToolsStatus = Record<string, { available?: boolean; version?: string }>;
type GhidraStatus = { installed?: boolean; http_server_running?: boolean; version?: string };

export function Status() {
  const [tools, setTools] = useState<ToolsStatus | null>(null);
  const [ghidra, setGhidra] = useState<GhidraStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = () => {
    setLoading(true);
    setError(null);
    const base = getApiBase();
    Promise.all([
      fetch(`${base}/tools/status`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch(`${base}/ghidra/status`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ])
      .then(([toolsRes, ghidraRes]) => {
        setTools(toolsRes?.tools ?? null);
        setGhidra(ghidraRes ?? null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => fetchStatus(), []);

  if (loading && !tools && !ghidra) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">System Status</h2>
          <p className="text-slate-400">Tools and Ghidra from backend ({getApiBase()})</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStatus} disabled={loading} className="border-slate-700">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-400">{error}</CardContent>
        </Card>
      )}

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Tools</CardTitle>
        </CardHeader>
        <CardContent>
          {tools ? (
            <div className="space-y-2">
              {Object.entries(tools).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
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
            <p className="text-slate-500 text-sm">No tools data (backend down?)</p>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Ghidra</CardTitle>
        </CardHeader>
        <CardContent>
          {ghidra !== null ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">Installed (binary on disk)</span>
                {ghidra.installed ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">Plugin (HTTP server)</span>
                {ghidra.http_server_running ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              {ghidra.version && (
                <p className="text-xs text-slate-500 mt-2">Version: {ghidra.version}</p>
              )}
            </div>
          ) : (
            <p className="text-slate-500 text-sm">Could not load Ghidra status</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
