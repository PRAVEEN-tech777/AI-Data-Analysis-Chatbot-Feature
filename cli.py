#!/usr/bin/env python3
"""
Command-line interface for AI-Powered Database View Generator


Usage:
    python cli.py --schema schema.json --num-views 5 --output results.json
    python cli.py --help
"""


import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path


from pipeline import run_pipeline_from_file
from config import config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered database views from schema"
    )
   
    # Required arguments
    parser.add_argument(
        '--schema',
        required=True,
        help='Path to schema JSON file'
    )
   
    # Optional arguments
    parser.add_argument(
        '--num-views',
        type=int,
        default=config.app.default_num_views,
        help=f'Number of views to generate (default: {config.app.default_num_views})'
    )
   
    parser.add_argument(
        '--provider',
        choices=['ollama', 'litellm'],
        default=config.llm.provider,
        help=f'LLM provider (default: {config.llm.provider})'
    )
   
    parser.add_argument(
        '--model',
        help='Model name (provider-specific)'
    )
   
    parser.add_argument(
        '--temperature',
        type=float,
        default=config.llm.temperature,
        help=f'LLM temperature (default: {config.llm.temperature})'
    )
   
    parser.add_argument(
        '--output',
        help='Output file for results (JSON)'
    )
   
    parser.add_argument(
        '--sql-output',
        help='Output file for SQL (all valid views)'
    )
   
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.app.log_level,
        help=f'Logging level (default: {config.app.log_level})'
    )
   
    args = parser.parse_args()
   
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
   
    # Validate schema file
    schema_path = Path(args.schema)
    if not schema_path.exists():
        logger.error(f"Schema file not found: {args.schema}")
        sys.exit(1)
   
    try:
        # Run pipeline
        logger.info("=" * 70)
        logger.info("AI-Powered Database View Generator")
        logger.info("=" * 70)
        logger.info(f"Schema: {args.schema}")
        logger.info(f"Provider: {args.provider}")
        logger.info(f"Model: {args.model or 'default'}")
        logger.info(f"Num Views: {args.num_views}")
        logger.info("=" * 70)
       
        results = asyncio.run(
            run_pipeline_from_file(
                schema_file=args.schema,
                num_views=args.num_views,
                provider=args.provider,
                model=args.model,
                output_file=args.output
            )
        )
       
        # Print summary
        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"Total Generated:  {results.total_generated}")
        print(f"Valid Views:      {results.valid_views}")
        print(f"Invalid Views:    {results.invalid_views}")
        print(f"Success Rate:     {results.summary.get('success_rate', 'N/A')}")
        print("=" * 70)
       
        # Display valid views
        valid_views = [v for v in results.views if v.is_valid]
       
        if valid_views:
            print(f"\n✓ VALID VIEWS ({len(valid_views)}):")
            print("-" * 70)
            for i, view in enumerate(valid_views, 1):
                print(f"{i}. {view.view_name}")
                if view.warnings:
                    print(f"   Warnings: {len(view.warnings)}")
       
        # Display invalid views
        invalid_views = [v for v in results.views if not v.is_valid]
       
        if invalid_views:
            print(f"\n✗ INVALID VIEWS ({len(invalid_views)}):")
            print("-" * 70)
            for i, view in enumerate(invalid_views, 1):
                print(f"{i}. {view.view_name}")
                print(f"   Errors: {len(view.errors)}")
                for error in view.errors[:3]:  # Show first 3 errors
                    print(f"   - {error}")
                if len(view.errors) > 3:
                    print(f"   ... and {len(view.errors) - 3} more")
       
        # Export SQL if requested
        if args.sql_output and valid_views:
            sql_path = Path(args.sql_output)
            sql_content = ""
           
            for view in valid_views:
                if view.sql:
                    sql_content += f"-- View: {view.view_name}\n"
                    sql_content += f"-- Description: {view.view_name}\n"
                    sql_content += f"CREATE OR REPLACE VIEW {view.view_name} AS\n"
                    sql_content += view.sql + "\n\n"
           
            sql_path.write_text(sql_content, encoding='utf-8')
            logger.info(f"SQL exported to {sql_path}")
       
        print("\n" + "=" * 70)
       
        if results.valid_views == 0:
            logger.warning("No valid views generated")
            sys.exit(1)
       
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
   
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)




if __name__ == "__main__":
    main()



