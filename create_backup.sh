#!/bin/bash
# SafeRoute AI Backup Creator
# Excludes: node_modules, virtual environments, build folders, caches, .git, IDE dirs

 set -e

 PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
 BACKUP_NAME="saferoute-ai-backup-${TIMESTAMP}.tar.gz"
 # Create backup in parent directory to avoid file changing while archiving
 BACKUP_DIR="$(dirname "${PROJECT_ROOT}")"
 BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

 echo "Creating backup: ${BACKUP_NAME}"
 echo "Project root: ${PROJECT_ROOT}"
 echo "Storing in: ${BACKUP_DIR}"

 # Change to project root and create archive, excluding unwanted files/dirs
 cd "${PROJECT_ROOT}"
 tar -czf "${BACKUP_PATH}" \
   --exclude='.git' \
   --exclude='.venv' \
   --exclude='venv' \
   --exclude='*/node_modules' \
   --exclude='*/__pycache__' \
   --exclude='*/.next' \
   --exclude='*/.cache' \
   --exclude='*/build' \
   --exclude='*.pyc' \
   --exclude='*.pyo' \
   --exclude='*.pyd' \
   --exclude='*.tar.gz' \
   --exclude='.DS_Store' \
   --exclude='Thumbs.db' \
   --exclude='*~' \
   --exclude='*.tmp' \
   --exclude='.idea' \
   --exclude='.vscode' \
   .

 echo "Backup created successfully: ${BACKUP_PATH}"
 echo "Size: $(du -h "${BACKUP_PATH}" | cut -f1)"
 echo "Listing contents (first 20 entries):"
 tar -tzf "${BACKUP_PATH}" | head -20
 echo "..."