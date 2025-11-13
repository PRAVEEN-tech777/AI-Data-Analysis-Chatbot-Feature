"""
Streamlit UI for AI-Powered Database View Generator


Provides interactive interface for:
1. Loading schema (file upload or database connection)
2. Configuring LLM parameters
3. Generating views
4. Analyzing and visualizing results
5. Exporting SQL and JSON
"""


import streamlit as st
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import pandas as pd
from io import StringIO
import hashlib
from datetime import datetime


# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


from schema_parser import SchemaParser
from pipeline import ViewGeneratorPipeline, run_pipeline_from_dict
from config import config
from models import AnalysisResult
from db_executor import DatabaseExecutor, build_connection_string


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.app.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="AI Database View Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .sql-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)




def init_session_state():
    """Initialize session state variables"""
    if 'schema' not in st.session_state:
        st.session_state.schema = None
    if 'schema_parser' not in st.session_state:
        st.session_state.schema_parser = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = False
    if 'db_connection_string' not in st.session_state:
        st.session_state.db_connection_string = None
    if 'db_type' not in st.session_state:
        st.session_state.db_type = None
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
    if 'selected_view_for_execution' not in st.session_state:
        st.session_state.selected_view_for_execution = None
    if 'execution_results' not in st.session_state:
        st.session_state.execution_results = {}
    if 'show_visualization' not in st.session_state:
        st.session_state.show_visualization = False




def compute_sql_signature(sql: str) -> str:
    """
    Build a stable signature for SQL strings so we can detect repeats.
   
    Normalizes whitespace before hashing to avoid false mismatches.
    """
    if not sql:
        return ""
    normalized_sql = " ".join(sql.split())
    return hashlib.sha256(normalized_sql.encode('utf-8')).hexdigest()




def load_schema_from_upload(uploaded_file) -> Optional[SchemaParser]:
    """Load schema from uploaded JSON file"""
    try:
        schema_json = json.load(uploaded_file)
        st.session_state.schema = schema_json
        parser = SchemaParser.from_dict(schema_json)
        st.session_state.schema_parser = parser
        return parser
    except Exception as e:
        st.error(f"Failed to load schema: {str(e)}")
        logger.exception("Schema load failed")
        return None




def render_schema_info(parser: SchemaParser):
    """Display schema information"""
    st.markdown('<div class="sub-header">📊 Schema Information</div>', unsafe_allow_html=True)
   
    col1, col2, col3 = st.columns(3)
   
    with col1:
        st.metric("Tables", len(parser.tables))
   
    with col2:
        total_columns = sum(len(t.columns) for t in parser.tables.values())
        st.metric("Columns", total_columns)
   
    with col3:
        total_fks = len(parser.relationship_graph.edges()) // 2
        st.metric("Foreign Keys", total_fks)
   
    # Show tables
    with st.expander("View Tables", expanded=False):
        for table_name, table in parser.tables.items():
            st.markdown(f"**{table_name}**")
            if table.description:
                st.caption(table.description)
           
            cols_text = ", ".join([f"{c.name} ({c.type})" for c in table.columns[:5]])
            if len(table.columns) > 5:
                cols_text += f" ... +{len(table.columns) - 5} more"
            st.text(cols_text)
            st.markdown("---")




def render_results(results: AnalysisResult):
    """Display analysis results"""
    st.markdown('<div class="sub-header">📈 Results</div>', unsafe_allow_html=True)
   
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
   
    with col1:
        st.metric("Generated", results.total_generated)
   
    with col2:
        st.metric("Valid", results.valid_views,
                 delta=None if results.valid_views == 0 else "✓")
   
    with col3:
        st.metric("Invalid", results.invalid_views,
                 delta=None if results.invalid_views == 0 else "✗")
   
    with col4:
        success_rate = results.summary.get('success_rate', '0%')
        st.metric("Success Rate", success_rate)
   
    # Tabs for valid and invalid views
    valid_views = [v for v in results.views if v.is_valid]
    invalid_views = [v for v in results.views if not v.is_valid]
   
    tab1, tab2 = st.tabs([f"✓ Valid Views ({len(valid_views)})",
                          f"✗ Invalid Views ({len(invalid_views)})"])
   
    with tab1:
        if valid_views:
            render_valid_views(valid_views)
        else:
            st.info("No valid views generated")
   
    with tab2:
        if invalid_views:
            render_invalid_views(invalid_views)
        else:
            st.success("All generated views are valid!")




