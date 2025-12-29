#!/usr/bin/env python3
"""
FastAPI Backend for Reversing MCP WebApp

This API server bridges the Next.js frontend with the MCP reversing server,
providing REST endpoints for file analysis, Ghidra integration, and tool management.
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from reversing_mcp.analyzers import BinaryAnalyzer
from reversing_mcp.logging_config import get_logger

# Try to import Ghidra bridge
try:
    from reversing_mcp.bridge_mcp_ghidra import (
        list_functions, decompile_function, check_ghidra_status,
        disassemble_function, get_function_by_address
    )
    ghidra_available = True
except ImportError:
    ghidra_available = False

logger = get_logger("reversing_api")

# Global analyzer instance
analyzer = BinaryAnalyzer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Reversing MCP API server")
    yield
    logger.info("Shutting down Reversing MCP API server")

# Create FastAPI app
app = FastAPI(
    title="Reversing MCP API",
    description="REST API for reverse engineering analysis with Ghidra integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:11111", "http://127.0.0.1:11111"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisRequest(BaseModel):
    file_path: str
    tools: Optional[List[str]] = None

class GhidraStatus(BaseModel):
    available: bool
    version: Optional[str] = None
    http_server_running: bool = False
    http_port: Optional[int] = None

class AnalysisResponse(BaseModel):
    file_path: str
    file_size: int
    tools_used: List[str]
    results: Dict[str, Any]
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
        "ghidra_available": ghidra_available,
        "endpoints": [
            "/analyze/file",
            "/analyze/upload",
            "/ghidra/status",
            "/ghidra/functions",
            "/tools/status"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-12-02"}

@app.get("/tools/status")
async def get_tools_status():
    """Get status of available analysis tools"""
    try:
        # Check Ghidra status
        ghidra_status = await check_ghidra_status() if ghidra_available else {
            "available": False,
            "error": "Ghidra MCP bridge not available"
        }

        return {
            "tools": {
                "file": {"available": True, "version": "5.39"},
                "strings": {"available": True, "version": "2.6"},
                "entropy": {"available": True, "version": "1.0"},
                "pefile": {"available": True, "version": "2023.2.7"},
                "ghidra_mcp": ghidra_status
            }
        }
    except Exception as e:
        logger.error(f"Error checking tools status: {e}")
        raise HTTPException(status_code=500, detail=f"Tools status check failed: {str(e)}")

@app.post("/analyze/upload")
async def analyze_uploaded_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tools: Optional[str] = None
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
            is_obfuscated=is_obfuscated
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
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/file")
async def analyze_file_path(request: AnalysisRequest):
    """Analyze a file by path"""
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    try:
        # Analyze the file
        results = analyzer.analyze_file(request.file_path, request.tools or ["file", "strings", "entropy"])

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
            is_obfuscated=is_obfuscated
        )

        return response.dict()

    except Exception as e:
        logger.error(f"Error analyzing file {request.file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/ghidra/status")
async def get_ghidra_status():
    """Get Ghidra integration status"""
    if not ghidra_available:
        return GhidraStatus(available=False).dict()

    try:
        status = await check_ghidra_status()
        return GhidraStatus(**status).dict()
    except Exception as e:
        logger.error(f"Error checking Ghidra status: {e}")
        return GhidraStatus(available=False, error=str(e)).dict()

@app.get("/ghidra/functions")
async def get_ghidra_functions():
    """Get list of functions from Ghidra"""
    if not ghidra_available:
        raise HTTPException(status_code=503, detail="Ghidra MCP bridge not available")

    try:
        functions = await list_functions()
        return {"functions": functions, "count": len(functions) if functions else 0}
    except Exception as e:
        logger.error(f"Error getting Ghidra functions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get functions: {str(e)}")

@app.post("/ghidra/decompile")
async def decompile_ghidra_function(function_name: str):
    """Decompile a function using Ghidra"""
    if not ghidra_available:
        raise HTTPException(status_code=503, detail="Ghidra MCP bridge not available")

    try:
        code = await decompile_function(function_name)
        return {"function_name": function_name, "decompiled_code": code}
    except Exception as e:
        logger.error(f"Error decompiling function {function_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Decompilation failed: {str(e)}")

@app.post("/ghidra/disassemble")
async def disassemble_ghidra_function(address: str):
    """Disassemble a function using Ghidra"""
    if not ghidra_available:
        raise HTTPException(status_code=503, detail="Ghidra MCP bridge not available")

    try:
        asm = await disassemble_function(address)
        return {"address": address, "assembly": asm}
    except Exception as e:
        logger.error(f"Error disassembling at {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Disassembly failed: {str(e)}")

# Helper functions
def calculate_analysis_score(results: Dict[str, Any]) -> float:
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

def detect_language_hint(results: Dict[str, Any]) -> str:
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
        "javascript": ["function ", "console.log", "node.js", "npm"]
    }

    for lang, indicators in hints.items():
        if any(indicator in strings_text for indicator in indicators):
            return lang.title()

    return "Unknown"

def check_for_pdb(results: Dict[str, Any]) -> bool:
    """Check if PDB debug symbols are present"""
    strings = results.get("strings", [])
    strings_text = " ".join(str(s) for s in strings).lower()
    return "pdb" in strings_text or ".pdb" in strings_text

def check_for_obfuscation(results: Dict[str, Any]) -> bool:
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
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=11112,
        reload=True,  # Enable auto-reload for development
        reload_dirs=["."]  # Watch current directory and subdirectories
    )