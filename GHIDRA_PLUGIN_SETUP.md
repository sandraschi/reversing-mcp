# Ghidra Plugin Setup for Reversing MCP

## Problem
The reversing-mcp was unable to find and execute Ghidra for exe file analysis.

## Solution
We've integrated the proven GhidraMCP plugin architecture from the directmedia-mcp project.

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

## Available Ghidra Tools

Once set up, you have access to these Ghidra analysis tools:

- `ghidra_decompile_function(name)` - Decompile function by name
- `ghidra_list_functions()` - List all functions
- `ghidra_get_function_by_address(address)` - Get function at address
- `ghidra_disassemble_function(address)` - Get assembly code
- `ghidra_list_strings()` - Extract strings with addresses
- `ghidra_get_xrefs_to(address)` - Find references to address
- `ghidra_get_xrefs_from(address)` - Find references from address
- `ghidra_rename_function(old, new)` - Rename functions
- `ghidra_set_decompiler_comment(addr, comment)` - Add comments

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

## Architecture

The integration uses:
1. **Ghidra Plugin**: Java plugin that exposes Ghidra's analysis engine via HTTP
2. **Python Bridge**: MCP server that connects to the Ghidra HTTP server
3. **MCP Tools**: FastMCP-compatible tools for reverse engineering operations

This approach is much more reliable than Ghidra's headless mode and provides full access to Ghidra's analysis capabilities.