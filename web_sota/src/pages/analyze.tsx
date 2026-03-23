import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getApiBase } from "@/common/api";
import { Upload, Loader2, Search, CheckCircle, XCircle } from "lucide-react";

const BINARY_EXTS = [".exe", ".dll", ".so", ".dylib", ".bin", ".com", ".sys", ".drv"];

function isValidBinary(file: File): boolean {
  const name = file.name.toLowerCase();
  return BINARY_EXTS.some((ext) => name.endsWith(ext)) || file.type === "application/octet-stream";
}

function formatSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

export function Analyze() {
  const [file, setFile] = useState<File | null>(null);
  const [basic, setBasic] = useState(true);
  const [pe, setPe] = useState(true);
  const [ghidra, setGhidra] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setFile(f || null);
    setError(null);
    setResult(null);
  };

  const runAnalysis = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const tools: string[] = [];
      if (basic) tools.push("file", "strings", "entropy");
      if (pe) tools.push("pefile");
      if (ghidra) tools.push("ghidra");
      if (tools.length) formData.append("tools", tools.join(","));

      const res = await fetch(`${getApiBase()}/analyze/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Analyze Binary</h2>
        <p className="text-slate-400">Upload an executable for reverse engineering analysis</p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Upload className="h-5 w-5" />
            File Upload
          </CardTitle>
          <CardDescription className="text-slate-400">
            Choose a binary (.exe, .dll, .so, .bin, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/50 p-4 hover:bg-slate-800/50">
              <input
                type="file"
                accept={BINARY_EXTS.join(",")}
                className="hidden"
                onChange={onFileChange}
              />
              <Upload className="h-5 w-5 text-slate-400" />
              <span className="text-sm text-slate-300">
                {file ? file.name : "Select a binary file"}
              </span>
            </label>
            {file && (
              <div className="flex flex-wrap gap-2 text-sm text-slate-400">
                <span>{formatSize(file.size)}</span>
                {!isValidBinary(file) && (
                  <Badge variant="destructive">Unsupported type</Badge>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {file && isValidBinary(file) && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Analysis options</CardTitle>
            <CardDescription className="text-slate-400">
              Select tools to run (backend: {getApiBase()})
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={basic}
                  onChange={(e) => setBasic(e.target.checked)}
                  className="rounded border-slate-600"
                />
                <span className="text-sm text-slate-300">Basic (file, strings, entropy)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={pe}
                  onChange={(e) => setPe(e.target.checked)}
                  className="rounded border-slate-600"
                />
                <span className="text-sm text-slate-300">PE (Windows)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ghidra}
                  onChange={(e) => setGhidra(e.target.checked)}
                  className="rounded border-slate-600"
                />
                <span className="text-sm text-slate-300">Ghidra</span>
              </label>
            </div>
            <Button
              onClick={runAnalysis}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running analysis…
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Start analysis
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 flex items-center gap-2 text-red-400">
            <XCircle className="h-5 w-5 shrink-0" />
            <span>{error}. Ensure backend is running (e.g. start-webapp.ps1).</span>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <CheckCircle className="h-5 w-5 text-emerald-500" />
              Analysis result
            </CardTitle>
            <CardDescription className="text-slate-400">
              {String(result.file_path)} — score {Number(result.analysis_score ?? 0).toFixed(0)}%
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-slate-500">Tools</div>
                <div className="text-slate-200 font-mono">
                  {(result.tools_used as string[])?.join(", ") ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-slate-500">Strings</div>
                <div className="text-slate-200">{Number(result.strings ?? 0)}</div>
              </div>
              <div>
                <div className="text-slate-500">Functions</div>
                <div className="text-slate-200">{Number(result.functions ?? 0)}</div>
              </div>
              <div>
                <div className="text-slate-500">Language hint</div>
                <div className="text-slate-200">{String(result.language_hint ?? "—")}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!file && (
        <p className="text-sm text-slate-500">
          Need help? See <a href="/help" className="text-blue-400 hover:underline">Help</a>.
        </p>
      )}
    </div>
  );
}
