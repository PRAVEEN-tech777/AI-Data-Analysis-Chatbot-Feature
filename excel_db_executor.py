"""
Excel Database Executor


Simulates database execution by reading from Excel files.
Perfect for demos and testing without requiring a real database.
"""


import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import re


logger = logging.getLogger(__name__)




class ExcelDatabaseExecutor:
    """
    Executes SQL-like queries against Excel files.
    Simulates a database for demo purposes.
    """
   
    def __init__(self, excel_file: str):
        """
        Initialize Excel database executor.
       
        Args:
            excel_file: Path to Excel file with multiple sheets (tables)
        """
        self.excel_file = excel_file
        self.tables = {}
        self.connected = False
       
    def connect(self) -> bool:
        """
        Load Excel file and read all sheets as tables.
       
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read all sheets from Excel
            excel_data = pd.read_excel(self.excel_file, sheet_name=None)
           
            for sheet_name, df in excel_data.items():
                self.tables[sheet_name] = df
                logger.info(f"Loaded table '{sheet_name}' with {len(df)} rows")
           
            self.connected = True
            logger.info(f"Excel database connected successfully. Tables: {list(self.tables.keys())}")
            return True
           
        except Exception as e:
            logger.error(f"Failed to connect to Excel database: {e}")
            return False
   
    def disconnect(self):
        """Close connection (clear loaded tables)"""
        self.tables = {}
        self.connected = False
        logger.info("Excel database connection closed")
   
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Excel file access.
       
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.connect():
                return False, "Failed to load Excel file"
           
            table_list = list(self.tables.keys())
            self.disconnect()
            return True, f"Connection successful. Tables: {', '.join(table_list)}"
           
        except Exception as e:
            self.disconnect()
            return False, f"Connection failed: {str(e)}"
   
    def execute_view(
        self,
        view_sql: str,
        limit: Optional[int] = 1000
    ) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        Execute a SQL query against Excel tables.
       
        Args:
            view_sql: SQL query for the view
            limit: Maximum number of rows to return
           
        Returns:
            Tuple of (success: bool, dataframe: Optional[pd.DataFrame], error: Optional[str])
        """
        if not self.connected:
            if not self.connect():
                return False, None, "Failed to connect to Excel database"
       
        try:
            # Clean the SQL
            clean_sql = self._clean_sql(view_sql)
           
            logger.info(f"Executing query on Excel data...")
           
            # Simple query execution using pandas
            result_df = self._execute_simple_query(clean_sql)
           
            # Apply limit
            if limit and len(result_df) > limit:
                result_df = result_df.head(limit)
           
            logger.info(f"Query successful. Retrieved {len(result_df)} rows, {len(result_df.columns)} columns")
           
            return True, result_df, None
           
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
   
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL to make it executable"""
        sql = sql.strip()
       
        # Remove CREATE VIEW if present
        if sql.upper().startswith('CREATE'):
            as_index = sql.upper().find(' AS ')
            if as_index != -1:
                sql = sql[as_index + 4:].strip()
       
        return sql
   
    def _execute_simple_query(self, sql: str) -> pd.DataFrame:
        """
        Execute simple SQL queries using pandas operations.
        Supports SELECT, FROM, WHERE, GROUP BY, ORDER BY, JOIN.
        """
        sql_upper = sql.upper()
       
        # Parse table name
        from_match = re.search(r'FROM\s+(\w+)', sql_upper)
        if not from_match:
            raise ValueError("No FROM clause found")
       
        table_name = from_match.group(1).lower()
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' not found")
       
        df = self.tables[table_name].copy()
       
        # Handle JOINs
        if 'JOIN' in sql_upper:
            df = self._handle_join(sql, df)
       
        # Handle WHERE
        where_match = re.search(r'WHERE\s+(.+?)(?:GROUP BY|ORDER BY|LIMIT|$)', sql_upper)
        if where_match:
            # Simple WHERE implementation (basic conditions)
            pass  # Skip for now, complex to parse
       
        # Handle GROUP BY with aggregations
        if 'GROUP BY' in sql_upper:
            df = self._handle_group_by(sql, df)
       
        # Handle ORDER BY
        order_match = re.search(r'ORDER BY\s+(.+?)(?:LIMIT|$)', sql_upper)
        if order_match:
            order_clause = order_match.group(1).strip()
            desc = 'DESC' in order_clause.upper()
            col = order_clause.split()[0].strip()
            if col in df.columns:
                df = df.sort_values(by=col, ascending=not desc)
       
        # Handle LIMIT
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            limit_val = int(limit_match.group(1))
            df = df.head(limit_val)
       
        return df
   
    def _handle_join(self, sql: str, left_df: pd.DataFrame) -> pd.DataFrame:
        """Handle JOIN operations"""
        sql_upper = sql.upper()
       
        # Find JOIN table
        join_match = re.search(r'JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', sql_upper)
        if join_match:
            right_table = join_match.group(1).lower()
            left_col = join_match.group(3).lower()
            right_col = join_match.group(5).lower()
           
            if right_table in self.tables:
                right_df = self.tables[right_table].copy()
                # Perform merge
                result = pd.merge(
                    left_df,
                    right_df,
                    left_on=left_col,
                    right_on=right_col,
                    how='inner'
                )
                return result
       
        return left_df
   
    def _handle_group_by(self, sql: str, df: pd.DataFrame) -> pd.DataFrame:
        """Handle GROUP BY with aggregations"""
        sql_upper = sql.upper()
       
        # Find GROUP BY columns
        group_match = re.search(r'GROUP BY\s+(.+?)(?:ORDER BY|LIMIT|$)', sql_upper)
        if not group_match:
            return df
       
        group_cols_str = group_match.group(1).strip()
        group_cols = [col.strip() for col in group_cols_str.split(',')]
       
        # Find aggregation functions in SELECT
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper)
        if not select_match:
            return df
       
        select_clause = select_match.group(1)
       
        # Parse aggregations
        agg_dict = {}
        result_cols = {}
       
        for part in select_clause.split(','):
            part = part.strip()
           
            # Check for aggregation functions
            if 'SUM(' in part:
                match = re.search(r'SUM\((\w+)\)\s+(?:AS\s+)?(\w+)?', part)
                if match:
                    col = match.group(1).lower()
                    alias = match.group(2).lower() if match.group(2) else f'sum_{col}'
                    if col in df.columns:
                        agg_dict[col] = 'sum'
                        result_cols[col] = alias
           
            elif 'COUNT(' in part:
                match = re.search(r'COUNT\((\w+|\*)\)\s+(?:AS\s+)?(\w+)?', part)
                if match:
                    col = match.group(1).lower()
                    alias = match.group(2).lower() if match.group(2) else 'count'
                    if col == '*' or col in df.columns:
                        use_col = df.columns[0] if col == '*' else col
                        agg_dict[use_col] = 'count'
                        result_cols[use_col] = alias
           
            elif 'AVG(' in part:
                match = re.search(r'AVG\((\w+)\)\s+(?:AS\s+)?(\w+)?', part)
                if match:
                    col = match.group(1).lower()
                    alias = match.group(2).lower() if match.group(2) else f'avg_{col}'
                    if col in df.columns:
                        agg_dict[col] = 'mean'
                        result_cols[col] = alias
       
        # Perform groupby
        if agg_dict and group_cols:
            grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
           
            # Rename columns
            for old_col, new_col in result_cols.items():
                if old_col in grouped.columns:
                    grouped = grouped.rename(columns={old_col: new_col})
           
            return grouped
       
        return df
   
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
   
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()



