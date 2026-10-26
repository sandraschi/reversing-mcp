import { getApiBase } from "@/common/api";
import { Markdown } from "@/components/Markdown";
import {
  Book,
  ChevronDown,
  Cpu,
  FileQuestion,
  HelpCircle,
  Network,
  Wrench,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type HelpTab =
  | "overview"
  | "wrappee"
  | "tools"
  | "api"
  | "troubleshoot"
  | "faq";

const TABS: Array<{ id: HelpTab; name: string; description: string }> = [
  {
    id: "overview",
    name: "Overview",
    description: "What this app is, pages, architecture",
  },
  {
    id: "wrappee",
    name: "Engines",
    description: "Wrapped RE tools, live install state",
  },
  {
    id: "tools",
    name: "MCP Tools",
    description: "Every tool the server exposes",
  },
  {
    id: "api",
    name: "API & Ports",
    description: "Ports, env vars, endpoints, restart",
  },
  {
    id: "troubleshoot",
    name: "Error fix",
    description: "Symptoms, causes and exact fixes",
  },
  { id: "faq", name: "FAQ", description: "Frequently asked questions" },
];

const TAB_ICONS: Record<HelpTab, typeof Book> = {
  overview: Book,
  wrappee: Cpu,
  tools: Wrench,
  api: Network,
  troubleshoot: Wrench,
  faq: HelpCircle,
};

function Card({
  children,
  testid,
}: {
  children: React.ReactNode;
  testid?: string;
}) {
  return (
    <section
      data-testid={testid}
      className="rounded-lg border border-slate-800 bg-slate-950/50 p-5 space-y-3"
    >
      {children}
    </section>
  );
}

function H({ children }: { children: React.ReactNode }) {
  return <h3 className="text-base font-semibold text-white">{children}</h3>;
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-slate-300 leading-relaxed">{children}</p>;
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded bg-slate-800 px-1 py-0.5 font-mono text-xs text-slate-200">
      {children}
    </code>
  );
}

