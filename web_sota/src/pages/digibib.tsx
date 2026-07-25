import { getApiBase } from "@/common/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  FileSearch,
  Globe,
  Loader2,
  Search,
  Sigma,
} from "lucide-react";
import { useState } from "react";

type SnapData = Record<string, unknown>;

export function DigiBib() {
  const [loading, setLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [findResult, setFindResult] = useState<Record<string, unknown> | null>(null);
  const [snapResult, setSnapResult] = useState<SnapData | null>(null);
  const [stringsResult, setStringsResult] = useState<Record<string, unknown> | null>(null);
  const [dkiPath, setDkiPath] = useState("");
  const [dkiResult, setDkiResult] = useState<Record<string, unknown> | null>(null);

  const base = getApiBase();

  async function runStep(stepId: number, url: string) {
    setLoading(stepId);
    setError(null);
    try {
      const r = await fetch(`${base}${url}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      if (stepId === 0) setFindResult(data);
      else if (stepId === 1) setSnapResult(data as SnapData);
      else if (stepId === 2) setStringsResult(data);
      return data;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      return null;
    } finally {
      setLoading(null);
    }
  }

  async function decodeDki() {
    if (!dkiPath.trim()) return;
    setLoading(4);
    setError(null);
    try {
      const r = await fetch(`${base}/api/v1/digibib/decode-dki?path=${encodeURIComponent(dkiPath)}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setDkiResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Decode failed");
    } finally {
      setLoading(null);
    }
  }

  const steps = [
    { id: 0, label: "Find Binary", done: findResult?.found },
    { id: 1, label: "Snapshot", done: snapResult?.success },
    { id: 2, label: "Strings", done: stringsResult?.success },
    { id: 3, label: "Entropy", done: snapResult?.success },
    { id: 4, label: "DKI Decode", done: dkiResult?.success },
  ];

  const snap = (snapResult?.file_info as SnapData) || null;
  const ent = (snapResult?.entropy as SnapData) || null;

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-lg border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6">
        <div className="flex items-center gap-3 mb-3">
          <BookOpen className="h-8 w-8 text-amber-500" />
          <div>
            <h2 className="text-2xl font-bold text-white">DigiBib Reversing Lab</h2>
            <p className="text-slate-400 text-sm">
              Walk through the Digibib5.exe / Directmedia reversing workflow step by step
            </p>
          </div>
        </div>
        <p className="text-slate-400 text-sm leading-relaxed max-w-3xl">
          <strong className="text-slate-200">Digitale Bibliothek</strong> was a 1990s German e-book
          platform by Directmedia Publishing. This lab walks through reversing Digibib5.exe and its
          proprietary .DKI container format. See the{" "}
          <a href="https://github.com/sandraschi/reversing-mcp/blob/master/docs/DIGIBIB_REVERSING_GUIDE.md"
            className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">
            full reversing guide <ExternalLink className="h-3 w-3 inline" />
          </a>{" "}
          for detailed methodology.
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {steps.map((s) => (
          <div key={s.id} className="flex items-center gap-1 shrink-0">
            <Badge variant={s.done ? "default" : "outline"}
              className={s.done
                ? "bg-emerald-900/50 text-emerald-400 border-emerald-700"
                : "border-slate-700 text-slate-500"}>
              {s.done ? <CheckCircle2 className="h-3 w-3 mr-1" /> : null}
              {s.label}
            </Badge>
            {s.id < steps.length - 1 && <ChevronRight className="h-4 w-4 text-slate-600" />}
          </div>
        ))}
      </div>

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-400 text-sm">{error}</CardContent>
        </Card>
      )}

      {/* Step 0 */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            <FileSearch className="h-5 w-5 text-blue-500" />
            Step 0 — Find Digibib5.exe
            {findResult?.found ? <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">Found</Badge> : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-400">Scan known paths (fixtures, Program Files) for Digibib5.exe.</p>
          <Button onClick={() => runStep(0, "/api/v1/digibib/find")} disabled={loading === 0} size="sm">
            {loading === 0 ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileSearch className="h-4 w-4 mr-2" />}
            Scan for binary
          </Button>
          {findResult && (
            <div className="text-sm space-y-1">
              <p className={findResult.found ? "text-emerald-400" : "text-red-400"}>
                {findResult.found ? `Found at ${findResult.path}` : "Not found in standard paths"}
              </p>
              {!findResult.found && (
                <p className="text-slate-500 text-xs">
                  Searched: {(findResult.paths_searched as string[])?.join(", ") || "—"}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 1 */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            <Search className="h-5 w-5 text-blue-500" />
            Step 1 — Research Snapshot
            {snapResult?.success ? <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">Done</Badge> : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-400">Full static analysis: PE summary, entropy, keyword strings, tool availability.</p>
          <Button onClick={() => runStep(1, "/api/v1/digibib/snapshot")} disabled={loading === 1 || !findResult?.found} size="sm">
            {loading === 1 ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
            Run snapshot
          </Button>
          {snapResult?.success && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mt-2">
              <div>
                <p className="text-slate-500 text-xs">File size</p>
                <p className="text-white font-mono">{Number(snap?.size || 0).toLocaleString()} bytes</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Type</p>
                <p className="text-white font-mono">{(snap?.type as string) || "—"}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">DM string hits</p>
                <p className="text-white font-mono">{String(snapResult.directmedia_string_hits_total || 0)}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Overall entropy</p>
                <p className="text-white font-mono">{String(ent?.overall || "—")}</p>
              </div>
            </div>
          )}
          {snapResult && !snapResult.success && (
            <p className="text-red-400 text-sm">{String(snapResult.error)}</p>
          )}
        </CardContent>
      </Card>

      {/* Step 2 */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            <Globe className="h-5 w-5 text-blue-500" />
            Step 2 — Directmedia Keyword Strings
            {stringsResult?.success ? (
              <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">
                {String((stringsResult.hits as unknown[])?.length || 0)} hits
              </Badge>
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-400">
            Strings matching DKI, decompress, inflate, ReadFile and other keywords. Xref anchors for Ghidra/ReVa.
          </p>
          <Button onClick={() => runStep(2, "/api/v1/digibib/directmedia-strings")} disabled={loading === 2 || !findResult?.found} size="sm">
            {loading === 2 ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
            Extract keyword strings
          </Button>
          {stringsResult?.success && (
            <div className="max-h-64 overflow-y-auto space-y-1 mt-2 border border-slate-800 rounded-lg p-2">
              {(stringsResult.hits as Array<Record<string, unknown>>)?.slice(0, 50).map((h, i) => (
                <div key={i} className="flex items-start gap-2 text-xs font-mono border-b border-slate-800 py-1">
                  <span className="text-slate-500 shrink-0">0x{(h.offset as number)?.toString(16).padStart(8, "0")}</span>
                  <span className="text-slate-300 truncate">{(h.string as string)?.slice(0, 120)}</span>
                  <Badge className="shrink-0 bg-amber-900/30 text-amber-400 border-amber-800 text-[10px]">
                    {h.keyword_hit as string}
                  </Badge>
                </div>
              ))}
              {((stringsResult.hits as unknown[])?.length || 0) > 50 && (
                <p className="text-xs text-slate-500 pt-1">...and {(stringsResult.hits as unknown[]).length - 50} more</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 3 */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            <Sigma className="h-5 w-5 text-purple-500" />
            Step 3 — Entropy Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          {snapResult?.success ? (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div />
              <div>
                <p className="text-slate-500 text-xs">Overall entropy</p>
                <p className="text-white font-mono text-lg">{Number(ent?.overall || 0).toFixed(2)}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {Number(ent?.overall || 0) > 7.5
                    ? "High — likely compressed/encrypted"
                    : Number(ent?.overall || 0) > 5.5
                      ? "Medium — mixed content"
                      : "Low — plain text/code"}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Compressed regions</p>
                <p className="text-white font-mono">{String(ent?.compressed_region_count || 0)}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Random/encrypted regions</p>
                <p className="text-white font-mono">{String(ent?.random_region_count || 0)}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Run Step 1 first to see entropy data.</p>
          )}
        </CardContent>
      </Card>

      {/* Step 4 */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            <BookOpen className="h-5 w-5 text-blue-500" />
            Step 4 — DKI Decode
            {dkiResult?.success ? <Badge className="bg-emerald-900/50 text-emerald-400 border-emerald-700">Decoded</Badge> : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-400">
            Try the heuristic decoder on a .DKI file (zlib/gzip autodetection with header skips).
            Enter a path to a .DKI file on disk.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={dkiPath}
              onChange={(e) => setDkiPath(e.target.value)}
              placeholder="e.g. L:/Multimedia Files/.../DB094/Data/TEXT.DKI"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
            />
            <Button onClick={decodeDki} disabled={loading === 4 || !dkiPath.trim()} size="sm">
              {loading === 4 ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <BookOpen className="h-4 w-4 mr-2" />}
              Decode
            </Button>
          </div>
          {dkiResult && (
            <div className="text-sm space-y-2 mt-2">
              <div className="flex gap-4">
                <div>
                  <p className="text-slate-500 text-xs">Strategy</p>
                  <p className="text-white font-mono">{String(dkiResult.strategy_used || "—")}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs">Encoding</p>
                  <p className="text-white font-mono">{String(dkiResult.encoding_guess || "—")}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs">Uncompressed</p>
                  <p className="text-white font-mono">{Number(dkiResult.uncompressed_bytes || 0).toLocaleString()} bytes</p>
                </div>
              </div>
              {dkiResult.text_preview && (
                <div>
                  <p className="text-slate-500 text-xs mb-1">Preview</p>
                  <pre className="text-xs text-slate-300 bg-slate-900 rounded-lg p-3 max-h-40 overflow-y-auto whitespace-pre-wrap font-mono">
                    {String(dkiResult.text_preview).slice(0, 2000)}
                  </pre>
                </div>
              )}
              {!dkiResult.success && (
                <p className="text-red-400 text-xs">{String(dkiResult.error)}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Next steps */}
      <Card className="border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950">
        <CardHeader>
          <CardTitle className="text-white text-lg">Next Steps</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-4 text-sm">
          <a href="https://github.com/sandraschi/reversing-mcp/blob/master/docs/GHIDRA.md"
            target="_blank" rel="noreferrer"
            className="block rounded-lg border border-slate-700 bg-slate-900/50 p-3 hover:bg-slate-800/50 transition-colors">
            <p className="text-blue-400 font-medium mb-1">Ghidra + ReVa <ExternalLink className="h-3 w-3 inline" /></p>
            <p className="text-slate-400 text-xs">Interactive decompilation and xrefs in Ghidra via ReVa MCP</p>
          </a>
          <a href="https://github.com/sandraschi/reversing-mcp/blob/master/docs/IDR.md"
            target="_blank" rel="noreferrer"
            className="block rounded-lg border border-slate-700 bg-slate-900/50 p-3 hover:bg-slate-800/50 transition-colors">
            <p className="text-blue-400 font-medium mb-1">IDR Delphi Reconstructor <ExternalLink className="h-3 w-3 inline" /></p>
            <p className="text-slate-400 text-xs">Recover symbols, forms, and event handlers from the Delphi PE</p>
          </a>
          <a href="https://github.com/sandraschi/reversing-mcp/blob/master/docs/DIGIBIB_REVERSING_GUIDE.md"
            target="_blank" rel="noreferrer"
            className="block rounded-lg border border-slate-700 bg-slate-900/50 p-3 hover:bg-slate-800/50 transition-colors">
            <p className="text-blue-400 font-medium mb-1">Full Reversing Guide <ExternalLink className="h-3 w-3 inline" /></p>
            <p className="text-slate-400 text-xs">Dynamic tracing with Frida, procmon, offset-table extraction</p>
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
