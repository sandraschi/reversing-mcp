#!/usr/bin/env python3
"""
FastAPI Backend for Reversing MCP WebApp (FastMCP 3.1 single-backend pattern).

Serves REST (analysis, Ghidra, LLM, chat) and mounts MCP at /mcp.
"""

import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path for imports
_repo_root = Path(__file__).resolve().parent.parent.parent
_src = _repo_root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from reversing_mcp.analyzers import BinaryAnalyzer
from reversing_mcp.logging_config import get_logger

logger = get_logger("reversing_api")

# Ghidra MCP: use ReVa (reverse-engineering-assistant) in your MCP client — not this HTTP API.
REVERSING_MCP_GHIDRA_NOTE = (
    "Ghidra MCP is provided by ReVa; connect it in Cursor/Claude. "
    "This API no longer proxies LaurieWired GhidraMCP. See docs/GHIDRA.md."
)

# Global analyzer instance
analyzer = BinaryAnalyzer()

# Ollama: base URL and selected model (in-memory state)
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_selected_ollama_model: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Reversing MCP API server")
    yield
    logger.info("Shutting down Reversing MCP API server")


# Create FastAPI app
app = FastAPI(
    title="Reversing MCP API",
    description="REST API for static RE analysis; Ghidra MCP via ReVa separately",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10751",
        "http://127.0.0.1:10751",
        "http://localhost:11111",
        "http://127.0.0.1:11111",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount FastMCP 3.1 at /mcp (single-backend pattern)
try:
    from reversing_mcp.server import mcp

    app.mount("/mcp", mcp.http_app())
    logger.info("MCP mounted at /mcp (FastMCP 3.1)")
except Exception as e:
    logger.warning("Could not mount MCP: %s", e)


# Pydantic models
class AnalysisRequest(BaseModel):
    file_path: str
    tools: list[str] | None = None


class GhidraStatus(BaseModel):
    available: bool
    installed: bool = False  # Ghidra binary found on disk
    version: str | None = None
    http_server_running: bool = False
    http_port: int | None = None


class AnalysisResponse(BaseModel):
    file_path: str
    file_size: int
    tools_used: list[str]
    results: dict[str, Any]
    analysis_score: float
    language_hint: str
    entropy_score: float
    functions: int
    strings: int
    has_pdb: bool
    is_obfuscated: bool


# Routes
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Reversing MCP API Server",
        "version": "1.0.0",
        "ghidra_mcp": REVERSING_MCP_GHIDRA_NOTE,
        "endpoints": [
            "/analyze/file",
            "/analyze/upload",
            "/ghidra/status",
            "/ghidra/functions",
            "/tools/status",
            "/llm/list_providers",
            "/llm/list_models",
            "/llm/select_model",
            "/llm/load_model",
            "/llm/unload_model",
            "/llm/status",
            "/llm/health",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-12-02"}


@app.get("/tools/status")
async def get_tools_status():
    """Get status of available analysis tools"""
    try:
        ghidra_bin = analyzer.check_available_tools().get("ghidra", {})
        ghidra_status = {
            "available": False,
            "installed": bool(ghidra_bin.get("available")),
            "version": ghidra_bin.get("version"),
            "note": REVERSING_MCP_GHIDRA_NOTE,
        }

        return {
            "tools": {
                "file": {"available": True, "version": "5.39"},
                "strings": {"available": True, "version": "2.6"},
                "entropy": {"available": True, "version": "1.0"},
                "pefile": {"available": True, "version": "2023.2.7"},
                "ghidra_mcp": ghidra_status,
            }
        }
    except Exception as e:
        logger.error(f"Error checking tools status: {e}")
        raise HTTPException(status_code=500, detail=f"Tools status check failed: {e!s}")


@app.post("/analyze/upload")
async def analyze_uploaded_file(
    background_tasks: BackgroundTasks, file: UploadFile = File(...), tools: str | None = None
):
    """Analyze an uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Parse tools parameter
    tool_list = tools.split(",") if tools else ["file", "strings", "entropy"]

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Analyze the file
        results = analyzer.analyze_file(temp_file_path, tool_list)

        # Calculate analysis metrics
        analysis_score = calculate_analysis_score(results)
        language_hint = detect_language_hint(results)
        entropy_score = results.get("entropy_analysis", {}).get("overall_entropy", 0.0)
        functions = len(results.get("functions", []))
        strings = len(results.get("strings", []))
        has_pdb = check_for_pdb(results)
        is_obfuscated = check_for_obfuscation(results)

        response = AnalysisResponse(
            file_path=file.filename,
            file_size=len(content),
            tools_used=tool_list,
            results=results,
            analysis_score=analysis_score,
            language_hint=language_hint,
            entropy_score=entropy_score,
            functions=functions,
            strings=strings,
            has_pdb=has_pdb,
            is_obfuscated=is_obfuscated,
        )

        # Clean up temp file in background
        background_tasks.add_task(os.unlink, temp_file_path)

        return response.dict()

    except Exception as e:
        # Clean up temp file on error
        try:
            os.unlink(temp_file_path)
        except:
            pass

        logger.error(f"Error analyzing uploaded file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}")


@app.post("/analyze/file")
async def analyze_file_path(request: AnalysisRequest):
    """Analyze a file by path"""
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    try:
        # Analyze the file
        results = analyzer.analyze_file(
            request.file_path, request.tools or ["file", "strings", "entropy"]
        )

        # Calculate analysis metrics
        analysis_score = calculate_analysis_score(results)
        language_hint = detect_language_hint(results)
        entropy_score = results.get("entropy_analysis", {}).get("overall_entropy", 0.0)
        functions = len(results.get("functions", []))
        strings = len(results.get("strings", []))
        has_pdb = check_for_pdb(results)
        is_obfuscated = check_for_obfuscation(results)

        response = AnalysisResponse(
            file_path=request.file_path,
            file_size=os.path.getsize(request.file_path),
            tools_used=request.tools or ["file", "strings", "entropy"],
            results=results,
            analysis_score=analysis_score,
            language_hint=language_hint,
            entropy_score=entropy_score,
            functions=functions,
            strings=strings,
            has_pdb=has_pdb,
            is_obfuscated=is_obfuscated,
        )

        return response.dict()

    except Exception as e:
        logger.error(f"Error analyzing file {request.file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}")


@app.post("/start_ghidra")
async def start_ghidra():
    """Legacy endpoint: launch Ghidra from the desktop; use ReVa MCP for agentic Ghidra."""
    return {
        "ok": True,
        "message": (
            "Start Ghidra from the desktop if you need the GUI. "
            "For MCP decompilation and analysis, add ReVa to your MCP client (see docs/GHIDRA.md)."
        ),
    }


@app.get("/ghidra/status")
async def get_ghidra_status():
    """Ghidra binary detection only; MCP/plugin status lives in ReVa."""
    installed = False
    version = None
    try:
        tools = analyzer.check_available_tools()
        g = tools.get("ghidra", {}) if tools else {}
        installed = bool(g.get("available"))
        version = g.get("version")
    except Exception:
        pass

    return GhidraStatus(
        available=False,
        installed=installed,
        version=version,
        http_server_running=False,
        http_port=None,
    ).dict() | {"note": REVERSING_MCP_GHIDRA_NOTE}


@app.get("/ghidra/functions")
async def get_ghidra_functions():
    """Deprecated: use ReVa MCP for Ghidra function lists."""
    raise HTTPException(status_code=503, detail=REVERSING_MCP_GHIDRA_NOTE)


@app.post("/ghidra/decompile")
async def decompile_ghidra_function(function_name: str):
    """Deprecated: use ReVa MCP for decompilation."""
    raise HTTPException(status_code=503, detail=REVERSING_MCP_GHIDRA_NOTE)


@app.post("/ghidra/disassemble")
async def disassemble_ghidra_function(address: str):
    """Deprecated: use ReVa MCP for disassembly."""
    raise HTTPException(status_code=503, detail=REVERSING_MCP_GHIDRA_NOTE)


# --- Ollama (local LLM) helpers ---
async def _ollama_tags() -> dict:
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{OLLAMA_BASE}/api/tags")
        r.raise_for_status()
        return r.json()


# LLM Management Endpoints (Ollama: list/select, status, health)
@app.post("/llm/list_providers")
async def list_llm_providers():
    """List available LLM providers (Ollama for local stack)."""
    return {"providers": [{"id": "ollama", "name": "Ollama"}]}


class LLMProviderBody(BaseModel):
    provider: str = "ollama"


class LLMSelectBody(BaseModel):
    provider: str = "ollama"
    model: str = ""


@app.post("/llm/list_models")
async def list_llm_models(body: LLMProviderBody | None = None):
    """List models for Ollama (GET /api/tags)."""
    provider = body.provider if body else "ollama"
    if provider != "ollama":
        return {"models": []}
    try:
        data = await _ollama_tags()
        models = [m.get("name", m.get("model", "")) for m in data.get("models", [])]
        return {"models": models}
    except Exception as e:
        logger.error("Ollama list_models: %s", e)
        return {"models": [], "error": str(e)}


@app.post("/llm/select_model")
async def select_llm_model(body: LLMSelectBody | None = None):
    """Select Ollama model for chat."""
    global _selected_ollama_model
    if not body:
        body = LLMSelectBody()
    provider = body.provider
    model = body.model
    if provider == "ollama" and model:
        _selected_ollama_model = model
    return {"ok": True, "provider": provider, "model": model}


@app.post("/llm/load_model")
async def load_llm_model(body: LLMSelectBody | None = None):
    """Ollama loads on first use; we just select."""
    return await select_llm_model(body)


@app.post("/llm/unload_model")
async def unload_llm_model(body: dict | None = None):
    """Ollama has no unload; clear selection."""
    global _selected_ollama_model
    _selected_ollama_model = None
    return {"ok": True}


@app.post("/llm/status")
async def get_llm_status():
    """Current Ollama selection and health."""
    try:
        await _ollama_tags()
        healthy = True
    except Exception:
        healthy = False
    return {
        "provider": "ollama",
        "model": _selected_ollama_model,
        "healthy": healthy,
        "base_url": OLLAMA_BASE,
    }


@app.post("/llm/health")
async def check_llm_health(body: LLMProviderBody | None = None):
    """Check Ollama reachability."""
    provider = body.provider if body else "ollama"
    if provider != "ollama":
        return {"healthy": False, "error": "Unknown provider"}
    try:
        await _ollama_tags()
        return {"healthy": True, "provider": "ollama"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


# Chat (Ollama)
class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Send message to selected Ollama model; returns reply."""
    import httpx

    model = _selected_ollama_model or "llama2"
    messages = [{"role": "user", "content": request.message}]
    for h in request.history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_BASE}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "")
            return {"reply": reply, "model": model}
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=502, detail=f"Ollama chat failed: {e!s}")