function Table({ head, rows }: { head: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left text-slate-300">
        <thead>
          <tr className="border-b border-slate-700 text-slate-400">
            {head.map((h) => (
              <th key={h} className="py-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j} className="py-2 pr-4 align-top">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * In-app doc viewer: fetches docs/*.md from the backend (/api/docs/{name})
 * and renders inline. Guide links never leave the app for GitHub - the
 * descriptions live in docs/, this only opens them where you stand.
 */
function DocLink({ file, label }: { file: string; label?: string }) {
  const [openFile, setOpenFile] = useState<string | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (f: string) => {
    setOpenFile(f);
    setContent(null);
    setError(null);
    try {
      const d = await fetch(`${getApiBase()}/api/docs/${f}`).then((r) =>
        r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)),
      );
      if (d.success) setContent(d.content);
      else setError(d.error ?? "Could not load doc");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load doc");
    }
  };

  return (
    <span className="inline">
      <button
        type="button"
        onClick={() => (openFile ? setOpenFile(null) : load(file))}
        className="inline-flex items-center gap-1 text-emerald-400 hover:underline"
        data-testid={`doclink-${file}`}
      >
        {label ?? file}
        <ChevronDown
          className={`h-3 w-3 transition-transform ${openFile ? "rotate-180" : ""}`}
        />
      </button>
      {openFile && (
        <span className="block mt-2 rounded-lg border border-slate-800 bg-slate-900/60 p-4 max-h-96 overflow-y-auto">
          {error && <span className="text-sm text-red-400">{error}</span>}
          {!error && content === null && (
            <span className="text-sm text-slate-300">Loading {openFile}…</span>
          )}
          {content !== null && (
            <Markdown text={content} onLocalDoc={(f) => load(f)} />
          )}
        </span>
      )}
    </span>
  );
}

/* ------------------------------------------------------------------ overview */

const PAGES: Array<[string, string, string]> = [
  [
    "Overview",
    "/",
    "Backend, tool count, Ghidra bridge and analysis readiness",
  ],
  [
    "Analyze",
    "/analyze",
    "Upload a binary: file type, strings, entropy, PE, optional engines",
  ],
  ["Inbox", "/inbox", "Incoming events and results"],
  [
    "DigiBib Lab",
    "/digibib",
    "Digibib5 / Directmedia DKI research (the reference target)",
  ],
  [
    "Ghidra",
    "/ghidra",
    "Decompile, xrefs, rename via ReVa behind one session (headless or attach to GUI)",
  ],
  ["Tools", "/tools", "Engine inventory"],
  ["Skills", "/skills", "Skill packs served to MCP clients (skill://)"],
  ["Status", "/status", "Engine + Ghidra bridge health"],
  ["Server", "/apps", "Capabilities and fleet apps"],
  [
    "AI Command",
    "/chat",
    "Chat with a local Ollama model, skill-first preprompt",
  ],
  ["Settings", "/settings", "API base URL, LLM provider and model"],
  ["Logs", "/logs", "Backend ring-buffer log (empty after restart)"],
];

function OverviewTab() {
  return (
    <div className="space-y-4" data-testid="help-overview">
      <Card>
        <H>What this is</H>
        <P>
          reversing-mcp is an MCP server plus web UI for agent-driven binary
          analysis. Static triage (file type, strings, entropy, PE structure)
          works with no extra installs; real RE engines (Ghidra, radare2, IDA,
          REA, ...) plug in when present. Its reference target is Digibib5.exe
          and the Directmedia <Code>.DKI</Code> format.
        </P>
      </Card>
      <Card>
        <H>Architecture</H>
        <Table
          head={["Part", "Where", "Notes"]}
          rows={[
            [
              "Web UI",
              <Code key="a">:10751</Code>,
              "Vite dev server (web_sota/)",
            ],
            [
              "Backend",
              <Code key="b">:10750</Code>,
              "FastAPI: REST routes + MCP over streamable HTTP at /mcp",
            ],
            [
              "Ghidra bridge",
              <Code key="c">:8089</Code>,
              "ReVa bridge, optional - only for interactive Ghidra status/decompile",
            ],
            [
              "Engines",
              "local executables",
              "Probed per request; see the Engines tab",
            ],
          ]}
        />
      </Card>
      <Card>
        <H>The Twin Methods: Disassembly + CUA Clickthrough</H>
        <P>
          Binary reverse engineering in reversing-mcp unifies two historically
          separate disciplines:
        </P>
        <ul className="list-disc pl-5 text-sm text-slate-300 space-y-1">
          <li>
            <strong>Conventional Disassembly (White-Box)</strong>: Ghidra, IDA,
            radare2, Hopper, capa, DiE, and Frida provide granular inspection of
            PE sections, decompiled C syntax, cross-references, and API hooks.
            However, large stripped binaries suffer from{" "}
            <em>Static Blindness</em> (thousands of unlabeled subroutines
            without user-context anchors).
          </li>
          <li>
            <strong>CUA Clickthrough &amp; Gym Oracle Loops (Black-Box)</strong>
            : Computer Use Agents drive the running binary via Windows
            accessibility (pywinauto) and OCR, recording real user interactions.
            However, pure UI testing suffers from <em>Dynamic Blindness</em>{" "}
            (observing external behavior without knowing the internal
            decompilation or encryption algorithm).
          </li>
        </ul>
        <P>
          <strong>Feature-to-Code Maps</strong>: Through{" "}
          <Code>correlate_session</Code> (ClickerLab / Gym Stage 3), runtime UI
          strings and interaction tokens are correlated with static
          cross-references in the binary. This automatically generates Ghidra
          plate comments and IDA import scripts (<Code>map_import_ida.py</Code>
          ), turning blind disassembly into verified feature maps.
        </P>
        <div className="pt-1 flex flex-wrap gap-4">
          <DocLink
            file="CUA_DISASSEMBLY_COMBO.md"
            label="Read Tier 3 CUA Disassembly Combo Spec"
          />
          <DocLink
            file="REVERSE_TO_CRAFT_PLAYBOOK.md"
            label="Read Reverse-to-Craft Playbook"
          />
        </div>
      </Card>
      <Card>
        <H>Pages</H>
        <Table
          head={["Page", "Route", "Purpose"]}
          rows={PAGES.map(([n, r, p]) => [n, <Code key={r}>{r}</Code>, p])}
        />
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------- engines */

type EngineInfo = {
  available?: boolean;
  version?: string | null;
  path?: string | null;
};

type EngineDef = {
  id: string;
  name: string;
  probe?: string; // key in /tools/status "engines"
  cost: string;
  /** What the tool IS and DOES (several lines) - the description lives here, not on GitHub. */
  blurb: string;
  wiring: string;
  status: string;
  doc: string;
  setup: string;
};

const ENGINES: EngineDef[] = [
  {
    id: "ghidra",
    name: "Ghidra",
    probe: "ghidra",
    cost: "free",
    blurb:
      "Ghidra is the NSA's free, open-source reverse-engineering framework: disassembler, decompiler, scriptable analysis, project database. " +
      "It turns machine code back into readable C-like pseudocode and maps every cross-reference. " +
      "Here it runs two ways: headless analyzeHeadless for batch jobs (function lists, batch decompile), and the ReVa bridge for interactive work (rename a function, ask for callers). " +
      "If you do one deep thing to a native binary, it happens in Ghidra.",
    wiring:
      "Headless analyzeHeadless; ReVa MCP bridge on :8089 for interactive work",
    status: "Implemented",
    doc: "GHIDRA.md",
    setup:
      "Install Ghidra, set GHIDRA_INSTALL_DIR (or GHIDRA_HOME), restart the backend.",
  },
  {
    id: "rea",
    name: "REA",
    probe: "rea",
    cost: "free (MIT)",
    blurb:
      "REA (Reverse Engineer Anything) is an agent-native sidecar: an MCP server plus CLI that opens targets Ghidra alone fumbles — JS/Electron bundles, .NET assemblies, APKs, firmware images, websites. " +
      "For native code it delegates to a provider (Hopper, Ghidra, IDA) and returns evidence with excerpts. " +
      "Think of it as the specialist you call when the target is not a plain PE: it picks the right tool and brings back receipts. " +
      "Separate process (npx rea-agents); this repo shells out to it and truncates large outputs with snapshot hints.",
    wiring:
      "rea_investigate -> npx rea-agents (JS/Electron, .NET, APK, native via provider)",
    status: "Implemented",
    doc: "REA.md",
    setup: "Node 22.19+, then just setup-rea, then restart the agent.",
  },
  {
    id: "idr",
    name: "IDR",
    cost: "free",
    blurb:
      "IDR (Interactive Delphi Reconstructor) decompiles Delphi executables and recovers what generic disassemblers cannot: form layouts, class hierarchies, RTTI symbols, event handlers. " +
      "Without it, Borland metadata looks like opaque blobs and every function is FUN_00xxxxxx; with it you get TTextReader.ReadLn. " +
      "It is a manual GUI tool, not an API — open the target, recover structure, import the map into Ghidra. " +
      "Mandatory reading for the Digibib5 mission (Delphi 7 target).",
    wiring: "Manual GUI; /api/v1/digibib/check-idr probes the install",
    status: "Probe only",
    doc: "IDR.md",
    setup: "Download IDR, open the target, use its Delphi form/VMT recovery.",
  },
  {
    id: "r2",
    name: "radare2",
    probe: "r2",
    cost: "free",
    blurb:
      "radare2 is a free, scriptable command-line analysis framework: disassemble, list functions and imports, inspect headers, all from flags and one-letter commands. " +
      "It is the fast, dependency-free complement to Ghidra — no project database, no JVM, answers in milliseconds. " +
      "Here it runs as a subprocess (r2 -A -q -c i for info, afl for functions) and is the default backend of find_functions auto mode. " +
      "Best first engine when Ghidra feels like bringing a mainframe.",
    wiring: "Subprocess r2 -A -q -c i / afl",
    status: "Implemented, unverified on dev host",
    doc: "RADARE2.md",
    setup: "Put the radare2 bin directory on PATH, restart the backend.",
  },
  {
    id: "binwalk",
    name: "binwalk",
    probe: "binwalk",
    cost: "free",
    blurb:
      "binwalk scans any file for embedded content: compressed streams, filesystems, images, executables hiding inside containers. " +
      "It answers 'is this data file secretly an archive?' — directly relevant to Directmedia .DKI volumes, which may wrap known formats. " +
      "This repo wires the signature scan only (binwalk -J, parsed as JSON); extraction (-e) is deliberately not wired. " +
      "Note the v2/v3 flag split: if a scan returns only raw_output, the -J assumption broke — check binwalk --help first.",
    wiring: "Subprocess binwalk -J (signature scan)",
    status: "Implemented, unverified on dev host",
    doc: "BINWALK.md",
    setup: "Install binwalk v3 or v2, put it on PATH, restart the backend.",
  },
  {
    id: "ida",
    name: "IDA Pro / Home",
    probe: "ida",
    cost: "EUR 365+/yr",
    blurb:
      "IDA Pro is the commercial reference disassembler/decompiler (Hex-Rays): best-in-class decompilation, FLIRT signatures, IDAPython scripting, headless batch mode. " +
      "This repo drives it headless (idat -A -S script) for analysis and function discovery, and gloms onto a running instance when one exists — licensing is your business, never checked. " +
      "IDA Free cannot do headless (no IDAPython), so it is detected but not wired. " +
      "Use it when Ghidra's output is ambiguous and a second decompiler opinion is worth more than the wait.",
    wiring:
      "Headless ida64.exe -A -S<script>; IDA Free cannot run it (no IDAPython)",
    status: "Implemented, never run against a real install",
    doc: "IDA.md",
    setup: "Install IDA Pro or Home; for 9.x or custom paths set IDA_DIR.",
  },
  {
    id: "hopper",
    name: "Hopper",
    cost: "~USD 100",
    blurb:
      "Hopper is a commercial macOS/Linux disassembler with a fast pseudo-code decompiler and a beloved UI — the indie alternative to IDA for Apple platforms. " +
      "There is no Windows build, so on this host it is reachable only as an REA provider name, never directly. " +
      "On macOS/Linux it is REA's first-ranked native provider; pass provider=hopper or let auto-select find it. " +
      "Do not buy it for a Windows-only setup.",
    wiring: "Only as an REA provider (provider=hopper)",
    status: "macOS/Linux only - not available on Windows",
    doc: "HOPPER.md",
    setup:
      "On macOS/Linux: just setup-rea can install it. On Windows: use Ghidra.",
  },
  {
    id: "die",
    name: "Detect It Easy",
    probe: "die",
    cost: "free",
    blurb:
      "Detect It Easy identifies what built a binary — compiler, linker, packer, protector, libraries — from signatures, in well under a second. " +
      "It is the right first question before any disassembly: a Delphi 7 tag (like Digibib5's) sends you to IDR; a UPX tag sends you to unpack first. " +
      "The packed flag (packer/protector/cryptor hit) gates the whole pipeline: packed means dynamic analysis, not static. " +
      "Gym triage runs it automatically on every run.",
    wiring:
      'engine(operation="die") -> diec -j: compiler, linker, packer, libraries',
    status: "Implemented, verified",
    doc: "DIE.md",
    setup:
      "Extract the DiE portable zip to D:\\Dev\\tools\\die or set DIE_DIR.",
  },
  {
    id: "capa",
    name: "capa",
    probe: "capa",
    cost: "free",
    blurb:
      "capa (Mandiant) matches ~1,000 rules against a binary and reports what it can do: file writes, crypto, anti-VM checks — each with ATT&CK/MBC ids. " +
      "For cloning, its output is a behaviour map: which capabilities exist and roughly where, before you read a single function. " +
      "It is slow on real targets (Digibib5: 42 minutes, 96 rules incl. anti-VM flags that matter for the clicker-in-VM plan), so Gym triage budgets it and says so on timeout. " +
      "Raw JSON is never returned whole; you get ranked rule rows.",
    wiring:
      'engine(operation="capa") -> capa -j with rules + signatures; Gym triage',
    status: "Implemented, verified - slow (~42 min on Digibib5)",
    doc: "CAPA.md",
    setup:
      "uv tool install flare-capa, plus capa-rules and sigs (CAPA_RULES / CAPA_SIGS). The standalone exe is blocked by Defender.",
  },
  {
    id: "frida",
    name: "Frida",
    probe: "frida",
    cost: "free",
    blurb:
      "Frida is a dynamic instrumentation toolkit: inject a JavaScript agent into a running process and hook functions, read arguments, dump buffers. " +
      "Static analysis says what code could run; Frida shows what does — for Digibib5 the shortcut is hooking ReadFile filtered on .DKI paths and reading decoded text out of the buffers. " +
      "It spawns or attaches (pid), so every call needs confirm=True and a trusted-or-VM target. " +
      "Feeds Gym stage 2 oracle capture: what the original reads and writes.",
    wiring:
      'engine(operation="frida_trace" | "frida_script", confirm=True): spawn or attach, hook module!export',
    status: "Implemented, verified",
    doc: "FRIDA.md",
    setup:
      "uv sync --extra dynamic (Python binding). Executes the target - VM or trusted only.",
  },
];

function LiveBadge({
  def,
  live,
}: {
  def: EngineDef;
  live: Record<string, EngineInfo> | null;
}) {
  if (!def.probe) {
    return <span className="text-xs text-slate-500">not probed</span>;
  }
  if (live === null) {
    return <span className="text-xs text-slate-500">probing...</span>;
  }
  const info = live[def.probe];
  return info?.available ? (
    <span
      className="text-xs text-emerald-400"
      data-testid={`engine-live-${def.id}`}
    >
      installed{info.version ? ` (${String(info.version).slice(0, 40)})` : ""}
    </span>
  ) : (
    <span
      className="text-xs text-amber-400"
      data-testid={`engine-live-${def.id}`}
    >
      not found
    </span>
  );
}

function WrappeeTab() {
  const [live, setLive] = useState<Record<string, EngineInfo> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState(ENGINES[0].id);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/tools/status`)
      .then((r) =>
        r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)),
      )
      .then((d) => {
        if (!cancelled)
          setLive((d.engines ?? {}) as Record<string, EngineInfo>);
      })
      .catch((e: Error) => {
        if (!cancelled) {
          setError(e.message);
          setLive({});
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const def = ENGINES.find((e) => e.id === active) ?? ENGINES[0];
  const info = def.probe && live ? live[def.probe] : undefined;

  return (
    <div className="space-y-4" data-testid="help-wrappee">
      <Card>
        <P>
          The wrapped things are reverse-engineering engines. None is required
          for static triage. Live state comes from{" "}
          <Code>GET /tools/status</Code> (same data as the{" "}
          <Code>check_tools()</Code> MCP tool). The probe takes ~20 s because
          the REA check shells out to npx. Full table:{" "}
          <DocLink file="ENGINES.md" />. First-time setup:{" "}
          <DocLink file="ONBOARDING.md" />.
        </P>
        {live === null && (
          <p className="text-xs text-slate-500" data-testid="engines-probing">
            Probing engines...
          </p>
        )}
        {error && (
          <p className="text-xs text-red-400">
            Engine probe failed ({error}). Is the backend on :10750 running?
          </p>
        )}
      </Card>

      <div className="flex flex-wrap gap-2" data-testid="engine-tabs">
        {ENGINES.map((e) => (
          <button
            key={e.id}
            type="button"
            data-testid={`engine-tab-${e.id}`}
            onClick={() => setActive(e.id)}
            className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
              active === e.id
                ? "border-emerald-500 bg-emerald-500/10 text-white"
                : "border-slate-700 text-slate-400 hover:text-slate-200"
            }`}
          >
            {e.name}
          </button>
        ))}
      </div>

      <Card testid={`engine-panel-${def.id}`}>
        <div className="flex items-center justify-between gap-4">
          <H>{def.name}</H>
          <LiveBadge def={def} live={live} />
        </div>
        <P>{def.blurb}</P>
        <Table
          head={["Field", "Value"]}
          rows={[
            ["Cost", def.cost],
            ["How it is wired", def.wiring],
            ["Status in code", def.status],
            ["Setup", def.setup],
            ...(info?.path
              ? [["Detected at", <Code key="p">{info.path}</Code>]]
              : []),
            ["Guide", <DocLink key="d" file={def.doc} />],
          ]}
        />
      </Card>
    </div>
  );
}

