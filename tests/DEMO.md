# Reverse engineering pipeline tests — demo

Demonstrates the **compilation–decompilation–comparison** workflow used in this repo.

## Commands

### List fixtures

```bash
python tests/run_tests.py --fixtures
```

### Smoke tests (no compiler required)

```bash
pytest tests/test_reverse_engineering_pipeline.py::test_fixture_discovery tests/test_reverse_engineering_pipeline.py::test_analyzer_initialization -v
```

### Compilation pipeline (needs GCC)

```bash
pytest tests/test_reverse_engineering_pipeline.py::test_compilation_pipeline -v
```

## Flow

```
Source (.c, .asm) → compiler → binary
       → analysis (Ghidra, strings, entropy, …)
       → compare results to expectations where defined
```

## Fixtures (summary)

| Fixture | Role |
|---------|------|
| `hello_world.c` | Minimal C |
| `simple_math.c` | Multiple functions |
| `data_structures.c` | Structs / allocation |
| `simple_asm.asm` | Assembly sample |

See [README.md](README.md) in this folder for full tables and Windows compiler notes.

## Purpose

End-to-end checks that the analyzer and pipeline behave plausibly on compiled fixtures and catch regressions when tools or code change.
