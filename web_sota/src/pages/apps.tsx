import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu, Loader2, Server, Wrench } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

interface Capabilities {
  name: string;
  version: string;
  ports: { backend: number; frontend: number };
  features: Record<string, boolean>;
  tools: string[];
}

export function Apps() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/capabilities`)
      .then((r) => {
        if (!r.ok) throw new Error(`capabilities: ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (!cancelled) {
          setCaps(d);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Capabilities unavailable");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tools = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const list = caps?.tools ?? [];
    if (!q) return list;
    return list.filter((t) => t.toLowerCase().includes(q));
  }, [caps, filter]);

  return (
    <div className="space-y-6" data-testid="apps-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          This Server
        </h2>
        <p className="text-slate-300">
          Live capabilities from the backend ({getApiBase()})
        </p>
      </div>

      {loading && (
        <p
          className="text-sm text-slate-300 flex items-center gap-2"
          data-testid="apps-loading"
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading capabilities…
        </p>
      )}

      {error && (
        <Card
          className="border-red-900/50 bg-red-950/20"
          data-testid="apps-error"
        >
          <CardContent className="pt-6 text-sm text-red-400">
            {error}. Is the backend running?
          </CardContent>
        </Card>
      )}

      {caps && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card
              className="border-slate-800 bg-slate-950/50"
              data-testid="apps-identity"
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                  <Server className="h-4 w-4 text-blue-500" /> Server
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white font-mono">
                  {caps.name}
                </div>
                <p className="text-sm text-slate-300">
                  v{caps.version} · :{caps.ports.backend} / :
                  {caps.ports.frontend}
                </p>
              </CardContent>
            </Card>
            <Card
              className="border-slate-800 bg-slate-950/50 md:col-span-2"
              data-testid="apps-features"
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-emerald-500" /> Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(caps.features).map(([k, v]) => (
                    <span
                      key={k}
                      className={`text-sm px-2 py-0.5 rounded border ${
                        v
                          ? "text-emerald-400 bg-emerald-900/30 border-emerald-800/50"
                          : "text-slate-300 bg-slate-900 border-slate-800"
                      }`}
                    >
                      {k}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter tools…"
            className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            data-testid="apps-filter"
          />

          <Card
            className="border-slate-800 bg-slate-950/50"
            data-testid="apps-tools"
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                <Wrench className="h-4 w-4 text-slate-300" /> MCP tools (
                {tools.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {tools.length === 0 ? (
                <p className="text-sm text-slate-300">
                  No tools match this filter.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {tools.map((t) => (
                    <span
                      key={t}
                      className="text-sm font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
