from dataclasses import dataclass
import math
import matplotlib.pyplot as plt

@dataclass
class TriangleData:
    a: float                        #    B
    b: float                        #    |  \
    c: float                        #    |     \
    A: tuple[float, float]          #    | a       \ c
    B: tuple[float, float]          #    |             \
    C: tuple[float, float]          #    |                 \
    is_valid: bool                  #    A__________b__________C


def compute_triangle(a: float, b: float, c: float) -> TriangleData:
    a, b, c = sorted([float(a), float(b), float(c)])

    is_valid = math.isclose(a*a + b*b, c*c, rel_tol=1e-9)
    if not is_valid:
        return TriangleData(a, b, c, (0, 0), (0, 0), (0, 0), False)

    # Coordinates:
    A = (0, 0)    
    B = (0, a)      
    C = (b, 0)   

    return TriangleData(a, b, c, A, B, C, True) 


def draw_triangle(triangle : TriangleData):
    A, B, C = triangle.A, triangle.B, triangle.C

    xs = [A[0], B[0], C[0], A[0]]
    ys = [A[1], B[1], C[1], A[1]]

    plt.figure()
    plt.plot(xs, ys, marker="o")
    plt.gca().set_aspect("equal", adjustable="box")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    raw = input("Enter three side lengths (e.g. 3 4 5) separated by spaces: ").strip().split()
    if len(raw) != 3:
        raise SystemExit("Please enter exactly 3 numbers.")
        
    a, b, c = map(float, raw)    
    if a <= 0 or b <= 0 or c <= 0:
        raise SystemExit("Invalid input: sides must be positive numbers.")

    triangle = compute_triangle(a, b, c)

    if not triangle.a + triangle.b > triangle.c:
        raise SystemExit("Invalid input: Triangle data is invalid.")
    if not triangle.is_valid:
        raise SystemExit("Triangle is NOT right-angled.")
    
    draw_triangle(triangle)

    