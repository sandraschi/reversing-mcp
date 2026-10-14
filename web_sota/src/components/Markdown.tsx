import { useMemo } from "react";

interface Props {
  text: string;
  onLocalDoc?: (file: string) => void;
}

/** Render inline code spans, bold, italic and links inside a line of text. */
function Inline({
  text,
  onLocalDoc,
}: {
  text: string;
  onLocalDoc?: (file: string) => void;
}) {
  const parts: React.ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  const pushText = (s: string) => {
    if (s) parts.push(<span key={k++}>{s}</span>);
  };
  while ((m = re.exec(text)) !== null) {
    pushText(text.slice(last, m.index));
    last = m.index + m[0].length;
    const tok = m[0];
    if (tok.startsWith("`")) {
      parts.push(
        <code
          key={k++}
          className="px-1 rounded bg-slate-800 text-emerald-300 font-mono text-[0.9em]"
        >
          {tok.slice(1, -1)}
        </code>,
      );
    } else if (tok.startsWith("**")) {
      parts.push(<strong key={k++}>{tok.slice(2, -2)}</strong>);
    } else if (tok.startsWith("[")) {
      const label = tok.slice(1, tok.indexOf("]"));
      const href = tok.slice(tok.indexOf("(") + 1, -1);
      if (/^[A-Za-z0-9_-]+\.md(#.*)?$/.test(href) && onLocalDoc) {
        parts.push(
          <button
            key={k++}
            type="button"
            onClick={() => onLocalDoc(href.split("#")[0])}
            className="text-emerald-400 hover:underline"
          >
            {label}
          </button>,
        );
      } else {
        parts.push(
          <a
            key={k++}
            href={href}
            target="_blank"
            rel="noreferrer"
            className="text-emerald-400 hover:underline"
          >
            {label}
          </a>,
        );
      }
    } else {
      parts.push(<em key={k++}>{tok.slice(1, -1)}</em>);
    }
  }
  pushText(text.slice(last));
  return <>{parts}</>;
}

/**
 * Minimal markdown subset renderer for repo docs (headings, paragraphs, bold,
 * code spans/blocks, lists, tables, links). Local `*.md` links open in-app
 * via onLocalDoc; external links open a new tab. No dependency, no raw HTML.
 */
export function Markdown({ text, onLocalDoc }: Props) {
  const blocks = useMemo(() => {
    const lines = text.split("\n");
    const out: React.ReactNode[] = [];
    let i = 0;
    let k = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (line.startsWith("```")) {
        const buf: string[] = [];
        i++;
        while (i < lines.length && !lines[i].startsWith("```")) {
          buf.push(lines[i]);
          i++;
        }
        i++;
        out.push(
          <pre
            key={k++}
            className="my-2 p-3 rounded bg-slate-900 overflow-x-auto text-sm font-mono text-slate-200"
          >
            {buf.join("\n")}
          </pre>,
        );
        continue;
      }
      const h = line.match(/^(#{1,4})\s+(.*)/);
      if (h) {
        const depth = h[1].length;
        const cls =
          depth === 1
            ? "text-lg font-bold text-white mt-4 mb-2"
            : "text-base font-semibold text-white mt-3 mb-1";
        out.push(
          <div key={k++} className={cls}>
            <Inline text={h[2]} onLocalDoc={onLocalDoc} />
          </div>,
        );
        i++;
        continue;
      }
      if (
        /^\s*\|.*\|\s*$/.test(line) &&
        i + 1 < lines.length &&
        /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])
      ) {
        const rows = [line];
        i += 2;
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
          rows.push(lines[i]);
          i++;
        }
        const cells = (r: string) =>
          r
            .trim()
            .replace(/^\||\|$/g, "")
            .split("|")
            .map((c) => c.trim());
        const head = cells(rows[0]);
        out.push(
          <table key={k++} className="my-2 w-full text-sm border-collapse">
            <thead>
              <tr>
                {head.map((c, ci) => (
                  <th
                    key={ci}
                    className="border border-slate-700 px-2 py-1 text-left text-slate-200 bg-slate-800/50"
                  >
                    <Inline text={c} onLocalDoc={onLocalDoc} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(1).map((r, ri) => (
                <tr key={ri}>
                  {cells(r).map((c, ci) => (
                    <td
                      key={ci}
                      className="border border-slate-800 px-2 py-1 text-slate-300 align-top"
                    >
                      <Inline text={c} onLocalDoc={onLocalDoc} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>,
        );
        continue;
      }
      const li = line.match(/^\s*([-*]|\d+\.)\s+(.*)/);
      if (li) {
        out.push(
          <div key={k++} className="text-sm text-slate-300 ml-4 my-0.5">
            <span className="text-slate-500 mr-2">•</span>
            <Inline text={li[2]} onLocalDoc={onLocalDoc} />
          </div>,
        );
        i++;
        continue;
      }
      if (line.trim() === "" || line.trim() === "---") {
        i++;
        continue;
      }
      out.push(
        <p key={k++} className="text-sm text-slate-300 my-1.5 leading-relaxed">
          <Inline text={line} onLocalDoc={onLocalDoc} />
        </p>,
      );
      i++;
    }
    return out;
  }, [text, onLocalDoc]);
  return <div>{blocks}</div>;
}
