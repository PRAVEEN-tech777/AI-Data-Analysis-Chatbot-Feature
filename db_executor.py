"""
Database Executor Module


Handles execution of generated views against actual databases.
Provides connection management and query execution with proper error handling.
"""


import logging
import psycopg2
from psycopg2 import sql
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from urllib.parse import urlparse


logger = logging.getLogger(__name__)




class DatabaseExecutor:
    """
    Executes SQL views against a database and retrieves results.
    Supports PostgreSQL with extensibility for other databases.
    """
   
    def __init__(self, connection_string: str):
        """
        Initialize database executor with connection string.
       
        Args:
            connection_string: Database connection string
                Format: postgresql://user:password@host:port/database
        """
        self.connection_string = connection_string
        self.connection = None
        self.db_type = self._parse_db_type(connection_string)
       
    def _parse_db_type(self, connection_string: str) -> str:
        """Extract database type from connection string"""
        try:
            parsed = urlparse(connection_string)
            return parsed.scheme.split('+')[0]
        except:
            return 'postgresql'  # Default
   
    def connect(self) -> bool:
        """
        Establish database connection.
       
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(self.connection_string)
                logger.info("Database connection established successfully")
                return True
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
   
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.connection = None
   
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test database connection and return status.
       
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.connect():
                return False, "Failed to establish connection"
           
            # Test query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.disconnect()
                return True, f"Connection successful. {version}"
        except Exception as e:
            self.disconnect()
            return False, f"Connection failed: {str(e)}"
   
    def execute_view(
        self,
        view_sql: str,
        limit: Optional[int] = 1000
    ) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        Execute a view query and return results as DataFrame.
       
        Args:
            view_sql: SQL query for the view
            limit: Maximum number of rows to return
           
        Returns:
            Tuple of (success: bool, dataframe: Optional[pd.DataFrame], error: Optional[str])
        """
        if not self.connection:
            if not self.connect():
                return False, None, "Failed to connect to database"
       
        try:
            # Clean the SQL (remove CREATE VIEW if present)
            clean_sql = self._clean_sql(view_sql)
           
            # Add LIMIT if specified
            if limit:
                clean_sql = f"{clean_sql.rstrip(';')} LIMIT {limit};"
           
            logger.info(f"Executing query: {clean_sql[:100]}...")
           
            # Execute query and load into DataFrame
            df = pd.read_sql_query(clean_sql, self.connection)
           
            logger.info(f"Query successful. Retrieved {len(df)} rows, {len(df.columns)} columns")
           
            return True, df, None
           
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
   
    def _clean_sql(self, sql: str) -> str:
        """
        Clean SQL to make it executable as a SELECT query.
        Removes CREATE VIEW statements and extracts SELECT portion.
        """
        sql = sql.strip()
       
        # If it starts with CREATE VIEW, extract the SELECT portion
        if sql.upper().startswith('CREATE'):
            # Find the AS keyword
            as_index = sql.upper().find(' AS ')
            if as_index != -1:
                sql = sql[as_index + 4:].strip()
       
        return sql
   
    def get_table_preview(
        self,
        table_name: str,
        limit: int = 100
    ) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        Get a preview of a table's data.
       
        Args:
            table_name: Name of the table
            limit: Number of rows to retrieve
           
        Returns:
            Tuple of (success, dataframe, error_message)
        """
        if not self.connection:
            if not self.connect():
                return False, None, "Failed to connect to database"
       
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit};"
            df = pd.read_sql_query(query, self.connection)
            return True, df, None
        except Exception as e:
            return False, None, f"Failed to preview table: {str(e)}"
   
    def get_row_count(self, view_sql: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Get the total row count for a view without retrieving all data.
       
        Args:
            view_sql: SQL query for the view
           
        Returns:
            Tuple of (success, row_count, error_message)
        """
        if not self.connection:
            if not self.connect():
                return False, None, "Failed to connect to database"
       
        try:
            clean_sql = self._clean_sql(view_sql)
            count_query = f"SELECT COUNT(*) FROM ({clean_sql.rstrip(';')}) AS count_query;"
           
            with self.connection.cursor() as cursor:
                cursor.execute(count_query)
                count = cursor.fetchone()[0]
                return True, count, None
        except Exception as e:
            return False, None, f"Failed to get row count: {str(e)}"
   
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
   
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()




def parse_connection_string(connection_string: str) -> Dict[str, str]:
    """
    Parse connection string into components.
   
    Args:
        connection_string: Database connection string
       
    Returns:
        Dictionary with connection parameters
    """
    try:
        parsed = urlparse(connection_string)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password,
            'scheme': parsed.scheme
        }
    except Exception as e:
        logger.error(f"Failed to parse connection string: {e}")
        return {}




def build_connection_string(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    db_type: str = 'postgresql'
) -> str:
    """
    Build connection string from components.
   
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Username
        password: Password
        db_type: Database type (default: postgresql)
       
    Returns:
        Formatted connection string
    """
    return f"{db_type}://{user}:{password}@{host}:{port}/{database}"



