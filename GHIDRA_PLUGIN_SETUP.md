# 🐉 Ghidra Plugin Setup for Reversing MCP

**OBSOLETE (2026-03-23):** This repo no longer uses LaurieWired + `bridge_mcp_ghidra.py`.
Use **ReVa** per `docs/GHIDRA.md`. Kept for historical context only.

## 🔍 **Architecture: Clear Separation**

**IMPORTANT DISTINCTION**:
- **GhidraMCP.zip**: LaurieWired's proven Ghidra plugin (we use this directly)
- **bridge_mcp_ghidra.py**: Our custom MCP server that connects to their plugin
- **server.py**: Our FastMCP 2.13+ integration with all our tools

## Problem Solved
The reversing-mcp needed reliable Ghidra integration. We use LaurieWired's excellent plugin but built our own MCP layer on top.

## Solution Architecture
**Hybrid Approach**: Their proven Java plugin + Our modern MCP integration

## Setup Steps

### 1. Install Ghidra Plugin
1. Locate the `GhidraMCP.zip` file in the reversing-mcp repository root
2. Open Ghidra
3. Go to `File` → `Install Extensions`
4. Click the `+` button
5. Select the `GhidraMCP.zip` file
6. Restart Ghidra

### 2. Enable Plugin
1. In Ghidra: `File` → `Configure` → `Developer`
2. Ensure `GhidraMCP HTTP Server` is checked/enabled

### 3. Start Ghidra with Plugin
1. Launch Ghidra normally
2. The plugin will automatically start an HTTP server on `http://127.0.0.1:8080/`
3. Load a binary file (.exe, .dll, etc.) in Ghidra for analysis

### 4. Verify Setup
```bash
# Start the reversing MCP server
python -m reversing_mcp.server

# In another terminal, check available tools
# The server will show ghidra_mcp as available
```

## 🛠️ **Available Ghidra Tools (Our MCP Wrappers)**

Once set up, you have access to **our MCP tools** that connect to **their Ghidra plugin**:

### Our MCP Tool Names (wrapping their HTTP API):
- `ghidra_decompile_function(name)` - Decompile function by name
- `ghidra_list_functions()` - List all functions in loaded binary
- `ghidra_get_function_by_address(address)` - Get function at specific address
- `ghidra_disassemble_function(address)` - Get assembly code for function
- `ghidra_list_strings()` - Extract strings with memory addresses
- `ghidra_get_xrefs_to(address)` - Find all references to an address
- `ghidra_get_xrefs_from(address)` - Find all references from an address
- `ghidra_rename_function(old, new)` - Rename a function in Ghidra
- `ghidra_set_decompiler_comment(addr, comment)` - Add comments to decompiled code

**Note**: These are **our FastMCP 2.13+ tools** that call **their Ghidra plugin's HTTP API**.

### Manual Ghidra Launch
If you prefer to use Ghidra's GUI directly (rare, since it's complex):

```bash
# Launch Ghidra GUI without any file
start_ghidra()

# Launch Ghidra and open a specific binary
start_ghidra(file_path="C:/path/to/binary.exe")

# Launch with custom project name
start_ghidra(file_path="binary.exe", project_name="my_analysis")

# Wait for Ghidra to exit (synchronous)
start_ghidra(file_path="binary.exe", wait=true)
```

The `start_ghidra` tool automatically detects your Ghidra installation and launches it with the appropriate parameters.

### Advanced Ghidra Help
For deep technical information about Ghidra's NSA origins, architecture, and expert usage:

```bash
# Complete Ghidra expertise and references
help("advanced", "ghidra")
```

This provides detailed information about Ghidra's development by the NSA, technical capabilities, integration architecture, and links to official documentation, community resources, and academic references.

## Troubleshooting

### Plugin Not Loading
- Ensure GhidraMCP.zip is not corrupted
- Check Ghidra logs for plugin loading errors
- Try reinstalling the extension

### HTTP Server Not Starting
- Check if port 8080 is available: `netstat -an | find "8080"`
- Look in Ghidra logs for server startup messages
- Try changing port in plugin settings

### MCP Can't Connect
- Verify Ghidra is running with plugin enabled
- Check that HTTP server is accessible: `curl http://127.0.0.1:8080/`
- Ensure firewall allows local connections

## 🏗️ **Architecture: Hybrid Integration**

### Three Distinct Layers:

1. **🐉 Ghidra Plugin** (Theirs - LaurieWired):
   - Java plugin that runs inside Ghidra
   - Exposes Ghidra's analysis engine via HTTP on port 8080
   - **Source**: `GhidraMCP.zip` (directly from their GitHub)

2. **🌉 Python Bridge** (Ours - Custom):
   - MCP server written in Python using FastMCP 2.13+
   - Connects to their HTTP server using `requests` library
   - **Source**: `src/reversing_mcp/bridge_mcp_ghidra.py` (our code)

3. **⚡ MCP Integration** (Ours - Custom):
   - Imports our bridge and exposes tools via FastMCP
   - Adds our other reverse engineering tools (strings, entropy, etc.)
   - **Source**: `src/reversing_mcp/server.py` (our integration)

### Why This Hybrid Approach?
- **Their plugin is excellent** - no need to reinvent the HTTP server
- **MCP standards evolved** - we needed FastMCP 2.13+ compatibility
- **Reliability** - HTTP bridge is more stable than Ghidra's headless mode
- **Extensibility** - We can add our own tools alongside Ghidra

### Data Flow:
```
User → Our MCP Server → Our Bridge → HTTP → Their Ghidra Plugin → Ghidra Analysis
```