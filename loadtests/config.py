"""Load test configuration"""

# Target URL
BASE_URL = "http://localhost:8000"

# Test URLs for /analyze endpoint
# Use variety to avoid caching/same-response issues
TEST_URLS = [
    "https://stripe.com",
    "https://github.com",
    "https://notion.so",
    "https://linear.app",
    "https://figma.com",
]

# Rate limit: 10/min per IP
RATE_LIMIT = 10
RATE_LIMIT_WINDOW = 60  # seconds

# Test scenarios
SCENARIOS = {
    "normal": {
        "users": 5,
        "spawn_rate": 1,
        "duration": "2m",
    },
    "burst": {
        "users": 20,
        "spawn_rate": 20,  # All at once
        "duration": "30s",
    },
    "sustained": {
        "users": 10,
        "spawn_rate": 2,
        "duration": "10m",
    },
}
