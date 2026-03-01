"""Pre-built task templates for demos and testing."""

TEMPLATES: dict[str, dict] = {
    "cpu-stress": {
        "name": "CPU Stress Test",
        "image": "alpine:latest",
        "command": ["sh", "-c", "dd if=/dev/urandom bs=1M count=100 | md5sum"],
        "resource_cpu": 1.0,
        "resource_memory": 128,
        "timeout_seconds": 120,
        "description": "Burns CPU computing MD5 of random data",
    },
    "memory-allocator": {
        "name": "Memory Allocation Test",
        "image": "python:3.12-slim",
        "command": [
            "python",
            "-c",
            "x = bytearray(50 * 1024 * 1024); import time; time.sleep(10); print('Allocated 50MB successfully')",
        ],
        "resource_cpu": 0.5,
        "resource_memory": 128,
        "timeout_seconds": 60,
        "description": "Allocates 50MB of memory and holds it",
    },
    "web-scraper": {
        "name": "Web Scraper",
        "image": "python:3.12-slim",
        "command": [
            "python",
            "-c",
            "import urllib.request; r = urllib.request.urlopen('https://httpbin.org/json'); print(r.read().decode())",
        ],
        "resource_cpu": 0.5,
        "resource_memory": 256,
        "timeout_seconds": 60,
        "description": "Fetches JSON from httpbin.org",
    },
    "disk-io": {
        "name": "Disk I/O Benchmark",
        "image": "alpine:latest",
        "command": [
            "sh",
            "-c",
            "dd if=/dev/zero of=/tmp/testfile bs=1M count=50 && echo 'Wrote 50MB' && rm /tmp/testfile",
        ],
        "resource_cpu": 0.5,
        "resource_memory": 64,
        "timeout_seconds": 60,
        "description": "Writes 50MB to disk to test I/O",
    },
    "sleep-job": {
        "name": "Simple Sleep Job",
        "image": "alpine:latest",
        "command": ["sleep", "15"],
        "resource_cpu": 0.25,
        "resource_memory": 32,
        "timeout_seconds": 60,
        "description": "Sleeps for 15 seconds (basic connectivity test)",
    },
    "fibonacci": {
        "name": "Fibonacci Calculator",
        "image": "python:3.12-slim",
        "command": [
            "python",
            "-c",
            (
                "def fib(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
                "result = fib(100000)\n"
                "print(f'Computed fib(100000), digit count: {len(str(result))}')"
            ),
        ],
        "resource_cpu": 2.0,
        "resource_memory": 512,
        "timeout_seconds": 300,
        "description": "Computes fibonacci(100000) — CPU-intensive",
    },
}
