import { Inbox as InboxIcon, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface InboxEntry {
  id: string;
  ts: string;
  kind: string;
  title: string;
  detail: string;
}

const LS_KEY = "reversing-mcp-inbox";

/** Read by Inbox page; written by Analyze (and later the tour runner). */
export function pushInbox(entry: Omit<InboxEntry, "id" | "ts">) {
  try {
    const raw = localStorage.getItem(LS_KEY);
    const arr: InboxEntry[] = raw ? JSON.parse(raw) : [];
    arr.unshift({
      ...entry,
      id: String(Date.now()),
      ts: new Date().toISOString(),
    });
    localStorage.setItem(LS_KEY, JSON.stringify(arr.slice(0, 100)));
  } catch {
    /* private mode */
  }
}

function loadInbox(): InboxEntry[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function Inbox() {
  const [entries, setEntries] = useState<InboxEntry[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setEntries(loadInbox());
    setLoading(false);
  }, []);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      (e) =>
        e.title.toLowerCase().includes(q) ||
        e.detail.toLowerCase().includes(q) ||
        e.kind.toLowerCase().includes(q),
    );
  }, [entries, filter]);

  const clear = () => {
    setEntries([]);
    try {
      localStorage.removeItem(LS_KEY);
    } catch {
      /* private mode */
    }
  };

  return (
    <div className="space-y-6" data-testid="inbox-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Inbox
          </h2>
          <p className="text-slate-400">
            Recent analysis results, newest first
          </p>
        </div>
        <button
          type="button"
          onClick={clear}
          disabled={entries.length === 0}
          className="text-sm text-red-400 border border-red-900/30 rounded-md px-3 py-1.5 hover:bg-red-950/20 disabled:opacity-40 flex items-center gap-1"
          data-testid="inbox-clear"
        >
          <Trash2 className="h-3 w-3" /> Clear
        </button>
      </div>

      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by title, kind, detail…"
        className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
        data-testid="inbox-filter"
      />

      {loading && (
        <p className="text-sm text-slate-500" data-testid="inbox-loading">
          Loading…
        </p>
      )}

      {!loading && visible.length === 0 && (
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="inbox-empty"
        >
          <CardContent className="pt-6 text-sm text-slate-400">
            {entries.length === 0 ? (
              <span>
                Nothing here yet.{" "}
                <a className="underline text-blue-400" href="#/analyze">
                  Analyze a binary
                </a>{" "}
                and results land in this inbox.
              </span>
            ) : (
              "No entries match this filter."
            )}
          </CardContent>
        </Card>
      )}

      {visible.map((e) => (
        <Card
          key={e.id}
          className="border-slate-800 bg-slate-950/50"
          data-testid="inbox-entry"
        >
          <CardHeader>
            <CardTitle className="text-white text-base flex items-center gap-2">
              <InboxIcon className="h-4 w-4 text-blue-400" />
              {e.title}
              <span className="text-sm font-normal text-slate-500">
                [{e.kind}]
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 whitespace-pre-wrap break-words">
              {e.detail}
            </p>
            <p className="text-sm text-slate-500 mt-1 font-mono">{e.ts}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
