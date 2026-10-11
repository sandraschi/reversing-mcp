# Fixtures depot — manifest (spec, 2026-10-11)

Ground-truth table for every reverse target in `tests/fixtures/`. Rule Zero: every
binary is either **self-built from committed source** or **skip-if-absent local**.
No redistributed commercial binaries, ever (Sysinternals, Borland, IDA-adjacent:
all forbidden by license). `dangerous/` stays source-only — never commit binaries there.

Toolchains on Goliath today: Rust YES, dotnet YES, Go/FPC/MinGW/nasm NO.
Missing ones install via winget/manual (noted per fixture) or get byte-built (option B).

## Tier 1 — unit (committed, hermetic, byte-sized)

| Fixture | Build | Ground truth asserted |
|---------|-------|----------------------|
| `dos/hello.com` (replaces 0-byte `binaries/hello.com`) | **B: byte-built** by script (`mov ah,9 / int 21h` + `Hello$`): every byte known, ~20 B | exact byte match, strings finds `Hello`, entropy < 5 |
| `dos/loop.com` (replaces 0-byte `loop.com`) | **B**: tight `jmp $` loop + padding variant | entropy map flat, no strings ≥ 4, size exact |
| `dos/tp-style.exe` (new) | **A**: Free Pascal → DOS GO32v2 `writeln('TP-HELLO-MARKER')` (install FPC once) **or B**: MZ stub + marker string, documented as synthetic | `TP-HELLO-MARKER` in strings, MZ header parse, Borland-overlay note: real TP overlay parsing stays integration-only |
| `pe/mini.exe` (replaces/audits 0.7 KB `test_pe.exe`) | **A**: MSVC `cl.exe` if present (TO-VERIFY) else MinGW (winget) — hello + `PE-MARKER-STRING` + version resource | PE sections/imports parse, marker string, version info present |
| `pe/stripped.exe` (new) | same source, `/STRIP` or `-s` | graceful degradation: tools report, nothing crashes, no marker |
| `dotnet/hello.dll` (new) | `dotnet new console` + `DOTNET-MARKER`, self-contained or framework-dependent (note which) | metadata tables, marker string (REA `managed-code` path, integration-gated) |
| `rust/hello.exe` (new) | `cargo build` hello + `RUST-MARKER-STRING` | long monomorphized symbols in strings; `*_MARKER` found |
| `rust/hello-stripped.exe` (new) | `cargo build --release` + `strip` | degradation twin of the above |
| `js/sample-app/` (new) | hand-written 3-file node script with known `require` graph + `JS-MARKER` | REA `javascript` kind module graph (integration-gated, needs REA) |
| `dki/mini.dki` (new, if absent) | byte-built: valid header + 1 zlib stream + `DKI-MARKER` text | `decode_dki_file` success path with known strategy |

Existing C sources (`hello_world.c`, `classic_game.c`, …) stay as *build inputs* once a C
toolchain lands; until then they are documentation, not fixtures. `packed_test.bin` stays
(1 KB, documents the entropy > 7.5 path).

## Tier 2 — integration (committed-if-small else skip-if-absent, never unit)

| Fixture | Source | Asserts |
|---------|--------|---------|
| `exe files/Digibib5.exe` (4.5 MB, already vendored) | mission target | snapshot runs, keyword hits > 0. No new multi-MB binaries without LFS |
| `go/hello.exe` (~2 MB, TO-BUILD after `winget install GoLang.Go`) | `package main` + `GO-MARKER-FUNC` named function | **pclntab function names**: `find_functions` must return our named func; strings contain `GO-MARKER` |
| real DKI volumes | env `DIGITALE_BIBLIOTHEK_ROOT` | existing volume tests, unchanged |

## Tier 3 — dangerous (source-only, forever)

`dangerous/*.c` as today. No binaries, no exceptions: a packed/obfuscated binary in git
is indistinguishable from malware to every scanner on earth.

## Build & verify protocol

1. Each Tier-1 binary gets a builder script next to it (`build_*.py`/documented one-liner).
2. Each asserts its row in a `test_fixtures_ground_truth.py` (exists? create): marker strings,
   exact sizes where byte-built, degradation twins must not crash.
3. Toolchain installs are one-liners in the manifest row, run once, never in CI.
4. REA-gated rows (`js/`, `dotnet/` deep paths) skip when REA is absent (`check_rea`).

## Open

- MSVC `cl.exe` presence (else MinGW via winget for `pe/`).
- FPC install vs synthetic-only `tp-style.exe` (B unblocks now, A upgrades later).
- Go install (`winget install GoLang.Go`, ~2 min) unlocks the best `find_functions` fixture we have.
