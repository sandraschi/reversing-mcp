import { Link } from "react-router-dom";

/**
 * Hardware index — the frankendingus landing.
 * Two live exemplars (M1 synth, GRiDCase 1520), the 8-stage pipeline, and the
 * metarevival tier where Robbie operates unmodified objects (banker lamp).
 * Profiles live in rust-mame-mcp; procedure lives in docs/*.md.
 */
const STAGES = [
  "Trawl attic",
  "Find + score",
  "Analyze",
  "Repair",
  "Improve",
  "Clone (oracle)",
  "Raspi implant",
  "LLM face",
];

function ExemplarCard(props: {
  to: string;
  title: string;
  sub: string;
  profile: string;
  tier: string;
  body: string;
}) {
  return (
    <Link
      to={props.to}
      className="block rounded border border-slate-800 bg-slate-900/60 p-4 transition-colors hover:border-slate-600"
    >
      <div className="text-lg font-semibold text-slate-100">{props.title}</div>
      <div className="text-xs text-slate-400">{props.sub}</div>
      <div className="mt-2 flex gap-2 text-xs">
        <span className="rounded border border-slate-700 px-2 py-1 font-mono text-slate-300">
          {props.profile}
        </span>
        <span className="rounded border border-slate-700 px-2 py-1 text-slate-300">
          {props.tier}
        </span>
      </div>
      <div className="mt-2 text-sm text-slate-400">{props.body}</div>
    </Link>
  );
}

export function HardwareIndex() {
  return (
    <div className="space-y-4 p-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">
          Hardware — frankendingus exemplars
        </h1>
        <p className="text-sm text-slate-400">
          Dead machines come back in stages: trawl, score, analyze, repair,
          improve, clone into an oracle, implant a Pi, give it an LLM face.
          Nothing advances without the previous stage's receipt. Doctrine:
          docs/FRANKENDINGUS.md.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <ExemplarCard
          to="/hardware-m1"
          title="Korg M1 — megasynth"
          sub="1988 music workstation · 61 keys · AI synthesis"
          profile="mame_korgm1_panel"
          tier="Tier 2 → 3 (carrier rev A)"
          body="Battery-dead, MIDI alive. three.js panel wired to the Y-matrix; carrier PCB rev A DRC-clean. Twenty-machine shortlist in docs/MEGASYNTH_SHORTLIST.md."
        />
        <ExemplarCard
          to="/hardware-grid"
          title="GRiDCase 1520 — chatbot in a clamshell"
          sub="1985 rugged portable · 286 · amber plasma"
          profile="mame_gridcase1520_profile"
          tier="Tier 0 (attic → plate photo)"
          body="MS-DOS native, Micro Switch keys, plasma glass. Branch A first: Kermit + Pi over serial, the glass becomes the bot's face. Docs/GRID_REVIVE.md."
        />
      </div>

      <div className="rounded border border-slate-800 p-4">
        <div className="text-sm font-semibold text-slate-200">The pipeline</div>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {STAGES.map((s, i) => (
            <span
              key={s}
              className="rounded border border-slate-700 px-2 py-1 text-slate-300"
            >
              {i + 1}. {s}
            </span>
          ))}
        </div>
      </div>

      <div className="rounded border border-slate-800 p-4">
        <div className="text-sm font-semibold text-slate-200">
          Metarevival — Robbie operates the unmodified object
        </div>
        <p className="mt-1 text-sm text-slate-400">
          Purely mechanical dinguses need no implant: the robot is the hands,
          the camera is the verification. Hello-world: the brass banker lamp —
          navigate by SLAM waypoint, PTZ-aim, gripper pulls the chain, camera
          brightness-delta confirms, Robbie says it. Ops exist today in
          yahboom-mcp: gripper_open/close, camera set_pos, say, missions. Start
          with a big toggle switch; graduate to the pull-chain.
        </p>
      </div>

      <div className="text-xs text-slate-500">
        Candidates pool: docs/DINGUS_POOL.md · intake forms:
        docs/ATTIC_INTAKE.md · bench rule: scope trace + LA capture before any
        chip is declared dead.
      </div>
    </div>
  );
}
