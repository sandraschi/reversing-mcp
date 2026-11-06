import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  type ExtensionEntry,
  type InstalledExtension,
  extensionsApi,
} from "@/lib/extensions";
import { Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

export function Extensions() {
  const [catalog, setCatalog] = useState<ExtensionEntry[] | null>(null);
  const [installed, setInstalled] = useState<InstalledExtension[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [note, setNote] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [c, l] = await Promise.all([
        extensionsApi.catalog(),
        extensionsApi.list(),
      ]);
      if (!c.success) throw new Error("catalog failed");
      if (!l.success) throw new Error("list failed");
      setCatalog(c.entries);
      setInstalled(l.extensions);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function run(
    label: string,
    fn: () => Promise<{ success: boolean; message?: string; error?: string }>,
  ) {
    setBusy(label);
    setNote(null);
    try {
      const r = await fn();
      setNote(r.success ? (r.message ?? "OK") : (r.error ?? "Failed"));
      await refresh();
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-5" data-testid="extensions-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">
            Ghidra Extensions
          </h1>
          <p className="text-sm text-slate-400">
            Community loaders + processors (SNES/65816 first). Installs into the
            user Extensions dir - restart Ghidra to pick up.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refresh}
          disabled={loading}
          className="border-slate-700"
          data-testid="extensions-refresh"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </div>

      {err && <p className="text-sm text-red-400">{err}</p>}
      {note && <p className="text-sm text-slate-300">{note}</p>}

      <Card className="border-slate-800 bg-slate-950/50">
        <CardContent className="flex flex-wrap items-center gap-3 pt-6">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="ghidra-65816, owner/repo, or https .zip URL"
            className="min-w-[16rem] flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none focus:border-red-500"
            data-testid="extensions-install-input"
          />
          <Button
            size="sm"
            disabled={!name.trim() || busy !== null}
            onClick={() =>
              run(`install:${name}`, () => extensionsApi.install(name.trim()))
            }
            data-testid="extensions-install-btn"
          >
            {busy?.startsWith("install:") ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Install"
            )}
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-2" data-testid="extensions-catalog">
        {(catalog ?? []).map((e) => (
          <div
            key={e.name}
            className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
            data-testid="extensions-catalog-item"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-slate-100">
                  {e.name}
                </span>
                <span className="rounded border border-slate-700 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                  {e.kind}
                </span>
                {e.installed && (
                  <span className="rounded border border-green-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-green-400">
                    {e.enabled ? "enabled" : "disabled"}
                  </span>
                )}
              </div>
              <p className="truncate text-sm text-slate-400">{e.description}</p>
              <p className="truncate font-mono text-xs text-slate-500">
                {e.repo}
              </p>
            </div>
            {!e.installed && e.install_kind === "github_release" && (
              <Button
                variant="outline"
                size="sm"
                disabled={busy !== null}
                onClick={() =>
                  run(`install:${e.name}`, () => extensionsApi.install(e.name))
                }
                className="border-slate-700"
              >
                Install
              </Button>
            )}
          </div>
        ))}
      </div>

      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        Installed ({installed?.length ?? 0})
      </h2>
      <div className="space-y-2" data-testid="extensions-installed">
        {(installed ?? []).map((x) => (
          <div
            key={x.path}
            className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
            data-testid="extensions-installed-item"
          >
            <div className="min-w-0">
              <span className="font-mono text-sm text-slate-100">{x.name}</span>
              <p className="truncate font-mono text-xs text-slate-500">
                {x.path}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={busy !== null}
                onClick={() =>
                  run(`toggle:${x.name}`, () =>
                    extensionsApi.setEnabled(x.name, !x.enabled),
                  )
                }
                className="border-slate-700"
              >
                {x.enabled ? "Disable" : "Enable"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={busy !== null}
                onClick={() => {
                  if (
                    window.confirm(
                      `Delete extension '${x.name}'? This removes the directory.`,
                    )
                  ) {
                    run(`remove:${x.name}`, () =>
                      extensionsApi.remove(x.name, true),
                    );
                  }
                }}
                className="border-red-900/60 text-red-400"
              >
                Remove
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
