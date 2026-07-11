#!/bin/bash
# SafeRoute AI Backup Creator
# Excludes: node_modules, virtual environments, build folders, caches, .git, and existing backups

set -e

# Get project root (directory of this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="saferoute-ai-backup-${TIMESTAMP}.tar.gz"

echo "Creating SafeRoute AI backup..."
echo "Project root: $PROJECT_ROOT"
echo "Backup name: $BACKUP_NAME"

# Create tarball with exclusions
tar -czf "$BACKUP_NAME" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.pyd' \
    --exclude='.next' \
    --exclude='.cache' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='.git' \
    --exclude='saferoute-ai-backup-*.tar.gz' \
    -C "$PROJECT_ROOT" .

# Verify backup created
if [[ -f "$BACKUP_NAME" ]]; then
    echo ""
    echo "✅ Backup created successfully!"
    echo "📁 Location: $PROJECT_ROOT/$BACKUP_NAME"
    echo "📦 Size: $(du -h "$BACKUP_NAME" | cut -f1)"
    echo ""
    echo "To restore:"
    echo "  1. Extract: tar -xzf $BACKUP_NAME"
    echo "  2. cd saferoute-ai"
    echo "  3. Backend: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo "  4. Frontend: cd frontend && npm install"
    echo "  5. Set MAPBOX_TOKEN in frontend/.env.local (get free token at mapbox.com)"
    echo "  6. Start: docker-compose up --build  OR  (backend: uvicorn app.main:app --reload, frontend: npm run dev)"
else
    echo "❌ Backup creation failed!"
    exit 1
fi