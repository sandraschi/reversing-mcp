# Feature-to-code map (static v1): Digibib5.exe

Target: `tests\fixtures\exe files\Digibib5.exe` (4,695,552 bytes)
Generated: 2026-10-11T11:00:15+00:00
Method: seed-string correlation (static only; no live tour yet)

## Seeds

### `DKI` — 7 hit(s)

- `0x1327F1` [ascii] Text.dki
- `0x134CD1` [ascii] Data\Text.dki
- `0x135102` [ascii] Data\Tree.dki
- `0x135A48` [ascii] data\text.dki
- `0x135A70` [ascii] data\tree.dki
- `0x13626B` [ascii] tree.dki
- `0x13692D` [ascii] text.dki

### `TEXT.DKI` — 4 hit(s)

- `0x1327F1` [ascii] Text.dki
- `0x134CD1` [ascii] Data\Text.dki
- `0x135A48` [ascii] data\text.dki
- `0x13692D` [ascii] text.dki

### `decompress` — 4 hit(s)

- `0x16ED35` [ascii] TZDecompressionStream
- `0x16EE36` [ascii] EZDecompressionError@
- `0x1E09F4` [ascii] Decompression error
- `0x1E16AA` [ascii] Decompression Error

### `expand` — 85 hit(s)

- `0x5F073` [ascii] DXNAVBARADVEXPLORERBAREXPANDSIGN
- `0x5F2C4` [ascii] DXNAVBAROFFICE11EXPANDSIGN
- `0x66AFF` [ascii] Expandable
- `0x66B21` [ascii] Expanded
- `0x66C3E` [ascii] ShowExpandButtonT
- `0x66E92` [ascii] OnExpanded
- `0x6D9E4` [ascii] Expanded
- `0x6DA84` [ascii] ShowExpandButton
- `0x6E5F6` [ascii] Expanded
- `0x6E6A6` [ascii] ShowExpandButton
- `0x6F2A9` [ascii] TMyNavBarCollapsedExpandedEvent
- `0x6F4BF` [ascii] OnCollapsedExpandedSVt
- `0x77353` [ascii] TCustomMenuExpandBtn@
- `0x7736D` [ascii] TCustomMenuExpandBtnL
- `0x77F5B` [ascii] ExpandDelay@B
- `0xEF251` [ascii] ivsExpanded
- `0xEF93E` [ascii] toAutoDropExpand
- `0xEF94F` [ascii] toAutoExpand
- `0xEF969` [ascii] toAutoScrollOnExpand
- `0xF0F04` [ascii] tsExpanding
- `0xF4C88` [ascii] AutoExpandDelay
- `0xF5A87` [ascii] OnExpandedmZ
- `0xF5AA7` [ascii] OnExpandingqZ
- `0xFD863` [ascii] voAutoDropExpand
- `0xFD874` [ascii] voAutoExpand
- …and 60 more (see tool output for full list).

### `ReadFile` — 2 hit(s)

- `0x21C299` [ascii] ReadFile
- `0x21C693` [ascii] ReadFile

### `TForm` — 66 hit(s)

- `0x49412` [ascii] TFormBorderStyle
- `0x4A4CC` [ascii] TFormStyle
- `0x4AB65` [ascii] TForm
- `0x4AB6F` [ascii] TForm
- `0xC03CA` [ascii] TForm
- `0xC980B` [ascii] TForm
- `0xEFD97` [ascii] TFormatEtcArray
- `0xEFDC5` [ascii] TFormatArray
- `0xF2D4F` [ascii] TFormatArray
- `0xF2E97` [ascii] TFormatEtcArray
- `0x12ACAA` [ascii] TWaitForm
- `0x12ACC0` [ascii] TWaitForm<`
- `0x137745` [ascii] ExportFormat
- `0x13776E` [ascii] ExportFormat
- `0x1418DE` [ascii] WSAWaitForMultipleEvents
- `0x15C621` [ascii] THintForm
- `0x15C633` [ascii] THintFormle
- `0x15EF5D` [ascii] TFormControlList@
- `0x160B22` [ascii] TFormSubmitEvent
- `0x1610E3` [ascii] TFormControlObj~f
- `0x16124E` [ascii] TEditFormControlObjf
- `0x161D89` [ascii] TFormRadioButtonTf
- `0x161D9E` [ascii] TFormRadioButtonTf
- `0x161EB2` [ascii] TFormCheckBoxf
- `0x161EC3` [ascii] TFormCheckBoxf
- …and 41 more (see tool output for full list).

### `CreateFile` — 3 hit(s)

- `0x21C2FD` [ascii] CreateFileA
- `0x21CC09` [ascii] CreateFileMappingA
- `0x21CC1F` [ascii] CreateFileA

## Functions

- No engine answered ([WinError 2] The system cannot find the file specified).
  Verdict: code refs pending — rerun with Ghidra/REA or after a live tour.

## Verdict key

- mapped: seed has offsets above; next step is xrefs/decompile per hit.
- unmapped statically: needs a live tour (behavioral evidence) or an engine.
