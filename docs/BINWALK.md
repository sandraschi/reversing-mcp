# binwalk Integration

[binwalk](https://github.com/ReFirmLabs/binwalk) scans a file for embedded files and known
signatures (compressed streams, filesystems, images, executables). Useful when a data file
(for example a Directmedia `.DKI`) might be a container of known formats.

**Status:** implemented but **unverified on the dev host** (binwalk is not installed on
Goliath).

---

## 1. What works

| Operation | MCP tool | Command run | Returns |
|-----------|----------|-------------|---------|
| Detection | `check_tools()` | `binwalk --version` | version string |
| Signature scan | `analyze_binary(file)` (in the default tool set) or `analyze_binary(file, ['binwalk'])` | `binwalk -J <file>` | parsed JSON as `signatures`, else `raw_output` |

Timeout 30 s (detection 5 s). Code: `src/reversing_mcp/analyzers.py` (`_check_binwalk`,
`_analyze_with_binwalk`).

## 2. Install

binwalk exists in two lines:

* **v3 (Rust rewrite)** - current upstream. Prebuilt binaries / `cargo install binwalk`.
* **v2 (Python)** - legacy, `pip install binwalk`; many extractors assume Linux.

Either way, put `binwalk` on `PATH` and restart the backend.

## 3. Known doubts (check on first real run)

* **The `-J` flag.** The code assumes `-J` produces JSON on stdout. Flag meanings differ between
  v2 and v3, so on a real install check `binwalk --help` first. If JSON goes to a file instead
  of stdout, `_analyze_with_binwalk` needs to pass an output path and read it back. If the scan
  "succeeds" with only `raw_output`, this is why.
* **Extraction** (`-e`) is not wired; only the scan is.
* REA's firmware path also uses binwalk/unblob and expects Linux - see [REA.md](REA.md).

## 4. References

* Engine overview: [ENGINES.md](ENGINES.md)
