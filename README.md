# AI-Powered Database View Generator

An intelligent system that automatically generates semantically meaningful database views using Large Language Models (LLMs). This tool analyzes database schemas and creates optimized views for business analytics and reporting.

## 🌟 Key Features

- **Schema Parser**: Load and analyze database schemas from JSON files
- **AI-Powered View Generation**: Uses LLMs to generate meaningful database views
- **Comprehensive Validation**: Validates foreign key relationships, semantic relevance, and SQL compilability
- **Multiple Execution Modes**: Streamlit UI, CLI, and Python API
- **Database Execution**: Execute generated views against PostgreSQL or Excel files
- **AI Data Analysis**: Interactive chatbot for analyzing query results
- **Multi-Provider Support**: Works with Ollama (local) and LiteLLM (cloud providers)

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended for large schemas)

### Optional Requirements
- **Ollama**: For local LLM inference (recommended for beginners)
- **PostgreSQL**: For executing views against real databases
- **Excel**: For demo mode using Excel files as databases

## 🚀 Quick Start (3 Steps)

### Step 1: Clone or Download the Repository

```bash
git clone <your-repository-url>
cd ai-database-view-generator
```

### Step 2: Run the Setup Script

**For Linux/macOS:**
```bash
chmod +x quickstart.sh
./quickstart.sh
```

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Choose Your Interface

**Option A: Streamlit UI (Recommended for Beginners)**
```bash
streamlit run app.py
```

**Option B: Command Line Interface**
```bash
python cli.py --schema demo_schema.json --num-views 5
```

**Option C: Python API**
```python
from pipeline import run_pipeline_from_file
import asyncio

results = asyncio.run(
    run_pipeline_from_file('demo_schema.json', num_views=5)
)
```

## 📦 Installation (Detailed)

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Dependencies Include:**
- `pydantic>=2.0.0` - Data validation and schema parsing
- `requests>=2.31.0` - HTTP client for LLM API calls
- `networkx>=3.0` - Graph-based join path validation
- `psycopg2-binary>=2.9.9` - PostgreSQL database connector
- `litellm>=1.20.0` - Multi-provider LLM interface
- `streamlit>=1.28.0` - Web UI framework
- `pandas` - Data manipulation
- `openpyxl` - Excel file support

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_PROVIDER=ollama                          # or 'litellm'
OLLAMA_URL=http://localhost:11434            # Ollama server URL
OLLAMA_MODEL=llama3.2:3b                     # Ollama model name
OLLAMA_TIMEOUT=180                           # Request timeout in seconds

# For cloud LLMs (if using litellm)
LITELLM_MODEL=claude-sonnet-4-20250514       # Model identifier
OPENAI_API_KEY=your_openai_key_here          # Optional
ANTHROPIC_API_KEY=your_anthropic_key_here    # Optional

# Database Configuration (Optional - for real database execution)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

# Application Settings
LOG_LEVEL=INFO                               # DEBUG, INFO, WARNING, ERROR
OUTPUT_DIR=./output                          # Output directory
DEFAULT_NUM_VIEWS=5                          # Default number of views to generate
MAX_VIEWS=20                                 # Maximum views allowed
MIN_SEMANTIC_SCORE=0.05                      # Minimum semantic similarity score
ENABLE_SEMANTIC_VALIDATION=true              # Enable semantic validation
```

### 4. Setup LLM Provider

#### Option A: Ollama (Recommended for Local Development)

**Install Ollama:**
- Visit: https://ollama.com/download
- Download and install for your OS

**Pull a Model:**
```bash
# Pull a small, efficient model (recommended)
ollama pull llama3.2:3b

# Or pull a larger model for better quality
ollama pull llama3:8b
```

**Start Ollama Server:**
```bash
ollama serve
```

**Update `.env`:**
```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

#### Option B: Cloud LLM (OpenAI, Anthropic, etc.)

**Update `.env`:**
```bash
LLM_PROVIDER=litellm
LITELLM_MODEL=gpt-4  # or claude-sonnet-4-20250514
OPENAI_API_KEY=your_key_here  # or ANTHROPIC_API_KEY
```

## 🎮 Usage Guide

### Using the Streamlit UI

1. **Start the application:**
   ```bash
   streamlit run app.py
   ```

2. **Load a schema:**
   - Option 1: Upload your own schema JSON file
   - Option 2: Use the provided sample schema

3. **Configure LLM settings:**
   - Select provider (Ollama or LiteLLM)
   - Set model name
   - Adjust temperature (0.0 = deterministic, 1.0 = creative)

4. **Generate views:**
   - Set number of views to generate
   - Click "Generate Views"
   - Review valid and invalid views

5. **Execute and analyze (Optional):**
   - Connect to a database or use Excel demo
   - Select a valid view to execute
   - Use AI chatbot to analyze results

