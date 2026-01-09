# Load Testing for /analyze Endpoint

Load tests for the LaunchAd `/analyze` endpoint using [Locust](https://locust.io/).

## Setup

```bash
pip install locust
```

## Running Tests

### Interactive UI (Recommended for exploration)
```bash
./run_tests.sh ui
# Open http://localhost:8089
```

### Automated Scenarios

```bash
# Normal load (5 users, 2 min)
./run_tests.sh normal

# Burst test (20 users at once, 30 sec) - tests rate limiting
./run_tests.sh burst

# Sustained load (10 users, 10 min)
./run_tests.sh sustained

# Health check baseline (5 users, 1 min)
./run_tests.sh health
```

### Custom Target
```bash
HOST=https://api.launchad.io ./run_tests.sh normal
```

## Test Scenarios

| Scenario | Users | Duration | Purpose |
|----------|-------|----------|---------|
| normal | 5 | 2 min | Baseline performance |
| burst | 20 | 30 sec | Rate limiting verification |
| sustained | 10 | 10 min | Stability under load |
| health | 5 | 1 min | Baseline health check |

## Metrics to Track

1. **Response Time**
   - Average (target: <30s for full analysis)
   - 95th percentile
   - Max

2. **Error Rates**
   - 429 (rate limited) - expected at high load
   - 400 (bad request) - scraper failures
   - 500 (server error) - bugs

3. **Rate Limiting**
   - Should kick in at 10 req/min/IP
   - Verify 429 responses in burst test

4. **Throughput**
   - Requests/second
   - Successful requests/second

## Expected Results

- **Normal**: All requests succeed, <5% rate limited
- **Burst**: 50%+ rate limited (expected - proves rate limiting works)
- **Sustained**: Steady performance, occasional rate limiting

## Bottlenecks to Watch

1. **Playwright** - Browser startup time, resource consumption
2. **Gemini API** - External API rate limits
3. **Vertex AI** - Image generation quotas (2 images per request)
4. **S3** - Upload bandwidth

## Output

Results saved to `results/` directory as HTML reports:
- `normal_YYYYMMDD_HHMMSS.html`
- `burst_YYYYMMDD_HHMMSS.html`
- `sustained_YYYYMMDD_HHMMSS.html`

## User Classes

- `AnalyzeUser` - Normal user flow with 6-12s wait between requests
- `RateLimitTestUser` - Rapid requests to test rate limiting
- `HealthCheckUser` - Light baseline testing

## Notes

- /analyze is computationally expensive (Playwright + AI)
- Rate limit: 10 requests/minute/IP
- Timeout set to 60s to accommodate AI processing
- Test URLs are public sites - no authentication needed
