"""
LLM Interface Module


Provides unified interface to LLM providers (Ollama, LiteLLM).
Requirement 2: LLM Interface with structured output validation
"""


import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
import requests
from config import config


logger = logging.getLogger(__name__)


# Try to import litellm for multi-provider support
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not available. Only Ollama provider will work.")




class LLMInterface:
    """
    Unified interface for LLM providers.
   
    Supports:
    - Ollama (local models)
    - LiteLLM (OpenAI, Anthropic, etc.)
    """
   
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        self.provider = provider or config.llm.provider
        self.model = model
       
        # Provider-specific settings
        if self.provider == "ollama":
            self.ollama_url = kwargs.get('ollama_url', config.llm.ollama_url)
            self.ollama_model = kwargs.get('ollama_model', config.llm.ollama_model)
            self.ollama_timeout = kwargs.get('ollama_timeout', config.llm.ollama_timeout)
            self.model = self.model or self.ollama_model
       
        elif self.provider == "litellm":
            if not LITELLM_AVAILABLE:
                raise RuntimeError(
                    "LiteLLM provider requested but 'litellm' package is not installed. "
                    "Install it with: pip install litellm"
                )
            self.litellm_model = kwargs.get('litellm_model', config.llm.litellm_model)
            self.model = self.model or self.litellm_model
           
            # Set API keys if available
            if config.llm.openai_api_key:
                litellm.openai_key = config.llm.openai_api_key
            if config.llm.anthropic_api_key:
                litellm.anthropic_key = config.llm.anthropic_api_key
       
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
       
        self.temperature = kwargs.get('temperature', config.llm.temperature)
        self.max_retries = kwargs.get('max_retries', config.llm.max_retries)
        self.retry_backoff = kwargs.get('retry_backoff', config.llm.retry_backoff)
       
        logger.info(f"Initialized LLM interface: provider={self.provider}, model={self.model}")
   
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: str = "json"
    ) -> str:
        """
        Generate completion from LLM.
       
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            response_format: Expected format ('json' or 'text')
       
        Returns:
            Raw response text from LLM
        """
        temp = temperature if temperature is not None else self.temperature
       
        if self.provider == "ollama":
            return await self._call_ollama(
                prompt,
                system_prompt=system_prompt,
                temperature=temp,
                response_format=response_format
            )
        elif self.provider == "litellm":
            return await self._call_litellm(
                prompt,
                system_prompt=system_prompt,
                temperature=temp
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
   
    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json"
    ) -> str:
        """Call Ollama API"""
       
        def _post() -> str:
            # Build the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
           
            payload = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
           
            # Request JSON format if specified
            if response_format == "json":
                payload["format"] = "json"
           
            headers = {"Content-Type": "application/json"}
           
            # Construct the API endpoint
            api_url = f"{self.ollama_url.rstrip('/')}/api/generate"
           
            logger.debug(f"Calling Ollama at {api_url}")
           
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=self.ollama_timeout
            )
            response.raise_for_status()
           
            try:
                data = response.json()
            except ValueError:
                return response.text
           
            # Extract response text from Ollama format
            if isinstance(data, dict):
                return data.get('response', str(data))
           
            return response.text
       
        # Run in thread pool to avoid blocking
        for attempt in range(self.max_retries):
            try:
                return await asyncio.to_thread(_post)
            except Exception as e:
                logger.warning(
                    f"Ollama call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_backoff * (attempt + 1))
                else:
                    raise
   
    async def _call_litellm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """Call LiteLLM API"""
       
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
       
        for attempt in range(self.max_retries):
            try:
                response = await litellm.acompletion(
                    model=self.litellm_model,
                    messages=messages,
                    temperature=temperature
                )
               
                # Extract content from response
                if isinstance(response, dict):
                    choices = response.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        content = message.get("content", "")
                        return content
               
                return str(response)
           
            except Exception as e:
                logger.warning(
                    f"LiteLLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_backoff * (attempt + 1))
                else:
                    raise
   
    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LLM response text.
        Handles markdown code blocks and other formatting.
        """
        if not text:
            return None
       
        text = text.strip()
       
        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
       
        # Try to parse as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object/array in text
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start_idx = text.find(start_char)
                if start_idx != -1:
                    # Find matching closing bracket
                    depth = 0
                    for i in range(start_idx, len(text)):
                        if text[i] == start_char:
                            depth += 1
                        elif text[i] == end_char:
                            depth -= 1
                            if depth == 0:
                                try:
                                    return json.loads(text[start_idx:i+1])
                                except json.JSONDecodeError:
                                    continue
       
        logger.error("Failed to extract JSON from LLM response")
        return None




def build_system_prompt() -> str:
    """Build the system prompt for view generation"""
    return """You are an expert database architect and SQL expert.


Your task is to generate semantically meaningful database views based on a provided schema.


CRITICAL RULES:
1. Output ONLY valid JSON conforming to the ViewGenerationResponse schema
2. Use ONLY table and column names that exist in the provided schema
3. Create joins ONLY along existing foreign key relationships
4. Each view must be semantically meaningful and useful for business analytics
5. View names must be lowercase with underscores (snake_case)
6. Include a clear description of each view's business purpose


JSON SCHEMA:
{
  "views": [
    {
      "name": "view_name_here",
      "description": "Clear description of view purpose",
      "query": {
        "select": ["list", "of", "columns"],
        "from": "base_table",
        "joins": [
          {
            "type": "INNER",
            "table": "joined_table",
            "on": "base.id = joined.foreign_key"
          }
        ],
        "where": ["optional", "conditions"],
        "group_by": ["optional", "grouping"],
        "order_by": ["optional", "ordering"]
      }
    }
  ],
  "reasoning": "Optional explanation of design choices"
}


Return ONLY the JSON object. No markdown, no explanation outside the JSON."""




def build_user_prompt(schema_context: str, num_views: int = 5) -> str:
    """Build the user prompt with schema context"""
    return f"""Generate {num_views} useful database views for the following schema:


{schema_context}


REQUIREMENTS:
- Create views that would be valuable for business analytics and reporting
- Use appropriate joins based on foreign key relationships
- Include aggregations where meaningful (SUM, COUNT, AVG, etc.)
- Consider common business questions and metrics
- Ensure each view has a clear, specific purpose


Generate {num_views} distinct, high-quality views and return ONLY the JSON response."""



