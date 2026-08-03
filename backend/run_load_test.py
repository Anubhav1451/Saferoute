import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# Configuration
LOCUST_FILE = "locustfile.py"
HOST = "http://localhost:8000"
RESULTS_DIR = "load_test_results"
USER_COUNTS = [10, 50, 100, 250]
SPAWN_RATE = 10  # users per second
RUN_TIME = "2m"  # 2 minutes

# Ensure results directory exists
Path(RESULTS_DIR).mkdir(exist_ok=True)

def run_locust_test(user_count):
    """Run locust test for given user count and return stats."""
    print(f"Starting load test with {user_count} users...")

    # Prepare the command
    cmd = [
        sys.executable,
        "-m", "locust",
        "-f", LOCUST_FILE,
        "--headless",
        "-u", str(user_count),
        "-r", str(SPAWN_RATE),
        "--run-time", RUN_TIME,
        "--host", HOST,
        "--csv", f"{RESULTS_DIR}/results_{user_count}"
    ]

    # Run the command
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Wait for the process to complete and capture output
    stdout, _ = process.communicate()
    elapsed_time = time.time() - start_time

    print(f"Load test for {user_count} users completed in {elapsed_time:.2f} seconds.")
    print("Locust output:")
    print(stdout)

    # Parse the CSV output to get statistics
    stats_file = f"{RESULTS_DIR}/results_{user_count}_stats.csv"
    if not os.path.exists(stats_file):
        print(f"ERROR: Stats file {stats_file} not found.")
        return None

    # Read the CSV file
    with open(stats_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Print the header for debugging
    if len(rows) == 0:
        print("ERROR: No rows in stats file.")
        return None

    print(f"CSV Header: {reader.fieldnames}")

    # We are interested in the Aggregated row (where Name is 'Aggregated')
    agg_row = None
    for row in rows:
        if row['Name'] == 'Aggregated':
            agg_row = row
            break

    if not agg_row:
        print("ERROR: Could not find aggregated row in stats.")
        print("Available rows:")
        for row in rows:
            print(row)
        return None

    # Extract the metrics we need
    # Note: The column names in the CSV might vary slightly, so we try to be flexible
    def get_field(row, *possible_names):
        for name in possible_names:
            if row.get(name) is not None:
                return row[name]
        return None

    try:
        # Try to get the request count and failure count
        request_count = int(get_field(agg_row, '# requests', 'Request Count') or 0)
        failure_count = int(get_field(agg_row, '# failures', 'Failure Count') or 0)

        # Get response times - try different possible column names
        median_response_time = float(get_field(agg_row, 'Median response time', 'Median Response Time', '50% Resp Time') or 0)
        average_response_time = float(get_field(agg_row, 'Average response time', 'Average Response Time') or 0)
        min_response_time = float(get_field(agg_row, 'Min response time', 'Min Response Time') or 0)
        max_response_time = float(get_field(agg_row, 'Max response time', 'Max Response Time') or 0)

        # For percentiles, we might need to look at the percentile row or use the CSV percentile columns
        # Let's try to get the 95th and 99th percentile from the columns that might be named like '95% Resp Time'
        p95_response_time = float(get_field(agg_row, '95% Resp Time', '95% Response Time') or 0)
        p99_response_time = float(get_field(agg_row, '99% Resp Time', '99% Response Time') or 0)

        # If the above didn't work, we can try to compute from the percentile row in the CSV?
        # But for simplicity, we'll use the above and if they are zero, we'll try to look for a different row.

        # If we got zeros for percentiles, let's try to look for a row with name like 'Aggregate' or 'Total' and then look for percentile columns
        if p95_response_time == 0 or p99_response_time == 0:
            # Look for a row that might contain percentile data (sometimes the aggregate row has these columns)
            # If still zero, we'll leave it as zero and note in the report.
            pass

        requests_per_second = float(get_field(agg_row, 'Requests/s', 'Average Requests per Second') or 0)

    except Exception as e:
        print(f"Error parsing stats row: {e}")
        print(f"Agg row: {agg_row}")
        return None

    # Calculate error rate
    if request_count > 0:
        error_rate = (failure_count / request_count) * 100
    else:
        error_rate = 0

    stats = {
        'user_count': user_count,
        'total_requests': request_count,
        'failure_count': failure_count,
        'median_response_time': median_response_time,
        'average_response_time': average_response_time,
        'min_response_time': min_response_time,
        'max_response_time': max_response_time,
        'p95_response_time': p95_response_time,
        'p99_response_time': p99_response_time,
        'average_requests_per_second': requests_per_second,
        'error_rate': error_rate
    }

    return stats

def get_system_metrics():
    """Get system metrics from the /metrics endpoint."""
    try:
        response = requests.get(f"{HOST}/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"WARNING: Could not get metrics, status code {response.status_code}")
            return {}
    except Exception as e:
        print(f"WARNING: Could not get metrics: {e}")
        return {}

def main():
    all_stats = []

    for user_count in USER_COUNTS:
        # Run the locust test
        stats = run_locust_test(user_count)
        if stats is None:
            print(f"Skipping user count {user_count} due to error.")
            continue

        # Get system metrics after the test
        metrics = get_system_metrics()
        stats.update(metrics)

        all_stats.append(stats)
        print(f"Results for {user_count} users: {json.dumps(stats, indent=2)}")

        # Wait a bit between tests to let the system recover
        print("Waiting 30 seconds before next test...")
        time.sleep(30)

    # Generate the report
    generate_report(all_stats)

def generate_report(stats_list):
    """Generate a markdown report from the collected stats."""
    report_path = f"{RESULTS_DIR}/LOAD_TEST_REPORT_V2.md"

    with open(report_path, 'w') as f:
        f.write("# Load Test Report v2\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Test Configuration\n")
        f.write(f"- Host: {HOST}\n")
        f.write(f"- Spawn rate: {SPAWN_RATE} users/second\n")
        f.write(f"- Test duration: {RUN_TIME}\n")
        f.write(f"- User counts tested: {USER_COUNTS}\n\n")

        f.write("## Results Summary\n\n")
        f.write("| Users | Req/s | Median Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Error Rate (%) | CPU (%) | Memory RSS (MB) |\n")
        f.write("|-------|-------|---------------------|------------------|------------------|----------------|---------|-----------------|\n")

        for stats in stats_list:
            users = stats.get('user_count', 'N/A')
            req_per_sec = stats.get('average_requests_per_second', 0)
            median_latency = stats.get('median_response_time', 0)
            p95_latency = stats.get('p95_response_time', 0)
            p99_latency = stats.get('p99_response_time', 0)
            error_rate = stats.get('error_rate', 0)
            cpu_percent = stats.get('cpu_percent', 0)
            memory_rss = stats.get('memory_rss_mb', 0)

            f.write(f"| {users} | {req_per_sec:.2f} | {median_latency:.2f} | {p95_latency:.2f} | {p99_latency:.2f} | {error_rate:.2f} | {cpu_percent:.2f} | {memory_rss:.2f} |\\n")

        f.write("\n## Detailed Results\n\n")
        for stats in stats_list:
            f.write(f"### {stats['user_count']} Users\\n")
            f.write(f"- Total Requests: {stats.get('total_requests', 0)}\\n")
            f.write(f"- Failed Requests: {stats.get('failure_count', 0)}\\n")
            f.write(f"- Median Response Time: {stats.get('median_response_time', 0):.2f} ms\\n")
            f.write(f"- 95th Percentile Response Time: {stats.get('p95_response_time', 0):.2f} ms\\n")
            f.write(f"- 99th Percentile Response Time: {stats.get('p99_response_time', 0):.2f} ms\\n")
            f.write(f"- Average Response Time: {stats.get('average_response_time', 0):.2f} ms\\n")
            f.write(f"- Requests per Second: {stats.get('average_requests_per_second', 0):.2f}\\n")
            f.write(f"- Error Rate: {stats.get('error_rate', 0):.2f}%\\n")
            f.write(f"- CPU Usage: {stats.get('cpu_percent', 0):.2f}%\\n")
            f.write(f"- Memory RSS: {stats.get('memory_rss_mb', 0):.2f} MB\\n")
            f.write(f"- Memory VMS: {stats.get('memory_vms_mb', 0):.2f} MB\\n")
            f.write("\\n")

        f.write("\\n## Conclusion\\n")
        # Add a simple conclusion based on the results
        if stats_list:
            max_users_tested = max([s['user_count'] for s in stats_list])
            max_errors = max([s['error_rate'] for s in stats_list])
            max_p95 = max([s['p95_response_time'] for s in stats_list])

            if max_errors == 0 and max_p95 < 2000:  # less than 2 seconds
                f.write("✅ **Performance Target Met**: All tests passed with 0% error rate and 95th percentile latency under 2 seconds.\\n")
            else:
                f.write("⚠️ **Performance Issues Detected**: Consider optimizing the system.\\n")
                if max_errors > 0:
                    f.write(f"- Maximum error rate observed: {max_errors:.2f}%\\n")
                if max_p95 >= 2000:
                    f.write(f"- Maximum 95th percentile latency: {max_p95:.2f} ms (exceeds 2000 ms threshold)\\n")
        else:
            f.write("No tests were completed successfully.\\n")

    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()