"""
Load tests for /analyze endpoint

Run: locust -f loadtests/locustfile.py --host=http://localhost:8000
Interactive: locust -f loadtests/locustfile.py --host=http://localhost:8000 (opens http://localhost:8089)
"""
import random
from locust import HttpUser, task, between, events

# Test URLs - public sites for analysis
TEST_URLS = [
    "https://stripe.com",
    "https://github.com",
    "https://notion.so",
    "https://linear.app",
    "https://figma.com",
]


class AnalyzeUser(HttpUser):
    """Simulates user calling /analyze endpoint"""

    # Wait 6-12 seconds between requests (respect rate limit of 10/min)
    wait_time = between(6, 12)

    def on_start(self):
        """Initialize counters"""
        self._rate_limited_count = 0
        self._success_count = 0
        self._error_count = 0

    @task
    def analyze_url(self):
        """POST to /analyze with random test URL"""
        url = random.choice(TEST_URLS)

        with self.client.post(
            "/analyze",
            json={"url": url},
            catch_response=True,
            name="/analyze",
            timeout=60,  # Long timeout for AI processing
        ) as response:
            if response.status_code == 200:
                response.success()
                self._success_count += 1
            elif response.status_code == 429:
                # Rate limited - expected behavior at high load
                response.success()
                self._rate_limited_count += 1
            elif response.status_code == 400:
                # Bad URL or scrape failure
                response.failure(f"Bad request: {response.text[:100]}")
                self._error_count += 1
            else:
                response.failure(f"Unexpected {response.status_code}: {response.text[:100]}")
                self._error_count += 1

    def on_stop(self):
        """Log summary on user stop"""
        total = self._success_count + self._rate_limited_count + self._error_count
        if total > 0:
            print(f"User stats - Success: {self._success_count}, "
                  f"Rate limited: {self._rate_limited_count}, "
                  f"Errors: {self._error_count}")


class RateLimitTestUser(HttpUser):
    """Specifically tests rate limiting behavior with rapid requests"""

    # Fast requests to trigger rate limit
    wait_time = between(0.5, 1)

    def on_start(self):
        """Initialize counters"""
        self._rate_limited_count = 0
        self._passed_count = 0

    @task
    def burst_analyze(self):
        """Rapid-fire requests to test rate limiting"""
        url = random.choice(TEST_URLS)

        with self.client.post(
            "/analyze",
            json={"url": url},
            catch_response=True,
            name="/analyze (burst)",
            timeout=60,
        ) as response:
            if response.status_code == 429:
                response.success()  # Expected - rate limit working
                self._rate_limited_count += 1
            elif response.status_code == 200:
                response.success()
                self._passed_count += 1
            else:
                response.failure(f"Unexpected: {response.status_code}")

    def on_stop(self):
        """Log rate limit summary"""
        total = self._rate_limited_count + self._passed_count
        if total > 0:
            rate_limited_pct = (self._rate_limited_count / total) * 100
            print(f"Rate limit test - Passed: {self._passed_count}, "
                  f"Rate limited: {self._rate_limited_count} ({rate_limited_pct:.1f}%)")


class HealthCheckUser(HttpUser):
    """Light user for baseline health check testing"""

    wait_time = between(1, 2)

    @task(10)
    def health_check(self):
        """Check /health endpoint"""
        self.client.get("/health", name="/health")

    @task(1)
    def root_check(self):
        """Check / endpoint"""
        self.client.get("/", name="/")


# Event hooks for custom reporting
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate summary report on test stop"""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    if stats.total.num_requests > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"Failure rate: {failure_rate:.2f}%")
    print(f"Avg response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Median response time: {stats.total.median_response_time or 0:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("=" * 60)

    # Per-endpoint stats
    print("\nPer-endpoint breakdown:")
    for name, entry in stats.entries.items():
        print(f"  {name[1]}: {entry.num_requests} reqs, "
              f"{entry.num_failures} fails, "
              f"avg {entry.avg_response_time:.0f}ms")
    print()