def render_valid_views(valid_views):
    """Render valid views with SQL"""
    for i, view in enumerate(valid_views, 1):
        with st.expander(f"{i}. {view.view_name}", expanded=i==1):
            # View description
            st.markdown("**Description:**")
            st.info(view.view_name)  # Using view_name as placeholder for description
           
            # SQL
            if view.sql:
                st.markdown("**SQL:**")
                st.code(view.sql, language="sql")
               
                # Download button
                st.download_button(
                    label="Download SQL",
                    data=view.sql,
                    file_name=f"{view.view_name}.sql",
                    mime="text/plain",
                    key=f"download_sql_{i}"
                )
           
            # Warnings
            if view.warnings:
                st.markdown("**Warnings:**")
                for warning in view.warnings:
                    st.warning(warning)




def render_invalid_views(invalid_views):
    """Render invalid views with error details"""
    for i, view in enumerate(invalid_views, 1):
        with st.expander(f"{i}. {view.view_name}", expanded=i==1):
            # Errors
            st.markdown("**Errors:**")
            for error in view.errors:
                st.error(error)
           
            # Warnings
            if view.warnings:
                st.markdown("**Warnings:**")
                for warning in view.warnings:
                    st.warning(warning)




def render_database_connection_dialog():
    """Render database connection configuration dialog"""
    st.markdown('<div class="sub-header">🔌 Database Connection</div>', unsafe_allow_html=True)
   
    if st.session_state.db_connected:
        st.success("✓ Database connected successfully!")
       
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Disconnect", use_container_width=True, key="btn_disconnect_db"):
                st.session_state.db_connected = False
                st.session_state.db_connection_string = None
                st.session_state.db_type = None
                st.rerun()
    else:
        st.info("💡 Connect to a database to execute and visualize generated views")
       
        # Database type selection
        db_type = st.radio(
            "Database Type",
            ["Excel File (Demo)", "PostgreSQL"],
            horizontal=True,
            help="Choose Excel for demo without database setup",
            key="radio_db_type"
        )
       
        if db_type == "Excel File (Demo)":
            st.markdown("**📊 Excel File as Database**")
            st.caption("Perfect for demos! Use Excel file with multiple sheets as tables.")
           
            # Check if demo file exists
            import os
            demo_file = "/mnt/project/demo_database.xlsx"
            if os.path.exists(demo_file):
                st.success(f"✓ Demo file found: demo_database.xlsx")
                st.caption("Tables: customers (100 rows), orders (810 rows)")
               
                if st.button("Connect to Demo Database", type="primary", use_container_width=True, key="btn_connect_demo_excel"):
                    try:
                        from excel_db_executor import ExcelDatabaseExecutor
                        executor = ExcelDatabaseExecutor(demo_file)
                        success, message = executor.test_connection()
                       
                        if success:
                            st.session_state.db_connection_string = demo_file
                            st.session_state.db_type = "excel"
                            st.session_state.db_connected = True
                            st.success("Connected to Excel database!")
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")
            else:
                st.warning("Demo file not found. Upload your own Excel file.")
           
            # Allow custom Excel upload
            uploaded_excel = st.file_uploader(
                "Or upload your own Excel file",
                type=['xlsx', 'xls'],
                help="Excel file with multiple sheets (each sheet = one table)",
                key="uploader_custom_excel"
            )
           
            if uploaded_excel:
                # Save uploaded file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_excel.getvalue())
                    tmp_path = tmp_file.name
               
                if st.button("Connect to Uploaded Excel", use_container_width=True, key="btn_connect_uploaded_excel"):
                    try:
                        from excel_db_executor import ExcelDatabaseExecutor
                        executor = ExcelDatabaseExecutor(tmp_path)
                        success, message = executor.test_connection()
                       
                        if success:
                            st.session_state.db_connection_string = tmp_path
                            st.session_state.db_type = "excel"
                            st.session_state.db_connected = True
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")
       
        else:  # PostgreSQL
            connection_method = st.radio(
                "Connection Method",
                ["Connection String", "Manual Configuration"],
                horizontal=True,
                key="radio_pg_connection_method"
            )
           
            if connection_method == "Connection String":
                conn_string = st.text_input(
                    "Connection String",
                    placeholder="postgresql://user:password@host:port/database",
                    type="password",
                    help="Format: postgresql://username:password@host:port/database",
                    key="input_pg_connection_string"
                )
               
                col1, col2 = st.columns([1, 1])
               
                with col1:
                    if st.button("Test Connection", use_container_width=True, disabled=not conn_string, key="btn_test_pg_string"):
                        with st.spinner("Testing connection..."):
                            try:
                                executor = DatabaseExecutor(conn_string)
                                success, message = executor.test_connection()
                               
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Connection test failed: {str(e)}")
               
                with col2:
                    if st.button("Connect", type="primary", use_container_width=True, disabled=not conn_string, key="btn_connect_pg_string"):
                        with st.spinner("Connecting to database..."):
                            try:
                                executor = DatabaseExecutor(conn_string)
                                success, message = executor.test_connection()
                               
                                if success:
                                    st.session_state.db_connection_string = conn_string
                                    st.session_state.db_type = "postgresql"
                                    st.session_state.db_connected = True
                                    st.success("Connected successfully!")
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Connection failed: {str(e)}")
           
            else:  # Manual Configuration
                col1, col2 = st.columns(2)
               
                with col1:
                    host = st.text_input("Host", value="localhost", key="input_pg_host")
                    database = st.text_input("Database", value="", key="input_pg_database")
                    user = st.text_input("Username", value="postgres", key="input_pg_user")
               
                with col2:
                    port = st.number_input("Port", value=5432, min_value=1, max_value=65535, key="input_pg_port")
                    password = st.text_input("Password", type="password", key="input_pg_password")
                    db_type_manual = st.selectbox("Database Type", ["postgresql"], index=0, key="select_pg_type")
               
                col1, col2 = st.columns([1, 1])
               
                if all([host, database, user, password]):
                    conn_string = build_connection_string(host, port, database, user, password, db_type_manual)
                   
                    with col1:
                        if st.button("Test Connection", use_container_width=True, key="btn_test_pg_manual"):
                            with st.spinner("Testing connection..."):
                                try:
                                    executor = DatabaseExecutor(conn_string)
                                    success, message = executor.test_connection()
                                   
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Connection test failed: {str(e)}")
                   
                    with col2:
                        if st.button("Connect", type="primary", use_container_width=True, key="btn_connect_pg_manual"):
                            with st.spinner("Connecting to database..."):
                                try:
                                    executor = DatabaseExecutor(conn_string)
                                    success, message = executor.test_connection()
                                   
                                    if success:
                                        st.session_state.db_connection_string = conn_string
                                        st.session_state.db_type = "postgresql"
                                        st.session_state.db_connected = True
                                        st.success("Connected successfully!")
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Connection failed: {str(e)}")
    """Render database connection configuration dialog"""
    st.markdown('<div class="sub-header">🔌 Database Connection</div>', unsafe_allow_html=True)
   
    if st.session_state.db_connected:
        st.success("✓ Database connected successfully!")
       
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Disconnect", use_container_width=True):
                st.session_state.db_connected = False
                st.session_state.db_connection_string = None
                st.rerun()
    else:
        st.info("💡 Connect to a database to execute and visualize generated views")
       
        connection_method = st.radio(
            "Connection Method",
            ["Connection String", "Manual Configuration"],
            horizontal=True
        )
       
        if connection_method == "Connection String":
            conn_string = st.text_input(
                "Connection String",
                placeholder="postgresql://user:password@host:port/database",
                type="password",
                help="Format: postgresql://username:password@host:port/database"
            )
           
            col1, col2 = st.columns([1, 1])
           
            with col1:
                if st.button("Test Connection", use_container_width=True, disabled=not conn_string):
                    with st.spinner("Testing connection..."):
                        try:
                            executor = DatabaseExecutor(conn_string)
                            success, message = executor.test_connection()
                           
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        except Exception as e:
                            st.error(f"Connection test failed: {str(e)}")
           
            with col2:
                if st.button("Connect", type="primary", use_container_width=True, disabled=not conn_string):
                    with st.spinner("Connecting to database..."):
                        try:
                            executor = DatabaseExecutor(conn_string)
                            success, message = executor.test_connection()
                           
                            if success:
                                st.session_state.db_connection_string = conn_string
                                st.session_state.db_connected = True
                                st.success("Connected successfully!")
                                st.rerun()
                            else:
                                st.error(message)
                        except Exception as e:
                            st.error(f"Connection failed: {str(e)}")
       
        else:  # Manual Configuration
            col1, col2 = st.columns(2)
           
            with col1:
                host = st.text_input("Host", value="localhost")
                database = st.text_input("Database", value="")
                user = st.text_input("Username", value="postgres")
           
            with col2:
                port = st.number_input("Port", value=5432, min_value=1, max_value=65535)
                password = st.text_input("Password", type="password")
                db_type = st.selectbox("Database Type", ["postgresql"], index=0)
           
            col1, col2 = st.columns([1, 1])
           
            if all([host, database, user, password]):
                conn_string = build_connection_string(host, port, database, user, password, db_type)
               
                with col1:
                    if st.button("Test Connection", use_container_width=True):
                        with st.spinner("Testing connection..."):
                            try:
                                executor = DatabaseExecutor(conn_string)
                                success, message = executor.test_connection()
                               
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Connection test failed: {str(e)}")
               
                with col2:
                    if st.button("Connect", type="primary", use_container_width=True):
                        with st.spinner("Connecting to database..."):
                            try:
                                executor = DatabaseExecutor(conn_string)
                                success, message = executor.test_connection()
                               
                                if success:
                                    st.session_state.db_connection_string = conn_string
                                    st.session_state.db_connected = True
                                    st.success("Connected successfully!")
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Connection failed: {str(e)}")




