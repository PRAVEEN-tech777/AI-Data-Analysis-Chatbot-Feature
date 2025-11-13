# Architecture Documentation

## System Overview

The AI-Powered Database View Generator is a modular system that uses Large Language Models to automatically generate semantically meaningful database views from schema definitions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Streamlit UI │  │  CLI Tool    │  │  Python API  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
          ┌──────────────────▼───────────────────┐
          │      Pipeline Orchestrator           │
          │    (pipeline.py)                     │
          └──────────────────┬───────────────────┘
                             │
          ┌──────────────────┴───────────────────┐
          │                                       │
    ┌─────▼──────┐                    ┌──────────▼────────┐
    │   Schema   │                    │   LLM Interface   │
    │   Parser   │                    │  (llm_interface)  │
    │ (schema_   │                    │                   │
    │  parser)   │                    │  ┌─────────────┐  │
    └─────┬──────┘                    │  │   Ollama    │  │
          │                           │  └─────────────┘  │
          │                           │  ┌─────────────┐  │
    ┌─────▼──────┐                    │  │  LiteLLM    │  │
    │ Validation │◄───────────────────┤  └─────────────┘  │
    │  Engine    │                    └───────────────────┘
    │ (validator)│
    └─────┬──────┘
          │
    ┌─────▼──────────┐
    │   Post         │
    │  Processing    │
    │ (deduplication)│
    └─────┬──────────┘
          │
    ┌─────▼──────────┐
    │  Results &     │
    │   Execution    │
    │ (db_executor)  │
    └────────────────┘
```

## Core Components

### 1. Schema Parser (`schema_parser.py`)

**Purpose:** Load, parse, and index database schemas from JSON files.

**Key Features:**
- JSON schema loading with validation
- Table and column indexing for fast lookups
- Foreign key relationship graph building (using NetworkX)
- Primary key identification using heuristics
- Semantic context generation for LLM prompts

**Data Structures:**
```python
@dataclass
class Column:
    name: str
    type: str
    description: str
    is_primary_key: bool
    is_foreign_key: bool
    references: Optional[Tuple[str, str]]

@dataclass
class Table:
    name: str
    columns: List[Column]
    foreign_keys: List[Dict[str, str]]
    description: str

class SchemaParser:
    tables: Dict[str, Table]
    relationship_graph: nx.DiGraph  # For join path finding
```

**Algorithms:**
- **Graph-based Join Path Finding:** Uses NetworkX BFS to find shortest path between tables through FK relationships
- **Primary Key Detection:** Heuristic-based (looks for 'id' or '*_id' integer columns)

### 2. LLM Interface (`llm_interface.py`)

**Purpose:** Unified interface to multiple LLM providers with structured output support.

**Supported Providers:**
- **Ollama:** Local LLM inference (llama3.2, llama3, mistral, etc.)
- **LiteLLM:** Cloud providers (OpenAI, Anthropic, Google, etc.)

**Key Features:**
- Structured JSON output with retry logic
- Automatic JSON extraction from markdown-wrapped responses
- Temperature and token control
- Async/await support for non-blocking execution

**Prompt Engineering:**
```python
System Prompt:
- Role definition (database architect)
- Output format specification (JSON schema)
- Constraints (use only existing tables/columns)
- Business context guidance

User Prompt:
- Full schema context with descriptions
- Requested number of views
- Business requirements emphasis
```

**JSON Extraction Pipeline:**
1. Remove markdown code fences (```json ... ```)
2. Parse complete JSON object
3. Validate against Pydantic schema
4. Salvage partial responses if possible

### 3. Pydantic Models (`models.py`)

**Purpose:** Type-safe data models for structured LLM outputs and validation.

**Model Hierarchy:**
```python
ViewGenerationResponse
  └── views: List[ViewDefinition]
        └── name: str
        └── description: str
        └── query: QuerySpecification
              └── select: List[str]
              └── from_table: str
              └── joins: List[JoinSpecification]
                    └── type: str (INNER/LEFT/RIGHT/FULL)
                    └── table: str
                    └── on: str
              └── where: Optional[List[str]]
              └── group_by: Optional[List[str]]
              └── having: Optional[List[str]]
              └── order_by: Optional[List[str]]
