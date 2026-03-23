import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wrench, Zap, Search, Terminal, Loader2, CheckCircle, XCircle } from "lucide-react";
import { getApiBase } from "@/common/api";

type ToolsStatus = Record<string, { available?: boolean; version?: string }>;

const TOOL_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  file: Terminal,
  strings: Search,
  entropy: Zap,
  pefile: Terminal,
  ghidra_mcp: Wrench,
};

export function Tools() {
  const [tools, setTools] = useState<ToolsStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${getApiBase()}/tools/status`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setTools(data?.tools ?? null))
      .catch(() => setTools(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Tool Inventory</h2>
        <p className="text-slate-400">Backend tools from {getApiBase()}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tools
          ? Object.entries(tools).map(([name, info]) => {
              const Icon = TOOL_ICONS[name] ?? Wrench;
              return (
                <Card key={name} className="border-slate-800 bg-slate-950/50">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                      <Icon className="h-4 w-4 text-slate-400" />
                      {name}
                    </CardTitle>
                    {info?.available ? (
                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-slate-400">
                      {info?.available ? `Available${info.version ? ` (${info.version})` : ""}` : "Unavailable"}
                    </p>
                  </CardContent>
                </Card>
              );
            })
          : (
            <Card className="border-slate-800 bg-slate-950/50 col-span-full">
              <CardContent className="pt-6 text-slate-500">
                Could not load tools. Is the backend running?
              </CardContent>
            </Card>
          )}
      </div>
    </div>
  );
}
