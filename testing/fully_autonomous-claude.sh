cat > autonomous-claude.sh << 'EOF'
#!/bin/bash

MAX_ITERATIONS=${2:-10}
PROMPT="$1"
ITERATION=0

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    echo "=== Iteration $((ITERATION + 1))/$MAX_ITERATIONS ==="
    
    claude --dangerously-skip-permissions --allowedTools "Bash(*),Read(*),Write(*),Edit(*)" -p "$PROMPT"
    EXIT_CODE=$?
    
    if [ -f "package.json" ]; then
        npm test
        TEST_EXIT=$?
    elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
        pytest
        TEST_EXIT=$?
    else
        TEST_EXIT=0
    fi
    
    if [ $TEST_EXIT -eq 0 ] && [ $EXIT_CODE -eq 0 ]; then
        if ! grep -q "- \[ \]" todo.md 2>/dev/null; then
            echo "✅ All tasks complete!"
            exit 0
        fi
    fi
    
    ((ITERATION++))
    sleep 2
done

echo "⚠️  Max iterations reached"
EOF

chmod +x autonomous-claude.sh