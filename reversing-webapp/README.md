# Reversing MCP WebApp

Next.js + TypeScript frontend and FastAPI backend for binary upload and static analysis. Interactive Ghidra decompilation is done via **ReVa MCP** in the IDE, not inside this UI.

## Features

- Next.js 14, TypeScript, Tailwind, Radix UI
- Drag-and-drop binary upload with validation
- Static analysis: file type, strings, entropy, PE
- Security-oriented summaries where implemented (entropy, basic heuristics)
- Charts / dashboards for analysis output
- FastAPI backend with hot reload (watchfiles)

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
- **React Dropzone** - File upload handling
- **Recharts** - Data visualization

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Reversing MCP** - Core analysis engine

## Quick Start

### Prerequisites

- **Node.js 18+** - Frontend runtime
- **Python 3.8+** - Backend runtime
- **Ghidra** (optional) - Advanced reverse engineering

### Installation

1. **Clone and navigate:**
   ```bash
   cd D:\Dev\repos\reversing-mcp
   ```

2. **Start everything:**
   ```powershell
   .\start-webapp.ps1
   ```

   This will:
   - Create Python virtual environment
   - Install backend dependencies
   - Install Node.js dependencies
   - Start FastAPI backend on port 10750
   - Start Next.js frontend on port 10751

   **From fleet:** run `mcp-central-docs\starts\reversing-start.bat` (same ports). Or from this folder: `start.bat` or `.\start.ps1`.

### Manual Setup (Alternative)

If you prefer manual control:

1. **Backend Setup:**
   ```powershell
   cd reversing-webapp\api
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   $env:REVERSING_API_PORT = "10750"
   python main.py
   ```
   Backend listens on 10750 (default).

2. **Frontend Setup:**
   ```powershell
   cd reversing-webapp
   npm install
   npm run dev
   ```
   Frontend runs on 10751.

## Usage

### Basic Workflow

1. **Upload Binary**: Drag and drop or browse for executable files
2. **Configure Analysis**: Select analysis tools (basic, PE, Ghidra)
3. **Start Analysis**: Click "Start Analysis" to begin processing
4. **View Results**: Explore results in the analysis dashboard

### Supported File Types

- **Executables**: `.exe`, `.dll`, `.so`, `.dylib`
- **Libraries**: `.ocx`, `.sys`, `.drv`
- **Other**: `.bin`, `.com`, `.scr`, `.cpl`

### Analysis Tools

- **File Analysis**: Basic file type detection and metadata
- **Strings Extraction**: ASCII/Unicode string extraction with encoding detection
- **Entropy Analysis**: Compression/encryption detection
- **PE Analysis**: Windows executable structure analysis
- **Ghidra**: Decompilation in the IDE via ReVa MCP; webapp may show status or proxies where configured

## API Documentation

### Backend Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /tools/status` - Available tools status
- `POST /analyze/upload` - Analyze uploaded file
- `POST /analyze/file` - Analyze file by path
- `GET /ghidra/status` - Ghidra integration status
- `GET /ghidra/functions` - List functions (Ghidra)
- `POST /ghidra/decompile` - Decompile function (Ghidra)
- `POST /ghidra/disassemble` - Disassemble function (Ghidra)

### Frontend Pages

- `/` - Homepage with overview
- `/loader` - File upload and analysis configuration
- `/analysis` - Analysis results and detailed view
- `/settings` - Ghidra configuration and tool settings

## Configuration

### Environment Variables

Create `.env.local` in the frontend directory:

```bash
# API Configuration (backend default 10750)
NEXT_PUBLIC_API_URL=http://localhost:10750

# Development
NODE_ENV=development
```

### Ghidra + ReVa MCP

1. Download and install Ghidra from NSA's official site
2. Install the **ReVa** extension (release zip matching your Ghidra version)
3. Add **ReVa** to Cursor or Claude Desktop MCP config (see parent repo `docs/GHIDRA.md`)
4. Use this webapp for static analysis; use ReVa from the IDE for decompilation

## Development

### Project Structure

```
reversing-webapp/
├── api/                    # FastAPI backend
│   ├── main.py            # Main API server
│   └── requirements.txt   # Python dependencies
├── src/
│   ├── app/               # Next.js pages
│   ├── components/        # React components
│   └── lib/               # Utilities and MCP client
├── package.json           # Node.js dependencies
└── tailwind.config.js     # Tailwind configuration
```

### Development Commands

```bash
# Frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking

# Backend
cd api
python main.py       # Start API server with hot reload
```

### Testing

```bash
# Frontend tests
npm run test
npm run test:watch
npm run test:coverage

# Backend tests (when available)
cd api
pytest
```

## Troubleshooting

### Common Issues

1. **Backend won't start:**
   - Ensure Python 3.8+ is installed
   - Check virtual environment activation
   - Verify all dependencies are installed

2. **Frontend won't start:**
   - Ensure Node.js 18+ is installed
   - Check `node_modules` installation
   - Clear `.next` cache: `Remove-Item -Recurse -Force .next`

3. **Analysis fails:**
   - Check if MCP server is running
   - Verify file permissions
   - Check console for error messages

4. **Ghidra / decompilation:**
   - Install Ghidra; add **ReVa** per parent `docs/GHIDRA.md`
   - Decompilation runs through the MCP client, not necessarily through these REST stubs

### Logs

- **Frontend**: Browser console (F12)
- **Backend**: Console output from API server
- **MCP Server**: Check reversing-mcp server logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Reversing MCP suite. See the main repository for licensing information.

## Links

- [Reversing MCP Repository](https://github.com/sandraschi/reversing-mcp)
- [Ghidra NSA](https://ghidra-sre.org/)
- [ReVa (Ghidra MCP)](https://github.com/cyberkaida/reverse-engineering-assistant)
- [FastMCP](https://fastmcp.io/)