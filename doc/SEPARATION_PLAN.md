# PyBlink Repository Separation Plan

This document outlines the plan to extract `projects/pyblink` from the `py-learn` monorepo into its own standalone repository while preserving git history and ensuring no unrelated code is leaked.

## Table of Contents

1. [Overview](#overview)
2. [Part 1: Migration to New Repository](#part-1-migration-to-new-repository)
3. [Part 2: Post-Migration Cleanup in py-learn](#part-2-post-migration-cleanup-in-py-learn)
4. [Appendix: Files Inventory](#appendix-files-inventory)

---

## Overview

### Current State
- **Location**: `py-learn/projects/pyblink/`
- **Git History**: 38 commits touching pyblink files
- **Dependencies**: Self-contained with no imports from other py-learn projects
- **External Coupling**: None (no other projects depend on pyblink)

### Goals
1. Create a new standalone `pyblink` repository
2. Preserve relevant git commit history
3. Migrate all necessary code, tests, and configuration
4. Clean up the py-learn repository after migration
5. Ensure no leakage of unrelated py-learn code

---

## Part 1: Migration to New Repository

### 1.1 Prerequisites

Before starting the migration:

```bash
# Install git-filter-repo (recommended tool for history rewriting)
pip install git-filter-repo

# Create a working directory for the migration
mkdir ~/pyblink-migration
cd ~/pyblink-migration
```

### 1.2 Extract pyblink with Git History

#### Step 1: Clone the source repository

```bash
# Create a fresh clone specifically for extraction (do NOT use your working copy)
git clone /home/ligeng/Codes/py-learn py-learn-extraction
cd py-learn-extraction
```

#### Step 2: Extract pyblink subdirectory with history

Using `git-filter-repo` to extract only the `projects/pyblink` directory:

```bash
# Extract only projects/pyblink and rewrite history
git filter-repo --subdirectory-filter projects/pyblink

# This will:
# - Keep only commits that touched files in projects/pyblink
# - Rewrite paths so files appear at the repository root
# - Remove all other files and commits from history
```

#### Step 3: Verify the extraction

```bash
# Check that only pyblink files exist
ls -la

# Verify git history is intact
git log --oneline | head -20

# Verify no unrelated files leaked through
find . -type f -name "*.py" | head -20
```

#### Step 4: Create the new remote repository

```bash
# Create a new repository on GitHub (or your preferred host)
# Name suggestion: pyblink

# Add the new remote
git remote add origin git@github.com:<your-org>/pyblink.git

# Push with history
git push -u origin main
```

### 1.3 Post-Extraction Code Fixes

After extraction, several path references need updating because files now live at the repository root instead of `projects/pyblink/`:

#### Fix 1: Backend sys.path Manipulation

**Files to update:**
- `backend/app/services/converter.py`
- `backend/app/services/binary_analyzer.py`

**Current code:**
```python
pyblink_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(pyblink_root))
```

**Updated code:**
```python
# In the new repo structure, blink/ is at the root
pyblink_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(pyblink_root))
```

**Better alternative - use proper package installation:**
```python
# No sys.path manipulation needed if you run:
# pip install -e . (from repo root)
```

#### Fix 2: Test Configuration

**File:** `tests/conftest.py`

Verify the sys.path insertion still works. The current code should work if it uses relative path calculation:

```python
# Verify this points to the repo root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

#### Fix 3: Documentation Path References

Update paths in documentation files that reference `projects/pyblink/`:

**Files to review:**
- `README.md`
- `doc/QUICKSTART.md`
- `doc/USER_GUIDE.md`
- `doc/IMPLEMENTATION.md`

**Example changes:**
```diff
- cd projects/pyblink
+ cd pyblink  # or just refer to repo root

- python -m pytest projects/pyblink/tests
+ python -m pytest tests
```

### 1.4 DevContainer Setup

Create a dedicated `.devcontainer/` directory in the new repository.

#### Create `.devcontainer/devcontainer.json`:

```json
{
    "name": "PyBlink Development",
    "image": "mcr.microsoft.com/devcontainers/python:3.11",
    "features": {
        "ghcr.io/devcontainers/features/node:1": {
            "version": "20"
        }
    },
    "postCreateCommand": "pip install -e '.[dev]' && cd frontend && npm install",
    "forwardPorts": [3000, 8000],
    "portsAttributes": {
        "3000": {
            "label": "Frontend (React)",
            "onAutoForward": "notify"
        },
        "8000": {
            "label": "Backend (FastAPI)",
            "onAutoForward": "notify"
        }
    },
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "dbaeumer.vscode-eslint",
                "esbenp.prettier-vscode",
                "bradlc.vscode-tailwindcss"
            ],
            "settings": {
                "python.defaultInterpreterPath": "/usr/local/bin/python",
                "python.testing.pytestEnabled": true,
                "python.testing.pytestArgs": ["tests"]
            }
        }
    }
}
```

#### Alternative: Docker Compose based devcontainer

If more complex setup is needed, create `.devcontainer/docker-compose.yml`:

```yaml
version: '3.8'
services:
  pyblink:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    ports:
      - "3000:3000"
      - "8000:8000"
    command: sleep infinity
```

And `.devcontainer/Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js for frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Python dev dependencies
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

WORKDIR /workspace
```

### 1.5 GitHub Actions CI Setup

Create `.github/workflows/ci.yml` in the new repository:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e '.[dev]'
          pip install -r backend/requirements.txt

      - name: Run pytest with coverage
        run: |
          pytest tests/ --cov=blink --cov-report=term-missing --cov-fail-under=80

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Run frontend lint
        working-directory: frontend
        run: npm run lint

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install Python dependencies
        run: |
          pip install -e .
          pip install -r backend/requirements.txt

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Install Playwright
        working-directory: frontend
        run: npx playwright install --with-deps chromium

      - name: Start backend
        run: |
          cd backend && uvicorn app.main:app --port 8000 &
          sleep 5

      - name: Run Playwright tests
        working-directory: frontend
        run: npm run test:e2e

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

### 1.6 Update setup.py for Standalone Use

Ensure `setup.py` has proper dev dependencies:

```python
from setuptools import setup, find_packages

setup(
    name="pyblink",
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*", "backend", "frontend"]),
    python_requires=">=3.11",
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "hypothesis>=6.0",
        ],
    },
)
```

### 1.7 Create/Update .gitignore

Ensure the new repository has a proper `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
*.egg-info/
dist/
build/
.eggs/
.pytest_cache/
.coverage
htmlcov/

