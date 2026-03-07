#!/usr/bin/env bash
# Generates fixture .diff files from actual git operations.
# Run from the project root: bash tests/fixtures/generate.sh

set -euo pipefail

FIXTURES_DIR="$(cd "$(dirname "$0")" && pwd)"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cd "$TMPDIR"
git init -q
git config user.email "fixture@test.local"
git config user.name "Fixture Generator"

# -----------------------------------------------------------------------
# Fixture: rename_only
# A file is renamed, no content changes.
# -----------------------------------------------------------------------
mkdir -p src
cat > src/old_name.py << 'EOF'
def greet(name: str) -> str:
    return f"Hello, {name}!"
EOF

git add .
git commit -q -m "initial"

git mv src/old_name.py src/greeter.py
git commit -q -m "rename old_name -> greeter"

git diff HEAD~1 HEAD -- > "$FIXTURES_DIR/rename_only.diff"

# -----------------------------------------------------------------------
# Fixture: logic_change
# A function's logic is changed in a single file.
# -----------------------------------------------------------------------
cat > src/greeter.py << 'EOF'
def greet(name: str) -> str:
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}!"
EOF

git add .
git commit -q -m "add validation to greet()"

git diff HEAD~1 HEAD -- > "$FIXTURES_DIR/logic_change.diff"

# -----------------------------------------------------------------------
# Fixture: tangled_commit
# Logic change + rename in one commit.
# -----------------------------------------------------------------------
cat > src/hello.py << 'EOF'
def say_hello(name: str) -> str:
    return f"Hi, {name}!"
EOF
git add .
git commit -q -m "add say_hello"

git mv src/hello.py src/farewell.py
cat > src/farewell.py << 'EOF'
def say_goodbye(name: str) -> str:
    if not name:
        raise ValueError("name required")
    return f"Goodbye, {name}!"
EOF
git add .
git commit -q -m "rename hello->farewell + change logic"

git diff HEAD~1 HEAD -- > "$FIXTURES_DIR/tangled_commit.diff"

# -----------------------------------------------------------------------
# Fixture: multi_file_change
# Changes spread across multiple files.
# -----------------------------------------------------------------------
cat > src/greeter.py << 'EOF'
DEFAULT_GREETING = "Hello"

def greet(name: str, greeting: str = DEFAULT_GREETING) -> str:
    if not name:
        raise ValueError("name must not be empty")
    return f"{greeting}, {name}!"
EOF

cat > src/farewell.py << 'EOF'
DEFAULT_FAREWELL = "Goodbye"

def say_goodbye(name: str, farewell: str = DEFAULT_FAREWELL) -> str:
    if not name:
        raise ValueError("name required")
    return f"{farewell}, {name}!"
EOF

git add .
git commit -q -m "add configurable greeting/farewell to both files"

git diff HEAD~1 HEAD -- > "$FIXTURES_DIR/multi_file_change.diff"

echo "Generated fixtures:"
for f in "$FIXTURES_DIR"/*.diff; do
    echo "  $(basename "$f") ($(wc -l < "$f") lines)"
done
