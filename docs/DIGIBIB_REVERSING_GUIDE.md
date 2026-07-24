# DigiBib Reversing Guide

**Example project:** Digibib5.exe and the Directmedia `.DKI` format.  
**Goal:** Document the read/decode pipeline enough to build an independent viewer.

This is the **primary worked example** for the reversing-mcp toolchain — a real, modest-sized Windows binary with a proprietary packed format.

---

## Contents

1. [What DigiBib is](#1-what-digibib-is)
2. [Why this is hard](#2-why-this-is-hard)
3. [Approach A: Static analysis (Ghidra + ReVa)](#3-approach-a-static-analysis-ghidra--reva)
4. [Approach B: Dynamic tracing (recommended next step)](#4-approach-b-dynamic-tracing-recommended-next-step)
5. [Approach C: Offset-table extraction](#5-approach-c-offset-table-extraction)
6. [Approach D: Runtime identification](#6-approach-d-runtime-identification)
7. [Tools matrix](#7-tools-matrix)
8. [Related docs](#8-related-docs)

---

## 1. What DigiBib is

**Digitale Bibliothek** was a 1990s German e-book product line by **Directmedia Publishing GmbH** (Berlin). Each CD-ROM contained dozens to hundreds of books in a proprietary format. The reader application, Digibib5.exe, opened volumes from CD or disk and displayed formatted text.

| Component | Description |
|-----------|-------------|
| **Digibib5.exe** | Reader application (PE, ~2 MB) |
| **`*.DKI` / `*.DKA`** | Container files — `TEXT.DKI` (body text), `TREE.DKI` (TOC), index files |
| **Offset table** | Header + `uint32[]` LE monotonic offsets → packed records |
| **Codec** | Unknown — **not** whole-file zlib. Appears to be a custom bitstream (Huffman/LZ variant) |

The format was never publicly documented. No open-source decoder exists. **DiBiLit** and similar projects are unrelated (TEI text archives, not this binary format).

---

## 2. Why this is hard

| Problem | Why |
|---------|-----|
| **No symbols** | Stripped PE, no public PDB |
| **Likely Delphi** | 90s German Windows app — Delphi (Borland) was the standard IDE. Ghidra's Delphi support is limited. |
| **Custom codec** | Not standard zlib/gzip. Heuristic whole-file scans fail. |
| **Co-installed DLLs** | Real reader logic may be in a DLL, not the EXE. |
| **DRM layer** | CD-check / registration wrapper may obfuscate entry. |

The in-repo heuristic decoder (`directmedia_dki.py`) tries zlib/gzip with header skips — it works on some `tree.dki` (plain CP1252) but **fails on large `text.dki`** which uses a header + offset table + proprietary packed stream.

---

## 3. Approach A: Static analysis (Ghidra + ReVa)

The original plan. Steps:

1. Load Digibib5.exe in Ghidra, run auto-analysis
2. Connect ReVa MCP for decompile / xrefs
3. Find `CreateFileW` → `ReadFile` → trace up the call graph
4. Identify the `text.dki` read pipeline
5. Reverse the codec from decompiled output

**Why it stalls:** Delphi output in Ghidra is noisy. Function signatures are often unrecognisable (`FUN_00xxxxxx`). Without RTTI recovery, you spend most of your time mapping the control flow before you ever find the read path.

---

## 4. Approach B: Dynamic tracing (recommended next step)

Skip the static slog. Watch what the binary **actually does** at runtime.

### 4.1 Process Monitor (procmon) — zero effort, high signal

Filter: `Process Name is Digibib5.exe` then `Operation is ReadFile`.

This tells you **exactly**:
- Which files it opens (config? registry? DLLs? or just the DKI?)
- At what offsets it reads
- How many bytes per read
- The I/O pattern (sequential? random-access via offset table?)

If you see it reading the offset table then seeking to scattered positions, you've confirmed the archive structure without a single Ghidra session.

### 4.2 API Monitor — next level

Hook `ReadFile`, `CreateFileMappingW`, `VirtualAlloc`, `RtlDecompressBuffer`, `CryptDecrypt`.

After each `ReadFile` completes, dump the buffer and run Shannon entropy on it. If a buffer goes from high entropy (>7.5) to low entropy (<5.5), you've found the decompression point. Note the call stack.

### 4.3 Frida — surgical

A ~20-line Frida script can:
```javascript
Interceptor.attach(Module.findExportByName("kernel32.dll", "ReadFile"), {
    onLeave: function(retval) {
        var buf = this.context.rcx;  // or appropriate reg
        send("ReadFile completed, first 32 hex: " + hexdump(buf));
    }
});
```

Run Digibib5.exe under Frida, open a volume, trigger any text display. The read buffers tell the story.

### 4.4 WinDbg / x64dbg

Breakpoint `CreateFileW` with a filename filter for `.dki`. Once hit, trace to the read/decompress chain. Less automated than Frida but gives full control flow context.

---

## 5. Approach C: Offset-table extraction

Even without knowing the codec, you can **parse the container structure** from the offset table.

`text.dki` structure (from empirical observation):
```
[0x00]  uint32  header_magic    (shared with index files)
[0x04]  uint32  subtype         (0x02 for indices, 0x04 for text)
[0x08]  ...     possibly more header fields
[off_table_start]  uint32[] LE  monotonic file offsets
[...]   packed_payload          binary stream from offset_table[N-1] to EOF
```

The offset table defines record boundaries. Extract and test individually:

```python
import struct, binwalk

data = open("TEXT.DKI", "rb").read()
# Crude: find offset table by scanning for ascending uint32 sequence
# or skip known header size empirically
header_size = 0x10  # guess
table_data = data[header_size:header_size + 4*10000]
offsets = struct.unpack(f"<{len(table_data)//4}I", table_data[:len(table_data)//4*4])

# Filter non-monotonic (table ends at first non-ascending value)
valid = []
for i, o in enumerate(offsets):
    if o < len(data) and (not valid or o > valid[-1]):
        valid.append(o)
    else:
        break

print(f"Found {len(valid)} valid offsets")
for i in range(min(5, len(valid)-1)):
    rec = data[valid[i]:valid[i+1]]
    print(f"  Record {i}: offset 0x{valid[i]:x}, {len(rec)} bytes, entropy={shannon(rec):.2f}")
```

Then feed each extracted record to `binwalk`, or try per-record zlib/gzip/xzip decompression. If the codec is per-record rather than whole-stream, individual records may use standard compression even if the container wrapper is custom.

---

## 6. Approach D: Runtime identification

### Check if it's Delphi

Before deep analysis, confirm the runtime:

| Import signature | Runtime | Best tool |
|-----------------|---------|-----------|
| `vcl*.bpl`, `borlndmm.dll`, `cc32*.dll` | **Delphi** | IDR (free), IDA Pro |
| `msvcrt.dll`, `kernel32.dll` | MSVC/C++ | Ghidra/ReVa is fine |
| `? MFC` | MFC/C++ | Ghidra/ReVa |

**If it's Delphi:**
- **IDR (Interactive Delphi Reconstructor)** is **free** and recovers forms, RTTI, event handlers — vastly better than Ghidra for Delphi. Run the EXE through IDR first, export map, load into Ghidra. See the **[detailed IDR guide](IDR.md)** for full workflow, Ghidra integration, and Delphi internals.
- **IDA Pro** handles Delphi well but is **expensive** ($2k+) — we do not have it. The fleet path is Ghidra + IDR.

### Check for DRM

Look for `CD-ROM` strings, `RegQueryValue`, `Crypt*` imports. If DRM-wrapped, the real reader code may only initialise after a successful check. A NOP-patch of the check at the entry point may be needed before dynamic tracing works.

---

## 7. Tools matrix

| Tool | Cost | Best for |
|------|------|----------|
| **Ghidra** | Free | Static analysis, decompiler, headless batch |
| **ReVa** | Free | Ghidra MCP bridge (interactive) |
| **IDR** | Free | Delphi reconstruction (forms, RTTI) — [detailed guide](IDR.md) |
| **Process Monitor** | Free (Sysinternals) | File I/O trace |
| **API Monitor** | Free | API call + buffer capture |
| **Frida** | Free | Surgical hooking, automation |
| **x64dbg** | Free | Assembly-level debugging |
| **IDA Pro** | ~$2k+ | Best-in-class Delphi support, but **not in fleet** — too expensive for hobby use |

---

## 8. Related docs

| Document | What it covers |
|----------|----------------|
| [DIGIBIB_DECOMPILE_PLAN.md](DIGIBIB_DECOMPILE_PLAN.md) | Original phased reverse plan (Phases A–E) |
| [DIRECTMEDIA_MISSION.md](DIRECTMEDIA_MISSION.md) | Mission scope and toolchain role |
| [DIRECTMEDIA_REVERSING_TOOLKIT.md](DIRECTMEDIA_REVERSING_TOOLKIT.md) | CLI/MCP commands for DigiBib |
| [status.md](status.md) | Current reversing progress (Ghidra function names, addresses) |
| [GHIDRA.md](GHIDRA.md) | Ghidra/ReVa setup guide |
| [IDR.md](IDR.md) | Delphi reconstruction with IDR — full workflow, Ghidra integration, internals |
