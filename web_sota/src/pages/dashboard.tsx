import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Shield, Cpu, Search, Loader2, XCircle, CheckCircle } from "lucide-react";
import { getApiBase } from "@/common/api";
import { Link } from "react-router-dom";

type GhidraStatus = { installed?: boolean; http_server_running?: boolean };

export function Dashboard() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [ghidra, setGhidra] = useState<GhidraStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const base = getApiBase();
    Promise.all([
      fetch(`${base}/health`).then((r) => r.ok).catch(() => false),
      fetch(`${base}/ghidra/status`).then((r) => r.json()).catch(() => null),
    ]).then(([ok, g]) => {
      setBackendOk(ok);
      setGhidra(g);
      setLoading(false);
    });
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Reversing MCP Dashboard</h2>
          <p className="text-slate-400">System overview and status</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Backend</CardTitle>
            {backendOk === true ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : backendOk === false ? (
              <XCircle className="h-4 w-4 text-red-500" />
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk === true ? "Connected" : backendOk === false ? "Not reachable" : "—"}
            </div>
            <p className="text-xs text-slate-400 font-mono truncate">{getApiBase()}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Ghidra</CardTitle>
            {ghidra?.installed && ghidra?.http_server_running ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : ghidra?.installed ? (
              <span className="text-xs text-amber-500">Plugin off</span>
            ) : ghidra && !ghidra.installed ? (
              <XCircle className="h-4 w-4 text-red-500" />
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {ghidra?.installed && ghidra?.http_server_running
                ? "Found"
                : ghidra?.installed
                  ? "Found, plugin not running"
                  : ghidra
                    ? "Not found"
                    : "—"}
            </div>
            <p className="text-xs text-slate-400">Binary + MCP plugin</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">API Bridge</CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk === true ? "Active" : "Off"}
            </div>
            <p className="text-xs text-slate-400">FastMCP at /mcp</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Analyze</CardTitle>
            <Search className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <Link to="/analyze" className="text-2xl font-bold text-white hover:underline">
              Upload binary
            </Link>
            <p className="text-xs text-slate-400">Run analysis</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Quick links</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Link to="/analyze">
            <Badge className="cursor-pointer bg-slate-700 hover:bg-slate-600">Analyze</Badge>
          </Link>
          <Link to="/status">
            <Badge className="cursor-pointer bg-slate-700 hover:bg-slate-600">Status</Badge>
          </Link>
          <Link to="/chat">
            <Badge className="cursor-pointer bg-slate-700 hover:bg-slate-600">Chat</Badge>
          </Link>
          <Link to="/settings">
            <Badge className="cursor-pointer bg-slate-700 hover:bg-slate-600">Settings</Badge>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