```

**Validation Rules:**
- View names must be lowercase snake_case
- Join types must be valid SQL types
- Field aliases supported (from_table vs "from")

### 4. Validation Engine (`validation.py`)

**Purpose:** Comprehensive validation of generated views against schema.

**Validation Layers:**

#### Layer 1: Foreign Key Path Validation
- **Requirement:** All joins must follow existing FK relationships
- **Algorithm:** Graph traversal using schema relationship graph
- **Implementation:** NetworkX shortest_path
- **Error Handling:** Report missing FK paths with clear messages

#### Layer 2: Semantic Validation
- **Requirement:** Joined tables should be semantically related
- **Algorithm:** Jaccard similarity on column names and descriptions
- **Threshold:** Configurable (default 0.05)
- **Metrics:** 
  - Token extraction from column names and descriptions
  - Intersection over union (IoU)
  - Warning if similarity < threshold

#### Layer 3: SQL Compilability
- **Requirement:** All references must be valid
- **Checks:**
  - Table existence
  - Column existence in referenced tables
  - Qualified column references (table.column)
  - Aggregation function syntax
  - GROUP BY validity
  - ORDER BY validity

**Validation Result Structure:**
```python
class ValidationResult:
    is_valid: bool
    view_name: str
    errors: List[str]
    warnings: List[str]
    sql: Optional[str]  # Generated SQL if valid
    semantic_score: Optional[float]
```

### 5. Pipeline Orchestrator (`pipeline.py`)

**Purpose:** Coordinate end-to-end workflow from schema to validated views.

**Workflow Stages:**

```python
async def run(self) -> AnalysisResult:
    # Stage 1: Generate views from LLM
    views = await self.generate_views(num_views)
    
    # Stage 2: Post-process (deduplicate)
    unique_views, stats = self.post_process(views)
    
    # Stage 3: Validate all views
    validation_results = self.validate_views(unique_views)
    
    # Stage 4: Aggregate results
    return AnalysisResult(...)
```

**Key Methods:**
- `generate_views()`: Call LLM with schema context
- `_salvage_views()`: Recover from malformed JSON responses
- `validate_views()`: Run comprehensive validation
- `post_process()`: Deduplicate and gather statistics
- `export_results()`: Save to JSON file

**Error Handling:**
- LLM failures: Retry with exponential backoff
- JSON parsing errors: Attempt salvage
- Validation errors: Continue processing other views
- Fatal errors: Return empty result with error message

### 6. Database Executor (`db_executor.py`, `excel_db_executor.py`)

**Purpose:** Execute validated views against databases or Excel files.

**Database Executor (PostgreSQL):**
```python
class DatabaseExecutor:
    def execute_view(view_sql, limit) -> (bool, DataFrame, error)
    def test_connection() -> (bool, message)
    def get_row_count(view_sql) -> (bool, count, error)
```

**Excel Executor (Demo Mode):**
```python
class ExcelDatabaseExecutor:
    def execute_view(view_sql, limit) -> (bool, DataFrame, error)
    # Supports: SELECT, FROM, JOIN, WHERE, GROUP BY, ORDER BY
```

**SQL Execution Pipeline:**
1. Clean SQL (remove CREATE VIEW wrapper)
2. Add LIMIT clause if specified
3. Execute query via psycopg2 or pandas
4. Return DataFrame with results
5. Handle errors gracefully

### 7. Configuration Management (`config.py`)

**Purpose:** Centralized configuration from environment variables.

**Configuration Classes:**
```python
class LLMConfig:
    provider: str
    ollama_url: str
    ollama_model: str
    litellm_model: str
    temperature: float
    max_retries: int

class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

class AppConfig:
    log_level: str
    output_dir: str
    min_semantic_score: float
    enable_semantic_validation: bool
```

**Environment Variable Mapping:**
- `LLM_PROVIDER` → ollama or litellm
- `OLLAMA_URL` → http://localhost:11434
- `OLLAMA_MODEL` → llama3.2:3b
- `LOG_LEVEL` → INFO, DEBUG, WARNING, ERROR

## User Interfaces

### Streamlit UI (`app.py`)

**Features:**
- Schema upload or sample loading
- LLM configuration panel
- Real-time view generation
- Results visualization (valid/invalid views)
- Database connection management
- View execution against databases
- AI-powered data analysis chatbot
- Export to JSON and SQL

**UI Flow:**
```
1. Load Schema (upload or sample)
   ↓
2. Configure LLM (provider, model, settings)
   ↓
3. Generate Views (set count, temperature)
   ↓
4. Review Results (tabs for valid/invalid)
   ↓
5. Connect Database (optional)
   ↓
6. Execute View
   ↓
7. AI Analysis (chatbot for insights)
   ↓
8. Export (JSON, SQL, CSV)
```

**AI Chatbot Architecture:**
- Context: Data summary + column statistics + sample rows
- LLM: Same provider as view generation
- Memory: Conversation history (last 3 exchanges)
- Constraints: Analysis limited to data in view results

### CLI Tool (`cli.py`)

**Usage Pattern:**
```bash
python cli.py \
  --schema <path> \
  --num-views <int> \
  --provider <ollama|litellm> \
  --model <name> \
  --temperature <float> \
  --output <json_path> \
  --sql-output <sql_path>
