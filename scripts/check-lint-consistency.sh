#!/bin/bash
set -e

echo "🔍 Testing linting consistency between pre-commit and GitHub Actions..."

echo ""
echo "📋 Running pre-commit checks..."
uv run pre-commit run --all-files

echo ""
echo "🚀 Running GitHub Actions linting commands..."
uv run ruff check . --fix --output-format=github
uv run ruff format --check .
npx eslint -c config/eslint.config.js --fix static/*.js
npx htmlhint templates/*.html

echo ""
echo "✅ All linting checks passed! Pre-commit and GitHub Actions are consistent."
