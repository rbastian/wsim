for i in {1..100}; do
    cat PROMPT.md | claude -p --dangerously-skip-permissions
done
