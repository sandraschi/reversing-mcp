# IDR — Interactive Delphi Reconstructor

**What it is:** IDR is a free, open-source tool that decompiles Delphi executables and recovers high-level structure — form layouts, class hierarchies, RTTI symbols, and event handlers — that generic disassemblers like Ghidra cannot extract from Borland-generated metadata.

**Why it matters:** Digibib5.exe (and most 1990s German Windows applications) was likely built with Delphi. Without IDR, Ghidra sees Borland's VMT (Virtual Method Table), RTTI (Run-Time Type Information), and DFM (Delphi Form Metadata) as opaque data blobs. Every function shows up as `FUN_00xxxxxx`. IDR restores the original symbol names, giving you `TTextReader.ReadLn` instead of `FUN_00613458`.

---

## Contents

1. [What IDR recovers](#1-what-idr-recovers)
2. [Installation](#2-installation)
3. [Basic workflow](#3-basic-workflow)
4. [Loading IDR output into Ghidra](#4-loading-idr-output-into-ghidra)
5. [Interpreting IDR output](#5-interpreting-idr-output)
6. [Key Delphi concepts for reversers](#6-key-delphi-concepts-for-reversers)
7. [When IDR isn't enough](#7-when-idr-isnt-enough)
8. [References](#8-references)

---

## 1. What IDR recovers

After processing a Delphi PE, IDR produces:

| Artifact | Description |
|----------|-------------|
| **Form definitions** | DFM data decompiled to readable text — window layouts, control names (`Button1`, `Memo1`), property values, event handler bindings |
| **Class hierarchy** | All classes with their ancestor chain (e.g. `TTextReader → TCustomReader → TObject`), field offsets, method table |
| **Method names** | Every method recovered from RTTI — including published, public, and protected methods with full original names |
| **Event handlers** | Which method is called when a button is clicked, a timer fires, etc. — the single most useful piece of info for understanding control flow |
| **Type info** | Enum values, set types, published properties with their types |
| **Package references** | Which BPL/DLL packages the EXE depends on (can hint at which runtime libraries are in use) |
| **Map / symbol file** | A `.map` or `.idr` file you can import into Ghidra to apply recovered names |

---

## 2. Installation

### Auto-install (recommended)

```powershell
just install-idr
```

Downloads `Idr.exe` (3.4 MB) from the GitHub release to `%LOCALAPPDATA%\IDR\` and adds it to your user `PATH`.

If you don't have `just`:
```powershell
.\scripts\Install-IDR.ps1
```

### Manual

1. Download `Idr.exe` from [the releases page](https://github.com/crypto2011/IDR/releases/tag/27_01_2019)
2. Place it anywhere on your `PATH`
3. Run `Idr.exe`

**Note:** The last release was January 2019. It still works for Delphi 2–7 (Win9x to XP era) which is the likely range for Digibib5.exe. Delphi 2005+ may have partial support.

### Post-install check

```powershell
# Verify it's on PATH
Idr.exe --help
# Or just launch
Idr.exe
```

---

## 3. Basic workflow

### Step 1 — Open the EXE in IDR

Launch IDR.exe, `File → Open` → select `Digibib5.exe`.

IDR will:
- Parse the PE to find Borland's RTTI and VMT tables
- Walk the class hierarchy starting from `TObject`
- Decompile embedded DFM resources
- Extract all method names from RTTI

This takes 5–30 seconds depending on binary size.

### Step 2 — Examine recovered structure

| IDR panel | What to look for |
|-----------|-----------------|
| **Classes** | Tree of all classes. Look for names containing `Reader`, `Viewer`, `Decode`, `DKI`, `Stream`, `File`. These are your targets. |
| **Forms** | DFM decompilations. Each form shows controls and their event handlers. Find the main viewer window — the "open volume" button's `OnClick` handler is your entry point into the read pipeline. |
| **Methods** | Every recovered method by class. Scan for anything with "Read", "Open", "Decompress", "Decode" in the name. |
| **Imports** | Which APIs are called. `CreateFileW`, `ReadFile`, `MapViewOfFile` are the I/O chain you care about. |

### Step 3 — Export identification

Even before exporting to Ghidra, IDR's class tree alone may tell you the architecture:

- `TTextReader` → body text display
- `TTreeReader` → table-of-contents reader
- `TDKIStream` → low-level DKI I/O
- `TVolumeManager` → volume mounting / CD handling

### Step 4 — Export symbols

`File → Export → Map file` (or IDR's native `.idr` format).

The map file contains:

```
Ordinal  Name                                  Address
0001     TTextReader.ReadLn                    00613458
0002     TTextReader.OpenStream                00616dc0
0003     TDKIStream.ReadHeader                 0047027c
...
```

---

## 4. Loading IDR output into Ghidra

### Method A — Map file import (best)

1. Open Digibib5.exe in Ghidra as usual
2. Run auto-analysis
3. `File → Load → Map File...`
4. Select the `.map` file exported from IDR
5. Ghidra applies symbols by address — `FUN_00613458` → `TTextReader_ReadLn`

This is the recommended method. It gives you readable function names without modifying the binary.

### Method B — Scripted import

For repeated runs, use Ghidra's Python API:

```python
# In Ghidra's Script Manager (Python)
file = askFile("Select IDR map file", "Open")
for line in open(file.toString()):
    if "    " in line and line.strip():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0].isdigit():
            addr = toAddr(int(parts[2], 16))
            name = parts[1].replace(".", "_")
            createLabel(addr, name, True)
            print(f"  {addr} → {name}")
```

### Method C — Manual (for a handful of key functions)

If you only need a few critical names:

1. In IDR, note the address of the method you care about
2. In Ghidra, go to that address: `G → 00613458`
3. Right-click → `Add Label` → enter the name from IDR

---

## 5. Interpreting IDR output

### Class naming conventions

Delphi classes use Hungarian-adjacent prefixes:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `T` | Type (class) | `TTextReader`, `TFormMain` |
| `F` | Field | `FStream`, `FCurrentLine` |
| `E` | Exception | `EDKIReadError` |

Method names in IDR use Delphi's internal naming:

```
TTextReader.ReadLn              →  public method
TTextReader.SetCurrentLine       →  published property setter
TTextReader.GetTextBuffer        →  published property getter
TTextReader.FStream              →  field (may be private)
```

### Form event handlers

DFM decompilation tells you which method runs when:

```
object OpenButton: TButton
  OnClick = VolumeOpenClick        ←  user clicks "Open Volume"
end
object Timer1: TTimer
  OnTimer = ProgressCheck          ←  fires every N ms
end
```

This means the function `TFormMain.VolumeOpenClick` at address `XXXX` is where the volume-open workflow starts. The decompiler may show it calling `TVolumeManager.Open` → `TDKIStream.Create` → `TTextReader.LoadText`.

### RTTI fields

IDR also recovers class field layouts:

```
TTextReader = class(TCustomReader)
  FStream: TDKIStream;         // offset +0x04
  FCurrentLine: string;         // offset +0x08
  FLineNumber: Integer;         // offset +0x0C
  FBuffer: PChar;              // offset +0x10
  FBufferSize: Integer;        // offset +0x14
end
```

These offsets let you map Ghidra's stack variables to meaningful field names.

---

## 6. Key Delphi concepts for reversers

### VMT (Virtual Method Table)

Borland's VMT is different from MSVC's vtable. Each Delphi class carries a VMT at a **negative offset from the class reference**:

```
TObject                 VMT at -0x00
  - InstanceSize        at -0x04
  - ParentClass         at -0x08
  - MethodTable         at -0x10 ...  (entries per virtual method)
```

IDR resolves this automatically, but if you're reading raw Ghidra output, a call like `mov ecx, [eax]` followed by `call [ecx+0x24]` is a virtual method dispatch — the `+0x24` is the offset into the VMT.

### DFM resources

Delphi forms are stored as **RCDATA resources** in the PE. IDR decompiles these to text. Without IDR, you can find them manually:

1. In Ghidra, open `Window → Resource View`
2. Look for resources named `TFORM*`, `TFRAME*`, or numeric IDs in the RCDATA section
3. These are the raw DFM blobs — format is proprietary binary unless the EXE was compiled with `{$R *.dfm}` (Delphi 7+ may embed as text)

### Exception handling

Delphi uses SEH (Structured Exception Handling) but with Borland's own frame format. Ghidra's SEH analyser may not recognise it. IDR recovers `try/except` boundaries from the RTTI.

### String types

Delphi strings are **length-prefixed**, not null-terminated. A Delphi `string` at address P is:
```
P[-8]:  Integer   = reference count
P[-4]:  Integer   = length in characters (not bytes!)
P[0]:   Char      = first character
```

This matters when Ghidra's decompiler shows a function taking a `char*` parameter — it may actually be a Delphi `string`. The `Length()` call in the decompiled output is reading `P[-4]`.

---

## 7. When IDR isn't enough

| Scenario | Workaround |
|----------|------------|
| **UPX / packed** | Unpack first (upx -d, then IDR). If custom packer, unpack in x64dbg first. |
| **Delphi 2009+** | Newer RTTI format — IDR has partial support. Try the latest dev build. |
| **No RTTI** | Compiled with `{$RTTI EXPLICIT}` or stripped. IDR can still recover DFM forms but fewer method names. Fall back to dynamic tracing. |
| **Static linking** | If the Delphi runtime is statically linked (no BPL imports), IDR still works — the VMT/RTTI tables are embedded in the EXE. |
| **Mangled names** | IDR may show names like `@TTextReader@ReadLn$qqrv` — this is Delphi's internal mangling. Strip to `TTextReader.ReadLn`. |

---

## 8. References

- [IDR GitHub](https://github.com/crypto2011/IDR) — source, releases, issues
- [Delphi to Ghidra workflow (YouTube)](https://www.youtube.com/results?search_query=delphi+ghidra+idr) — community tutorials
- [Delphi RTTI internals (Hallvard's Blog)](https://hallvards.blogspot.com/) — authoritative reference on Borland RTTI structure
- [Ghidra Delphi loader](https://github.com/astrelsky/Ghidra-Delphi-Importer) — alternative: Ghidra plugin for Delphi (less mature than IDR)
- [DigiBib reversing guide](DIGIBIB_REVERSING_GUIDE.md) — how IDR fits into the overall DigiBib reverse workflow
- [ReVa MCP guide](REVA.md) — Ghidra MCP server for decompilation after IDR symbols are loaded