def render_view_execution_panel():
    """Render panel for selecting and executing views"""
    st.markdown('<div class="sub-header">▶️ Execute Views</div>', unsafe_allow_html=True)
   
    if not st.session_state.db_connected:
        st.warning("⚠️ Please connect to a database first to execute views")
        return
   
    valid_views = [v for v in st.session_state.results.views if v.is_valid]
   
    if not valid_views:
        st.info("No valid views available for execution")
        return
   
    # View selector
    view_names = [v.view_name for v in valid_views]
    selected_view_name = st.selectbox(
        "Select View to Execute",
        view_names,
        help="Choose a view to execute against the database",
        key="select_view_to_execute"
    )
   
    selected_view = next(v for v in valid_views if v.view_name == selected_view_name)
    current_signature = compute_sql_signature(selected_view.sql)
   
    # Display SQL
    with st.expander("📄 View SQL", expanded=False):
        st.code(selected_view.sql, language="sql")
   
    # Execution options
    col1, col2, col3 = st.columns([2, 2, 1])
   
    with col1:
        row_limit = st.number_input(
            "Row Limit",
            min_value=10,
            max_value=10000,
            value=1000,
            step=100,
            help="Maximum number of rows to retrieve",
            key="input_row_limit"
        )
   
    with col2:
        # Check if already executing to prevent duplicate clicks
        execution_lock_key = f"executing_{selected_view_name}"
        is_executing = st.session_state.get(execution_lock_key, False)
        cached_result = st.session_state.execution_results.get(selected_view_name)
        cache_matches = False
        if cached_result:
            cache_matches = (
                cached_result.get('sql_signature') == current_signature and
                cached_result.get('row_limit') == row_limit
            )
       
        if st.button(
            "▶️ Execute View",
            type="primary",
            use_container_width=True,
            disabled=is_executing,
            key="btn_execute_view"
        ):
            # Set execution lock IMMEDIATELY
            st.session_state[execution_lock_key] = True
           
            if cache_matches:
                st.session_state.selected_view_for_execution = selected_view_name
                st.session_state.show_visualization = True
                st.session_state[execution_lock_key] = False
                st.info("Using cached results from previous execution (same view and row limit).")
            else:
                with st.spinner(f"Executing view '{selected_view_name}'..."):
                    try:
                        # Choose appropriate executor based on database type
                        if st.session_state.db_type == "excel":
                            from excel_db_executor import ExcelDatabaseExecutor
                            executor = ExcelDatabaseExecutor(st.session_state.db_connection_string)
                        else:
                            executor = DatabaseExecutor(st.session_state.db_connection_string)
                       
                        # Execute query - this should happen only once
                        success, df, error = executor.execute_view(selected_view.sql, limit=row_limit)
                        executor.disconnect()
                       
                        if success:
                            st.session_state.execution_results[selected_view_name] = {
                                'dataframe': df,
                                'row_count': len(df),
                                'columns': list(df.columns),
                                'row_limit': row_limit,
                                'sql_signature': current_signature,
                                'executed_at': datetime.utcnow().isoformat()
                            }
                            st.session_state.selected_view_for_execution = selected_view_name
                            st.session_state.show_visualization = True
                           
                            for key in [
                                f"chat_history_{selected_view_name}",
                                f"analysis_done_{selected_view_name}",
                                f"last_question_{selected_view_name}",
                                f"active_question_{selected_view_name}"
                            ]:
                                if key in st.session_state:
                                    del st.session_state[key]
                           
                            st.session_state[execution_lock_key] = False
                           
                            st.success(f"✓ Retrieved {len(df)} rows with {len(df.columns)} columns")
                        else:
                            st.session_state[execution_lock_key] = False
                            st.error(f"Execution failed: {error}")
                           
                    except Exception as e:
                        st.session_state[execution_lock_key] = False
                        st.error(f"Unexpected error: {str(e)}")
                        logger.exception(f"View execution error: {e}")
   
    with col3:
        if st.button("🔄 Refresh", use_container_width=True, key="btn_refresh_execution"):
            st.session_state.execution_results.pop(selected_view_name, None)
            for key in [
                f"chat_history_{selected_view_name}",
                f"analysis_done_{selected_view_name}",
                f"last_question_{selected_view_name}",
                f"active_question_{selected_view_name}",
                f"executing_{selected_view_name}"
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.show_visualization = False
            st.rerun()




def render_visualization_panel():
    """Render AI-powered data analysis chatbot"""
    if not st.session_state.show_visualization:
        return
   
    selected_view = st.session_state.selected_view_for_execution
   
    if not selected_view or selected_view not in st.session_state.execution_results:
        return
   
    st.markdown("---")
    st.markdown('<div class="sub-header">🤖 AI Data Analysis</div>', unsafe_allow_html=True)
   
    result = st.session_state.execution_results[selected_view]
    df = result['dataframe']
   
    if df is None or df.empty:
        st.warning("No data to analyze")
        return
   
    # Display data preview
    with st.expander("📊 Data Preview", expanded=False):
        st.caption(f"Full dataset: {len(df)} rows × {len(df.columns)} columns")
        st.caption(f"Preview: Showing first 10 rows")
        st.dataframe(df.head(10), use_container_width=True, height=300)
       
        # Download full CSV
        try:
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
           
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Full Data (CSV)",
                    data=csv_data,
                    file_name=f"{selected_view}_full_data.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"download_csv_full_{selected_view}"
                )
           
            # Download as Excel
            with col2:
                try:
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_data = excel_buffer.getvalue()
                   
                    st.download_button(
                        label="📥 Download Full Data (Excel)",
                        data=excel_data,
                        file_name=f"{selected_view}_full_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key=f"download_excel_full_{selected_view}"
                    )
                except ImportError:
                    st.info("Install openpyxl for Excel export: pip install openpyxl")
                except Exception as e:
                    logger.error(f"Excel export error: {e}")
                    st.error(f"Excel export failed: {str(e)}")
                   
        except Exception as e:
            st.error(f"Error preparing downloads: {str(e)}")
   
    st.info(f"ℹ️ AI Analysis uses the data returned by the view. Download full data for complete dataset.")
   
    # Initialize chat history for this view
    chat_key = f"chat_history_{selected_view}"
    analysis_done_key = f"analysis_done_{selected_view}"
    last_question_key = f"last_question_{selected_view}"
    active_question_key = f"active_question_{selected_view}"
   
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
        st.session_state[analysis_done_key] = False
    if last_question_key not in st.session_state:
        st.session_state[last_question_key] = None
    if active_question_key not in st.session_state:
        st.session_state[active_question_key] = None
   
    # Render chatbot interface
    render_data_chatbot(
        df,
        selected_view,
        chat_key,
        analysis_done_key,
        last_question_key,
        active_question_key
    )


