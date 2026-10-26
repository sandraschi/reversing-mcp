# Digibib5.exe - reversing findings

Running depot of the Digitale Bibliothek 5 reversing work driven through ReVa.
Markup (renames, comments) lives in the Ghidra project; this file is the
human-readable trace and findings log.

- Target: `C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe`
- Imported into the ReVa Ghidra project as `/Digibib5.exe` on 2026-10-26.
- 32-bit PE (image base 0x00400000), 11,532 functions, full analysis checked in.
- Reference target for the `.DKI` Directmedia format.
- End goal: a working **clone** (reader) + a correct DKI decoder. Oracle = the
  real Digibib5, driven by CUA clickthrough (ClickerLab in reversing-mcp).

## CORRECTION LOG (read this first)

**2026-10-26, first pass was wrong.** Chasing the string "Decompression error"
(@ 0x0073ab2f) led into `FUN_00514dd0` / `FUN_00521234` / `FUN_00522294`, which
were written up as a bespoke "DKI bit-plane licensing codec". That was a
mistake: those three functions are **statically-linked libpng 1.0.x internals**
(`png_read_start_row`, the Adam7 interlace-pass dispatcher, and
`png_combine_row`). The string xref landed in a bundled library, not Digibib5's
own format. Ghidra comments on those three addresses have been corrected.

Lesson: before writing up a "custom codec", check for a library signature. This
binary bundles **libpng 1.0.3/1.0.4 and zlib 1.1.2 / 1.0.4** (confirmed via
version strings and the deflate/inflate copyright banners).

## What this reframes

- The page/image content is almost certainly **PNG** (hence libpng), and/or
  **zlib-deflated** streams. So the decoder job is likely: parse the DKI
  container -> pull out PNG / deflate blobs -> decode with stock libraries.
  NOT a from-scratch bespoke codec.
- The existing FOSS `directmedia_dki.py` using zlib is therefore not wrong to
  reach for zlib; whether it is "crap" is about container parsing / offsets, to
  be judged separately (not yet verified).

## Confirmed facts

- Statically linked: libpng 1.0.3 and 1.0.4, zlib 1.1.2 and 1.0.4. Multiple
  png_* error strings present (png_do_rgb_to_gray, png_do_dither,
  png_memcpy_check, png_read_start_row, "Incompatible libpng version").
- `.DKI` volume names referenced in code: `Data\Text.dki`, `Data\Tree.dki`
  (+ lowercase variants). `FUN_0061c6b0` references both text.dki and tree.dki
  together -> candidate volume/TOC loader.
