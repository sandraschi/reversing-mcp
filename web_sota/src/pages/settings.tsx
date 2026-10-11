import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getApiBase, setApiBase } from "@/common/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchDiscovery, loadSelection, saveSelection } from "@/lib/llm";
import { pickPreferredModel } from "@/lib/model-preference";

function LLMSettings() {
  const [models, setModels] = useState<string[]>([]);
  const [running, setRunning] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [note, setNote] = useState("");
  useEffect(() => {
    let cancelled = false;
    fetchDiscovery()
      .then((d) => {
        if (cancelled) return;
        if (!d.detected) {
          setModels([]);
          setRunning([]);
          setStatus("error");
          setNote(d.error || `Ollama not reachable at ${d.base_url}`);
          return;
        }
        setModels(d.models);
        setRunning(d.running);
        const saved = loadSelection().model;
        // Resident-first: saved model only if still installed, else backend default.
        const current =
          saved && d.models.includes(saved)
            ? saved
            : (d.default_model ?? d.models[0] ?? "");
        // Cross-check client-side with the vendored preference table.
        const preferred = pickPreferredModel(d.running, d.models);
        setSelectedModel(current || preferred);
        setStatus(d.models.length > 0 ? "ready" : "error");
        setNote(
          d.running.length > 0
            ? `Resident in VRAM: ${d.running.join(", ")} (defaults never evict these)`
            : "No model resident; default is highest-preference installed.",
        );
      })
      .catch(() => {
        if (cancelled) return;
        // No fake stand-ins: error state, never an undeclared mock model.
        setModels([]);
        setRunning([]);
        setStatus("error");
        setNote("Backend not reachable. Start it (repo root start.ps1).");
      });
    return () => {
      cancelled = true;
    };
  }, []);
  const save = (p: string, m: string) => {
    saveSelection(p, m);
    fetch(`${getApiBase()}/llm/select_model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: p, model: m }),
    }).catch(() => {
      /* backend down - local selection applies on reconnect */
    });
  };
  const saveAndSelect = (p: string, m: string) => {
    setSelectedProvider(p);
    setSelectedModel(m);
    save(p, m);
  };
  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <CardTitle className="text-white">Local LLM</CardTitle>
        <CardDescription className="text-slate-400">
          Ollama provider · resident-first defaults (never evict a loaded model)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {status === "loading" && (
          <p className="text-sm text-slate-500 flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" /> Detecting Ollama…
          </p>
        )}
        {status === "error" && (
          <p className="text-sm text-red-400">
            {note || "Ollama not detected."}
          </p>
        )}
        {status === "ready" && (
          <>
            <select
              className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
              value={selectedProvider}
              onChange={(e) => {
                saveAndSelect(e.target.value, "");
              }}
            >
              <option value="ollama">Ollama</option>
            </select>
            <select
              className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
              value={selectedModel}
              onChange={(e) => {
                saveAndSelect(selectedProvider, e.target.value);
              }}
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                  {running.includes(m) ? " (resident)" : ""}
                </option>
              ))}
            </select>
            {note && <p className="text-xs text-slate-500">{note}</p>}
          </>
        )}
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
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) {
          setGhidraInstalled(d.installed === true);
          setGhidraPlugin(d.bridge_running === true);
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
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Configuration
        </h2>
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
              {testing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : null}
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
              {ghidraInstalled &&
                (ghidraPlugin ? ", plugin running" : ", plugin not running")}
            </p>
          )}
        </CardContent>
      </Card>

      <LLMSettings />
    </div>
  );
}