def render_data_chatbot(
    df: pd.DataFrame,
    view_name: str,
    chat_key: str,
    analysis_done_key: str,
    last_question_key: str,
    active_question_key: str
):
    """Render AI chatbot for data analysis with strict single-processing safeguards."""


    st.markdown("### 💬 Chat with Your Data")
    st.caption("Ask questions about the data, and the AI will analyze and respond based solely on the executed view results.")


    # Use the full dataset for AI analysis
    df_for_ai = df.head(len(df))


    # Ensure session state keys exist
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    if analysis_done_key not in st.session_state:
        st.session_state[analysis_done_key] = False
    if last_question_key not in st.session_state:
        st.session_state[last_question_key] = None
    if active_question_key not in st.session_state:
        st.session_state[active_question_key] = None


    # Try to backfill last_question from history (for sessions created before this safeguard)
    if st.session_state[last_question_key] is None and st.session_state[chat_key]:
        for history_item in reversed(st.session_state[chat_key]):
            if history_item["role"] == "user":
                st.session_state[last_question_key] = history_item["content"]
                break


    # --- Auto-analysis: runs once per view ---
    if not st.session_state.get(analysis_done_key, False):
        # Mark immediately to prevent re-entry on reruns
        st.session_state[analysis_done_key] = True
        default_question = "Given this view data, summarize all key observations and trends"


        already_answered_default = st.session_state[last_question_key] == default_question
        history_has_default = any(
            msg["role"] == "user" and msg["content"] == default_question
            for msg in st.session_state[chat_key]
        )


        if already_answered_default and history_has_default:
            # Nothing to do; the previous response is still valid
            pass
        else:
            if not history_has_default:
                st.session_state[chat_key].append({"role": "user", "content": default_question})


            st.session_state[active_question_key] = default_question


            # Call the LLM and append assistant response; log errors gracefully
            try:
                with st.spinner("🤖 Analyzing data..."):
                    response = analyze_data_with_llm(df_for_ai, len(df), default_question, view_name)
                st.session_state[chat_key].append({"role": "assistant", "content": response})
                st.session_state[last_question_key] = default_question
            except Exception as e:
                logger.exception("Auto-analysis failed")
                st.session_state[chat_key].append({"role": "assistant", "content": f"Error analyzing data: {e}"})
            finally:
                st.session_state[active_question_key] = None


    # --- Display chat history (after possible auto-analysis) ---
    for message in st.session_state[chat_key]:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])


    # --- Chat input for user questions ---
    user_question = st.chat_input("Ask a question about the data...", key=f"chat_input_{view_name}")


    if not user_question:
        return


    processing_key = f"processing_{view_name}"
    if st.session_state.get(processing_key, False):
        st.info("Your previous question is being processed. Please wait.")
        return


    if st.session_state.get(active_question_key) == user_question:
        st.info("This question is already being processed. Please wait.")
        return


    # Protect against duplicates (check last user message)
    last_user_msg = None
    if st.session_state[chat_key]:
        # find last user msg if any
        for m in reversed(st.session_state[chat_key]):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break


    if last_user_msg == user_question or st.session_state.get(last_question_key) == user_question:
        # Duplicate submission; ignore and inform user
        st.info("This question was already submitted. If you need a different analysis, rephrase and submit.")
        return


    # Process the user's question
    st.session_state[processing_key] = True
    st.session_state[active_question_key] = user_question


    try:
        # Append user message to history and render it immediately
        st.session_state[chat_key].append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)


        # Call LLM to analyze and append assistant response
        with st.spinner("🤖 Analyzing data..."):
            response = analyze_data_with_llm(
                df_for_ai,
                len(df),
                user_question,
                view_name,
                st.session_state[chat_key]
            )


        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.session_state[last_question_key] = user_question
        # Render assistant message immediately
        with st.chat_message("assistant"):
            st.markdown(response)


    except Exception as e:
        logger.exception("Chat question failed")
        err_text = f"Error analyzing data: {e}"
        st.session_state[chat_key].append({"role": "assistant", "content": err_text})
        with st.chat_message("assistant"):
            st.markdown(err_text)
    finally:
        # Always clear processing flag
        st.session_state[processing_key] = False
        st.session_state[active_question_key] = None


    # Provide a clear chat button
    if len(st.session_state[chat_key]) > 0:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear Chat", key=f"clear_chat_{view_name}"):
                st.session_state[chat_key] = []
                st.session_state[analysis_done_key] = False
                st.session_state[last_question_key] = None
                st.session_state[active_question_key] = None
                # Clear any processing flag too
                if processing_key in st.session_state:
                    del st.session_state[processing_key]
                # No st.rerun(); the page will re-render naturally






