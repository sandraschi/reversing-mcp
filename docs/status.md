# Digibib5.exe — reversing status (ReVa / Ghidra)

**Program:** `Digibib5.exe` (Ghidra project path `/Digibib5.exe`).  
**Companion:** [DIGIBIB_DECOMPILE_PLAN.md](DIGIBIB_DECOMPILE_PLAN.md) · [GHIDRA.md](GHIDRA.md)

**Reference volumes (local):** `L:\Multimedia Files\Written Word\Digitale Bibliothek\` — per-volume `Data\` holds `TEXT.DKI` / `Text.dki`, `TREE.DKI`, etc.

## Clarification / goals

**End goal:** Build an **independent DKI viewer** that outputs **plain book text** (and minimal structure for navigation), **not** full-text search, RAG, or Fundstellen-style workflows. **RAG** and **advanced search** are **out of scope** for this reversing track; they can consume **exported text + stable IDs** later.

**Scale:** CD-ROMs are usually **collections** (**dozens to hundreds of books** per volume). The viewer must support **two TOC levels**:

| TOC level | Purpose |
|-----------|---------|
| **Collection** | **Book list** — which title / openable unit in the volume (shell-level). |
| **Book** | **Chapter / section tree** — internal structure of a single book. |

**Reader-first reversing priorities**

1. **Body text** — **`FUN_00613458` → `FUN_00616dc0`** (stream → line buffers) + **`FUN_00614bb4`** (line bytes → UTF-8 / markup runs). This is the **spine** for “see the book.”
2. **Collection TOC** — **`TREE.DKI`** (and related catalog under `Data\`) + **`FUN_0061a880`** shell / volume wiring — **book list** and **open volume** paths.
3. **Book TOC** — **tree nodes** and/or **token / markup** path (**`FUN_00619c74` / `FUN_00619b7c`**) tying **titles → offsets, line ranges, or stream positions**.

**Deprioritized for the viewer goal:** Fundstellen / **`FUN_00628f10`** / **`wl`** / fleet registrar / search index internals — useful for parity features, **not** for sequential reading or TOC extraction.

Last updated: 2026-03-23 (ReVa batch: **`VMT+0x54`** → **`FUN_0047027c`**, **`FUN_00616af0`** **xrefs** re-check; **goals** section).

## Status notes

| Area | State |
|------|--------|
| **`Text.dki` load** | **`FUN_00616af0`** reads header + bulk into **`obj+0xc`** (`uint32[]` length **`*(obj+4)`**); magic **`0x001924CC`** on DB006 path. |
| **Layout / view** | **`FUN_00613458` → `FUN_00616dc0` / `FUN_00614bb4`**: stream + line bytes + **`+0xb8`** child for embed tokens; **no** **`*(loader+0xc)[i]`** walk in **`FUN_00614bb4`**. |
| **Repaint hook** | **`FUN_006154e4`**: **`VMT+0x80` → `FUN_00469848`** ( **`0xB03C`** dispatch), not hit-testing. |
| **`FUN_00628f10` vs `obj+0xc`** | **Ruled out** in decompilation: **no** **`Text.dki` loader** / **`host+0xcc`** / **`FUN_004691fc`**; **no** **`FUN_00420544` / `FUN_0040beb8` / `FUN_0061b278`**. Uses **internal** **`+0x802c` / `+0x8034`** tables + **stream** **`Seek`/`Read`** on **`param_1+0x10`/`+0xc`/`+0x8`**. |
| **Fundstellen** | **`FUN_006f9e2c`** → **`wl`** vtable ops; **`FUN_00628f10`** = **hit iterator** on **~0xA000-byte search object** (not `Text.dki` **loader**). **Host** frame **`FUN_0065e544`**: **VMT `0x0065e41c`**, **slot `0x28`**. **`wl`** runtime **class** still **unnamed**. |
| **`FUN_0060d4cc`** | **Full sweep:** **no** **`loader+0xc`** dword-table use — volume-type **`switch`** + string helpers only. |
| **`LAB_00420544` (`0x00420544`)** | **VMT slot** (data xrefs e.g. **`0x0041b6d8`** near fleet **registrar**); **`FUN_0042013c`** binary search calls **`(*obj+0x34)`** — **not** used from **`FUN_00628f10`**. |
| **Fleet registrar** | **`obj+0x60` / `+0x88`/`+0x8c`** **not** wired to **`wl`** / **`FUN_00628f10`** in traced code; **`FUN_00619834`** uses **`+0x18`/`+0x1c`**, not **`+0x60`**. |
| **Alternate magics** | **`DB002`/`DB008`** (`0x67200` family) **not** matched by named immediates in loaders analyzed — **open**. |
| **`wl` / Fundstellen UI** | **ReVa:** **`analyze-vtable`** **`0x006f7f24`** — **`+0x14`** **`FUN_0046d44c`**, **`+0x28`** **`FUN_0046959c`**, **`+0x3c`** **`FUN_00483b04`**, **`+0x44`** **`FUN_00470cfc`** aligns with **`FUN_006f9e2c`** on **`*( *(shell+0x29c) + 0x23c )`** (**`+0x54`** extends past first **~19** **slots** in dump). **`find-vtables-containing-function`** on **`FUN_00628d0c` / `FUN_00629ad8` / `FUN_00629ab8`** → **0** (**not** vtable methods). **`FUN_00616af0`** **incoming** **xrefs** = **only** **`FUN_0061a880`**. |

**Next (reader / TOC):** **`TREE.DKI`** open + parse path; **`FUN_0061a880`** → **book list**; **chapter** navigation (**tree** vs **tokens**); **`FUN_00616dc0` / `FUN_00614bb4`** **export-shaped** decompilation (plain text). **Optional** (search parity): **`wl`** / **`VMT` `0x006f7f24`** ctor proof.

---

## Fleet notes (high level)

- Zlib is **embedded** (no zlib DLL in IAT by name). **`FUN_0050b524`** → **`FUN_0051467c`** for zlib init/error strings; PNG/zlib paths use **`FUN_0050c338`** etc.
- **`FUN_0061c0f4`** registers `data\…` paths and accumulates **64-bit total file size**; **`FUN_00616af0`** is the **`Text.dki` loader** that **reads bytes**.
- Registrar object at **`obj+0x60`**: VMT **`~0x0041b6a4`**; **`+0x88`/`+0x8c`** = sorted string list **insert** / **binary search** (not file I/O).

---

## Text.dki format (draft)

- **Hex sample (confirmed magic path):** `L:\...\DB006\Data\Text.dki` — first **16** bytes: **`CC 24 19 00  04 00 00 00  74 DF 00 00`** → LE dwords **`0x001924CC`**, **`0x00000004`**, **`0x0000DF74`**. **`FUN_004c6f88`** reads the **first dword** (magic) from the stream; then **`FUN_00420598`** + **`Read` 0xC** into a **12-byte** buffer fills **three** dwords. Decompilation assigns **`*(obj+0x20) =` second dword** (here **`0x00000004`**) and **`*(obj+4) =` third dword** (here **`0x0000DF74`**). The **follow-on bulk `Read`** uses **`*(int *)(obj+4) << 2`** bytes into **`obj+0xc`** — on DB006 that is **`0xDF74 × 4`** bytes (**third dword** is the **scaled payload length**, not the second dword).
- **Third header dword (`0xDF74` on DB006):** **is** the value stored in **`*(obj+4)`** after the **12-byte** header read (see above). **`find-constant-uses`** has **no** immediate **`0xDF74`** — size is **file-driven only**.
- **Other on-disk families:** **`DB008\Data\TEXT.DKI`** begins **`56 17 00 00 …`**; **`DB002\Data\TEXT.DKI`** begins **`95 0D 01 00 …`** — **not** **`0x001924CC`**; likely **older or alternate `text.dki` layout** (still **LE dword tables**). Digibib5 may branch on magic or volume revision.
- **`DB008\Data\TEXT.DKI` (first 16 bytes, `Format-Hex`):** LE **`dword@0 = 0x00001756`**, **`dword@4 = 0x00067200`**, **`dword@8 = 0x000673ED`** — same **`0x67200`** at **+4** as DB002 below; **`+8`** onward is a **dword offset table** (ascending), not the DB006 **`0x04` / small-count** header shape.
- **`DB002\Data\TEXT.DKI` (first 16 bytes, `Format-Hex`):** LE **`dword@0 = 0x00010D95`**, **`dword@4 = 0x00067200`**, **`dword@8 = 0x00067398`** — **identical `dword@4`** to DB008 while **magic `dword@0`** differs; supports treating **`0x1756` / `0x10D95`** as **per-volume ids** sharing one **“`0x67200` family”** on-disk header, distinct from **`0x001924CC`** + **`dword@4 == 4`** (DB006).
- **Magic (code, immediate):** Ghidra **`find-constant-uses`** finds **`0x001924CC`** only at **`FUN_00616af0`**, **`FUN_005d7340`** (after **`Read` 0x20**: if magic match, copy second dword to **`obj+8`**, else **`obj+8 = 100`**), **`FUN_006072e8`** (after **`Read` 0x40** into **`obj+0xc`**: if **`*(obj+0xc)==0x1924cc`**, then **`Seek`** + fill **`obj+0x4c` / `+0x50` / `+0x54`** tables via stream **`Read`**), and **`FUN_006109f8`** (after **`Read` 0x20**: **must** match or **“Wrong magic number in …”**). **No** immediates **`0x1756`** or **`0x10D95`** in the binary — alternate on-disk magics are **not** selected by named constants here; **`DB002`/`DB008`-style** files likely need **another build**, **import path**, or **undiscovered** compare (e.g. table-driven).
- **Seek:** **`FUN_00420598`** → **`TStream::Seek` at VMT `+0x18`** (rewind before the **12-byte** header read).
- **Payload buffer:** **`obj+0xc`**, **`Read`** length **`*(obj+4) << 2`** for the **first** bulk slice right after header parse; interpreted as **`uint32_t[*(obj+4)]`** for that slice. Larger index data may be loaded in **other routines** (e.g. **`FUN_00616cdc`** / view refresh).
- **Checksum:** no validation in **`FUN_00616af0`** after read; flags only **`obj+0x1c`**, **`obj+0x10`**.
- **Unrelated hex:** High-entropy strings such as **`DA B0 F9 91 …`** that were pasted for comparison are **software registration codes**, not **`Text.dki`** bytes — they do **not** bound header vs payload for index files.
- **`FUN_006071f0` (teardown):** On **`FUN_006072e8`**’s **`else`** branch (magic **≠** **`0x001924CC`** after the **0x40** header read), **`FUN_006071f0`** runs: if **`*(param+8)`**, calls **`FUN_00404034`** and zeros **`+8`**; for each non-zero **`+0x4c`**, **`+0x50`**, **`+0x54`**, calls **`FUN_00402ab8`** and zeros the field — releases the **conversion** index object’s stream and three heap tables. Also invoked from **`FUN_00607608`**.
- **Zlib vs `Text.dki` bulk (snapshot):** Embedded **deflate/inflate** copyright strings exist; **`FUN_0051467c`** uses **`zlib memory/version/Unknown zlib error`**; **`zlib error`** is referenced from **`FUN_005282e4`**, **`FUN_00528b88`**, **`FUN_0052a8fc`** (PNG-style paths per fleet notes). **`FUN_0061b278`** decompiles to **`return *(param_1+0x24)`** (optional **`FUN_0061ad28`**), **not** inflate. **No** caller chain from **`FUN_00616af0`** / **`FUN_006072e8`** stream **`Read`** to those zlib helpers was traced in this pass — treat **post-header bulk** as **opaque** until a **post-load** consumer is xref’d.
- **Zlib call sites (downward, ReVa):** **`FUN_005282e4`** is **PNG `zTXt`** handling (**`Empty keyword in zTXt chunk`**, **`Unknown zTXt compression`**, **`FUN_0050c338`** inflate); callers **`FUN_00525134`**, **`FUN_00525540`**. **`FUN_00528b88`** / **`FUN_0052a8fc`** are **PNG IDAT** inflate (**`FUN_0050c338`**, **`FUN_00527930`**, **`FUN_00524ed4`** with **`zlib error`**); **`FUN_0052a8fc`** called from **`FUN_005291a8`**. **Verdict:** these **`zlib error`** paths are **PNG decode**, **not** **`Text.dki`** post-header bytes.
- **`FUN_00616dc0` vs `obj+0xc`:** Decompilation uses **`*(param_1+8)`** **`TStream`** (`**Read` at VMT **`+0xc`**) for **6-byte** or **word** metrics and a **bulk `Read`** into the **host buffer** — **no** **`*(param_1+0xc)`** use in **`FUN_00616dc0`**; the **`uint32[]`** table pointer remains for **other** consumers.
- **`obj+0xcc` / navigation / search:** **`FUN_00613458`** passes **`*(view+0x210)+0xcc`** into **`FUN_00616dc0`** ( **`Text.dki` loader object** ). **`FUN_006f9e2c`** (**Fundstellen** / **`%d Fundstellen`** strings) ends by **`FUN_00613458( *(main @ +0x2b4)+0xec, line )`** after **`FUN_0060d4cc`** — **search-hit → line layout refresh**, **stream-based** geometry, **not** a direct **subscript of `obj+0xc`** in the traced lines. **`FUN_00609af4`** (font metric loader) calls **`FUN_00613458`** but has **no** **`FUN_0050c338`** / zlib in the **first ~95** lines.
- **Ghidra:** Creating a single function for **`0x0072b070`–`0x0072bacb`** ( **`0x0072b1f3` → `FUN_0061111c`** ) is **manual** in Ghidra; not applied via ReVa here.
- **`FUN_0061111c` / strict magic — callers:** Besides **`FUN_0065ebf8`** ( **`konk;`** / concordance-style setup ), **`FUN_0061111c`** is also called from **`0x0072b1f3`**, inside Ghidra’s **`UndefinedFunction_0072b070`** range: decompilation there shows **main shell wiring**, strings **`Wikipedia`** and **`[Ohne Registrierung]`**, **`FUN_0061e9f4`**, and heavy **`FUN_0047c72c` / `FUN_006fd33c`** UI hooks — **not** the short **`FUN_0072af44`** volume-change stub (that path calls **`FUN_0061a880`** only).

---

## Consumers of `Text.dki` loader / `obj+0xc` table

**`FUN_0061a880`** (sole incoming xref **`FUN_0072af44`**, also from **`entry`** via app shell): builds the **main document / library shell**. It calls **`FUN_00616af0`** and stores the returned object pointer at **`host+0xcc`**. That value is the **Delphi “text index” object** holding stream handle, **`obj+0xc`** dword table pointer, **`obj+0x4` / `obj+0x20` header fields**, and flags; downstream **UI** and **layout** code (e.g. **`FUN_00613458`** → **`FUN_00616dc0`**) use it to **resize line buffers** and **`Read`** **word-count / dimension** data from the same **`TStream`**, not to reinterpret **`obj+0xc`** as strings.

**`FUN_00616dc0`** (incoming **`FUN_00613458`** only): **pagination / line-layout** when the user changes position. It takes **`*(view+0x210)+0xcc`** (same **`Text.dki` loader object**), rewinds the stream when loaded, and either reads **6 bytes** into **ushort** metadata or calls **`FUN_004c6f9c`** for a **single-word** metric when **`obj+0x20==1`**, then **reallocates** a **host buffer** (`*param_3`) sized **`count + 0x5dc`** and **`Read`**s **`count`** bytes into it — so it **consumes the binary index stream** for **geometry / run lengths**, while the **`uint32[]`** at **`obj+0xc`** remains the **in-memory offset table** from the **first** **`FUN_00616af0`** slice for other readers.

- **`FUN_00614bb4`** (incoming **`FUN_00613458`** only — **`get-call-tree` depth 2** shows callees **`FUN_0061b278`**, **`FUN_0061b3a4`**, **`FUN_006154bc`**, **`FUN_00619c74`**, **`FUN_00615e48`**, string ops, **no** `TStream::Read` symbol at depth 2): **UTF-8 / markup line scanner** over **`*(view+0x268)`** — an array of **pointers into host line bytes** (`pbVar1`), **not** subscripts of **`*( *(loader)+0xc )`** as **`uint32[i]`** in the decompilation. It maintains **`view+0x4bc`**, **`view+0x4c0`**, and parallel **`ushort`** buffers at **`view+0x4c4`** / **`view+0x4c8`** for **run/column** pairs. It **does** read the **loader object** at **`*(view+0x210)+0xcc`**, but only to test **`*(loader+0x20) > 2`** (for **`0x81`/`0x82`** markers) and to call **`FUN_00619c74(*(…+0x210)+0xb8, …)`** — **`+0xb8`**, **not `+0xc`**. **Conclusion (this pass):** **layout / tagging** uses **line-byte pointers + ushort run tables + `loader+0x20` / `+0xb8` child**; **no** **`*(loader+0xc)[k]`** walk appears in **`FUN_00614bb4`**’s decompilation.

- **`FUN_006154bc`**: sets **`*(param+0x288)=0`**; if **`*(param+0x280)`**, calls **`FUN_00403698`** on that buffer with length **`*(param+0x284)*0x13+400`** — **strip/glyph working buffer** maintenance, **not** dword-table lookup.

- **`FUN_006154e4`**: **`FUN_006154bc(param)`** then, if **`param[0x26d]!=1`**, **`vcall *( *param + 0x80 )()`** — see **Consumers** bullet **`FUN_006154e4 → *(*view+0x80)`** (**`FUN_00469848`** / **`0xB03C`** dispatch).

- **`FUN_0061ba3c`:** **`return *(param_1 + 0xd4 + (param_2 & 0x7f)*4)`** — **indexed slot getter** on **whatever object** is passed. **`FUN_006f9e2c`** calls it with **`*(shell+0x2b4)`** (and **`FUN_006f8150`** with **`*(+0x220)`**); it is **not** tied to **`view+0xec`** / **`FUN_00613458`**’s **`Text.dki`** view pointer — **font / metric / child-object table**, separate from **`obj+0xc`**.

- **`FUN_00619c74`** (only **2** xrefs: **`FUN_00614bb4`**, **`FUN_0061a244`**): thin wrapper — **`FUN_00405324`**, then **`FUN_00619b7c(param_1, …)`**. **`FUN_00619b7c`** calls **`FUN_00619208(param_1)`** (lazy init on **`param_1+0x2c` / `+0x34` / `+0x30` / `+0x18`**) and branches on **`*(param_1+0x24)`** vs **`0xe1`** into **`FUN_00619318`** / **`FUN_0061927c`** / **`FUN_0061992c`** (token / run resolution). **`FUN_00614bb4`** uses **`*( *(view+0x210)+0xb8 )`** only for **`FUN_00619c74`** on **inline object** opcodes (**`10` / `0x86`** path after **`FUN_00615e48`**); it uses **`*( *(view+0x210)+0xcc )`** for **`*(loader+0x20)`** width checks (**`0x81`/`0x82`**) and (elsewhere in the app) **`FUN_00616dc0`** takes **`+0xcc`** — **role split: `+0xb8` = child “resolver/registrar” object for embed/image (and related) tokens; `+0xcc` = main `Text.dki` loader / stream for metrics and pagination.**

- **`FUN_006154e4` → `*(*view + 0x80)`:** **`param_1`** is the **Delphi object** (`*param_1` = **VMT**). **`get-data`** at **`VMT+0x80`** for representative **`TWinControl`**-style tables (**e.g. `0x006f90f0+0x80` → `0x00469848`**, same pointer at **`0x006ec1a8+0x80`**) resolves to **`FUN_00469848`**: if **`param_2 != *(param_1+0x5f)`**, stores **`param_2`**, clears **`*(param_1+0x60)`**, **`FUN_0046a9b8(param_1, 0xB03C, 0, 0)`** — **VCL-style `Dispatch` / CM message** (**not** coordinate hit-test; **display-state / invalidate-style** side effects).

- **`FUN_006543fc`** (xrefs **`FUN_00654358`**, **`FUN_0065ebf8`**): **`*(host+0x2d8)=child`**, **`*(child+0x54)=host`**, **`FUN_00598ea4`**, index fill **`host+0x338+…`**, **`FUN_0065444c`**. **`FUN_0065ebf8`** then **`FUN_0061111c( *( *(child+0x84) + 0xc0 ) )`** — **concordance / “konk;”** wiring, **no** **`Text.dki` `obj+0xc`** or **registrar `obj+0x60`** in this routine.

- **`FUN_0060d4cc`**: large **`FUN_0061b278(loader)`**-driven **`switch`** (string **`Read` / merge** cases use **`FUN_00405280`**, **`FUN_004c6ac4`**, **`FUN_004c5b78`**, etc.); **no** **`*(loader+0xc)[i]`** subscript in sampled decompilation lines (**~200–400**). **`FUN_006f9e2c`** (**`%d Fundstellen`**, **`Keine Fundstelle.`**) calls **`FUN_0060d4cc( *(shell+0x2b4), … )`** then **`FUN_00613458( *(loader+0xec), line )`** — **search-hit UI → layout refresh**, still **not** a direct **`uint32[]` at `loader+0xc`** walk in the traced slice.

- **`FUN_006f9e2c`** — **word-list object** **`wl = *( *(shell+0x29c) + 0x23c )`** ( **`shell`** = **`local_8`**): **vtable** calls on **`wl`** include **`+0x14`** **`()`** → **element count** (checked vs **15999**, **`"wortliste_voll"`**); **`+0x54`** **`(wl, unaff_EDI)`** → **allocate / fetch entry** (returns **`local_1c`**); **`+0x3c`** **`(wl, unaff_EDI, 1)`** if **`local_1c == -1`** → **insert default**; **`+0x18`** **`(wl, local_1c)`** → **length / span**; **`+0x24`** **`(wl, local_1c, iVar6+1)`** → **grow / append**; **`+0x44`** **`()`** → **predicate** (paired with **`*(shell+0x298)+200`** **`()`** — **`+0xC8`** on sibling). Related: **`*(shell+0x29c)+0xd0`** **`(shell@+0x29c, 0)`** — **clear** on parent; **`*(shell+0x2a0)+100`** **`(…, bool)`** — **notify** ( **`+0x64`** ). **Verdict:** **dynamic word-bag** with **count / append / slot lookup**, **not** shown to call **`FUN_00420544`** / fleet **registrar `+0x88`/`+0x8c`** in this function.

- **`FUN_0040beb8`** **+ binary search** ( **`FUN_00619834`**, from **`FUN_00619b7c`**): **`while`** loop **`mid = (lo+hi)>>1`**, **`FUN_00420598(*(obj+0x18))`**, **`TStream::Read` via `**(obj+0x18)+0xc`**, **`FUN_0040beb8(key, probe)`** — **sorted string key lookup** on **`obj+0x18`/`+0x1c` bounds** on the **`+0xb8`** child layout path. **Same `CompareStringA` helper** as **`FUN_00420544`**, but **offsets `+0x18`/`+0x1c`**, **not** **`obj+0x60`** / **`+0x88`/`+0x8c`** from fleet **registrar** notes — **parallel “sorted table”** machinery.

- **`FUN_0060d4cc`** **full decompilation sweep** (**754** lines): **no** use of **`*(param_1+0xc)`** as **`Text.dki` dword table** or **indexed load**; **`param_1`** is **`FUN_0061b278`**-typed **loader**. The only prominent **`0xc`** is **stack init** **`iVar4 = 0xc` / `do…while`**. **`FUN_004c5b78` / `FUN_004c6ac4`** here are **Delphi string slice / merge** helpers for **hard-coded** **`switch`** cases, **not** tied to **`loader+0xc`**.

- **`FUN_00628f10`** (**Fundstellen hit iterator**; callees **`FUN_00627f3c`**, **`FUN_00628d0c`**, **`FUN_00628bf4`**, **`FUN_00629ab8`**, **`FUN_00629ad8`**, **`FUN_00627938`**, **`FUN_005d7138`**, **`FUN_0040513c`**, **`FUN_0040d558`** — **no** **`FUN_00420544`**, **`FUN_0040beb8`**, **`FUN_0061b278`**, **`FUN_004691fc`**): **large state** **`param_1`** (**`+0xa084` / `+0xa08c` / `+0xa090` / `+0xa098`** cursors, **`+0x802c`** line table, **`+0x8034`** dword buffer **÷3**, **`FUN_00628d0c`**, **`FUN_005d7138`**). **`Seek`/`Read`** on **`param_1+0x10`**, **`+0xc`**, **`+0x8`** (**`Read` `0x60`**). **`FUN_00629ab8`**: **`0x67208`** or **`(*(a044)+1)*4+4`** — **numeric** **`0x67200`**-family tie, **not** **`Text.dki` `loader+0xc`**.

- **`LAB_00420544` / `FUN_0042013c`:** **`to`** **`0x00420544`** = **vtable DATA** (e.g. **`0x0041b6d8`**, fleet **registrar** region). **`FUN_0042013c`** uses **`(*param_1+0x34)`** ( **`LAB_00420544`** ). **No** path from **`FUN_00628f10`**.

- **Fundstellen host (`FUN_006f8048`):** **`FUN_0065e544`** → **`*(param_1+0x230)`**; **`analyze-vtable`** **`0x0065e41c`**: **`FUN_0065e544`** at **`+0x28`**. **`piVar2[0x121] = *(param_1+0x23c)`** — **`wl`** / **id** field alignment.

- **ReVa `find-vtables-containing-function`:** **`FUN_00628d0c`**, **`FUN_00629ad8`**, **`FUN_00629ab8`** → **0** **vtables** each (**Fundstellen** **helpers**, **not** **virtual** **methods**).

- **`FUN_00616af0`** **`find-cross-references`** (**`to`**, **limit** **40**, **`includeContext`**): **only** **`FUN_0061a880`** (**stores** **`host+0xcc`**). **No** **second** **`Text.dki`** **loader** **ctor** **in** **incoming** **xref** **set** — **`obj+0xc`** **search-time** **consumer** **still** **not** **via** **alternate** **load** **path**.

- **`find-constant-uses`:** **`0x67200`** → **0** **hits**; **`0x67208`** → **only** **`FUN_00629ab8`** (**`MOV EAX,0x67208`**). **No** **overlap** **with** **`FUN_00616af0`** **/** **`Text.dki`** **loaders** — **`0x67200`** **on-disk** **family** **not** **wired** **by** **named** **immediates** **here**; **`FUN_00629ab8`** **numeric** **tie** **remains** **separate** **from** **header** **`dword@4`**.

- **`wl` VMT candidate (`0x006f7f24`):** **`analyze-vtable`** (**first** **~19** **slots**): **`+0x14`** **`FUN_0046d44c`**, **`+0x18`** **`FUN_0041e164`**, **`+0x24`** **`FUN_0046c100`**, **`+0x28`** **`FUN_0046959c`**, **`+0x3c`** **`FUN_00483b04`**, **`+0x44`** **`FUN_00470cfc`** — **matches** **`FUN_006f9e2c`** **vcalls** **through** **`+0x44`**; **`get-data`** **`0x006f7f24+0x54`** (**`0x006f7f78`**) → **`FUN_0047027c`** (**`+0x54`** **fetch/alloc**). **Distinct** **from** **Fundstellen** **host** **`0x0065e41c`** (**`FUN_0065e544`** **at** **`+0x28`**). **`find-cross-references`** **`to`** **`0x006f7f24`**: **0** (**vtable** **label** **not** **incoming-xref’d** **—** **use** **`find-vtables-containing-function`** **on** **slot** **impls** **instead**).

- **`FUN_006072e8`** / **`FUN_006109f8`** **incoming** **xrefs:** **`FUN_006072e8`** ← **only** **`FUN_006f779c`**; **`FUN_006109f8`** ← **only** **`FUN_0061111c`** (**callers** **`FUN_0065ebf8`**, **`0x0072b1f3`**). **`FUN_006072e8`** **decompilation:** **`if (*(int *)(obj+0xc)==0x1924cc)`** **then** **fill** **`+0x4c`/`+0x50`/`+0x54`** **tables**; **`else`** **`FUN_006071f0`** — **non-`0x1924cc`** **first** **dword** **→** **teardown** **without** **those** **loads** (**second** **on-disk** **family** **handled** **as** **failure** **path**, **not** **alternate** **parser** **in** **this** **routine**).

---

## Sorted-table compare (VMT `+0x34`)

- Slot **`+0x34`** on the same VMT as **`FUN_0042013c`** resolves to **`0x00420544`**: delegates to **`FUN_0040beb8`** or **`FUN_0040bf08`** → **`CompareStringA`** on **Delphi string contents** (flag **`*(obj+0x1e)`** picks **case-sensitive vs case-insensitive** sort). Keys are **string identity**, not a separate hash column.

---

## Open

- **`FUN_00619c74`** / **`+0xb8`** child: optional **Ghidra** type on **`wl`** / **vtable** labels for **`+0x14`…`+0x54`** (word-list class).
- **Fundstellen ↔ fleet registrar:** **`FUN_00628f10`** **does not** xref **`LAB_00420544`**; **`wl`** **Delphi** **class** **string** **still** **open** — **narrowed** **to** **`VMT` `0x006f7f24`** **by** **slot** **match**; **prove** **with** **ctor** **or** **`*(*wl)`** **at** **runtime**.
- Map **`Text.dki` `obj+0xc`** **indexing** to **any** **search** consumer (not layout) — **`FUN_0060d4cc`** **confirmed** **no** **`loader+0xc`** table read; **`FUN_00616af0`** **xrefs** **single** — **no** **parallel** **loader** **for** **search** **in** **ReVa** **xref** **list**.
- **`DB002`/`DB008` (`0x67200` family):** **`find-constant-uses`** **`0x67200`** **empty**; **`FUN_006072e8`** **non-`0x1924cc`** **→** **`FUN_006071f0`** — **no** **evidence** **this** **EXE** **parses** **`0x1756`/`0x10D95`** **headers** **in** **traced** **loaders** (**“wrong** **build”** **or** **undiscovered** **entry** **still** **possible**).
