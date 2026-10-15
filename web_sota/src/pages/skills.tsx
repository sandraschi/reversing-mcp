import { getApiBase } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";

export function Skills() {
  const [names, setNames] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/skills`)
      .then((r) => {
        if (!r.ok) throw new Error(`skills: ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (cancelled) return;
        const list: string[] = Array.isArray(d.skills) ? d.skills : [];
        setNames(list);
        if (list.length > 0) setSelected(list[0]);
        setLoading(false);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Skills unavailable");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    setContent("");
    setError(null);
    fetch(`${getApiBase()}/skill/${encodeURIComponent(selected)}`)
      .then((r) => {
        if (!r.ok) throw new Error(`skill ${selected}: ${r.status}`);
        return r.text();
      })
      .then(setContent)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Skill load failed"),
      );
  }, [selected]);

  return (
    <div className="space-y-6" data-testid="skills-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Skills</h2>
        <p className="text-slate-300">
          Agent skill preprompts served by the backend
        </p>
      </div>

      {loading && (
        <p className="text-sm text-slate-300" data-testid="skills-loading">
          Loading skills…
        </p>
      )}

      {error && (
        <Card
          className="border-red-900/50 bg-red-950/20"
          data-testid="skills-error"
        >
          <CardContent className="pt-6 text-sm text-red-400">
            {error}. Is the backend running?
          </CardContent>
        </Card>
      )}

      {!loading && !error && names.length === 0 && (
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="skills-empty"
        >
          <CardContent className="pt-6 text-sm text-slate-300">
            No skills registered. Skills live in{" "}
            <span className="font-mono">src/reversing_mcp/skills/</span>.
          </CardContent>
        </Card>
      )}

      {names.length > 0 && (
        <div className="flex flex-wrap gap-2" data-testid="skills-list">
          {names.map((n) => (
            <button
              type="button"
              key={n}
              onClick={() => setSelected(n)}
              className={`text-sm px-3 py-1.5 rounded-md border transition-colors ${
                n === selected
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      )}

      {selected && content && (
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="skills-content"
        >
          <CardHeader>
            <CardTitle className="text-white font-mono text-base">
              skill:{selected}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm text-slate-300 bg-slate-900 rounded-lg p-4 overflow-y-auto whitespace-pre-wrap font-mono">
              {content}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