# Helper functions
def calculate_analysis_score(results: dict[str, Any]) -> float:
    """Calculate a completeness score for the analysis"""
    score = 0.0
    max_score = 100.0

    # File analysis (20 points)
    if "file_info" in results:
        score += 20

    # Strings analysis (20 points)
    if "strings" in results and len(results["strings"]) > 0:
        score += 20

    # Entropy analysis (20 points)
    if "entropy_analysis" in results:
        score += 20

    # PE analysis (20 points)
    if "pe_analysis" in results:
        score += 20

    # Functions analysis (20 points)
    if "functions" in results and len(results["functions"]) > 0:
        score += 20

    return min(score, max_score)


def detect_language_hint(results: dict[str, Any]) -> str:
    """Detect programming language hints from analysis"""
    strings = results.get("strings", [])
    strings_text = " ".join(str(s) for s in strings).lower()

    hints = {
        "c/c++": ["printf", "scanf", "malloc", "free", "iostream", "std::"],
        "python": ["import ", "def ", "class ", "python", "pip"],
        "java": ["java", "public static void main", "system.out", "import java"],
        "csharp": ["using system", "console.writeline", "namespace", ".net"],
        "go": ["package main", "import (", "fmt.printf", "golang"],
        "rust": ["fn main", "println!", "cargo", "rust"],
        "javascript": ["function ", "console.log", "node.js", "npm"],
    }

    for lang, indicators in hints.items():
        if any(indicator in strings_text for indicator in indicators):
            return lang.title()

    return "Unknown"