- Index file `HTMLs.idx` referenced by `FUN_00605dc0`.
- Registry path `\SOFTWARE\Directmedia\Digibib4\` (FUN_0059ca70 / FUN_0059cb88).
- Content is rendered as XHTML (iso-8859-1) with `digibib5.css` - there is an
  HTML template string at 0x00712258 and CSS-link emission in FUN_006c4638 /
  FUN_00722760. So a "work/page" is surfaced as HTML referencing a stylesheet.

## Function map (corrected)

| Address | Identity | Notes | Confidence |
|---------|----------|-------|------------|
| FUN_00522294 | libpng png_read_start_row | rowbytes from color_type/bit_depth | high |
| FUN_00514dd0 | libpng interlace-pass dispatcher | 7 Adam7 passes | high |
| FUN_00521234 | libpng png_combine_row | 1/2/4/8-bit pixel merge w/ pass mask | high |
| FUN_0050b358 | thunk -> FUN_00402e48 (memcpy) | | high |
| FUN_0061c6b0 | dki_volume_loader (candidate) | opens text.dki + tree.dki together | low |
| FUN_00605dc0 | reads HTMLs.idx (candidate) | index loader | low |
| FUN_006c4638 / FUN_00722760 | HTML/CSS page emitter (candidate) | emits digibib5.css link | low |

## Volume file inventory (FUN_0061c6b0 - the manifest builder)

Builds an archive object (vtable `PTR_FUN_0041b6a4`, constructed at
0x0061c6d2) and registers each volume file via `FUN_0061c0f4` (called 20x).
A Digibib CD-ROM image `data\` folder contains:

| File | Likely role |
|------|-------------|
| digibib.txt | volume descriptor / manifest (plain text) |
| text.dki | main text content container (DKI) |
| tree.dki | TOC tree container (DKI) |
| tree.dka | tree companion - allocation/offset index for tree.dki (guess) |
| index.htx / .plx / .set / .ttx / .wlx | index family (htx=HTML? ttx=text? wlx=wordlist? plx/set=?) |
| links.htx / .plx / .ttx / .wlx | cross-reference link indexes |
| lemmata.txt | lemma list (lexicon) |
| sigel.dat / sigel.lib | sigla (source abbreviations) |
| tabellen.txt, tabelle0..3 | tables |
| images\images.lib | image library - PNG page scans almost certainly live here |

`FUN_0061c0f4` = per-file register (into the archive object). The actual
open/seek/header-read lives in the archive class behind `PTR_FUN_0041b6a4`.

## Next reversing step (the ACTUAL DKI format)

0. **`PTR_FUN_0041b6a4` vtable + `FUN_0061c0f4`** - the archive reader class.
   This is where a `.dki` file is opened and its header/record table parsed.
   Highest-value target now.

The container format is still unknown. Targets, in order:
1. `FUN_0061c6b0` - opens `Data\text.dki` + `Data\tree.dki` together. Find how
   it opens the file, reads a header, and locates records (offsets/sizes).
2. `HTMLs.idx` reader (`FUN_00605dc0`) - the index that maps a work/TOC node to
   content offsets.
3. `Tree.dki` structure - the TOC tree the clone must render.
4. Follow a content read from offset -> is the blob a PNG (\x89PNG) or a raw
   zlib stream (0x78 0x9c)? That decides the decoder shape.

## DKI FORMAT - cracked from real bytes (DB008 Hoffmann)

Reversed directly from a real image, far faster than disassembly. Image data
lives at `K:\Digitale Bibliothek\Bibliothek\DB<nnn>\data\` (NOT the pretty
"Band xx" folders, which are empty shells). DB008 = Hoffmann.

### Files in a volume's `data\`
- `DIGIBIB.TXT` - plain INI descriptor. Keys: CDMajor, CDMinor, CDSoftwareBuild,
  Caption, Signet, ShortTitle, [Libraries] Index=<bitmask>. This is what the
  CD-ROM picker lists. Encoding latin-1/cp1252.
- `TREE.DKI` - **the TOC, as plain CP1252 text**, CRLF-separated. **Leading-space
  count = tree depth.** e.g. `Hoffmann`(0) / ` Materialien...`(1) /
  `  Wittkop-Menardeau: Hoffmann`(2) / `   Leben und Werk`(3). No codec. Just
  read lines, count leading spaces, build the tree. DONE - clone can render the
  TOC from this alone.
- `TREE.DKA` - binary node index (LE u32 groups) linking tree lines to record
  numbers / child lists. Value 0x1757 (=count+1) recurs as a total/terminator.
  Structure: per node a small record of [childcount u16][... u32 record refs].
  Needs a bit more parsing but is small (800 bytes for Hoffmann).
- `TEXT.DKI` - **offset-indexed record store**:
  - `[0]` u32 = record count (5974 for Hoffmann).
  - then a u32 offset table, `count` entries, each = absolute file offset of a
    record. (Table is followed by other index data before the first record at
    0x67200; records are located purely by the table, so the gap does not
    matter.)
  - each **record** = `[u16 length][u16 ?][4-byte hdr ~ 00 08 00 0e][source-path
    marker: '#q:\digibib\8hoff\texte\hoff+NNN.txt'][TOKEN STREAM][trailing copy of
    the source-path marker][03]`. Record length verified: offs[1]-offs[0]=0x1ed
    matches the record's u16; record 2 (0xb2) too.

### The text codec is a TOKENIZED WORD STREAM (corrects "plaintext" guess)

The record content is NOT plain text and NOT zlib - it is a custom tokenized
encoding (this is the real "DKI codec" the FOSS decoder got wrong):
- A **word** = `<u8 len><len cp1252 bytes><0x00 terminator>`.
- Control bytes between words encode layout: `0x00` word-end, `0x01` spacing/
  formatting run markers (often in pairs `01 01`), `0x02 ..` paragraph/heading
  break (e.g. `02 02 02 00` = blank line). A 4-byte header (`19 08 03 01` in
  rec 0) precedes the first token; exact meaning TBD.
- Decoding proven: a from-scratch decoder (reports/dki_decoder_v1.py) pulls
  readable German from record 0: "Hoffmann / Werke / Ausgewaehlt von Mathias
  Bertram ... <<E.T.A. Hoffmann>> von Gabrielle Wittkop-Menardeau ... <<Der
  Sandmann>> vorgetragen von Achim Huebner ... Directmedia Berlin 1998 /
  Digitale Bibliothek Band" - i.e. the volume title page. Guillemets are
  cp1252 0xab/0xbb.
- REMAINING (polish, not mystery): exact control-code grammar for faithful
  spacing/paragraphs/headings/italics so output is clean HTML rather than
  word-joined text. Needs a few records cross-checked against the running
  Digibib5 oracle's rendered page. Best done in digibib5-mcp with a test corpus.

### TREE.DKA decoded
- Second half (from ~0x68) is a clean monotonic u32 array, **one entry per TOC
  line** (158 entries for Hoffmann, matching TREE.DKI's 158 lines). Each entry =
  that node's starting record index into TEXT.DKI. Values run 2,3,4,4,0x11,0x21,
  ... up to 0x1757 (=count+1, terminator). First ~0x68 bytes = a structural
  prefix (child-group counts + a few record refs). So: node -> record index is
  solved; the exact prefix layout is minor.
- `INDEX.{HTX,PLX,SHX,SWX,TTX,WLX}` + `LINKS.{HTX,PLX,TTX,WLX}` - search/index
  family (full-text, wordlist, etc.). Not needed for basic read/TOC/paging.
- `IMAGES\1..4\NNNN.BMP` - page images at 4 zoom levels (this volume uses plain
  BMP, not PNG/images.lib). So libpng is for OTHER volumes / UI; images here are
  BMP. Decoder must handle both per-volume.
- `SIGEL.DAT`, `VORTRAG.DAT`, `ta\CLICKS.DAT`, `COVER{1..8}.BMP` (cover art).

### Decoder implication
Minimum viable reader needs NO custom codec and NO libpng for DB008:
1. Parse DIGIBIB.TXT (INI) -> volume identity.
2. Read TREE.DKI -> indented-text TOC -> tree.
3. Parse TREE.DKA -> map each TOC node to a TEXT.DKI record index.
4. TEXT.DKI: read count + offset table; for a node's record, seek offset, read
   u16 length, skip header + source-path, take content.
5. Content encoding (plain cp1252 vs zlib-deflated) = the ONE remaining byte-level
   unknown; peek past the source-path NUL to confirm. zlib is linked so some
   volumes/records may deflate; DB008 records are small (178-493 B) so may be
   plain. Check both.

This is a weekend-sized decoder, not a research project. The earlier libpng
detour was a dead end; the format is mostly plaintext + offset tables.

## Clone plan (deferred until format is nailed)

Decision (2026-10-26): new repo **digibib5-mcp** (MCP server + SOTA webapp
reader; DKI codec as `src/digibib5_mcp/dki/` module). Reversing + oracle stay in
reversing-mcp. Build order: **finish the format first**, then the decoder, then
the clone shell. Nothing scaffolded yet.
