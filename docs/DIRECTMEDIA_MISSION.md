# Primary Mission: Directmedia / Digitale Bibliothek 5

## Goal

The main intent of the reversing-mcp server and webapp is to **decompile the Digitale Bibliothek 5 executable** to find out **how Directmedia files are read and expanded**.

## Target binary

- **Path (typical install):** `C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe`
- **Role:** Reader app for Directmedia “Digitale Bibliothek” (1990s e‑book/product). It reads proprietary container/data formats (e.g. DKI).
- **Objective:** Reverse the code paths that **read and expand** those Directmedia files so we can document or reimplement the format (e.g. for preservation or tooling).

## How this repo supports that

- **Ghidra (MCP + plugin):** Load `Digibib5.exe` in Ghidra, run analysis, then use `ghidra_*` tools (decompile, list functions, xrefs, rename) to locate and understand file-reading and expansion logic.
- **Binary analysis:** Strings, entropy, PE analysis to get an overview before deep dive in Ghidra.
- **Directmedia decompressor:** There is existing decompressor code in the repo, but it is **currently nonfunctional**. Reversing Digibib5.exe is needed to understand the real read/expand logic and fix or reimplement the decompressor.
- **Web UI + Ollama:** Load the binary, run analyses, and use the chat to reason about findings with a local LLM.

## Suggested workflow

1. Import `Digibib5.exe` into Ghidra (create a project, run analysis).
2. Start the GhidraMCP plugin and reversing-mcp so `ghidra_*` tools are available.
3. Use MCP/UI: list functions, search for strings related to “DKI”, “expand”, “read”, file extensions; decompile likely readers and decompressors; follow xrefs.
4. Use findings to fix or reimplement the (currently nonfunctional) Directmedia decompressor; cross-check with any known DKI layout/docs.
5. Document or implement the read/expand logic in this repo or a dedicated Directmedia tool.

## Legal / ethics

Reverse engineering for **interoperability and preservation** of abandoned software and formats is the stated use. Ensure your use complies with local law and any applicable licenses.
