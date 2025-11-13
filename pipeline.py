"""
View Generator Pipeline


Main orchestrator that coordinates:
1. Schema parsing
2. LLM-based view generation
3. Validation and post-processing
4. Result aggregation
"""


import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


from schema_parser import SchemaParser
from llm_interface import LLMInterface, build_system_prompt, build_user_prompt
from validator import ViewValidator, deduplicate_views
from models import (
    ViewDefinition,
    ViewGenerationResponse,
    ValidationResult,
    AnalysisResult
)
from config import config


logger = logging.getLogger(__name__)




class ViewGeneratorPipeline:
    """
    Main pipeline for generating and validating database views.
   
    Orchestrates the complete workflow:
    1. Load and parse schema
    2. Generate views using LLM
    3. Validate views
    4. Post-process and deduplicate
    5. Return analysis results
    """
   
    def __init__(
        self,
        schema: SchemaParser,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        **kwargs
    ):
        self.schema = schema
        self.validator = ViewValidator(schema)
       
        # Initialize LLM interface
        self.llm = LLMInterface(
            provider=llm_provider,
            model=llm_model,
            **kwargs
        )
       
        logger.info("Initialized ViewGeneratorPipeline")
   
    async def generate_views(
        self,
        num_views: int = 5,
        temperature: Optional[float] = None
    ) -> List[ViewDefinition]:
        """
        Generate views using LLM.
       
        Args:
            num_views: Number of views to generate
            temperature: LLM temperature (0.0 = deterministic)
       
        Returns:
            List of ViewDefinition objects
        """
        logger.info(f"Generating {num_views} views...")
       
        # Build prompts
        system_prompt = build_system_prompt()
        schema_context = self.schema.get_semantic_context()
        user_prompt = build_user_prompt(schema_context, num_views)
       
        # Call LLM
        try:
            response_text = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                response_format="json"
            )
           
            logger.debug(f"LLM Response: {response_text[:500]}...")
           
            # Extract and parse JSON
            response_json = self.llm.extract_json(response_text)
           
            if not response_json:
                logger.error("Failed to extract JSON from LLM response")
                return []
           
            # Parse into Pydantic model
            try:
                view_response = ViewGenerationResponse(**response_json)
                logger.info(f"Successfully parsed {len(view_response.views)} views")
                return view_response.views
            except Exception as e:
                logger.error(f"Failed to parse views from JSON: {e}")
                logger.debug(f"Response JSON: {json.dumps(response_json, indent=2)}")
               
                # Try to salvage views if response format is slightly off
                views = self._salvage_views(response_json)
                if views:
                    logger.info(f"Salvaged {len(views)} views from malformed response")
                return views
       
        except Exception as e:
            logger.exception(f"LLM generation failed: {e}")
            return []
   
    def _salvage_views(self, response_json: Dict[str, Any]) -> List[ViewDefinition]:
        """Try to extract views from malformed LLM response"""
        views = []
       
        # Try different possible locations for views
        candidates = []
        if isinstance(response_json, list):
            candidates = response_json
        elif isinstance(response_json, dict):
            for key in ['views', 'data', 'items', 'results']:
                if key in response_json:
                    val = response_json[key]
                    if isinstance(val, list):
                        candidates = val
                        break
                    elif isinstance(val, dict):
                        candidates = [val]
                        break
       
        # Try to parse each candidate
        for item in candidates:
            if not isinstance(item, dict):
                continue
           
            try:
                view = ViewDefinition(**item)
                views.append(view)
            except Exception as e:
                logger.debug(f"Failed to parse view candidate: {e}")
                continue
       
        return views
   
    def validate_views(self, views: List[ViewDefinition]) -> List[ValidationResult]:
        """
        Validate all views.
       
        Returns list of ValidationResult objects.
        """
        logger.info(f"Validating {len(views)} views...")
       
        results = []
        for view in views:
            result = self.validator.validate_view(view)
            results.append(result)
           
            if result.is_valid:
                logger.info(f"✓ View '{view.name}' is valid")
            else:
                logger.warning(
                    f"✗ View '{view.name}' is invalid: {len(result.errors)} errors"
                )
       
        return results
   
    def post_process(
        self,
        views: List[ViewDefinition]
    ) -> Tuple[List[ViewDefinition], Dict[str, Any]]:
        """
        Post-process views: deduplicate and gather statistics.
       
        Requirement 5: Output Post-Processing
        """
        logger.info("Post-processing views...")
       
        # Deduplicate
        original_count = len(views)
        unique_views = deduplicate_views(views)
        dedup_count = original_count - len(unique_views)
       
        if dedup_count > 0:
            logger.info(f"Removed {dedup_count} duplicate views")
       
        # Gather statistics
        stats = {
            'original_count': original_count,
            'after_deduplication': len(unique_views),
            'duplicates_removed': dedup_count
        }
       
        return unique_views, stats
   
    async def run(
        self,
        num_views: int = 5,
        temperature: Optional[float] = None
    ) -> AnalysisResult:
        """
        Run complete pipeline: generate, validate, post-process.
       
        Returns AnalysisResult with all details.
        """
        logger.info("=" * 60)
        logger.info("Starting View Generation Pipeline")
        logger.info("=" * 60)
       
        # Step 1: Generate views
        views = await self.generate_views(num_views, temperature)
       
        if not views:
            logger.error("No views generated")
            return AnalysisResult(
                total_generated=0,
                valid_views=0,
                invalid_views=0,
                views=[],
                summary={'error': 'No views generated by LLM'}
            )
       
        # Step 2: Post-process (deduplicate)
        unique_views, dedup_stats = self.post_process(views)
       
        # Step 3: Validate
        validation_results = self.validate_views(unique_views)
       
        # Separate valid and invalid
        valid_results = [r for r in validation_results if r.is_valid]
        invalid_results = [r for r in validation_results if not r.is_valid]
       
        # Build summary
        summary = {
            'total_generated': len(views),
            'after_deduplication': len(unique_views),
            'duplicates_removed': dedup_stats['duplicates_removed'],
            'valid': len(valid_results),
            'invalid': len(invalid_results),
            'success_rate': f"{len(valid_results)/len(unique_views)*100:.1f}%" if unique_views else "0%"
        }
       
        logger.info("=" * 60)
        logger.info("Pipeline Complete")
        logger.info(f"Generated: {summary['total_generated']}")
        logger.info(f"After deduplication: {summary['after_deduplication']}")
        logger.info(f"Valid: {summary['valid']}")
        logger.info(f"Invalid: {summary['invalid']}")
        logger.info(f"Success rate: {summary['success_rate']}")
        logger.info("=" * 60)
       
        return AnalysisResult(
            total_generated=len(views),
            valid_views=len(valid_results),
            invalid_views=len(invalid_results),
            views=validation_results,
            summary=summary
        )
   
    def export_results(
        self,
        results: AnalysisResult,
        output_file: str
    ):
        """Export results to JSON file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
       
        # Convert to dict
        results_dict = results.dict()
       
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2)
       
        logger.info(f"Results exported to {output_path}")




async def run_pipeline_from_file(
    schema_file: str,
    num_views: int = 5,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    output_file: Optional[str] = None
) -> AnalysisResult:
    """
    Convenience function to run pipeline from schema file.
   
    Args:
        schema_file: Path to schema JSON file
        num_views: Number of views to generate
        provider: LLM provider ('ollama' or 'litellm')
        model: Model name
        output_file: Optional path to export results
   
    Returns:
        AnalysisResult object
    """
    # Load schema
    logger.info(f"Loading schema from {schema_file}")
    schema = SchemaParser.from_file(schema_file)
   
    # Create pipeline
    pipeline = ViewGeneratorPipeline(
        schema=schema,
        llm_provider=provider,
        llm_model=model
    )
   
    # Run pipeline
    results = await pipeline.run(num_views=num_views)
   
    # Export if requested
    if output_file:
        pipeline.export_results(results, output_file)
   
    return results




async def run_pipeline_from_dict(
    schema_dict: Dict[str, Any],
    num_views: int = 5,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> AnalysisResult:
    """
    Convenience function to run pipeline from schema dictionary.
   
    Args:
        schema_dict: Schema as dictionary
        num_views: Number of views to generate
        provider: LLM provider
        model: Model name
   
    Returns:
        AnalysisResult object
    """
    # Load schema
    schema = SchemaParser.from_dict(schema_dict)
   
    # Create pipeline
    pipeline = ViewGeneratorPipeline(
        schema=schema,
        llm_provider=provider,
        llm_model=model
    )
   
    # Run pipeline
    results = await pipeline.run(num_views=num_views)
   
    return results