def analyze_data_with_llm(df: pd.DataFrame, total_rows: int, question: str, view_name: str, chat_history: list = None) -> str:
    """
    Analyze data using LLM with strict data-only context.
   
    Args:
        df: DataFrame with the query results
        total_rows: Total number of rows in full dataset
        question: User's question about the data
        view_name: Name of the view being analyzed
        chat_history: Previous chat messages for context
       
    Returns:
        AI-generated analysis based only on the data
    """
    try:
        # Prepare data summary
        data_summary = prepare_data_summary(df, total_rows)
       
        # Build context-aware prompt
        system_prompt = f"""You are a data analysis assistant. Your ONLY job is to analyze and answer questions about the provided dataset.


STRICT RULES:
1. ONLY use information from the provided data
2. DO NOT use any external knowledge or make assumptions beyond the data
3. If the data doesn't contain information to answer a question, say so clearly
4. Focus on facts, patterns, and insights visible in the data
5. Provide specific numbers, percentages, and statistics from the data
6. Be concise but thorough in your analysis


DATA CONTEXT:
View Name: {view_name}
Total Rows in Full Dataset: {total_rows}
Rows Analyzed: {len(df)} (data returned by the view)
Number of Columns: {len(df.columns)}


NOTE: Analysis is based on the data returned by the view. Patterns may vary in complete dataset.


{data_summary}
"""


        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
       
        # Add relevant chat history (last 3 exchanges to keep context manageable)
        if chat_history:
            recent_history = chat_history[-6:]  # Last 3 Q&A pairs
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
       
        # Add current question
        messages.append({
            "role": "user",
            "content": question
        })
       
        # Call LLM
        from llm_interface import LLMInterface
       
        llm = LLMInterface(
            provider=config.llm.provider,
            model=config.llm.ollama_model if config.llm.provider == "ollama" else config.llm.litellm_model,
            temperature=0.3  # Lower temperature for more factual responses
        )
       
        # For chat-style interaction, we need to format differently
        # Convert messages to a single prompt for simple LLM interfaces
        full_prompt = system_prompt + "\n\n"
        if chat_history:
            recent_history = chat_history[-6:]
            for msg in recent_history:
                role_label = "Human" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role_label}: {msg['content']}\n\n"
        full_prompt += f"Human: {question}\n\nAssistant: "
       
        response = asyncio.run(llm.generate(full_prompt))
       
        return response.strip()
       
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
        return f"I encountered an error while analyzing the data: {str(e)}\n\nPlease try rephrasing your question or check the data."




