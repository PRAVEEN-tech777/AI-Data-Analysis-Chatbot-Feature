"""
Validation Module


Implements comprehensive validation for generated views:
- Requirement 3: Join Path Validation (FK-based)
- Requirement 4: Semantic Validation (column descriptions)
- Requirement 5: SQL Compilability (table/column references)
"""


import re
import logging
from typing import List, Tuple, Optional, Set, Dict, Any
from models import ViewDefinition, JoinSpecification, ValidationResult
from schema_parser import SchemaParser
from config import config


logger = logging.getLogger(__name__)




class ViewValidator:
    """
    Comprehensive validator for generated database views.
   
    Validates:
    1. Join paths follow foreign key relationships
    2. Semantic relevance of joined tables
    3. SQL compilability (all references valid)
    """
   
    def __init__(self, schema: SchemaParser):
        self.schema = schema
        self.min_semantic_score = config.app.min_semantic_score
        self.enable_semantic = config.app.enable_semantic_validation
   
    def validate_view(self, view: ViewDefinition) -> ValidationResult:
        """
        Perform complete validation on a view.
       
        Returns ValidationResult with validation status, errors, and warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []
       
        # Extract base table
        base_table = self._extract_table_name(view.query.from_table)
       
        # 1. Validate base table exists
        if not self.schema.has_table(base_table):
            errors.append(f"Base table '{base_table}' does not exist in schema")
            return ValidationResult(
                is_valid=False,
                view_name=view.name,
                errors=errors,
                warnings=warnings
            )
       
        # 2. Validate joins (Requirement 3: Join Path Validation)
        tables_in_query = {base_table}
       
        for i, join in enumerate(view.query.joins):
            join_table = self._extract_table_name(join.table)
            tables_in_query.add(join_table)
           
            # Validate join table exists
            if not self.schema.has_table(join_table):
                errors.append(
                    f"Join #{i+1}: Table '{join_table}' does not exist in schema"
                )
                continue
           
            # Validate join path exists (FK relationship)
            join_errors, join_warnings = self._validate_join_path(
                base_table, join_table, join, i+1
            )
            errors.extend(join_errors)
            warnings.extend(join_warnings)
           
            # 3. Semantic validation (Requirement 4)
            if self.enable_semantic:
                sem_score, sem_warnings = self._validate_semantic_relevance(
                    base_table, join_table, i+1
                )
                warnings.extend(sem_warnings)
       
        # 4. Validate SELECT columns (Requirement 5: SQL Compilability)
        select_errors = self._validate_select_columns(
            view.query.select, tables_in_query
        )
        errors.extend(select_errors)
       
        # 5. Validate WHERE conditions
        if view.query.where:
            where_errors = self._validate_conditions(
                view.query.where, tables_in_query, "WHERE"
            )
            errors.extend(where_errors)
       
        # 6. Validate GROUP BY columns
        if view.query.group_by:
            group_errors = self._validate_column_list(
                view.query.group_by, tables_in_query, "GROUP BY"
            )
            errors.extend(group_errors)
       
        # 7. Validate HAVING conditions
        if view.query.having:
            having_errors = self._validate_conditions(
                view.query.having, tables_in_query, "HAVING"
            )
            errors.extend(having_errors)
       
        # 8. Validate ORDER BY columns
        if view.query.order_by:
            order_errors = self._validate_column_list(
                view.query.order_by, tables_in_query, "ORDER BY"
            )
            errors.extend(order_errors)
       
        # 9. Generate SQL if valid
        sql = None
        if not errors:
            try:
                sql = self._compile_to_sql(view)
            except Exception as e:
                errors.append(f"SQL compilation failed: {str(e)}")
       
        is_valid = len(errors) == 0
       
        return ValidationResult(
            is_valid=is_valid,
            view_name=view.name,
            errors=errors,
            warnings=warnings,
            sql=sql
        )
   
    def _extract_table_name(self, table_spec: str) -> str:
        """Extract table name from 'table' or 'table alias' format"""
        return table_spec.split()[0].strip()
   
    def _extract_alias(self, table_spec: str) -> Optional[str]:
        """Extract alias from 'table alias' format"""
        parts = table_spec.split()
        if len(parts) > 1:
            # Remove 'AS' keyword if present
            alias = parts[-1].strip()
            if alias.upper() != 'AS':
                return alias
        return None
   
    def _validate_join_path(
        self,
        base_table: str,
        join_table: str,
        join: JoinSpecification,
        join_num: int
    ) -> Tuple[List[str], List[str]]:
        """
        Validate that join follows a valid foreign key path.
       
        Requirement 3: Join Path Validation
        """
        errors = []
        warnings = []
       
        # Check if FK path exists
        path = self.schema.get_join_path(base_table, join_table)
       
        if path is None:
            errors.append(
                f"Join #{join_num}: No foreign key path exists between "
                f"'{base_table}' and '{join_table}'"
            )
            return errors, warnings
       
        # Parse the join condition
        try:
            left, right = join.on.split('=')
            left = left.strip()
            right = right.strip()
        except ValueError:
            errors.append(
                f"Join #{join_num}: Invalid join condition format: '{join.on}'. "
                "Expected format: 'table.column = table.column'"
            )
            return errors, warnings
       
        # Verify the join condition matches the FK relationship
        # Extract table and column from both sides
        left_parts = left.split('.')
        right_parts = right.split('.')
       
        if len(left_parts) != 2 or len(right_parts) != 2:
            warnings.append(
                f"Join #{join_num}: Join condition should use qualified names "
                "(table.column = table.column)"
            )
       
        return errors, warnings
   
    def _validate_semantic_relevance(
        self,
        table1: str,
        table2: str,
        join_num: int
    ) -> Tuple[float, List[str]]:
        """
        Validate semantic relevance between joined tables.
       
        Requirement 4: Semantic Validation
        Uses column descriptions and names to compute similarity.
        """
        warnings = []
       
        # Get tables
        t1 = self.schema.get_table(table1)
        t2 = self.schema.get_table(table2)
       
        if not t1 or not t2:
            return 0.0, warnings
       
        # Compute semantic similarity based on:
        # 1. Column name overlap
        # 2. Column description keyword overlap
       
        tokens1 = set()
        tokens2 = set()
       
        # Extract tokens from column names and descriptions
        for col in t1.columns:
            # Column name tokens
            tokens1.update(self._tokenize(col.name))
            # Description tokens
            if col.description:
                tokens1.update(self._tokenize(col.description))
       
        for col in t2.columns:
            tokens2.update(self._tokenize(col.name))
            if col.description:
                tokens2.update(self._tokenize(col.description))
       
        # Compute Jaccard similarity
        if not tokens1 or not tokens2:
            score = 0.0
        else:
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            score = len(intersection) / len(union) if union else 0.0
       
        # Warn if score is very low
        if score < self.min_semantic_score:
            warnings.append(
                f"Join #{join_num}: Low semantic similarity ({score:.3f}) between "
                f"'{table1}' and '{table2}'. Tables may not be semantically related."
            )
       
        return score, warnings
   
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into meaningful words"""
        # Convert to lowercase
        text = text.lower()
        # Split on non-alphanumeric
        tokens = re.findall(r'[a-z0-9]+', text)
        # Filter out common stop words and very short tokens
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        tokens = {t for t in tokens if len(t) > 2 and t not in stop_words}
        return tokens
   
    def _validate_select_columns(
        self,
        select_list: List[str],
        tables: Set[str]
    ) -> List[str]:
        """Validate all columns in SELECT clause"""
        errors = []
       
        for expr in select_list:
            # Check if it's a qualified column reference (table.column)
            if '.' in expr:
                # Extract table and column
                parts = expr.split('.')
                if len(parts) >= 2:
                    table_or_alias = parts[0].strip()
                    column = parts[1].strip()
                   
                    # Remove any AS alias
                    column = column.split()[0].strip()
                   
                    # Check if table exists
                    found = False
                    for table in tables:
                        if (table.lower() == table_or_alias.lower() or
                            self.schema.has_table(table_or_alias)):
                            # Verify column exists
                            if not self.schema.has_column(table, column):
                                errors.append(
                                    f"SELECT: Column '{column}' does not exist in "
                                    f"table '{table}'"
                                )
                            found = True
                            break
                   
                    if not found:
                        errors.append(
                            f"SELECT: Unknown table reference '{table_or_alias}'"
                        )
       
        return errors
   
    def _validate_conditions(
        self,
        conditions: List[str],
        tables: Set[str],
        clause_name: str
    ) -> List[str]:
        """Validate conditions in WHERE or HAVING clause"""
        errors = []
       
        for condition in conditions:
            # Find all table.column references in condition
            matches = re.findall(r'(\w+)\.(\w+)', condition)
            for table_or_alias, column in matches:
                # Check if table exists
                found = False
                for table in tables:
                    if (table.lower() == table_or_alias.lower() or
                        self.schema.has_table(table_or_alias)):
                        # Verify column exists
                        if not self.schema.has_column(table, column):
                            errors.append(
                                f"{clause_name}: Column '{column}' does not exist in "
                                f"table '{table}'"
                            )
                        found = True
                        break
               
                if not found:
                    errors.append(
                        f"{clause_name}: Unknown table reference '{table_or_alias}'"
                    )
       
        return errors
   
    def _validate_column_list(
        self,
        columns: List[str],
        tables: Set[str],
        clause_name: str
    ) -> List[str]:
        """Validate column list in GROUP BY or ORDER BY"""
        errors = []
       
        for col_expr in columns:
            # Remove DESC/ASC keywords
            col_expr = re.sub(r'\s+(DESC|ASC)$', '', col_expr, flags=re.IGNORECASE)
            col_expr = col_expr.strip()
           
            # Check if qualified reference
            if '.' in col_expr:
                parts = col_expr.split('.')
                if len(parts) >= 2:
                    table_or_alias = parts[0].strip()
                    column = parts[1].strip()
                   
                    # Check if table exists
                    found = False
                    for table in tables:
                        if (table.lower() == table_or_alias.lower() or
                            self.schema.has_table(table_or_alias)):
                            # Verify column exists
                            if not self.schema.has_column(table, column):
                                errors.append(
                                    f"{clause_name}: Column '{column}' does not exist "
                                    f"in table '{table}'"
                                )
                            found = True
                            break
                   
                    if not found:
                        errors.append(
                            f"{clause_name}: Unknown table reference '{table_or_alias}'"
                        )
       
        return errors
   
    def _compile_to_sql(self, view: ViewDefinition) -> str:
        """
        Compile view definition to SQL.
       
        Requirement 5: Ensure SQL compilability
        """
        sql_parts = []
       
        # SELECT clause
        select_clause = "SELECT " + ", ".join(view.query.select)
        sql_parts.append(select_clause)
       
        # FROM clause
        sql_parts.append(f"FROM {view.query.from_table}")
       
        # JOIN clauses
        for join in view.query.joins:
            join_clause = f"{join.type} JOIN {join.table} ON {join.on}"
            sql_parts.append(join_clause)
       
        # WHERE clause
        if view.query.where:
            where_clause = "WHERE " + " AND ".join(view.query.where)
            sql_parts.append(where_clause)
       
        # GROUP BY clause
        if view.query.group_by:
            group_clause = "GROUP BY " + ", ".join(view.query.group_by)
            sql_parts.append(group_clause)
       
        # HAVING clause
        if view.query.having:
            having_clause = "HAVING " + " AND ".join(view.query.having)
            sql_parts.append(having_clause)
       
        # ORDER BY clause
        if view.query.order_by:
            order_clause = "ORDER BY " + ", ".join(view.query.order_by)
            sql_parts.append(order_clause)
       
        return "\n".join(sql_parts) + ";"




def deduplicate_views(views: List[ViewDefinition]) -> List[ViewDefinition]:
    """
    Remove duplicate or overlapping views.
   
    Requirement 5: Output Post-Processing - Deduplicate overlapping views
    """
    unique_views = []
    seen_signatures = set()
   
    for view in views:
        # Create signature based on tables and columns involved
        tables = {view.query.from_table.split()[0]}
        for join in view.query.joins:
            tables.add(join.table.split()[0])
       
        # Include selected columns in signature
        columns = sorted(view.query.select)
       
        signature = frozenset(tables), tuple(columns)
       
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_views.append(view)
        else:
            logger.info(f"Deduplicated view: {view.name} (duplicate signature)")
   
    return unique_views