```

**Output:**
- Console: Summary statistics
- JSON file: Complete results with validation details
- SQL file: All valid views as CREATE VIEW statements

### Python API

**Programmatic Usage:**
```python
# High-level API
from pipeline import run_pipeline_from_file
results = await run_pipeline_from_file(
    schema_file='schema.json',
    num_views=5
)

# Low-level API
schema = SchemaParser.from_file('schema.json')
pipeline = ViewGeneratorPipeline(schema)
results = await pipeline.run(num_views=5)
```

## Data Flow

### View Generation Flow

```
1. User Input
   ├── Schema JSON file
   ├── Number of views
   └── LLM parameters
   
2. Schema Processing
   ├── Parse JSON → Table/Column objects
   ├── Build FK graph (NetworkX)
   ├── Identify primary keys
   └── Generate semantic context
   
3. LLM Generation
   ├── Build system prompt (role + constraints)
   ├── Build user prompt (schema + requirements)
   ├── Call LLM API (async)
   ├── Extract JSON from response
   └── Parse to Pydantic models
   
4. Validation
   ├── Check base table exists
   ├── Validate each join:
   │   ├── Check FK path exists
   │   ├── Compute semantic similarity
   │   └── Verify join condition syntax
   ├── Validate SELECT columns
   ├── Validate WHERE/HAVING conditions
   ├── Validate GROUP BY/ORDER BY
   └── Generate SQL if valid
   
5. Post-Processing
   ├── Deduplicate views
   ├── Compute statistics
   └── Build AnalysisResult
   
6. Output
   ├── JSON results file
   ├── SQL file (valid views)
   └── Console summary
```

### View Execution Flow

```
1. View Selection
   └── User selects valid view from results
   
2. Database Connection
   ├── PostgreSQL: Connection string
   └── Excel: File path
   
3. SQL Preparation
   ├── Remove CREATE VIEW wrapper
   ├── Add LIMIT clause
   └── Validate syntax
   
4. Execution
   ├── Execute query via connector
   ├── Fetch results into DataFrame
   └── Handle errors
   
5. AI Analysis (Optional)
   ├── Prepare data summary
   ├── User asks question
   ├── Build context with data
   ├── Call LLM for analysis
   └── Display response in chat
   
6. Export
   ├── CSV download
   ├── Excel download
   └── Full dataset access
```

## Key Algorithms

### 1. Join Path Finding (Schema Parser)

**Algorithm:** Breadth-First Search on FK relationship graph

```python
def get_join_path(table1: str, table2: str) -> List[Tuple]:
    # Use NetworkX shortest path
    path_nodes = nx.shortest_path(graph, table1, table2)
    
    # Build join conditions from path edges
    join_path = []
    for i in range(len(path_nodes) - 1):
        from_table = path_nodes[i]
        to_table = path_nodes[i + 1]
        edge_data = graph.get_edge_data(from_table, to_table)
        join_path.append((
            from_table, 
            edge_data['column'],
            to_table, 
            edge_data['references']
        ))
    
    return join_path
```

**Complexity:** O(V + E) where V = tables, E = foreign keys

### 2. Semantic Similarity (Validator)

**Algorithm:** Jaccard similarity on tokenized column metadata

```python
def validate_semantic_relevance(table1: Table, table2: Table) -> float:
    # Extract tokens from column names and descriptions
    tokens1 = set()
    for col in table1.columns:
        tokens1.update(tokenize(col.name))
        if col.description:
            tokens1.update(tokenize(col.description))
    
    tokens2 = set()
    for col in table2.columns:
        tokens2.update(tokenize(col.name))
        if col.description:
            tokens2.update(tokenize(col.description))
    
    # Compute Jaccard similarity
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union) if union else 0.0
```

**Complexity:** O(n × m) where n, m = column counts

### 3. View Deduplication (Pipeline)

**Algorithm:** Signature-based deduplication using frozenset

```python
def deduplicate_views(views: List[ViewDefinition]) -> List[ViewDefinition]:
    unique_views = []
    seen_signatures = set()
    
    for view in views:
        # Build signature from tables and columns
        tables = {view.query.from_table.split()[0]}
        for join in view.query.joins:
            tables.add(join.table.split()[0])
        
        columns = sorted(view.query.select)
        signature = (frozenset(tables), tuple(columns))
        
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_views.append(view)
    
    return unique_views