### Using the CLI

**Basic usage:**
```bash
python cli.py --schema demo_schema.json --num-views 5
```

**With output files:**
```bash
python cli.py \
  --schema demo_schema.json \
  --num-views 10 \
  --output results.json \
  --sql-output views.sql \
  --provider ollama \
  --model llama3.2:3b \
  --temperature 0.0
```

**Available CLI options:**
```
--schema         Path to schema JSON file (required)
--num-views      Number of views to generate (default: 5)
--provider       LLM provider: ollama or litellm (default: ollama)
--model          Model name (provider-specific)
--temperature    LLM temperature 0.0-1.0 (default: 0.0)
--output         Output file for JSON results
--sql-output     Output file for SQL scripts
--log-level      Logging level: DEBUG, INFO, WARNING, ERROR
```

### Using the Python API

**Basic example:**
```python
import asyncio
from pipeline import run_pipeline_from_file

# Generate views from schema file
results = asyncio.run(
    run_pipeline_from_file(
        schema_file='demo_schema.json',
        num_views=5,
        provider='ollama',
        model='llama3.2:3b',
        output_file='results.json'
    )
)

# Access results
print(f"Total Generated: {results.total_generated}")
print(f"Valid Views: {results.valid_views}")
print(f"Invalid Views: {results.invalid_views}")

# Process valid views
for view in results.views:
    if view.is_valid:
        print(f"\nView: {view.view_name}")
        print(f"SQL: {view.sql}")
```

**Advanced example with custom configuration:**
```python
from schema_parser import SchemaParser
from pipeline import ViewGeneratorPipeline
import asyncio

# Load schema
schema = SchemaParser.from_file('my_schema.json')

# Create pipeline with custom settings
pipeline = ViewGeneratorPipeline(
    schema=schema,
    llm_provider='ollama',
    llm_model='llama3.2:3b',
    temperature=0.2,
    max_retries=3
)

# Generate and validate views
results = asyncio.run(pipeline.run(num_views=10))

# Export results
pipeline.export_results(results, 'output/results.json')

# Execute views against database (optional)
from db_executor import DatabaseExecutor

executor = DatabaseExecutor('postgresql://user:pass@localhost:5432/db')
for view in results.views:
    if view.is_valid:
        success, df, error = executor.execute_view(view.sql, limit=100)
        if success:
            print(f"Executed {view.view_name}: {len(df)} rows")
```

## 📄 Schema Format

Your schema JSON file should follow this structure:

```json
{
  "tables": [
    {
      "name": "customers",
      "description": "Customer information",
      "columns": [
        {
          "name": "customer_id",
          "type": "integer",
          "description": "Unique customer identifier"
        },
        {
          "name": "name",
          "type": "text",
          "description": "Customer full name"
        }
      ],
      "foreign_keys": []
    },
    {
      "name": "orders",
      "description": "Customer orders",
      "columns": [
        {
          "name": "order_id",
          "type": "integer",
          "description": "Unique order identifier"
        },
        {
          "name": "customer_id",
          "type": "integer",
          "description": "Reference to customer"
        },
        {
          "name": "total_amount",
          "type": "numeric",
          "description": "Order total"
        }
      ],
      "foreign_keys": [
        {
          "column": "customer_id",
          "references_table": "customers",
          "references_column": "customer_id"
        }
      ]
    }
  ]
}
```

## 🧪 Demo Mode (No Database Required)

### Using Excel Files as Database

1. **Create or use demo database:**
   ```bash
   python create_demo_data.py
   ```
   This creates `demo_database.xlsx` with sample data.

2. **In Streamlit UI:**
   - Go to "Database Connection" section
   - Select "Excel File (Demo)"
   - Click "Connect to Demo Database"

3. **Execute views:**
   - Generate views as usual
   - Execute them against the Excel database
   - Analyze results with AI chatbot

### Sample Schemas Included

- `demo_schema.json` - Simple customer/orders schema for testing
- `test_schema.json` - More complex schema with multiple relationships

## 🔧 Troubleshooting

### Common Issues

**1. Ollama connection failed**
```
Error: Cannot connect to Ollama at http://localhost:11434
```
**Solution:**
- Check if Ollama is running: `ollama serve`
- Verify URL in `.env` or pass correct URL to CLI
- Try: `curl http://localhost:11434/api/version`

**2. Module not found errors**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**3. Database connection errors**
```
Failed to connect to database
```
**Solution:**
- Verify database is running
- Check connection string format
- Test credentials with `psql` or database client
- Ensure PostgreSQL port (5432) is accessible

**4. Out of memory errors**
```
RuntimeError: CUDA out of memory
```
**Solution:**
- Use smaller Ollama model: `llama3.2:3b` instead of larger ones
- Reduce `num_views` parameter
- Increase system RAM or use cloud LLM

