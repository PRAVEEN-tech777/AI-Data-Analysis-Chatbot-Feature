# Installation Guide for AI Database View Generator

## Overview
This guide provides step-by-step instructions for installing and setting up the AI-Powered Database View Generator for the interviewer or evaluator.

---

## ⚡ Quick Install (5 Minutes)

### Prerequisites
- Python 3.8+ installed
- Internet connection
- 4GB+ RAM recommended

### One-Command Setup (Linux/macOS)

```bash
# Clone repo, setup environment, and start
git clone <repo-url> && cd ai-database-view-generator && chmod +x quickstart.sh && ./quickstart.sh
```

Then choose:
```bash
# Option 1: Launch UI (Recommended)
streamlit run app.py

# Option 2: CLI test
python cli.py --schema demo_schema.json --num-views 3
```

---

## 📋 Detailed Installation

### Step 1: System Requirements Check

**Required Software:**
```bash
# Check Python version (need 3.8+)
python3 --version

# Check pip is available
pip3 --version

# Install git if needed
git --version
```

**For Windows Users:**
- Download Python from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Install Git from: https://git-scm.com/download/win

### Step 2: Clone Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd ai-database-view-generator

# Or download ZIP and extract
# Then: cd ai-database-view-generator
```

### Step 3: Create Virtual Environment

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) in your prompt
```

**Windows:**
```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) in your prompt
```

### Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "pydantic|streamlit|requests"
```

**Expected packages:**
- pydantic >= 2.0.0
- streamlit >= 1.28.0
- requests >= 2.31.0
- networkx >= 3.0
- pandas
- openpyxl
- psycopg2-binary (optional, for PostgreSQL)
- litellm (optional, for cloud LLMs)

### Step 5: Configure Environment

**Create `.env` file:**
```bash
# Copy example if provided
cp .env.example .env

# Or create new file
touch .env
```

**Edit `.env` with minimal config:**
```bash
# Minimum configuration for demo
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
LOG_LEVEL=INFO
```

### Step 6: Setup LLM Provider

#### Option A: Ollama (Recommended - No API Keys Needed)

**Install Ollama:**
1. Visit: https://ollama.com/download
2. Download installer for your OS
3. Run installer

**Pull Model:**
```bash
# Pull a small model (3B parameters, ~2GB)
ollama pull llama3.2:3b

# Verify model is available
ollama list
```

**Start Ollama Server:**
```bash
# Start in background (Linux/macOS)
ollama serve &

# Or just run (Windows/all platforms)
ollama serve
```

**Test Connection:**
```bash
# Test Ollama is responding
curl http://localhost:11434/api/version

# Or use browser: http://localhost:11434
```

#### Option B: Skip LLM for Now (Testing Only)

You can test the schema parser and validator without LLM:
```bash
# This will fail at generation but test everything else
python cli.py --schema demo_schema.json --num-views 1
```

---

## 🧪 Verification Tests

### Test 1: Python Environment
```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Test imports
python -c "import pydantic, streamlit, requests, networkx; print('✅ All imports successful')"
```

### Test 2: Schema Parser
```python
# Create test_schema.py
python3 << 'EOF'
from schema_parser import SchemaParser
schema = SchemaParser.from_file('demo_schema.json')
print(f"✅ Loaded schema with {len(schema.tables)} tables")
for name in schema.get_all_tables():
    print(f"  - {name}")
EOF
```

### Test 3: Demo Data Generation
```bash
# Generate demo Excel database
python create_demo_data.py

# Should create demo_database.xlsx
ls -lh demo_database.xlsx
```

### Test 4: CLI Quick Test
```bash
# Test without LLM (will fail at generation)
python cli.py --schema demo_schema.json --num-views 1 2>&1 | head -20

# Should show schema loaded successfully
```

### Test 5: Streamlit UI
```bash
# Launch UI
streamlit run app.py

# Should open browser at http://localhost:8501
# Try loading sample schema in sidebar
```

---

## 🎯 Quick Start Scenarios

### Scenario 1: Demo with Excel (No Database Required)

**Perfect for quick evaluation without database setup**

```bash
# 1. Generate demo data
python create_demo_data.py

# 2. Start UI
streamlit run app.py

# 3. In UI:
#    - Load "Sample Schema" from sidebar
#    - Configure LLM (Ollama recommended)
#    - Generate 3 views
#    - Connect to Excel demo database
#    - Execute and analyze views
```

### Scenario 2: CLI Evaluation

**Quick command-line testing**

```bash
# Basic test with 3 views
python cli.py \
  --schema demo_schema.json \
  --num-views 3 \
  --provider ollama \
  --model llama3.2:3b

# With output files
python cli.py \
  --schema demo_schema.json \
  --num-views 5 \
  --output results.json \
  --sql-output views.sql \
  --log-level INFO
```

### Scenario 3: Python API Testing

**For programmatic evaluation**

```python
# Create test_api.py
import asyncio
from pipeline import run_pipeline_from_file

async def test():
    results = await run_pipeline_from_file(
        schema_file='demo_schema.json',
        num_views=3,
        provider='ollama',
        model='llama3.2:3b'
    )
    print(f"✅ Generated {results.total_generated} views")
    print(f"✅ Valid: {results.valid_views}")
    print(f"✅ Invalid: {results.invalid_views}")
    return results