def check_for_pdb(results: dict[str, Any]) -> bool:
    """Check if PDB debug symbols are present"""
    strings = results.get("strings", [])
    strings_text = " ".join(str(s) for s in strings).lower()
    return "pdb" in strings_text or ".pdb" in strings_text


def check_for_obfuscation(results: dict[str, Any]) -> bool:
    """Check for signs of obfuscation"""
    entropy = results.get("entropy_analysis", {}).get("overall_entropy", 0.0)
    strings = results.get("strings", [])

    # High entropy may indicate encryption/obfuscation
    if entropy > 7.5:
        return True

    # Very few strings may indicate stripping/obfuscation
    if len(strings) < 3:
        return True

    # Check for obfuscation indicators in strings
    strings_text = " ".join(str(s) for s in strings).lower()
    obfuscation_indicators = ["obfuscated", "packed", "encrypted", "compressed"]
    if any(indicator in strings_text for indicator in obfuscation_indicators):
        return True

    return False


if __name__ == "__main__":
    import os

    import uvicorn

    _port = int(os.environ.get("REVERSING_API_PORT", "10750"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=_port,
        reload=True,  # Enable auto-reload for development
        reload_dirs=[
            ".",  # Watch API directory
            "../../src",  # Watch core logic in src directory
        ],
    )