**5. LLM generates invalid JSON**
```
Failed to extract JSON from LLM response
```
**Solution:**
- Lower temperature (more deterministic): `--temperature 0.0`
- Try different model (some models are better at structured output)
- Check model is compatible with JSON formatting

### Debug Mode

Enable detailed logging:
```bash
# In CLI
python cli.py --schema demo_schema.json --log-level DEBUG

# In .env
LOG_LEVEL=DEBUG
```

View logs in console for detailed execution trace.

## 📊 Output Examples

### JSON Results Format
```json
{
  "total_generated": 5,
  "valid_views": 3,
  "invalid_views": 2,
  "views": [
    {
      "is_valid": true,
      "view_name": "customer_order_summary",
      "errors": [],
      "warnings": [],
      "sql": "SELECT c.name, SUM(o.total_amount)...",
      "semantic_score": 0.85
    }
  ],
  "summary": {
    "success_rate": "60.0%",
    "duplicates_removed": 1
  }
}
```

### Generated SQL Format
```sql
-- View: customer_order_summary
-- Summarizes orders by customer with total spend
CREATE OR REPLACE VIEW customer_order_summary AS
SELECT 
    c.name AS customer_name,
    c.region,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS total_spend
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.name, c.region
ORDER BY total_spend DESC;
```

## 🏗️ Architecture

### Core Components

1. **Schema Parser** (`schema_parser.py`)
   - Loads and indexes database schemas
   - Builds foreign key relationship graphs
   - Provides semantic context for LLMs

2. **LLM Interface** (`llm_interface.py`)
   - Unified interface for multiple LLM providers
   - Handles structured JSON output
   - Retry logic and error handling

3. **View Validator** (`validation.py`)
   - Validates foreign key relationships
   - Checks semantic relevance
   - Ensures SQL compilability

4. **Pipeline** (`pipeline.py`)
   - Orchestrates end-to-end workflow
   - Manages generation, validation, and post-processing
   - Handles deduplication

5. **Database Executor** (`db_executor.py`, `excel_db_executor.py`)
   - Executes views against databases
   - Supports PostgreSQL and Excel
   - Returns results as DataFrames

6. **UI Layer** (`app.py`)
   - Interactive Streamlit interface
   - AI-powered data analysis chatbot
   - Visualization and export capabilities

### Data Flow

```
Schema JSON → Parser → LLM → View Definitions → Validator → Results
                                                      ↓
                                          Database Executor (optional)
                                                      ↓
                                            AI Analysis Chatbot
```

## 🤝 Requirements Met

This project fulfills all assessment requirements:

1. ✅ **Schema Parser**: Loads JSON schemas with table/column indexing
2. ✅ **LLM Interface**: Supports Ollama and LiteLLM with structured outputs
3. ✅ **Join Path Validation**: Graph-based FK relationship validation
4. ✅ **Semantic Validation**: Column similarity scoring
5. ✅ **Output Post-Processing**: Deduplication and result aggregation

## 📝 Development Notes

### Project Structure
```
.
├── schema_parser.py          # Schema loading and indexing
├── llm_interface.py          # LLM provider interface
├── models.py                 # Pydantic data models
├── validator.py              # View validation logic
├── pipeline.py               # Main orchestration
├── db_executor.py            # PostgreSQL execution
├── excel_db_executor.py      # Excel execution
├── config.py                 # Configuration management
├── app.py                    # Streamlit UI
├── cli.py                    # Command-line interface
├── create_demo_data.py       # Demo data generator
├── requirements.txt          # Python dependencies
├── quickstart.sh             # Quick setup script
├── demo_schema.json          # Sample schema
└── README.md                 # This file
```

### Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Code Quality

```bash
# Format code
black *.py

# Lint code
pylint *.py

# Type checking
mypy *.py
```

## 🔒 Security Notes

- Never commit `.env` file with real credentials
- Use environment variables for sensitive data
- Sanitize user inputs in production
- Limit LLM token usage to prevent abuse
- Use read-only database credentials for view execution

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review error logs with `--log-level DEBUG`
3. Ensure all dependencies are installed
4. Verify LLM provider is accessible

## 📄 License

This project is provided as-is for assessment purposes.

## 🎯 Next Steps

After installation:
1. ✅ Run `quickstart.sh` or manual setup
2. ✅ Start with Streamlit UI: `streamlit run app.py`
3. ✅ Load sample schema to see it in action
4. ✅ Generate 3-5 views for quick testing
5. ✅ Try Excel demo mode (no database needed)
6. ✅ Explore AI data analysis chatbot

---

**Built with Python, Streamlit, and LLMs** | **Assessment Project** | **2025**
