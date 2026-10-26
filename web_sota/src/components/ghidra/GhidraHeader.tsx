import { useGhidraSession } from "@/lib/ghidra";
import { BookOpen, History, Microscope, Play } from "lucide-react";
import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

const SUBNAV = [
  {
    href: "/ghidra",
    label: "Workbench",
    icon: Microscope,
    testid: "ghidra-nav-workbench",
  },
  {
    href: "/ghidra/tools",
    label: "Tool catalogue",
    icon: BookOpen,
    testid: "ghidra-nav-tools",
  },
  {
    href: "/ghidra/history",
    label: "Call history",
    icon: History,
    testid: "ghidra-nav-history",
  },
];

const STATE_STYLE: Record<string, { dot: string; label: string }> = {
  ready: { dot: "bg-emerald-500", label: "Ready" },
  starting: { dot: "bg-amber-500 animate-pulse", label: "Starting" },
  error: { dot: "bg-red-500", label: "Error" },
  stopped: { dot: "bg-slate-500", label: "No session" },
};

interface Props {
  title: string;
  blurb: string;
  /** Primary call to action, rendered as the hero button. */
  cta?: { label: string; to: string; testid: string };
}

/** Hero + session pill + sub-navigation shared by the three Ghidra pages. */
export function GhidraHeader({ title, blurb, cta }: Props) {
  const { session, reachable, refresh } = useGhidraSession();
  const location = useLocation();

  useEffect(() => {
    refresh();
    const fast = session?.state === "starting";
    const t = setInterval(refresh, fast ? 2000 : 10000);
    return () => clearInterval(t);
  }, [refresh, session?.state]);

  const st = STATE_STYLE[session?.state ?? "stopped"] ?? STATE_STYLE.stopped;

  return (
    <div className="space-y-4">
      <div
        className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-red-950/30 px-6 py-5"
        data-testid="ghidra-hero"
      >
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="min-w-0 max-w-3xl">
            <p className="text-xs uppercase tracking-widest text-red-400/80 font-medium">
              Ghidra via ReVa
            </p>
            <h2 className="text-2xl font-bold tracking-tight text-white mt-1">
              {title}
            </h2>
            <p className="text-slate-300 mt-1">{blurb}</p>
          </div>
          <div
            className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1.5"
            data-testid="ghidra-session-pill"
          >
            <span
              className={`h-2 w-2 rounded-full ${reachable === false ? "bg-red-500" : st.dot}`}
            />
            <span className="text-sm text-slate-200">
              {reachable === false
                ? "Backend offline"
                : session
                  ? `${st.label}${session.mode ? ` · ${session.mode}` : ""}${
                      session.state === "ready"
                        ? ` · ${session.tool_count} tools`
                        : ""
                    }`
                  : "Checking..."}
            </span>
          </div>
        </div>
        {cta && (
          <div className="mt-4">
            <Link
              to={cta.to}
              data-testid={cta.testid}
              className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-md bg-red-700 text-white hover:bg-red-600 font-medium"
            >
              <Play className="h-4 w-4" />
              {cta.label}
            </Link>
          </div>
        )}
      </div>

      <nav
        className="flex flex-wrap gap-1 border-b border-slate-800"
        data-testid="ghidra-subnav"
      >
        {SUBNAV.map((n) => {
          const active = location.pathname === n.href;
          return (
            <Link
              key={n.href}
              to={n.href}
              data-testid={n.testid}
              className={`-mb-px flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "border-red-500 text-white"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
              }`}
            >
              <n.icon className="h-4 w-4" />
              {n.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
