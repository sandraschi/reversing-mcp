# capa

[capa](https://github.com/mandiant/capa) (Mandiant) matches ~1,000 rules against a binary's
code and reports *what it can do*: "read file on Windows", "decompress data using zlib",
"check for unmoving mouse cursor" - each with ATT&CK / MBC ids and match counts. For cloning,
that is a map of which behaviours exist and roughly where.

**Status:** implemented and verified on the dev host (capa 9.4.0, rules v9.4.0, 2026-10-12).

## Use

| Where | Call |
|-------|------|
| MCP | `engine(operation="capa", file_path="D:/apps/prog.exe", timeout_s=1800)` |
| Gym | stage 1 (triage); timeout `GYM_CAPA_TIMEOUT_S` (default 300 s) |

Returns one row per matched rule: `name`, `namespace`, `matches`, `attack`, `mbc`, plus
`count` and `top_namespaces`. capa's raw JSON (9 MB for Digibib5) is never returned whole.
Code: `src/reversing_mcp/engines.py` (`run_capa`, `summarize_capa`).

## It is slow

capa on Digibib5.exe (4.7 MB, Delphi) took **2511 s (~42 min)** on 2026-10-12 and matched 96
rules. The Gym's default 300 s triage budget therefore times out on targets this size and says
so ("capa timed out"); raise `GYM_CAPA_TIMEOUT_S` or call `engine(operation="capa")` with a long
`timeout_s` (max 1800 s) when you want the full pass.

Notable Digibib5 result: anti-VM checks (VirtualBox strings, unmoving-mouse detection). The Gym
flags this on the Oracle dimension because the clicker runs in a VM.

## Install (Windows)

The standalone Windows release (`capa-<ver>-windows.zip`) was **blocked by Microsoft Defender**
on the dev host (`Trojan:Win32/Suschil!rfn`, heuristic - capa bundles malware-detection rules
in a PyInstaller exe; very likely a false positive, but not overridden). Supported path instead:

```powershell
uv tool install flare-capa
# the pip build ships neither rules nor signatures:
gh api repos/mandiant/capa-rules/zipball/v<ver>  # extract to D:\Dev\tools\capa-rules
# sigs/ folder of mandiant/capa at the same tag  -> D:\Dev\tools\capa-sigs
```

Lookup: `CAPA_EXE` or `capa` on `PATH`; rules `CAPA_RULES` -> `D:\Dev\tools\capa-rules`;
signatures `CAPA_SIGS` -> `D:\Dev\tools\capa-sigs`. Keep the rules tag equal to the capa version.

## References

* Engine overview: [ENGINES.md](ENGINES.md)
