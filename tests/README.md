# Reverse Engineering Pipeline Tests

This test suite validates the complete reverse engineering pipeline using **compilation-decompilation-comparison** methodology.

## 🎯 Test Strategy

The tests follow this methodology:
1. **Compile** source code fixtures into binaries
2. **Decompile** binaries using reversing tools (Ghidra, radare2)
3. **Compare** decompiled output to original source code
4. **Validate** that key information is preserved

## 🧪 Test Fixtures

### Source Code Fixtures (Compiled to Binaries)

| Fixture | Language | Description | Expected Functions | Expected Strings |
|---------|----------|-------------|-------------------|------------------|
| `hello_world.c` | C | Simple Hello World | `main` | "Hello, World!" |
| `simple_math.c` | C | Functions + arithmetic | `main`, `add_numbers`, `multiply_numbers` | "Sum:", "Product:" |
| `data_structures.c` | C | Structs, memory, loops | `main`, `create_employee`, `print_employee`, `calculate_bonus` | "Name:", "Age:", "Salary:", "Bonus:" |
| `simple_asm.asm` | Assembly | x86 assembly program | `_start` | "Hello from assembly!" |

### Binary Test Fixtures (Ready-to-Use)

| Fixture | Type | Size | Description | Expected Analysis |
|---------|------|------|-------------|------------------|
| `minimal.com` | COM | 23 bytes | Minimal DOS COM file | Simple DOS program |
| `hello.com` | COM | 35 bytes | Hello World COM | Prints message |
| `loop.com` | COM | 28 bytes | Infinite loop | Demonstrates disassembly |
| `test_pe.exe` | PE | ~2KB | Minimal Windows PE | Standard PE structure |
| `packed_test.bin` | Raw | 1KB | Packed/compressed data | Entropy analysis |

### Dangerous Test Fixtures (Educational Only)

Located in `tests/fixtures/dangerous/` - these demonstrate malware analysis techniques:

| Fixture | Description | Analysis Focus |
|---------|-------------|----------------|
| `filesystem_suspicious.c` | Registry manipulation, hidden files | API hooking, persistence |
| `network_suspicious.c` | Suspicious network connections | C2 communications, data exfil |
| `obfuscated_malware.c` | String obfuscation, anti-debugging | Deobfuscation techniques |
| `packed_executable.c` | Runtime unpacking simulation | Packers, protectors |

## 🚀 Running Tests

### Prerequisites
- Python 3.10+
- GCC compiler (for C programs) - **Note: Not available on Windows by default**
- NASM + LD (for assembly programs, optional)
- MinGW or Visual Studio Build Tools recommended for Windows

### Install Dependencies
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Or install from pyproject.toml
pip install -e ".[dev]"
```

### Run All Tests
```bash
# Comprehensive test suite (NEW - recommended)
python tests/comprehensive_test_runner.py --coverage --verbose

# Original test runner
python tests/run_tests.py

# Pytest directly
python -m pytest tests/
```

### Run Specific Tests
```bash
# Comprehensive test runner options
python tests/comprehensive_test_runner.py --unit-only          # Unit tests only
python tests/comprehensive_test_runner.py --integration-only   # Integration tests only
python tests/comprehensive_test_runner.py --fixtures-only      # Binary fixtures only
python tests/comprehensive_test_runner.py --performance-only   # Performance tests only

# Original test runner options
python tests/run_tests.py --compile-only    # Compilation tests only
python tests/run_tests.py --fixture hello_world.c  # Specific fixture
python tests/run_tests.py --verbose         # Verbose output
python tests/run_tests.py --coverage        # With coverage
```

### List Available Fixtures
```bash
python tests/run_tests.py --fixtures
```

## 🏗️ Test Architecture

### Test Classes
- `ReverseEngineeringTestFixture`: Manages test fixtures and configuration
- `BinaryAnalyzer`: Performs analysis using reversing tools

### Test Categories
- **compilation**: Tests that source code can be compiled
- **analysis**: Tests that binaries can be analyzed
- **validation**: Tests that analysis results contain expected information

### Configuration
Test configuration is in `tests/fixtures/test_config.json`:
```json
{
  "fixtures": {
    "hello_world.c": {
      "language": "c",
      "compiler": "gcc",
      "compile_args": ["-o", "hello_world.exe"],
      "expected_strings": ["Hello, World!"],
      "expected_functions": ["main"]
    }
  }
}
```

## 📊 Test Results

Tests validate:
- ✅ **Compilation Success**: Source code compiles without errors
- ✅ **Binary Analysis**: Binaries can be analyzed by reversing tools
- ✅ **String Extraction**: Expected strings are found in binary
- ✅ **Function Detection**: Functions are identified in analysis
- ✅ **Information Preservation**: Key source code information is preserved

## 🛠️ Adding New Fixtures

1. Add source file to `tests/fixtures/`
2. Update `test_config.json` with compilation settings
3. Specify expected strings and functions
4. Run tests to verify

Example:
```c
// tests/fixtures/my_test.c
#include <stdio.h>

void my_function(int x) {
    printf("Value: %d\n", x);
}

int main() {
    my_function(42);
    return 0;
}
```

```json
// Add to test_config.json
"my_test.c": {
  "language": "c",
  "compiler": "gcc",
  "compile_args": ["-o", "my_test.exe"],
  "expected_strings": ["Value:"],
  "expected_functions": ["main", "my_function"]
}
```

## 🔍 Debugging Tests

### Common Issues
- **Compilation fails**: Check that GCC/NASM is installed and in PATH
- **Analysis empty**: Check that reversing tools are properly configured
- **String not found**: Strings might be encoded differently in binary

### Debug Commands
```bash
# Test compilation manually
cd tests/fixtures
gcc -o hello_world.exe hello_world.c

# Test analysis manually
python -c "
from reversing_mcp.analyzers import BinaryAnalyzer
analyzer = BinaryAnalyzer()
result = analyzer.analyze_file('build/hello_world.exe', ['strings'])
print(result)
"
```

## 📈 Coverage

Run tests with coverage:
```bash
python tests/run_tests.py --coverage
```

Coverage report will be generated in `htmlcov/` directory.

## 🤝 Contributing

When adding new test fixtures:
1. Follow the naming convention: `{name}.{extension}`
2. Add comprehensive expected results
3. Test on multiple platforms if possible
4. Update this README

## 🎯 Why This Matters

These tests ensure that:
- **Reverse engineering tools work correctly**
- **Analysis results are reliable and accurate**
- **New tool versions don't break functionality**
- **Complex analysis pipelines are validated end-to-end**

This methodology provides confidence that the reversing MCP can reliably analyze real-world binaries and extract meaningful information for reverse engineering tasks.
