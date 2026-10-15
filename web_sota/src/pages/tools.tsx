import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle,
  Loader2,
  Search,
  Terminal,
  Wrench,
  XCircle,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

type ToolsStatus = Record<string, { available?: boolean; version?: string }>;

const TOOL_ICONS: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  file: Terminal,
  strings: Search,
  entropy: Zap,
  pefile: Terminal,
  ghidra_mcp: Wrench,
};

export function Tools() {
  const [tools, setTools] = useState<ToolsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetch(`${getApiBase()}/tools/status`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setTools(data?.tools ?? null))
      .catch(() => setTools(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center py-12"
        data-testid="tools-loading"
      >
        <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
      </div>
    );
  }

  const names = tools ? Object.keys(tools) : [];
  const q = filter.trim().toLowerCase();
  const visible = q ? names.filter((n) => n.toLowerCase().includes(q)) : names;

  return (
    <div className="space-y-6" data-testid="tools-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Tool Inventory
        </h2>
        <p className="text-slate-300">Backend tools from {getApiBase()}</p>
      </div>

      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter tools…"
        className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
        data-testid="tools-filter"
      />

      <div
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        data-testid="tools-grid"
      >
        {tools ? (
          visible.length > 0 ? (
            visible.map((name) => {
              const info = tools[name];
              const Icon = TOOL_ICONS[name] ?? Wrench;
              return (
                <Card key={name} className="border-slate-800 bg-slate-950/50">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                      <Icon className="h-4 w-4 text-slate-300" />
                      {name}
                    </CardTitle>
                    {info?.available ? (
                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-300">
                      {info?.available
                        ? `Available${info.version ? ` (${info.version})` : ""}`
                        : "Unavailable"}
                    </p>
                  </CardContent>
                </Card>
              );
            })
          ) : (
            <Card className="border-slate-800 bg-slate-950/50 col-span-full">
              <CardContent className="pt-6 text-sm text-slate-300">
                No tools match this filter.
              </CardContent>
            </Card>
          )
        ) : (
          <Card className="border-slate-800 bg-slate-950/50 col-span-full">
            <CardContent className="pt-6 text-sm text-slate-300">
              Could not load tools. Is the backend running?
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
