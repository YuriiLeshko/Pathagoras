# Right Triangle – Pythagorean Tool

This project implements a Python tool for calculating, verifying, and visualizing right-angled triangles based on the Pythagorean theorem.

The application allows users to compute missing side lengths, verify whether given sides form a right triangle, and display a visual representation of the triangle.

---

## Analysis

### Functional Requirements
- The program shall calculate the missing side of a right-angled triangle if exactly two side lengths are provided.
- The program shall verify whether three given side lengths satisfy the Pythagorean theorem.
- The program shall validate user input and handle invalid or inconsistent values (e.g. negative values, impossible triangles).
- The program shall visualize the right triangle together with its side lengths.
- The program shall support both calculation and verification use cases.

### Non-Functional Requirements
- The code shall be modular and clearly structured.
- All functions and logic shall be documented with inline comments in English.
- The program shall be robust against invalid input and numerical inaccuracies.
- A separate test script shall be provided to ensure correctness of calculations.
- Test results shall be reproducible and documented.

---
## Requirements

- Python **3.10+**

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# OR (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 2. Install the project with development dependencies
```bash
pip install -e ".[dev]"
```

This installs:

runtime dependencies (PySide6),

development and test dependencies (pytest, pytest-qt, pytest-cov).

### 3. Run the application
```bash
pathagoras
```

### 4. Run tests with coverage
- Core logic tests (business logic only)
```bash

pytest -q --cov=pathagoras.core --cov-report=term-missing
```
This command:

runs all core-related tests,

shows coverage percentage,

lists uncovered lines directly in the terminal.

- Full test suite (core + UI)
```bash
pytest -q --cov=pathagoras --cov-report=term-missing
```
---
## Notes for reviewers
All computational logic is isolated in pathagoras.core and fully unit-tested.

GUI logic is separated in pathagoras.ui_qt and tested independently using pytest-qt.

Coverage output is displayed directly in the terminal for quick verification.
