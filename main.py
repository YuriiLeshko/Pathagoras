
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

    