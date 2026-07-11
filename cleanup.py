import sys

def main():
    filename = r"D:\\saferoute-ai\\backend\\app\\services\\routing.py"
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find the first occurrence of the method definition
    method_def = "def _get_directions_route(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:"
    first_idx = None
    for i, line in enumerate(lines):
        if method_def in line:
            first_idx = i
            break

    if first_idx is None:
        print("First method definition not found")
        sys.exit(1)

    # Find the second occurrence of the method definition after the first
    second_idx = None
    for i in range(first_idx + 1, len(lines)):
        if method_def in lines[i]:
            second_idx = i
            break

    if second_idx is None:
        print("Second method definition not found")
        sys.exit(1)

    # Find the comment line after the second method
    comment_line = "# --------------------- ROUTE COST ---------------------"
    comment_idx = None
    for i in range(second_idx, len(lines)):
        if comment_line in lines[i]:
            comment_idx = i
            break

    if comment_idx is None:
        print("Comment line not found after second method")
        sys.exit(1)

    # Remove the second method and any blank lines between it and the comment?
    # We'll delete from second_idx to comment_idx (exclusive of comment_idx)
    del lines[second_idx:comment_idx]

    with open(filename, 'w') as f:
        f.writelines(lines)

    print("Cleaned up duplicate method")

if __name__ == '__main__':
    main()