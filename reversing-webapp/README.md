# Reversing MCP WebApp

A modern React TypeScript web application for reverse engineering analysis with Ghidra MCP integration.

## Features

- 🏗️ **Modern Architecture**: Next.js 14 with TypeScript and Tailwind CSS
- 📁 **File Upload**: Drag-and-drop binary file upload with validation
- 🔍 **Multi-Tool Analysis**: File analysis, strings extraction, entropy analysis, PE parsing
- 🐉 **Ghidra Integration**: Decompilation, disassembly, and cross-reference analysis
- 🛡️ **Security Analysis**: Malware detection, obfuscation detection, PDB analysis
- 📊 **Rich Visualizations**: Interactive charts and analysis dashboards
- 🚀 **FastAPI Backend**: REST API bridging frontend with MCP server (with hot reload)
- 🔧 **Professional UI**: Radix UI components with modern design
- ⚡ **Hot Reload**: Automatic server restart on code changes (watchfiles)

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
   - Start FastAPI backend on port 10750 (SOTA)
   - Start Next.js frontend on port 10751 (SOTA)

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
- **Ghidra Integration**: Professional decompilation and disassembly

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
# API Configuration (SOTA backend port 10750)
NEXT_PUBLIC_API_URL=http://localhost:10750

# Development
NODE_ENV=development
```

### Ghidra Setup

1. Download and install Ghidra from NSA's official site
2. Install the GhidraMCP plugin
3. Enable the HTTP server in Ghidra developer settings
4. Configure the plugin to run on port 8080

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

4. **Ghidra not available:**
   - Install Ghidra from official site
   - Install GhidraMCP plugin
   - Enable HTTP server in Ghidra settings

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
- [GhidraMCP Plugin](https://github.com/LaurieWired/GhidraMCP)
- [FastMCP](https://fastmcp.io/)