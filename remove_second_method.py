import sys

def main():
    filename = r"D:\\saferoute-ai\\backend\\app\\services\\routing.py"
    with open(filename, 'r') as f:
        content = f.read()

    # Find the first occurrence of the method definition
    method_def = "def _get_directions_route(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:"
    first_pos = content.find(method_def)
    if first_pos == -1:
        print("First method definition not found")
        sys.exit(1)

    # Find the second occurrence after the first
    second_pos = content.find(method_def, first_pos + 1)
    if second_pos == -1:
        print("Second method definition not found")
        sys.exit(1)

    # Find the comment after the second method
    comment = "# --------------------- ROUTE COST ---------------------"
    comment_pos = content.find(comment, second_pos)
    if comment_pos == -1:
        print("Comment not found after second method")
        sys.exit(1)

    # We want to remove the second method, which starts at second_pos and goes up to comment_pos
    # But we want to keep the comment.
    # So we take everything before second_pos, and then everything from comment_pos onwards.
    new_content = content[:second_pos] + content[comment_pos:]

    with open(filename, 'w') as f:
        f.write(new_content)

    print("Removed second method")

if __name__ == '__main__':
    main()