"""Locust load test for Chronos-K8s-Scheduler.

Usage: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""
import random
import uuid

from locust import HttpUser, between, task


class ChronosUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(10)
    def submit_task(self):
        """Submit tasks with varying priorities and resource requirements."""
        priority = random.randint(0, 100)
        cpu = random.choice([0.5, 1.0, 2.0, 4.0])
        memory = random.choice([128.0, 256.0, 512.0, 1024.0, 2048.0])
        duration = random.uniform(1.0, 30.0)

        self.client.post(
            "/api/v1/tasks/",
            json={
                "name": f"load-test-{uuid.uuid4().hex[:8]}",
                "description": "Load test task",
                "priority": priority,
                "resource_cpu": cpu,
                "resource_memory": memory,
                "max_retries": 2,
                "duration_seconds": round(duration, 1),
            },
            name="/api/v1/tasks/ [POST]",
        )

    @task(5)
    def list_tasks(self):
        """List tasks with various filters."""
        state = random.choice([None, "PENDING", "RUNNING", "COMPLETED"])
        params = {"page_size": 20}
        if state:
            params["state"] = state
        self.client.get("/api/v1/tasks/", params=params, name="/api/v1/tasks/ [GET]")

    @task(3)
    def list_workers(self):
        """List all workers."""
        self.client.get("/api/v1/workers/", name="/api/v1/workers/ [GET]")

    @task(2)
    def health_check(self):
        """Hit health endpoint."""
        self.client.get("/health", name="/health [GET]")

    @task(1)
    def readiness_check(self):
        """Hit readiness endpoint."""
        self.client.get("/ready", name="/ready [GET]")


class HighPriorityUser(HttpUser):
    """Simulates a user that submits high-priority tasks to trigger preemption."""
    wait_time = between(5.0, 15.0)
    weight = 1  # Much less frequent than normal users

    @task
    def submit_high_priority_task(self):
        self.client.post(
            "/api/v1/tasks/",
            json={
                "name": f"urgent-{uuid.uuid4().hex[:8]}",
                "description": "High priority task for preemption testing",
                "priority": random.randint(80, 100),
                "resource_cpu": random.choice([2.0, 4.0]),
                "resource_memory": random.choice([1024.0, 2048.0]),
                "max_retries": 1,
                "duration_seconds": random.uniform(5.0, 15.0),
            },
            name="/api/v1/tasks/ [POST high-prio]",
        )
