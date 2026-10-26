import { GhidraHeader } from "@/components/ghidra/GhidraHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  type ToolSummary,
  ghidraApi,
  toolCategory,
  useGhidraSession,
} from "@/lib/ghidra";
import { ArrowRight, Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

type SortKey = "name" | "category";
const PAGE_SIZE = 20;

export function GhidraTools() {
  const { session, reachable, refresh } = useGhidraSession();
  const [tools, setTools] = useState<ToolSummary[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");
  const [sort, setSort] = useState<SortKey>("name");
  const [page, setPage] = useState(1);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const ready = session?.state === "ready";

  useEffect(() => {
    if (!ready) return;
    setLoading(true);
    setErr(null);
    ghidraApi
      .allTools()
      .then(setTools)
      .catch((e) =>
        setErr(e instanceof Error ? e.message : "Tool listing failed"),
      )
      .finally(() => setLoading(false));
  }, [ready]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const t of tools ?? []) set.add(toolCategory(t.name));
    return ["all", ...Array.from(set).sort()];
  }, [tools]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const rows = (tools ?? [])
      .filter((t) => cat === "all" || toolCategory(t.name) === cat)
      .filter(
        (t) =>
          !needle || `${t.name} ${t.summary}`.toLowerCase().includes(needle),
      );
    rows.sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name)
        : toolCategory(a.name).localeCompare(toolCategory(b.name)) ||
          a.name.localeCompare(b.name),
    );
    return rows;
  }, [tools, q, cat, sort]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: reset page when the result set changes
  useEffect(() => {
    setPage(1);
  }, [q, cat, sort]);

  const total = filtered.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="space-y-5" data-testid="ghidra-tools-page">
      <GhidraHeader
        title="ReVa Tool Catalogue"
        blurb="Every Ghidra tool the session exposes, searchable and grouped. Pick one to open it in the Workbench with its argument skeleton filled in."
      />

      {reachable === false && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-400">
            Backend not reachable.
          </CardContent>
        </Card>
      )}

      {session && !ready && reachable !== false && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6 text-slate-300">
            No ready session.{" "}
            <Link to="/ghidra" className="text-red-400 hover:underline">
              Start one in the Workbench
            </Link>{" "}
            to load the catalogue.
          </CardContent>
        </Card>
      )}

      {ready && (
        <>
          <div
            className="flex flex-wrap items-center gap-3"
            data-testid="ghidra-tools-controls"
          >
            <div className="relative flex-1 min-w-[12rem]">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Filter tools..."
                className="w-full rounded-md border border-slate-700 bg-slate-900 pl-9 pr-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none focus:border-red-500"
                data-testid="ghidra-tools-search"
              />
            </div>
            <select
              value={cat}
              onChange={(e) => setCat(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-red-500"
              data-testid="ghidra-tools-filter"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c === "all" ? "All categories" : c}
                </option>
              ))}
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-red-500"
              data-testid="ghidra-tools-sort"
            >
              <option value="name">Sort: name</option>
              <option value="category">Sort: category</option>
            </select>
            <span
              className="text-sm text-slate-400"
              data-testid="ghidra-tools-count"
            >
              {total} of {tools?.length ?? 0}
            </span>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-slate-300" />
            </div>
          )}
          {err && <p className="text-sm text-red-400">{err}</p>}

          {!loading && (
            <div className="space-y-2" data-testid="ghidra-tools-list">
              {shown.length === 0 && (
                <p className="text-sm text-slate-300">
                  No tool matches these filters.
                </p>
              )}
              {shown.map((t) => (
                <Link
                  key={t.name}
                  to={`/ghidra?tool=${encodeURIComponent(t.name)}`}
                  data-testid="ghidra-tool-item"
                  className="group flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3 hover:border-red-700/60"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-slate-100">
                        {t.name}
                      </span>
                      <span className="rounded border border-slate-700 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                        {toolCategory(t.name)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 truncate">
                      {t.summary}
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-slate-600 group-hover:text-red-400" />
                </Link>
              ))}
            </div>
          )}

          {pageCount > 1 && (
            <div
              className="flex items-center justify-center gap-3"
              data-testid="ghidra-tools-pager"
            >
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="border-slate-700 disabled:opacity-40"
              >
                Prev
              </Button>
              <span className="text-sm text-slate-400">
                Page {page} of {pageCount}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= pageCount}
                onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                className="border-slate-700 disabled:opacity-40"
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
