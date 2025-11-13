"""
Schema Parser Module


Loads JSON schema files and builds an indexed representation with:
- Table and column lookups
- Foreign key relationship graph
- Primary key identification
- Semantic context generation
"""


import json
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
import networkx as nx
from pathlib import Path


logger = logging.getLogger(__name__)




@dataclass
class Column:
    """Represents a database column with metadata"""
    name: str
    type: str
    description: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[Tuple[str, str]] = None  # (table, column)
   
    def __hash__(self):
        return hash((self.name, self.type))




@dataclass
class Table:
    """Represents a database table"""
    name: str
    columns: List[Column] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    description: str = ""
   
    def get_column(self, col_name: str) -> Optional[Column]:
        """Retrieve column by name (case-insensitive)"""
        col_name_lower = col_name.lower()
        return next(
            (c for c in self.columns if c.name.lower() == col_name_lower),
            None
        )
   
    def __hash__(self):
        return hash(self.name)




class SchemaParser:
    """
    Parses JSON schema and builds internal representation.
   
    Requirement 1: Schema Parser - Load JSON, index tables, columns, and foreign keys
    """
   
    def __init__(self, schema_json: Dict[str, Any]):
        self.raw_schema = schema_json
        self.tables: Dict[str, Table] = {}
        self.relationship_graph = nx.DiGraph()
        self._parse()
   
    @classmethod
    def from_file(cls, file_path: str) -> "SchemaParser":
        """Load schema from JSON file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {file_path}")
       
        with open(path, 'r', encoding='utf-8') as f:
            schema_json = json.load(f)
       
        return cls(schema_json)
   
    @classmethod
    def from_dict(cls, schema_dict: Dict[str, Any]) -> "SchemaParser":
        """Load schema from dictionary"""
        return cls(schema_dict)
   
    def _parse(self):
        """Parse JSON schema into Table and Column objects"""
        tables_data = self.raw_schema.get('tables', [])
       
        if not tables_data:
            raise ValueError("Schema must contain 'tables' array")
       
        # First pass: create tables and columns
        for table_data in tables_data:
            table_name = table_data.get('name')
            if not table_name:
                logger.warning("Skipping table without name")
                continue
           
            table = Table(
                name=table_name,
                description=table_data.get('description', '')
            )
           
            # Parse columns
            for col_data in table_data.get('columns', []):
                col_name = col_data.get('name')
                if not col_name:
                    logger.warning(f"Skipping column without name in table {table_name}")
                    continue
               
                column = Column(
                    name=col_name,
                    type=col_data.get('type', 'unknown'),
                    description=col_data.get('description', '')
                )
                table.columns.append(column)
           
            # Store foreign keys for second pass
            table.foreign_keys = table_data.get('foreign_keys', [])
            self.tables[table_name] = table
       
        # Second pass: establish foreign key relationships
        for table_name, table in self.tables.items():
            for fk in table.foreign_keys:
                col_name = fk.get('column')
                ref_table = fk.get('references_table')
                ref_column = fk.get('references_column')
               
                if not all([col_name, ref_table, ref_column]):
                    logger.warning(
                        f"Incomplete foreign key definition in table {table_name}: {fk}"
                    )
                    continue
               
                # Verify referenced table exists
                if ref_table not in self.tables:
                    logger.warning(
                        f"Foreign key in {table_name}.{col_name} references "
                        f"non-existent table: {ref_table}"
                    )
                    continue
               
                # Mark column as foreign key
                column = table.get_column(col_name)
                if column:
                    column.is_foreign_key = True
                    column.references = (ref_table, ref_column)
                else:
                    logger.warning(
                        f"Foreign key references non-existent column: "
                        f"{table_name}.{col_name}"
                    )
                    continue
               
                # Add edge to relationship graph (bidirectional for path finding)
                self.relationship_graph.add_edge(
                    table_name,
                    ref_table,
                    column=col_name,
                    references=ref_column,
                    direction='forward'
                )
                self.relationship_graph.add_edge(
                    ref_table,
                    table_name,
                    column=ref_column,
                    references=col_name,
                    direction='reverse'
                )
       
        # Third pass: identify primary keys (heuristic-based)
        self._identify_primary_keys()
       
        logger.info(
            f"Parsed schema: {len(self.tables)} tables, "
            f"{sum(len(t.columns) for t in self.tables.values())} columns, "
            f"{len(self.relationship_graph.edges()) // 2} foreign keys"
        )
   
    def _identify_primary_keys(self):
        """
        Identify primary keys using heuristics:
        - Column named 'id' that is not a foreign key
        - Column ending with '_id' that is not a foreign key and is integer type
        """
        for table in self.tables.values():
            for col in table.columns:
                if col.is_foreign_key:
                    continue
               
                # Primary heuristic: column named 'id'
                if col.name.lower() == 'id':
                    col.is_primary_key = True
                    continue
               
                # Secondary heuristic: ends with '_id', integer type, not FK
                if (col.name.lower().endswith('_id') and
                    'int' in col.type.lower()):
                    col.is_primary_key = True
   
    def get_table(self, table_name: str) -> Optional[Table]:
        """Retrieve table by name (case-insensitive)"""
        table_name_lower = table_name.lower()
        for name, table in self.tables.items():
            if name.lower() == table_name_lower:
                return table
        return None
   
    def has_table(self, table_name: str) -> bool:
        """Check if table exists (case-insensitive)"""
        return self.get_table(table_name) is not None
   
    def has_column(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table (case-insensitive)"""
        table = self.get_table(table_name)
        if not table:
            return False
        return table.get_column(column_name) is not None
   
    def get_join_path(
        self,
        table1: str,
        table2: str
    ) -> Optional[List[Tuple[str, str, str, str]]]:
        """
        Find join path between two tables using BFS on relationship graph.
       
        Returns list of (from_table, from_col, to_table, to_col) tuples
        representing the path.
       
        Requirement 3: Join Path Validation - Graph-based FK path traversal
        """
        if table1 == table2:
            return []
       
        # Normalize table names
        t1 = None
        t2 = None
        for name in self.tables.keys():
            if name.lower() == table1.lower():
                t1 = name
            if name.lower() == table2.lower():
                t2 = name
       
        if not t1 or not t2:
            return None
       
        if t1 not in self.relationship_graph or t2 not in self.relationship_graph:
            return None
       
        try:
            # Find shortest path
            path_nodes = nx.shortest_path(self.relationship_graph, t1, t2)
        except nx.NetworkXNoPath:
            return None
       
        # Build join conditions from path
        join_path = []
        for i in range(len(path_nodes) - 1):
            from_table = path_nodes[i]
            to_table = path_nodes[i + 1]
            edge_data = self.relationship_graph.get_edge_data(from_table, to_table)
           
            if edge_data:
                join_path.append((
                    from_table,
                    edge_data['column'],
                    to_table,
                    edge_data['references']
                ))
       
        return join_path if join_path else None
   
    def get_all_tables(self) -> List[str]:
        """Get list of all table names"""
        return list(self.tables.keys())
   
    def get_semantic_context(self) -> str:
        """
        Generate a text description of the schema for LLM context.
       
        Includes table names, columns with types and descriptions,
        and foreign key relationships.
        """
        context_parts = ["Database Schema:\n"]
       
        for table_name, table in sorted(self.tables.items()):
            context_parts.append(f"\nTable: {table_name}")
            if table.description:
                context_parts.append(f"Description: {table.description}")
           
            context_parts.append("Columns:")
            for col in table.columns:
                col_info = f"  - {col.name} ({col.type})"
                if col.description:
                    col_info += f": {col.description}"
               
                if col.is_primary_key:
                    col_info += " [PRIMARY KEY]"
                elif col.is_foreign_key and col.references:
                    col_info += f" [FK -> {col.references[0]}.{col.references[1]}]"
               
                context_parts.append(col_info)
       
        return "\n".join(context_parts)
   
    def to_dict(self) -> Dict[str, Any]:
        """Export schema to dictionary format"""
        return {
            'tables': [
                {
                    'name': table.name,
                    'description': table.description,
                    'columns': [
                        {
                            'name': col.name,
                            'type': col.type,
                            'description': col.description,
                            'is_primary_key': col.is_primary_key,
                            'is_foreign_key': col.is_foreign_key,
                            'references': col.references
                        }
                        for col in table.columns
                    ],
                    'foreign_keys': table.foreign_keys
                }
                for table in self.tables.values()
            ]
        }



