import re

with open('integration_test_output.txt', 'r') as f:
    content = f.read()

# Split the content by the failure markers
# We look for the pattern: ==================================== FAILURES ===================================
parts = re.split(r'=+ FAILURES =+', content)
if len(parts) < 2:
    print("No findingsound")
    exit(1)

stdout_part = parts[0].strip()
failures_section = parts[1]

# Now split each failure by the pattern: ___ Test... ___
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

    # For stdout, we use the stdout_part
    stdout = stdout_part

    # For stderr, we take the failure string
    stderr = failure.strip()

    # Root cause: we know from the error that the table 'osm_ways' is missing
    root_cause = "The table 'osm_ways' is missing in the database. This is likely because the test is running in a different context or the database has not been populated with the required OSM data for the integration tests."

    # Extract the exact file and line from the traceback
    # Look for a line that contains the file path and line number in the traceback
    # Example: "scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index"
    exact_file = "Unknown"
    exact_line = "Unknown"
    for line in stderr.split('\n'):
        # Look for a pattern: <path>\<file>.py:<line>: in <function>
        match = re.search(r'([^\s]+\.py):(\d+):\s+in', line)
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