/* --------------------------------------------------------------------- tools */

type ToolDoc = { name: string; description: string };

function ToolsTab({ query }: { query: string }) {
  const [tools, setTools] = useState<ToolDoc[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/capabilities`)
      .then((r) =>
        r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)),
      )
      .then((d) => {
        if (!cancelled) setTools((d.tool_docs ?? []) as ToolDoc[]);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const q = query.trim().toLowerCase();
  const shown = useMemo(
    () =>
      (tools ?? []).filter(
        (t) => !q || `${t.name} ${t.description}`.toLowerCase().includes(q),
      ),
    [tools, q],
  );

  if (error) {
    return (
      <Card>
        <P>Could not load the tool list from /api/capabilities ({error}).</P>
      </Card>
    );
  }
  if (tools === null) {
    return <p className="text-sm text-slate-500">Loading tools...</p>;
  }
  return (
    <div className="space-y-3" data-testid="help-tools">
      <P>
        {tools.length} tools, read live from the MCP server. Click a tool for
        its full docstring. One-line summary: <DocLink file="TOOLS.md" />.
      </P>
      {shown.length === 0 && <P>No tool matches "{query}".</P>}
      {shown.map((t) => (
        <details
          key={t.name}
          data-testid="tool-item"
          className="group rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
        >
          <summary className="cursor-pointer list-none flex items-center gap-3 text-sm">
            <Code>{t.name}</Code>
            <span className="flex-1 truncate text-slate-400">
              {t.description.split("\n").find((l) => l.trim()) ?? ""}
            </span>
            <span className="text-slate-500 group-open:rotate-90 transition-transform">
              &gt;
            </span>
          </summary>
          <pre className="mt-3 whitespace-pre-wrap font-mono text-xs text-slate-300">
            {t.description.trim() || "(no docstring)"}
          </pre>
        </details>
      ))}
    </div>
  );
}

/* ----------------------------------------------------------------------- api */

function ApiTab() {
  return (
    <div className="space-y-4" data-testid="help-api">
      <Card>
        <H>Ports (fleet registry: operations/WEBAPP_PORTS.md)</H>
        <Table
          head={["Port", "Owner", "Notes"]}
          rows={[
            [
              <Code key="1">10750</Code>,
              "backend",
              "REST + /mcp (streamable HTTP)",
            ],
            [<Code key="2">10751</Code>, "frontend", "Vite dev server"],
            [
              <Code key="3">8089</Code>,
              "ReVa / Ghidra bridge",
              "external, optional",
            ],
          ]}
        />
      </Card>
      <Card>
        <H>Environment variables</H>
        <Table
          head={["Name", "Default", "Effect"]}
          rows={[
            [
              "GHIDRA_INSTALL_DIR / GHIDRA_HOME",
              "auto-detect",
              "Ghidra install for headless analysis",
            ],
            [
              "GHIDRA_BRIDGE_URL",
              "http://127.0.0.1:8089",
              "Bridge proxied by /ghidra/*",
            ],
            [
              "IDA_DIR",
              "unset",
              "IDA install root; needed for IDA 9.x or custom paths",
            ],
            [
              "DIGITALE_BIBLIOTHEK_ROOT",
              "auto-detect",
              "Parent of DB* volumes for DKI batch decode",
            ],
            [
              "OLLAMA_BASE_URL",
              "http://localhost:11434",
              "Chat + model discovery",
            ],
            [
              "MCP_TRANSPORT / HOST / PORT / PATH",
              "stdio / 127.0.0.1 / 10750 / /mcp",
              "Standalone transport switch (reversing-mcp entry point)",
            ],
            [
              "REA_ANALYSIS_PROVIDER",
              "auto",
              "Read by REA: hopper | ghidra | ida",
            ],
            [
              "VITE_API_URL",
              "http://localhost:10750",
              "Frontend API base; Settings can override (localStorage)",
            ],
          ].map(([n, d, e]) => [<Code key={n}>{n}</Code>, d, e])}
        />
      </Card>
      <Card>
        <H>Key endpoints</H>
        <Table
          head={["Endpoint", "Purpose"]}
          rows={[
            ["GET /health", "Liveness"],
            [
              "GET /api/capabilities",
              "Ports, features, tool list with docstrings",
            ],
            ["GET /tools/status", "Engine inventory (slow: ~20 s, REA probe)"],
            ["GET /ghidra/status", "Ghidra install + bridge state"],
            [
              "GET /api/v1/ghidra/session",
              "Forwarding session state (stopped/starting/ready/error)",
            ],
            [
              "POST /api/v1/ghidra/session/start",
              "Start headless ReVa or attach to a Ghidra GUI",
            ],
            [
              "GET /api/v1/ghidra/tools",
              "Search ReVa's tool catalogue (paged)",
            ],
            ["POST /api/v1/ghidra/call", "Invoke one ReVa tool with arguments"],
            [
              "POST /analyze/upload",
              "Analyze an uploaded binary (temp file, deleted after)",
            ],
            ["GET /api/v1/diagnostics", "Diagnostics bundle"],
            ["GET /api/logs", "Backend ring-buffer log"],
            ["/mcp", "MCP streamable HTTP for clients"],
          ].map(([e, p]) => [<Code key={e}>{e}</Code>, p])}
        />
      </Card>
      <Card>
        <H>Start / restart</H>
        <P>
          Not an NSSM service. <Code>start.bat</Code> (or{" "}
          <Code>mcp-central-docs\starts\reversing-start.bat</Code>) runs{" "}
          <Code>start.ps1</Code>, which clears :10750/:10751, starts the
          backend, waits for <Code>/health</Code>, then starts Vite. Backend
          only: <Code>.\start.ps1 -BackendOnly</Code>. Python changes need a
          backend restart (no auto-reload); frontend changes hot-reload. After a
          restart, check that a new PID owns the port:{" "}
          <Code>Get-NetTCPConnection -LocalPort 10750</Code>.
        </P>
      </Card>
    </div>
  );
}

/* -------------------------------------------------------------- troubleshoot */

const FIXES: Array<{
  symptom: string;
  cause: string;
  fix: string;
  seen: string;
}> = [
  {
    symptom: 'Dashboard spins forever, top bar stuck on "Checking..."',
    cause:
      "Fixed 2026-10-12: /ghidra/status ran every engine probe on the event loop; the REA probe (~8 s) froze all requests including /health.",
    fix: "Update to commit ba0e327 or later and restart the backend (start.bat).",
    seen: "2026-10-12",
  },
  {
    symptom: 'Overview Ghidra card says "Bridge: Stopped"',
    cause:
      "Nothing listening on :8089 - the ReVa bridge is not running. Headless Ghidra still works.",
    fix: "Start Ghidra with ReVa (docs/REVA.md), or point GHIDRA_BRIDGE_URL at the running bridge.",
    seen: "2026-10-12",
  },
  {
    symptom: 'Gym triage: capa "timed out", Logic dimension unknown',
    cause:
      "capa needs minutes on real apps (Digibib5: 2511 s); the triage budget is 300 s by default.",
    fix: 'Set GYM_CAPA_TIMEOUT_S higher before starting the backend, or run engine(operation="capa", timeout_s=1800) separately.',
    seen: "2026-10-12",
  },
  {
    symptom:
      "Defender quarantines the capa Windows release (Trojan:Win32/Suschil!rfn)",
    cause:
      "Heuristic hit on the standalone PyInstaller build, which bundles malware-detection rules. Not overridden.",
    fix: "uv tool install flare-capa, plus capa-rules and sigs in D:\\Dev\\tools (docs/CAPA.md).",
    seen: "2026-10-12",
  },
  {
    symptom: "Tools / Status pages take ~20 s to fill in",
    cause:
      "The engine inventory runs the REA probe (npx) on every request; not cached yet.",
    fix: "Wait for it; caching is on the roadmap. It no longer blocks other pages.",
    seen: "2026-10-12",
  },
  {
    symptom: '"Hopper integration is not supported on win32"',
    cause: "Hopper has no Windows build; REA refuses the provider.",
    fix: 'Use provider="ghidra" or omit provider in rea_investigate.',
    seen: "2026-10-11",
  },
  {
    symptom: 'start.ps1: "Backend did not answer /health in 60s"',
    cause:
      "uvicorn missing from the venv, or :10750 held by a process the launcher could not stop.",
    fix: "uv sync --all-extras; then Get-NetTCPConnection -LocalPort 10750 and stop the owner.",
    seen: "2026-10-11",
  },
  {
    symptom: 'Chat returns 409 "No Ollama model available"',
    cause: "Honest signal: Ollama is not running or has no model.",
    fix: "Start Ollama, ollama pull <model>, retry; pick the model in Settings.",
    seen: "2026-10-11",
  },
];

function TroubleshootTab({ query }: { query: string }) {
  const q = query.trim().toLowerCase();
  const shown = FIXES.filter(
    (f) => !q || `${f.symptom} ${f.cause} ${f.fix}`.toLowerCase().includes(q),
  );
  return (
    <div className="space-y-3" data-testid="help-fixes">
      {shown.length === 0 && <P>No entry matches "{query}".</P>}
      {shown.map((f) => (
        <Card key={f.symptom}>
          <div className="flex items-start justify-between gap-4">
            <H>{f.symptom}</H>
            <span className="shrink-0 text-xs text-slate-500">
              first seen {f.seen}
            </span>
          </div>
          <P>
            <span className="text-slate-500">Cause: </span>
            {f.cause}
          </P>
          <P>
            <span className="text-slate-500">Fix: </span>
            {f.fix}
          </P>
        </Card>
      ))}
      <P>
        More: <DocLink file="TROUBLESHOOTING.md" />
      </P>
    </div>
  );
}

/* ----------------------------------------------------------------------- faq */

const FAQS: Array<{ q: string; a: string }> = [
  {
    q: "Where is my data?",
    a: "Nothing is stored centrally. Analyses run on files you point at; web uploads go to a temp file that is deleted after the analysis. DKI decode writes *_extracted.txt next to the source when you use analyze_directmedia_file.",
  },
  {
    q: "How do I pick a target?",
    a: "Web: Analyze page, upload the binary. MCP: analyze_binary(file_path=...). Digibib volumes: set DIGITALE_BIBLIOTHEK_ROOT or pass library_path.",
  },
  {
    q: "I installed an engine but it still shows not found.",
    a: "Engines are probed per request, but the backend inherits PATH at start. Restart the backend after installing, then check Help > Engines.",
  },
  {
    q: "How do MCP clients connect?",
    a: "Streamable HTTP at http://127.0.0.1:10750/mcp while the backend runs, or stdio via the reversing-mcp entry point (uv run reversing-mcp).",
  },
  {
    q: "Which process do I restart after a code change?",
    a: "Python: the backend (start.ps1 -BackendOnly or start.bat). Frontend: nothing, Vite hot-reloads. No NSSM service is involved.",
  },
  {
    q: "Where are the logs?",
    a: "Logs page (backend ring buffer, empty after restart). The start.ps1 window shows uvicorn output. Claude Desktop stdio logs: %APPDATA%\\Claude\\logs\\mcp-server-revops.log.",
  },
  {
    q: "What is the Ghidra page, and how is it different from the Status page?",
    a: "The Ghidra page (Workbench + Tool catalogue + Call history) drives Ghidra interactively through ReVa: start a session (headless mcp-reva, or attach to a running Ghidra GUI), browse the ~86 ReVa tools, and call them (decompile, xrefs, rename, retype). The Status page only reports whether Ghidra and the legacy :8089 bridge are installed and reachable. Note the webapp backend runs its own session, separate from one a chat client (Claude Desktop) started over stdio; GUI mode lets both attach to the same Ghidra.",
  },
  {
    q: "Headless start says mcp-reva not found.",
    a: "Headless needs the fleet ReVa venv (mcp-reva) and GHIDRA_INSTALL_DIR set. See D:/Dev/tools/reva/README.md. If you cannot install it, use GUI mode: open Ghidra, enable the ReVa plugin server (Edit > Tool Options > ReVa), then Attach to GUI.",
  },
  {
    q: "Can I use IDA Free?",
    a: "Not for automation: IDA Free has no IDAPython or headless mode, so the headless scripts cannot run. Use Ghidra, or IDA Home/Pro.",
  },
];

function FaqTab({ query }: { query: string }) {
  const q = query.trim().toLowerCase();
  const items = FAQS.filter(
    (f) => !q || `${f.q} ${f.a}`.toLowerCase().includes(q),
  );
  return (
    <div className="space-y-3" data-testid="help-faq">
      {items.length === 0 && <P>No FAQ matches "{query}".</P>}
      {items.map((f) => (
        <details
          key={f.q}
          data-testid="faq-item"
          className="group rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3"
        >
          <summary className="cursor-pointer list-none flex items-center gap-3 text-sm font-medium text-white">
            <FileQuestion className="h-4 w-4 text-emerald-400 shrink-0" />
            <span className="flex-1">{f.q}</span>
            <span className="text-slate-500 group-open:rotate-90 transition-transform">
              &gt;
            </span>
          </summary>
          <p className="mt-2 pl-7 text-sm text-slate-300 leading-relaxed">
            {f.a}
          </p>
        </details>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------------- page */

export function Help() {
  const [activeTab, setActiveTab] = useState<HelpTab>("overview");
  const [query, setQuery] = useState("");
  const showSearch =
    activeTab === "troubleshoot" ||
    activeTab === "faq" ||
    activeTab === "tools";

  return (
    <div className="space-y-6" data-testid="help-page">
      <header className="space-y-3">
        <h2 className="text-2xl font-bold tracking-tight text-white">Help</h2>
        <p className="text-slate-300">
          Engines, MCP tools, ports, error fixes and FAQ for reversing-mcp.
        </p>
        {showSearch && (
          <input
            data-testid="help-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              activeTab === "faq"
                ? "Filter questions..."
                : activeTab === "tools"
                  ? "Filter tools..."
                  : "Filter by symptom or error..."
            }
            className="w-full max-w-md rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none focus:border-emerald-500"
          />
        )}
      </header>

      <div className="border-b border-slate-800" data-testid="help-tabs">
        <nav className="flex flex-wrap gap-x-5 gap-y-1">
          {TABS.map((tab) => {
            const Icon = TAB_ICONS[tab.id];
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                data-testid={`help-tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 text-sm font-medium transition-colors flex items-center gap-2 -mb-px ${
                  active
                    ? "border-emerald-500 text-white"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="text-left whitespace-nowrap">
                  {tab.name}{" "}
                  <span className="font-normal opacity-70 hidden xl:inline">
                    {tab.description}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      <div>
        {activeTab === "overview" && <OverviewTab />}
        {activeTab === "wrappee" && <WrappeeTab />}
        {activeTab === "tools" && <ToolsTab query={query} />}
        {activeTab === "api" && <ApiTab />}
        {activeTab === "troubleshoot" && <TroubleshootTab query={query} />}
        {activeTab === "faq" && <FaqTab query={query} />}
      </div>
    </div>
  );
}