def prepare_data_summary(df: pd.DataFrame, total_rows: int = None) -> str:
    """
    Prepare a comprehensive summary of the DataFrame for LLM analysis.
   
    Args:
        df: DataFrame to summarize
        total_rows: Total rows in full dataset
       
    Returns:
        Formatted string with data summary
    """
    summary_parts = []
   
    if total_rows and total_rows > len(df):
        summary_parts.append(f"NOTE: Analyzing first {len(df)} of {total_rows} total rows\n")
   
    # Column information
    summary_parts.append("COLUMNS:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
        unique_count = df[col].nunique()
       
        summary_parts.append(f"- {col} ({dtype}): {unique_count} unique values, {null_pct:.1f}% null")
   
    summary_parts.append("\n")
   
    # Numeric columns statistics
    numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
    if len(numeric_cols) > 0:
        summary_parts.append("NUMERIC STATISTICS:")
        desc = df[numeric_cols].describe()
        for col in numeric_cols:
            if col in desc.columns:
                summary_parts.append(f"\n{col}:")
                summary_parts.append(f"  Mean: {desc[col]['mean']:.2f}")
                summary_parts.append(f"  Median: {desc[col]['50%']:.2f}")
                summary_parts.append(f"  Std Dev: {desc[col]['std']:.2f}")
                summary_parts.append(f"  Min: {desc[col]['min']:.2f}")
                summary_parts.append(f"  Max: {desc[col]['max']:.2f}")
        summary_parts.append("\n")
   
    # Categorical columns - top values
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        summary_parts.append("CATEGORICAL DATA (Top 5 values):")
        for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
            value_counts = df[col].value_counts().head(5)
            summary_parts.append(f"\n{col}:")
            for val, count in value_counts.items():
                pct = (count / len(df) * 100)
                summary_parts.append(f"  {val}: {count} ({pct:.1f}%)")
        summary_parts.append("\n")
   
    # Sample data (first 5 rows)
    summary_parts.append("SAMPLE DATA (First 5 rows):")
    sample_data = df.head(5).to_string()
    summary_parts.append(sample_data)
   
    # If dataset is small enough, include more rows
    if len(df) <= 20:
        summary_parts.append(f"\n\nCOMPLETE DATA ({len(df)} rows):")
        summary_parts.append(df.to_string())
   
    return "\n".join(summary_parts)






# Old visualization functions removed - replaced with AI chatbot analysis
# The following functions were removed: render_data_table, render_charts, render_statistics
# All data analysis is now done through the AI chatbot interface




def main():
    """Main application"""
    init_session_state()
   
    # Header
    st.markdown('<div class="main-header">🔍 AI-Powered Database View Generator</div>',
                unsafe_allow_html=True)
    st.markdown("Generate semantically meaningful database views using AI")
   
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
       
        # Schema input
        st.subheader("1. Load Schema")
        schema_source = st.radio(
            "Schema Source",
            ["Upload JSON", "Use Sample"],
            help="Upload your own schema or use a sample"
        )
       
        if schema_source == "Upload JSON":
            uploaded_file = st.file_uploader(
                "Upload Schema JSON",
                type=['json'],
                help="Upload a JSON file containing your database schema"
            )
           
            if uploaded_file:
                if st.button("Load Schema"):
                    with st.spinner("Loading schema..."):
                        parser = load_schema_from_upload(uploaded_file)
                        if parser:
                            st.success("Schema loaded successfully!")
       
        else:  # Use Sample
            if st.button("Load Sample Schema"):
                # Use the EOB sample schema
                sample_schema = {
                    "tables": [
                        {
                            "name": "eob_document_extracts",
                            "columns": [
                                {"name": "id", "type": "bigint", "description": "Primary key"},
                                {"name": "file_name", "type": "text", "description": "Name of the EOB file"},
                                {"name": "file_path", "type": "text", "description": "Path to the file"},
                                {"name": "total_page_count", "type": "integer", "description": "Number of pages"},
                                {"name": "transaction_count", "type": "integer", "description": "Number of transactions"},
                                {"name": "created_date", "type": "timestamp with time zone", "description": "Creation timestamp"}
                            ],
                            "foreign_keys": []
                        },
                        {
                            "name": "eob_pagewise_extraction",
                            "columns": [
                                {"name": "id", "type": "bigint", "description": "Primary key"},
                                {"name": "document_id", "type": "bigint", "description": "Reference to document"},
                                {"name": "page_no", "type": "integer", "description": "Page number"},
                                {"name": "patient_name", "type": "text", "description": "Patient name"},
                                {"name": "claim_number", "type": "text", "description": "Claim number"},
                                {"name": "bill_charge_amount", "type": "numeric", "description": "Billed amount"},
                                {"name": "payment_amount", "type": "numeric", "description": "Payment amount"},
                                {"name": "adjustment_amount", "type": "numeric", "description": "Adjustment amount"}
                            ],
                            "foreign_keys": [
                                {
                                    "column": "document_id",
                                    "references_table": "eob_document_extracts",
                                    "references_column": "id"
                                }
                            ]
                        }
                    ]
                }
               
                st.session_state.schema = sample_schema
                st.session_state.schema_parser = SchemaParser.from_dict(sample_schema)
                st.success("Sample schema loaded!")
       
        # LLM Configuration
        st.subheader("2. LLM Settings")
       
        provider = st.selectbox(
            "Provider",
            ["ollama", "litellm"],
            index=0,
            help="Select LLM provider"
        )
       
        if provider == "ollama":
            ollama_url = st.text_input(
                "Ollama URL",
                value=config.llm.ollama_url,
                help="URL of Ollama server"
            )
            model = st.text_input(
                "Model",
                value=config.llm.ollama_model,
                help="Ollama model name"
            )
        else:
            model = st.text_input(
                "Model",
                value=config.llm.litellm_model,
                help="LiteLLM model identifier"
            )
            ollama_url = None
       
        # Generation settings
        st.subheader("3. Generation Settings")
       
        num_views = st.slider(
            "Number of Views",
            min_value=1,
            max_value=config.app.max_views,
            value=config.app.default_num_views,
            help="Number of views to generate"
        )
       
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=config.llm.temperature,
            step=0.1,
            help="Higher = more creative, Lower = more deterministic"
        )
   
    # Main content area
    if st.session_state.schema_parser is None:
        st.info("👈 Please load a schema from the sidebar to begin")
        return
   
    # Display schema info
    render_schema_info(st.session_state.schema_parser)
   
    # Generate views button
    st.markdown('<div class="sub-header">🚀 Generate Views</div>', unsafe_allow_html=True)
   
    col1, col2 = st.columns([1, 3])
   
    with col1:
        if st.button("Generate Views", type="primary", use_container_width=True):
            st.session_state.analysis_done = False
           
            with st.spinner("Generating views... This may take a minute."):
                try:
                    # Run pipeline
                    kwargs = {}
                    if provider == "ollama" and ollama_url:
                        kwargs['ollama_url'] = ollama_url
                   
                    results = asyncio.run(
                        run_pipeline_from_dict(
                            schema_dict=st.session_state.schema,
                            num_views=num_views,
                            provider=provider,
                            model=model
                        )
                    )
                   
                    st.session_state.results = results
                    st.session_state.analysis_done = False
                    st.success("Views generated successfully!")
               
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")
                    logger.exception("View generation failed")
   
    with col2:
        if st.session_state.results:
            if st.button("📊 Analyze Results", use_container_width=True):
                st.session_state.analysis_done = True
   
    # Display results
    if st.session_state.results:
        render_results(st.session_state.results)
       
        # Database execution section
        st.markdown("---")
       
        # Connection setup
        with st.expander("🔌 Database Connection", expanded=not st.session_state.db_connected):
            render_database_connection_dialog()
       
        # View execution
        if st.session_state.db_connected:
            render_view_execution_panel()
           
            # Visualization
            if st.session_state.show_visualization:
                render_visualization_panel()
       
        # Export options
        st.markdown("---")
        st.markdown('<div class="sub-header">💾 Export</div>', unsafe_allow_html=True)
       
        col1, col2 = st.columns(2)
       
        with col1:
            # Export as JSON
            results_json = json.dumps(
                st.session_state.results.dict(),
                indent=2
            )
            st.download_button(
                label="Download Results (JSON)",
                data=results_json,
                file_name="view_generation_results.json",
                mime="application/json",
                use_container_width=True
            )
       
        with col2:
            # Export valid views as SQL
            valid_views = [v for v in st.session_state.results.views if v.is_valid]
            if valid_views:
                sql_content = ""
                for view in valid_views:
                    if view.sql:
                        sql_content += f"-- View: {view.view_name}\n"
                        sql_content += f"-- {view.view_name}\n"
                        sql_content += f"CREATE OR REPLACE VIEW {view.view_name} AS\n"
                        sql_content += view.sql + "\n\n"
               
                st.download_button(
                    label="Download All SQL",
                    data=sql_content,
                    file_name="generated_views.sql",
                    mime="text/plain",
                    use_container_width=True
                )




if __name__ == "__main__":
    main()



