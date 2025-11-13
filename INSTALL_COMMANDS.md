# Installation Commands Cheat Sheet

Quick reference for all installation commands.

## 🚀 Quick Install (Copy-Paste Ready)

### Complete Setup (Recommended)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install ALL dependencies
pip install -r requirements.txt

# 4. Verify installation
python verify_packages.py
```

### Minimal Setup (Fallback)

```bash
# If full install fails, use minimal requirements
pip install -r requirements-minimal.txt
```

### Manual Core Installation

```bash
# Install core packages one by one
pip install pydantic>=2.0.0
pip install requests>=2.31.0
pip install networkx>=3.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install streamlit>=1.28.0
pip install openpyxl>=3.1.0
pip install python-dotenv>=1.0.0
```

## 📋 What Each Command Does

### `pip install -r requirements.txt`
**Purpose:** Installs ALL packages from requirements.txt file
**Includes:** Core, optional, and development packages
**Size:** ~150MB download, ~300MB installed
**Time:** 2-5 minutes

**Installs:**
- ✅ pydantic>=2.0.0 - Data validation
- ✅ requests>=2.31.0 - HTTP client
- ✅ networkx>=3.0 - Graph algorithms
- ✅ pandas>=2.0.0 - Data manipulation
- ✅ numpy>=1.24.0 - Numerical computing
- ✅ streamlit>=1.28.0 - Web UI
- ✅ openpyxl>=3.1.0 - Excel support
- ✅ xlrd>=2.0.0 - Excel reading
- ✅ python-dotenv>=1.0.0 - Environment variables
- ✅ litellm>=1.20.0 - Cloud LLM support
- ✅ psycopg2-binary>=2.9.9 - PostgreSQL
- ✅ plotly>=5.17.0 - Visualization
- ✅ jsonschema>=4.19.0 - JSON validation
- ✅ colorlog>=6.7.0 - Enhanced logging
- ✅ python-dateutil>=2.8.0 - Date utilities
- ✅ pytest>=7.4.0 - Testing (dev)
- ✅ pytest-asyncio>=0.21.0 - Async testing (dev)
- ✅ black>=23.0.0 - Code formatting (dev)
- ✅ pylint>=3.0.0 - Linting (dev)
- ✅ mypy>=1.5.0 - Type checking (dev)

### `pip install -r requirements-minimal.txt`
**Purpose:** Installs only essential packages
**Includes:** Core functionality only
**Size:** ~80MB download, ~150MB installed
**Time:** 1-2 minutes

**Installs:**
- ✅ pydantic>=2.0.0
- ✅ requests>=2.31.0
- ✅ networkx>=3.0
- ✅ pandas>=2.0.0
- ✅ numpy>=1.24.0
- ✅ streamlit>=1.28.0
- ✅ openpyxl>=3.1.0
- ✅ python-dotenv>=1.0.0

## 🔧 Additional Commands

### Check Installed Packages
```bash
# List all installed packages
pip list

# Check specific packages
pip list | grep -E "pydantic|streamlit|requests|networkx|pandas"

# Show package details
pip show pydantic
```

### Verify Installation
```bash
# Automated verification
python verify_packages.py

# Manual verification
python -c "import pydantic, streamlit, requests, networkx, pandas; print('✅ Core packages OK')"
```

### Upgrade Packages
```bash
# Upgrade single package
pip install --upgrade pydantic

# Upgrade all packages in requirements
pip install --upgrade -r requirements.txt
```

### Uninstall Packages
```bash
# Uninstall single package
pip uninstall pydantic

# Uninstall all packages from requirements
pip uninstall -r requirements.txt -y
```

### Install Optional Packages

```bash
# Install cloud LLM support
pip install litellm>=1.20.0

# Install PostgreSQL support
pip install psycopg2-binary>=2.9.9

# Install visualization
pip install plotly>=5.17.0

# Install all development tools
pip install pytest>=7.4.0 pytest-asyncio>=0.21.0 black>=23.0.0 pylint>=3.0.0 mypy>=1.5.0
```

## 🐛 Troubleshooting Commands

### Fix Common Issues

```bash
# Clear pip cache and reinstall
pip cache purge
pip install -r requirements.txt --no-cache-dir

# Force reinstall specific package
pip install --force-reinstall pydantic

# Install with verbose output
pip install -r requirements.txt -v

# Skip dependency checks
pip install -r requirements.txt --no-deps
```

### Platform-Specific Issues

**macOS - psycopg2 fails:**
```bash
brew install postgresql
pip install psycopg2-binary>=2.9.9
```

**Windows - Visual C++ errors:**
```bash
# Use binary wheels (included in requirements)
pip install psycopg2-binary>=2.9.9
```

**Linux - Missing system dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libpq-dev

# Install packages
pip install -r requirements.txt
```

## 📦 Package Management Tips

### Create requirements.txt from installed packages
```bash
pip freeze > requirements-frozen.txt
```

### Compare installed vs required
```bash
pip check
```

### Show outdated packages
```bash
pip list --outdated
```

### Create virtual environment with system packages
```bash
python3 -m venv --system-site-packages venv
```

## ✅ Verification Checklist

After running `pip install -r requirements.txt`, verify:

```bash
# 1. Check pip installed successfully
pip --version

# 2. Check core packages
python -c "import pydantic; print(f'pydantic {pydantic.__version__}')"
python -c "import streamlit; print(f'streamlit {streamlit.__version__}')"
python -c "import pandas; print(f'pandas {pandas.__version__}')"

# 3. Run verification script
python verify_packages.py

# 4. Test project imports
python -c "from schema_parser import SchemaParser; print('✅ Project modules OK')"

# 5. Try running the app
streamlit run app.py --help
```

## 🎯 Installation Scenarios

### Scenario 1: Fresh Install (Most Common)
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python verify_packages.py
```

### Scenario 2: Minimal Install (Quick Test)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
python verify_packages.py
```

### Scenario 3: Development Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .  # If setup.py exists
pre-commit install  # If using pre-commit
```

### Scenario 4: Production Deploy
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
python verify_packages.py
```

## 📊 Size Reference

| Install Type | Download | Installed | Time |
|--------------|----------|-----------|------|
| Full (`requirements.txt`) | ~150MB | ~300MB | 2-5 min |
| Minimal (`requirements-minimal.txt`) | ~80MB | ~150MB | 1-2 min |
| Core only (manual) | ~70MB | ~140MB | 1-2 min |

## 🚀 One-Line Install

For experienced users:

```bash
python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python verify_packages.py
```

Or with the script:
```bash
chmod +x quickstart.sh && ./quickstart.sh
```

---

**Pro Tip:** Always activate your virtual environment before running pip commands!

**Reminder:** Run `python verify_packages.py` after installation to confirm everything is working.
