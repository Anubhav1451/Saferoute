import re

with open('integration_test_output.txt', 'r') as f:
    content = f.read()

# Split the content by the failure markers
# We look for the pattern: ==================================== FAILURES ===================================
# Then each failure starts with ___ Test... ___
parts = re.split(r'=+ FAILURES =+', content)
if len(parts) < 2:
    print("No failures found")
    exit(1)

failures_section = parts[1]

# Now split each failure by the pattern: ___ Test... ___
# We'll use a regex to split by lines that start with ___ and end with ___ and have the test name
lines = failures_section.split('\n')
failures = []
current = []
in_failure = False
for line in lines:
    if line.startswith('___') and line.endswith('___') and 'TestResolverIntegration' in line:
        if current:
            failures.append('\n'.join(current))
            current = []
        in_failure = True
        current.append(line)
    elif in_failure:
        if line.startswith('___') and line.endswith('___') and 'TestResolverIntegration' in line:
            # This should not happen because we already split, but just in case
            pass
        current.append(line)
if current:
    failures.append('\n'.join(current))

# Now, for each failure, extract the information
for i, failure in enumerate(failures):
    # Extract the test name from the first line
    first_line = failure.split('\n')[0]
    # The first line is like: ___ TestResolverIntegration.test_resolve_unknown_highway_returns_unresolved ___
    match = re.search(r'___ (Test\S+) ___', first_line)
    if match:
        test_name = match.group(1)
    else:
        test_name = f"unknown_test_{i}"

    # The command we ran is the same for all: the pytest command
    command = "python -m pytest -m integration -v 2>&1"

    # For stdout, we can take the part before the failures section
    # We'll use the part of the content before the "=+ FAILURES =+" line
    stdout = parts[0].strip()

    # For stderr, we take the failure traceback
    stderr = failure.strip()

    # Root cause: we know from the error that the table 'osm_ways' is missing
    root_cause = "The table 'osm_ways' is missing in the database. This is likely because the test is running in a different context or the database has not been populated with the required OSM data for the integration tests."

    # Extract the exact file and line from the traceback
    # Look for a line that contains the file path and line number in the traceback
    # Example: "scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index"
    # We'll look for a line that ends with ": in <function>" or similar
    exact_file = "Unknown"
    exact_line = "Unknown"
    for line in stderr.split('\n'):
        if '.py:' in line and ' in ' in line:
            # Example: "scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index"
            # We want to extract the file and line number
            parts = line.split(':')
            if len(parts) >= 3:
                # The file path might have colons? Not in Windows paths? Actually, Windows paths can have colons in the drive letter.
                # But the pattern is: <drive>:\<path>\<file>.py:<line>: in <function>
                # So we take the first two parts as the file? Not exactly.
                # Let's try to find the last occurrence of '.py:' before the line number.
                # We'll use a regex to find the pattern: (.*\.py):(\d+): in
                match = re.search(r'(.*\.py):(\d+): in', line)
                if match:
                    exact_file = match.group(1)
                    exact_line = match.group(2)
                    break

    # Now, print the markdown for this failure
    print(f"## Failed Command {i+1}: {test_name}")
    print()
    print(f"**Command**: {command}")
    print()
    print("**Stdout**:")
    print()
    print("```")
    print(stdout)
    print("```")
    print()
    print("**Stderr**:")
    print()
    print("```")
    print(stderr)
    print("```")
    print()
    print(f"**Root cause**: {root_cause}")
    print()
    print(f"**Exact file**: {exact_file}")
    print(f"**Exact line**: {exact_line}")
    print()
    print("--")
    print()
