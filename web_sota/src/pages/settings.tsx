import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { getApiBase, setApiBase } from "@/common/api";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

function LLMSettings() {
    const [providers, setProviders] = useState<Record<string, {name:string}[]>>({});
    const [selectedProvider, setSelectedProvider] = useState("ollama");
    const [selectedModel, setSelectedModel] = useState("");
    const [status, setStatus] = useState<"loading"|"ready"|"error">("loading");
    useEffect(() => {
        fetch("/api/llm/providers").then(r => r.json()).then(d => {
            setProviders(d);
            const savedP = localStorage.getItem("llm_provider") || "ollama";
            const savedM = localStorage.getItem("llm_model") || "";
            setSelectedProvider(savedP);
            const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
            setSelectedModel(savedM && models.some((m:{name:string}) => m.name === savedM) ? savedM : (models[0]?.name || ""));
            setStatus(models.length > 0 ? "ready" : "error");
        }).catch(() => {
            setProviders({ ollama: [{name:"llama3.2:3b"}] });
            setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
            setStatus("ready");
        });
    }, []);
    const save = (p:string, m:string) => { localStorage.setItem("llm_provider", p); localStorage.setItem("llm_model", m); };
    const models = providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
    return (
        <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
                <CardTitle className="text-white">Local LLM</CardTitle>
                <CardDescription className="text-slate-400">Select provider and model for AI features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
                <select className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
                    value={selectedProvider} onChange={(e) => { setSelectedProvider(e.target.value); save(e.target.value, ""); }}>
                    <option value="ollama">Ollama</option>
                    <option value="lm_studio">LM Studio</option>
                </select>
                <select className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
                    value={selectedModel} onChange={(e) => { setSelectedModel(e.target.value); save(selectedProvider, e.target.value); }}>
                    {models.map((m) => <option key={m.name} value={m.name}>{m.name}</option>)}
                </select>
            </CardContent>
        </Card>
    );
}

export function Settings() {
  const [apiHost, setApiHost] = useState(getApiBase());
  const [testing, setTesting] = useState(false);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [ghidraInstalled, setGhidraInstalled] = useState<boolean | null>(null);
  const [ghidraPlugin, setGhidraPlugin] = useState<boolean | null>(null);

  useEffect(() => {
    setApiBase(apiHost);
  }, [apiHost]);

  const testConnection = () => {
    setTesting(true);
    setBackendOk(null);
    setGhidraInstalled(null);
    setGhidraPlugin(null);
    const base = apiHost.trim() || getApiBase();
    fetch(`${base}/health`)
      .then((r) => r.ok)
      .then(setBackendOk)
      .catch(() => setBackendOk(false));
    fetch(`${base}/ghidra/status`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => {
        if (d) {
          setGhidraInstalled(d.installed === true);
          setGhidraPlugin(d.http_server_running === true);
        }
      })
      .catch(() => {
        setGhidraInstalled(false);
        setGhidraPlugin(false);
      })
      .finally(() => setTesting(false));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Configuration</h2>
        <p className="text-slate-400">Backend API and connection</p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">API Bridge</CardTitle>
          <CardDescription className="text-slate-400">
            FastAPI backend (SOTA port 10750). Saved in localStorage.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label className="text-slate-300">API base URL</Label>
            <Input
              className="bg-slate-900 border-slate-800 text-slate-100 font-mono"
              value={apiHost}
              onChange={(e) => setApiHost(e.target.value)}
              placeholder="http://localhost:10750"
            />
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={testConnection}
              disabled={testing}
            >
              {testing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Test connection
            </Button>
            {backendOk === true && (
              <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                <CheckCircle className="h-3 w-3 mr-1" /> Backend OK
              </Badge>
            )}
            {backendOk === false && (
              <Badge variant="destructive">
                <XCircle className="h-3 w-3 mr-1" /> Not reachable
              </Badge>
            )}
          </div>
          {ghidraInstalled !== null && (
            <p className="text-sm text-slate-400">
              Ghidra: {ghidraInstalled ? "installed" : "not found"}
              {ghidraInstalled && (ghidraPlugin ? ", plugin running" : ", plugin not running")}
            </p>
          )}
        </CardContent>
        </Card>

      <LLMSettings />
    </div>
  );
}
