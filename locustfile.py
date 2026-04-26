"""
AslipureCare API - Load Test
Run headless:
  locust -f locustfile.py --headless -u 10 -r 2 -t 30s --host https://aslipurecare-api-1.onrender.com
"""

from locust import HttpUser, task, between


class AslipureCareUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def get_products(self):
        self.client.get("/products", name="GET /products")

    @task(2)
    def get_health(self):
        self.client.get("/health", name="GET /health")

    @task(1)
    def get_metrics(self):
        self.client.get("/metrics", name="GET /metrics")
