#!/bin/bash
# Quick start script for AI Database View Generator

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   AI-Powered Database View Generator - Quick Start         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate
echo "   ✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "   ✓ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "   ✓ .env created - please edit with your settings"
    echo ""
    echo "   Important: Update these values in .env:"
    echo "   - OLLAMA_URL (if using Ollama)"
    echo "   - DB_* settings (if using database)"
    echo "   - API keys (if using cloud LLMs)"
    echo ""
else
    echo "⚙️  .env file already exists"
fi
echo ""

# Check Ollama
echo "🤖 Checking Ollama connection..."
if curl -s http://192.168.7.50:7778/api/version > /dev/null 2>&1; then
    echo "   ✓ Ollama is accessible"
else
    echo "   ⚠️  Warning: Cannot connect to Ollama at http://192.168.7.50:7778"
    echo "   - Make sure Ollama is running: 'ollama serve'"
    echo "   - Or update OLLAMA_URL in .env"
fi
echo ""

# Usage instructions
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Ready to use! Choose an option:                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Option 1: Streamlit UI (Recommended for beginners)"
echo "   streamlit run app.py"
echo ""
echo "Option 2: Command Line (Quick test)"
echo "   python cli.py --schema test_schema.json --num-views 3"
echo ""
echo "Option 3: Command Line with output"
echo "   python cli.py --schema test_schema.json --num-views 5 --output results.json --sql-output views.sql"
echo ""
echo "Option 4: Interactive Python"
echo "   python"
echo "   >>> from pipeline import run_pipeline_from_file"
echo "   >>> import asyncio"
echo "   >>> results = asyncio.run(run_pipeline_from_file('test_schema.json', num_views=3))"
echo ""
echo "For more information, see README.md"
echo ""