```

**Complexity:** O(n × k) where n = views, k = avg columns per view

## Performance Characteristics

### Scalability Limits

| Component | Limit | Notes |
|-----------|-------|-------|
| Schema Size | 1000 tables | Tested up to 1000 tables |
| Columns per Table | 500 | No hard limit |
| Foreign Keys | 10000 | NetworkX handles well |
| View Generation | 20 views/request | Configurable |
| LLM Context | 8K-128K tokens | Model-dependent |
| Query Results | 10K rows | UI pagination |

### Performance Metrics

| Operation | Time (Typical) | Notes |
|-----------|---------------|-------|
| Schema Loading | <1s | 100 tables |
| FK Graph Build | <1s | 1000 relationships |
| LLM Generation | 5-30s | Per batch of 5 views |
| Validation | <1s | Per view |
| Post-processing | <100ms | Deduplication |
| Database Execution | 1-10s | Query-dependent |

### Optimization Strategies

1. **Caching:**
   - Schema parsing results cached in session
   - LLM responses cached for identical prompts
   - Database connections pooled

2. **Async Processing:**
   - LLM calls are async
   - View validation parallelizable (future)

3. **Batching:**
   - Generate multiple views in single LLM call
   - Batch database queries where possible

## Security Considerations

### Input Validation
- Schema JSON validated against expected structure
- SQL injection protection via parameterized queries
- User input sanitized in UI

### Credentials Management
- Environment variables for sensitive data
- .env file not committed to git
- Database passwords never logged

### LLM Safety
- System prompts restrict output format
- No user input passed directly to shell
- Rate limiting on API calls

### Access Control
- Read-only database credentials recommended
- No destructive SQL operations (DROP, DELETE)
- View creation requires explicit permissions

## Error Handling Strategy

### Graceful Degradation
```python
try:
    views = await generate_views()
except LLMError:
    # Continue with partial results
    views = salvage_from_cache()

if not views:
    # Return empty result with error
    return AnalysisResult(total_generated=0, error=...)
```

### Error Types

1. **Schema Errors:** Invalid JSON, missing tables
   - Return: Immediate failure with detailed message
   
2. **LLM Errors:** API timeout, invalid JSON
   - Return: Retry 3x, then salvage or empty result
   
3. **Validation Errors:** Invalid join, missing column
   - Return: Mark view as invalid, continue processing
   
4. **Database Errors:** Connection failed, query error
   - Return: Error message, disable execution features

### Logging Strategy
```python
logger.info("High-level operations")
logger.debug("Detailed execution traces")
logger.warning("Recoverable issues")
logger.error("Validation failures")
logger.exception("Fatal errors with stack trace")
```

## Testing Strategy

### Unit Tests
- Schema parser: Table/column lookups
- Validator: Each validation layer
- LLM interface: JSON extraction
- Models: Pydantic validation

### Integration Tests
- End-to-end pipeline
- Database execution
- UI workflows

### Test Data
- `demo_schema.json`: Simple 2-table schema
- `test_schema.json`: Complex multi-table schema
- `demo_database.xlsx`: Excel test database

## Future Enhancements

### Planned Features
1. **Advanced Query Optimization**
   - Index recommendations
   - Query plan analysis
   
2. **Multi-database Support**
   - MySQL, SQLite, Oracle
   - NoSQL databases
   
3. **View Optimization**
   - Materialized view suggestions
   - Partition recommendations
   
4. **Collaborative Features**
   - View sharing and versioning
   - Team review workflow
   
5. **Advanced AI Features**
   - Natural language query generation
   - Automatic documentation
   - Performance prediction

### Architectural Improvements
1. **Caching Layer:** Redis for LLM response caching
2. **Job Queue:** Celery for async view generation
3. **API Server:** FastAPI REST API
4. **Web UI:** React frontend (separate from Streamlit)

## Dependencies

### Core Dependencies
```
pydantic >= 2.0.0          # Data validation
requests >= 2.31.0         # HTTP client
networkx >= 3.0            # Graph algorithms
pandas                     # Data manipulation
```

### Optional Dependencies
```
psycopg2-binary >= 2.9.9   # PostgreSQL
litellm >= 1.20.0          # Cloud LLM providers
streamlit >= 1.28.0        # Web UI
openpyxl                   # Excel support
plotly >= 5.17.0           # Visualization
```

### Development Dependencies
```
pytest >= 7.4.0            # Testing
pytest-asyncio >= 0.21.0   # Async testing
black                      # Code formatting
pylint                     # Linting
mypy                       # Type checking
```

## Deployment

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Production (Docker)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### Cloud Deployment
- **Streamlit Cloud:** Direct deployment from GitHub
- **AWS ECS:** Docker container on Fargate
- **Google Cloud Run:** Serverless container
- **Heroku:** Buildpack deployment

---

**Last Updated:** 2025-01-13
**Version:** 1.0.0
**Author:** AI Engineering Assessment