# Run test
if __name__ == "__main__":
    results = asyncio.run(test())
```

```bash
# Execute test
python test_api.py
```

---

## 🔧 Troubleshooting Installation

### Issue: Python version too old
```bash
# Error: Python 3.8+ required
# Solution: Update Python
# Ubuntu/Debian:
sudo apt update && sudo apt install python3.10

# macOS:
brew install python@3.10

# Windows: Download from python.org
```

### Issue: pip install fails
```bash
# Error: Could not install packages
# Solution 1: Upgrade pip
pip install --upgrade pip setuptools wheel

# Solution 2: Install with no cache
pip install --no-cache-dir -r requirements.txt

# Solution 3: Install individually
pip install pydantic requests networkx streamlit pandas
```

### Issue: Virtual environment not activating
```bash
# Windows PowerShell error
# Solution: Change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again
venv\Scripts\activate
```

### Issue: Ollama connection failed
```bash
# Error: Cannot connect to Ollama
# Solution 1: Check if running
curl http://localhost:11434/api/version

# Solution 2: Start Ollama
ollama serve

# Solution 3: Use different port
# Edit .env:
OLLAMA_URL=http://localhost:11434
```

### Issue: Module 'psycopg2' not found (when using PostgreSQL)
```bash
# Error: No module named 'psycopg2'
# Solution: Install binary version
pip install psycopg2-binary

# Or install from source (requires PostgreSQL dev packages)
# Ubuntu/Debian:
sudo apt-get install libpq-dev python3-dev
pip install psycopg2
```

### Issue: Streamlit port already in use
```bash
# Error: Port 8501 already in use
# Solution: Use different port
streamlit run app.py --server.port 8502
```

---

## 📦 Alternative Installation Methods

### Method 1: Docker (Coming Soon)
```bash
# Build image
docker build -t ai-view-generator .

# Run container
docker run -p 8501:8501 ai-view-generator
```

### Method 2: Conda Environment
```bash
# Create conda environment
conda create -n viewgen python=3.10
conda activate viewgen

# Install dependencies
pip install -r requirements.txt
```

### Method 3: System-wide Installation (Not Recommended)
```bash
# Install globally without venv
pip3 install -r requirements.txt

# Use full paths
python3 /path/to/cli.py --schema demo_schema.json
```

---

## ✅ Post-Installation Checklist

After installation, verify:

- [ ] Python 3.8+ is installed and accessible
- [ ] Virtual environment is created and activated
- [ ] All packages from `requirements.txt` installed successfully
- [ ] `.env` file created with basic configuration
- [ ] Ollama installed and running (or cloud LLM configured)
- [ ] Demo schema files (`demo_schema.json`) are present
- [ ] CLI runs without import errors
- [ ] Streamlit UI launches successfully
- [ ] Can load sample schema in UI
- [ ] Can generate at least 1 view (even if invalid)

**Verification Command:**
```bash
# Run this to verify everything
python3 << 'EOF'
import sys
print(f"✅ Python {sys.version}")

try:
    import pydantic, streamlit, requests, networkx, pandas
    print("✅ All core packages imported")
except ImportError as e:
    print(f"❌ Import failed: {e}")

try:
    from schema_parser import SchemaParser
    schema = SchemaParser.from_file('demo_schema.json')
    print(f"✅ Schema parser works: {len(schema.tables)} tables loaded")
except Exception as e:
    print(f"❌ Schema parser failed: {e}")

print("\n✅ Installation successful! Ready to use.")
EOF
```

---

## 🚀 Next Steps After Installation

1. **Run Quick Demo:**
   ```bash
   streamlit run app.py
   # Load sample schema → Generate 3 views
   ```

2. **Review Architecture:**
   - Check `README.md` for architecture overview
   - Review `ARCHITECTURE.md` for detailed design

3. **Evaluate Features:**
   - Schema parsing and indexing
   - LLM-based view generation
   - Validation (FK, semantic, SQL)
   - Excel demo mode
   - AI data analysis chatbot

4. **Test Custom Schema:**
   - Create your own `my_schema.json`
   - Test with CLI or UI
   - Review validation results

---

## 📞 Support for Interviewers

If you encounter issues during evaluation:

1. **Check Logs:**
   ```bash
   # Run with debug logging
   python cli.py --schema demo_schema.json --log-level DEBUG
   ```

2. **Minimal Test:**
   ```bash
   # Test without LLM generation (validates setup)
   python -c "from schema_parser import SchemaParser; s=SchemaParser.from_file('demo_schema.json'); print('OK')"
   ```

3. **Docker Alternative:**
   - If local setup fails, Docker image available
   - Contact for pre-built container

4. **Demo Video:**
   - Screen recording available showing full workflow
   - Contact if needed for evaluation

---

## 📚 Additional Resources

- **README.md** - Main documentation
- **ARCHITECTURE.md** - System design details
- **API_REFERENCE.md** - Python API documentation
- **demo_schema.json** - Sample schema for testing
- **create_demo_data.py** - Demo data generator

---

**Installation Time:** ~5-10 minutes
**Skill Level Required:** Basic Python knowledge
**Supported Platforms:** Linux, macOS, Windows
**LLM Provider:** Ollama (free) or LiteLLM (API key required)

---

**For Evaluation:** The system is ready to use immediately after installation with the demo schema and Excel database. No external database setup required for initial evaluation.
