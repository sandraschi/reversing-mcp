#!/usr/bin/env python3
"""
Reverse Engineering WebApp Demo

A web interface to demonstrate the reversing MCP capabilities,
including the dangerous test fixtures that trigger malware alerts.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reversing_mcp.analyzers import BinaryAnalyzer

app = Flask(__name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static"))

# Initialize analyzer
analyzer = BinaryAnalyzer()

# Load test fixtures info
fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
config_file = fixtures_dir / "test_config.json"

def load_fixtures_config():
    """Load test fixtures configuration"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"fixtures": {}}

fixtures_config = load_fixtures_config()

@app.route('/')
def index():
    """Main page showing available test fixtures"""
    fixtures = []
    for name, config in fixtures_config.get("fixtures", {}).items():
        fixtures.append({
            "name": name,
            "description": config.get("description", ""),
            "language": config.get("language", ""),
            "dangerous": "dangerous" in name,
            "suspicious_patterns": config.get("suspicious_patterns", [])
        })

    return render_template('index.html', fixtures=fixtures)

@app.route('/analyze', methods=['POST'])
def analyze_file():
    """Analyze an uploaded file or test fixture"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save uploaded file temporarily
        temp_path = Path(app.root_path) / "temp"
        temp_path.mkdir(exist_ok=True)
        file_path = temp_path / file.filename
        file.save(str(file_path))

        # Analyze the file
        analysis_result = analyzer.analyze_file(str(file_path), ["static", "strings", "entropy"])

        # Clean up
        file_path.unlink(missing_ok=True)

        # Format response
        response = {
            "filename": file.filename,
            "file_size": analysis_result.get("file_info", {}).get("size_bytes", 0),
            "file_type": analysis_result.get("file_info", {}).get("file_type", "Unknown"),
            "is_executable": analysis_result.get("file_info", {}).get("is_executable", False),
            "strings_found": len(analysis_result.get("strings", [])),
            "sample_strings": analysis_result.get("strings", [])[:10],  # First 10 strings
            "entropy_analysis": analysis_result.get("entropy_analysis", {}),
            "alerts": []
        }

        # Check for malware indicators
        strings_content = " ".join(analysis_result.get("strings", [])).lower()

        malware_indicators = {
            "🚨 MALWARE ALERT! 🚨": [
                "blofeld.org", "evil.", "malware", "trojan", "virus", "exploit"
            ],
            "🔗 Network Suspicion": [
                "connect", "socket", "wget", "curl", "download", "http://", "https://"
            ],
            "📁 File System Suspicion": [
                "system32", "hidden", "registry", "hkey", "delete", "overwrite"
            ],
            "💉 Process Manipulation": [
                "inject", "virtualalloc", "writeprocessmemory", "createremotethread"
            ],
            "🛡️ Anti-Analysis Techniques": [
                "debugger", "timing", "obfuscate", "encrypt", "decrypt", "polymorphic"
            ],
            "📦 Packer Indicators": [
                "upx", "packer", "compressed", "decompress", "unpack"
            ]
        }

        detected_alerts = []
        for alert_type, indicators in malware_indicators.items():
            for indicator in indicators:
                if indicator in strings_content:
                    if alert_type not in detected_alerts:
                        detected_alerts.append(alert_type)
                    break

        if detected_alerts:
            response["alerts"] = detected_alerts
            response["status"] = "⚠️ SUSPICIOUS FILE DETECTED"
        else:
            response["status"] = "✅ Analysis Complete"

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/test-fixture/<fixture_name>')
def analyze_test_fixture(fixture_name):
    """Analyze a built-in test fixture"""
    if fixture_name not in fixtures_config.get("fixtures", {}):
        return jsonify({"error": "Fixture not found"}), 404

    try:
        # Simulate analysis of the fixture (in real implementation, would compile and analyze)
        config = fixtures_config["fixtures"][fixture_name]

        # Mock analysis result based on config
        mock_result = {
            "filename": fixture_name,
            "file_size": 24576,  # Mock size
            "file_type": "PE32 executable (console) Intel 80386, for MS Windows",
            "is_executable": True,
            "strings_found": len(config.get("expected_strings", [])),
            "sample_strings": config.get("expected_strings", [])[:10],
            "entropy_analysis": {
                "overall_entropy": 6.85,
                "compressed_regions": [{"offset": 4096, "length": 8192}],
                "random_regions": []
            },
            "alerts": [],
            "status": "✅ Test Fixture Analysis"
        }

        # Add malware alerts for dangerous fixtures
        if "dangerous" in fixture_name:
            mock_result["alerts"] = [
                "🚨 MALWARE ALERT! 🚨",
                f"This simulates: {config.get('description', 'dangerous behavior')}"
            ]
            mock_result["status"] = "⚠️ MALWARE SIMULATION DETECTED"

            # Add specific alerts based on suspicious patterns
            for pattern in config.get("suspicious_patterns", []):
                if pattern == "network_connections":
                    mock_result["alerts"].append("🔗 Network connections detected")
                elif pattern == "suspicious_domains":
                    mock_result["alerts"].append("🌐 Suspicious domain connections detected")
                elif pattern == "downloads":
                    mock_result["alerts"].append("📥 Suspicious download operations detected")
                elif pattern == "filesystem_manipulation":
                    mock_result["alerts"].append("📁 File system manipulation detected")
                elif pattern == "anti_debugging":
                    mock_result["alerts"].append("🛡️ Anti-debugging techniques detected")
                elif pattern == "packer_signatures":
                    mock_result["alerts"].append("📦 Packer signatures detected")

        return jsonify(mock_result)

    except Exception as e:
        return jsonify({"error": f"Fixture analysis failed: {str(e)}"}), 500

@app.route('/cdc-demo')
def cdc_demo():
    """Compilation-Decompilation-Comparison demonstration"""
    return render_template('cdc_demo.html')

if __name__ == '__main__':
    print("🚀 Starting Reverse Engineering WebApp Demo")
    print("📁 Visit http://localhost:5000 to explore the interface")
    print("🧪 Test fixtures include 'dangerous' malware simulations")
    print("🔍 Upload files or analyze built-in test cases")
    app.run(debug=True, host='0.0.0.0', port=5000)





