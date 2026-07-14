# reversing-mcp (MCPB Bundle)

MCP server for static binary analysis and Directmedia tools (companion to ReVa for Ghidra MCP)

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "reversing-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "reversing_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **analyze_binary**: analyze_binary
- **extract_strings**: extract_strings
- **get_hexdump**: get_hexdump
- **analyze_entropy**: analyze_entropy
- **find_functions**: find_functions
- **get_file_info**: get_file_info
- **check_tools**: check_tools
- **digibib_research_snapshot**: digibib_research_snapshot
- **analyze_pe_file**: analyze_pe_file
- **decode_dki_file**: decode_dki_file
- **analyze_directmedia_file**: analyze_directmedia_file
- **decompress_directmedia_library**: decompress_directmedia_library
- **help**: help
- **_health**: _health
- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)

## Requirements

- Python 3.12+
- uv