# Node.js
node_modules/
frontend/build/
frontend/.cache/
.npm

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
backend/data/playgrounds/*
!backend/data/playgrounds/.gitkeep

# Playwright
frontend/playwright-report/
frontend/test-results/
```

### 1.8 Migration Verification Checklist

Before considering the migration complete:

- [ ] All 38 commits are present in the new repository
- [ ] `git log --all --oneline | wc -l` shows expected commit count
- [ ] No files outside original `projects/pyblink/` exist
- [ ] `grep -r "py-learn" .` returns no hardcoded references (or only in docs explaining migration)
- [ ] Python tests pass: `pytest tests/`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] E2E tests pass (with backend running)
- [ ] DevContainer opens successfully in VS Code
- [ ] CI pipeline passes on GitHub

---

## Part 2: Post-Migration Cleanup in py-learn

### 2.1 Remove pyblink Directory

After confirming the new repository is fully functional:

```bash
cd /home/ligeng/Codes/py-learn

# Remove the pyblink directory
git rm -r projects/pyblink

# Commit the removal
git commit -m "Remove pyblink project (migrated to standalone repository)

PyBlink has been extracted to its own repository at:
https://github.com/<your-org>/pyblink

See: projects/pyblink/doc/SEPARATION_PLAN.md (in the new repo)
for migration details."
```

### 2.2 Update GitHub Actions CI

**File:** `.github/workflows/test-all-projects.yml`

Remove pyblink-specific sections:

```yaml
# REMOVE these sections:
# - Backend requirements installation for pyblink (line ~263)
# - Frontend package-lock.json cache for pyblink (line ~273)
# - Frontend npm test job for pyblink (lines ~276-291)
# - Playwright report upload for pyblink (lines ~298-312)
```

The CI discovery tool (`tools/ci_discover_projects.py`) should automatically stop discovering pyblink once the directory is removed.

### 2.3 Update DevLogs (Optional)

Add a note to `devlogs/` explaining the migration:

```markdown
## PyBlink Migration

PyBlink has been migrated to its own repository:
- New location: https://github.com/<your-org>/pyblink
- Migration date: YYYY-MM-DD
- Historical devlogs referencing pyblink remain for archival purposes
```

### 2.4 Verify No Broken References

```bash
cd /home/ligeng/Codes/py-learn

# Search for any remaining references to pyblink
grep -r "pyblink" --include="*.py" --include="*.md" --include="*.yml" --include="*.json" .

# Check for broken imports
grep -r "from blink" --include="*.py" .
grep -r "import blink" --include="*.py" .
```

### 2.5 Cleanup Verification Checklist

- [ ] `projects/pyblink/` directory no longer exists
- [ ] `git status` shows clean state after removal commit
- [ ] CI pipeline still passes for remaining projects
- [ ] No broken references to pyblink in remaining code
- [ ] DevContainer still works for remaining projects (if applicable)

---

## Appendix: Files Inventory

### Files to Migrate (Included in git-filter-repo extraction)

```
projects/pyblink/
├── blink/                    # Core Python package (MIGRATE)
├── backend/                  # FastAPI application (MIGRATE)
├── frontend/                 # React application (MIGRATE)
├── tests/                    # Python unit tests (MIGRATE)
├── schema/                   # Blink schema examples (MIGRATE)
├── scripts/                  # CLI utilities (MIGRATE)
├── doc/                      # Documentation (MIGRATE)
├── specs/                    # Blink specifications (MIGRATE)
├── setup.py                  # Package setup (MIGRATE)
├── requirements.txt          # Dependencies (MIGRATE)
├── Makefile                  # Build targets (MIGRATE)
├── README.md                 # Project readme (MIGRATE)
├── SPEC.md                   # Specifications (MIGRATE)
├── SPEC_ENHANCED.md          # Enhanced specs (MIGRATE)
├── REVIEW.md                 # Implementation review (MIGRATE)
├── start.ps1                 # Windows scripts (MIGRATE)
├── start.bat                 # Windows scripts (MIGRATE)
└── .gitignore                # Git ignore rules (MIGRATE)
```

### Files to Exclude (Will NOT be in new repository)

```
# Build artifacts (regenerated)
.venv/
node_modules/
frontend/build/
pyblink.egg-info/
__pycache__/
.pytest_cache/

# IDE settings (user-specific)
.vscode/ (at repo root, not project-specific)
.idea/

# Parent repository files (NOT migrated)
.github/                      # Will create new CI config
.devcontainer/                # Will create new devcontainer
devlogs/                      # Parent repo specific
tools/                        # Parent repo specific
other projects/               # NOT part of pyblink
```

### Files to Create in New Repository

```
# New files needed post-extraction
.devcontainer/
├── devcontainer.json         # CREATE (see section 1.4)
└── Dockerfile                # CREATE (optional)

.github/
└── workflows/
    └── ci.yml                # CREATE (see section 1.5)
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| History loss during extraction | Low | High | Use git-filter-repo, verify commit count |
| Code leakage from other projects | Low | High | Use --subdirectory-filter, verify with find/grep |
| Broken paths post-migration | Medium | Medium | Documented fixes in section 1.3 |
| CI failures | Medium | Low | New CI config provided in section 1.5 |
| DevContainer issues | Low | Low | New config provided in section 1.4 |

---

## Timeline Estimate

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Extraction | Clone, filter-repo, push | 30 minutes |
| Code fixes | Path updates, sys.path fixes | 1 hour |
| Infrastructure | DevContainer, CI setup | 1 hour |
| Testing | Verify all tests pass | 1 hour |
| Documentation | Update paths in docs | 30 minutes |
| Cleanup (py-learn) | Remove directory, update CI | 30 minutes |
| **Total** | | **4-5 hours** |

---

## References

- [git-filter-repo documentation](https://github.com/newren/git-filter-repo)
- [GitHub: Splitting a subfolder into a new repository](https://docs.github.com/en/get-started/using-git/splitting-a-subfolder-out-into-a-new-repository)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
