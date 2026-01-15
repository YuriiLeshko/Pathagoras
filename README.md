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
- Python 3.10+

---

## Setup (2 commands)

### 1. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
# OR
.\venv\Scripts\Activate.ps1    # Windows (PowerShell)
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
### 3. Run

```bash
python main.py
```