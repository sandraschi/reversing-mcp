import { GhidraHeader } from "@/components/ghidra/GhidraHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { type HistoryEntry, useGhidraHistory } from "@/lib/ghidra";
import { CheckCircle, RotateCcw, Search, Trash2, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

type Filter = "all" | "ok" | "error";
const PAGE_SIZE = 20;

export function GhidraHistory() {
  const { entries, remove, clear } = useGhidraHistory();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [sort, setSort] = useState<"recent" | "tool">("recent");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const rows = entries
      .filter((e) => filter === "all" || (filter === "ok" ? e.ok : !e.ok))
      .filter(
        (e) =>
          !needle ||
          `${e.tool} ${e.preview} ${JSON.stringify(e.args)}`
            .toLowerCase()
            .includes(needle),
      );
    if (sort === "tool") {
      rows.sort(
        (a, b) => a.tool.localeCompare(b.tool) || b.at.localeCompare(a.at),
      );
    }
    // "recent" is the store's natural order (newest first).
    return rows;
  }, [entries, q, filter, sort]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: reset page on filter change
  useEffect(() => {
    setPage(1);
  }, [q, filter, sort]);

  const total = filtered.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const replayHref = (e: HistoryEntry) =>
    `/ghidra?tool=${encodeURIComponent(e.tool)}`;

  return (
    <div className="space-y-5" data-testid="ghidra-history-page">
      <GhidraHeader
        title="Call History"
        blurb="Every ReVa tool call you have run from the Workbench, kept in this browser. Re-open one to run it again, or clear the log."
      />

      <div
        className="flex flex-wrap items-center gap-3"
        data-testid="ghidra-history-controls"
      >
        <div className="relative flex-1 min-w-[12rem]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter by tool, args or output..."
            className="w-full rounded-md border border-slate-700 bg-slate-900 pl-9 pr-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none focus:border-red-500"
            data-testid="ghidra-history-search"
          />
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as Filter)}
          className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-red-500"
          data-testid="ghidra-history-filter"
        >
          <option value="all">All results</option>
          <option value="ok">OK only</option>
          <option value="error">Errors only</option>
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as "recent" | "tool")}
          className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-red-500"
          data-testid="ghidra-history-sort"
        >
          <option value="recent">Sort: most recent</option>
          <option value="tool">Sort: tool name</option>
        </select>
        <span
          className="text-sm text-slate-400"
          data-testid="ghidra-history-count"
        >
          {total} of {entries.length}
        </span>
        {entries.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={clear}
            className="border-amber-700 text-amber-400"
            data-testid="ghidra-history-clear"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear all
          </Button>
        )}
      </div>

      {entries.length === 0 ? (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6 text-slate-300">
            No calls yet. Run a tool from the{" "}
            <Link to="/ghidra" className="text-red-400 hover:underline">
              Workbench
            </Link>{" "}
            and it shows up here.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2" data-testid="ghidra-history-list">
          {shown.length === 0 && (
            <p className="text-sm text-slate-300">
              No entry matches these filters.
            </p>
          )}
          {shown.map((e) => (
            <div
              key={e.id}
              data-testid="ghidra-history-item"
              className="rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 min-w-0">
                  {e.ok ? (
                    <CheckCircle className="h-4 w-4 shrink-0 text-emerald-500" />
                  ) : (
                    <XCircle className="h-4 w-4 shrink-0 text-red-500" />
                  )}
                  <span className="font-mono text-sm text-slate-100 truncate">
                    {e.tool}
                  </span>
                  <span className="text-xs text-slate-500 shrink-0">
                    {e.at.slice(11, 19)}
                    {e.elapsed_s != null ? ` · ${e.elapsed_s}s` : ""}
                  </span>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Link
                    to={replayHref(e)}
                    className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
                    title="Re-open in Workbench"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Replay
                  </Link>
                  <button
                    type="button"
                    onClick={() => remove(e.id)}
                    className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                    title="Remove entry"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
              <p
                className="mt-1 pl-6 text-xs text-slate-400 font-mono truncate"
                title={e.preview}
              >
                {e.preview || "(no output)"}
              </p>
            </div>
          ))}
        </div>
      )}

      {pageCount > 1 && (
        <div
          className="flex items-center justify-center gap-3"
          data-testid="ghidra-history-pager"
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
    </div>
  );
}
