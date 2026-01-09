#!/bin/bash
# Run load tests with different scenarios
#
# Usage:
#   ./run_tests.sh normal    - 5 users, 2 minutes
#   ./run_tests.sh burst     - 20 users burst, 30 seconds
#   ./run_tests.sh sustained - 10 users, 10 minutes
#   ./run_tests.sh ui        - Interactive web UI
#   ./run_tests.sh health    - Health check only (baseline)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-http://localhost:8000}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCENARIO=${1:-ui}

cd "$SCRIPT_DIR"

case $SCENARIO in
    normal)
        echo "Running normal load test (5 users, 2 minutes)..."
        locust -f locustfile.py --host="$HOST" \
            --users 5 --spawn-rate 1 --run-time 2m \
            --headless \
            --html "results/normal_${TIMESTAMP}.html" \
            --only-summary
        ;;
    burst)
        echo "Running burst test (20 users at once, 30 seconds)..."
        locust -f locustfile.py --host="$HOST" \
            --users 20 --spawn-rate 20 --run-time 30s \
            --headless \
            --html "results/burst_${TIMESTAMP}.html" \
            --only-summary \
            RateLimitTestUser
        ;;
    sustained)
        echo "Running sustained load test (10 users, 10 minutes)..."
        locust -f locustfile.py --host="$HOST" \
            --users 10 --spawn-rate 2 --run-time 10m \
            --headless \
            --html "results/sustained_${TIMESTAMP}.html" \
            --only-summary
        ;;
    health)
        echo "Running health check baseline (5 users, 1 minute)..."
        locust -f locustfile.py --host="$HOST" \
            --users 5 --spawn-rate 5 --run-time 1m \
            --headless \
            --html "results/health_${TIMESTAMP}.html" \
            --only-summary \
            HealthCheckUser
        ;;
    ui)
        echo "Starting interactive UI mode..."
        echo "Open http://localhost:8089 in your browser"
        echo "Target host: $HOST"
        echo ""
        locust -f locustfile.py --host="$HOST"
        ;;
    *)
        echo "Usage: $0 {normal|burst|sustained|health|ui}"
        echo ""
        echo "Scenarios:"
        echo "  normal    - 5 concurrent users for 2 minutes"
        echo "  burst     - 20 users at once for 30 seconds (rate limit test)"
        echo "  sustained - 10 users for 10 minutes"
        echo "  health    - Health check baseline (5 users, 1 minute)"
        echo "  ui        - Interactive web UI (default)"
        echo ""
        echo "Environment variables:"
        echo "  HOST - Target host (default: http://localhost:8000)"
        exit 1
        ;;
esac

echo ""
echo "Results saved to: $SCRIPT_DIR/results/"
