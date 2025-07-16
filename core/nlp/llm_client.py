"""
LLM client for natural language processing and prompt parsing.
Supports multiple LLM providers (Anthropic, OpenAI, Gemini, Venice).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
import json
import logging
import asyncio
from datetime import datetime

from config import get_settings, LLM_PROVIDERS

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    VENICE = "venice"


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TradingInstruction:
    """Parsed trading instruction from natural language."""
    action: str  # buy, sell, swap, hold
    token_in: Optional[str] = None
    token_out: Optional[str] = None
    amount: Optional[float] = None
    amount_type: str = "absolute"  # absolute, percentage, all
    conditions: List[str] = None
    urgency: str = "normal"  # low, normal, high
    confidence: float = 0.0
    reasoning: str = ""
    raw_prompt: str = ""


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{provider}")
    
    @abstractmethod
    async def generate_response(self, prompt: str, model: str = None) -> LLMResponse:
        """
        Generate response from LLM.
        
        Args:
            prompt: Input prompt
            model: Model to use (optional)
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: str):
        super().__init__("anthropic", api_key)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed")
    
    async def generate_response(self, prompt: str, model: str = None) -> LLMResponse:
        """Generate response using Anthropic Claude."""
        if model is None:
            model = "claude-3-sonnet-20240229"
        
        start_time = datetime.utcnow()
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return LLMResponse(
                content=response.content[0].text,
                provider=self.provider,
                model=model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client."""
    
    def __init__(self, api_key: str):
        super().__init__("openai", api_key)
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed")
    
    async def generate_response(self, prompt: str, model: str = None) -> LLMResponse:
        """Generate response using OpenAI GPT."""
        if model is None:
            model = "gpt-4"
        
        start_time = datetime.utcnow()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=self.provider,
                model=model,
                tokens_used=response.usage.total_tokens,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return ["gpt-4", "gpt-3.5-turbo"]


class GeminiClient(BaseLLMClient):
    """Google Gemini client."""
    
    def __init__(self, api_key: str):
        super().__init__("gemini", api_key)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai
        except ImportError:
            raise ImportError("google-generativeai package not installed")
    
    async def generate_response(self, prompt: str, model: str = None) -> LLMResponse:
        """Generate response using Google Gemini."""
        if model is None:
            model = "gemini-pro"
        
        start_time = datetime.utcnow()
        
        try:
            model_instance = self.client.GenerativeModel(model)
            response = await asyncio.to_thread(model_instance.generate_content, prompt)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return LLMResponse(
                content=response.text,
                provider=self.provider,
                model=model,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Gemini models."""
        return ["gemini-pro", "gemini-pro-vision"]


class LLMManager:
    """
    Manages multiple LLM providers and handles prompt parsing.
    """
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_provider = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available LLM clients based on configuration."""
        
        # Anthropic
        if settings.anthropic_api_key:
            try:
                self.clients["anthropic"] = AnthropicClient(settings.anthropic_api_key)
                if not self.default_provider:
                    self.default_provider = "anthropic"
                logger.info("Initialized Anthropic client")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        # OpenAI
        if settings.openai_api_key:
            try:
                self.clients["openai"] = OpenAIClient(settings.openai_api_key)
                if not self.default_provider:
                    self.default_provider = "openai"
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Gemini
        if settings.gemini_api_key:
            try:
                self.clients["gemini"] = GeminiClient(settings.gemini_api_key)
                if not self.default_provider:
                    self.default_provider = "gemini"
                logger.info("Initialized Gemini client")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
        
        if not self.clients:
            logger.warning("No LLM clients initialized - check API key configuration")
    
    async def parse_trading_prompt(self, prompt: str, provider: str = None) -> Optional[TradingInstruction]:
        """
        Parse natural language trading prompt into structured instruction.
        
        Args:
            prompt: Natural language trading instruction
            provider: LLM provider to use (optional)
            
        Returns:
            Parsed trading instruction or None if parsing failed
        """
        if not self.clients:
            logger.error("No LLM clients available")
            return None
        
        provider = provider or self.default_provider
        
        if provider not in self.clients:
            logger.error(f"Provider {provider} not available")
            return None
        
        # Create structured prompt for trading instruction parsing
        system_prompt = self._create_trading_prompt(prompt)
        
        try:
            client = self.clients[provider]
            response = await client.generate_response(system_prompt)
            
            # Parse JSON response
            instruction = self._parse_llm_response(response.content, prompt)
            
            if instruction:
                logger.info(f"Parsed trading instruction: {instruction.action} {instruction.amount} {instruction.token_in} -> {instruction.token_out}")
            
            return instruction
            
        except Exception as e:
            logger.error(f"Error parsing trading prompt: {e}")
            return None
    
    def _create_trading_prompt(self, user_prompt: str) -> str:
        """
        Create structured prompt for trading instruction parsing.
        
        Args:
            user_prompt: User's natural language prompt
            
        Returns:
            Structured prompt for LLM
        """
        return f"""
You are a trading instruction parser. Parse the following natural language trading instruction into a structured JSON format.

User prompt: "{user_prompt}"

Extract the following information:
- action: "buy", "sell", "swap", or "hold"
- token_in: input token symbol (e.g., "ETH", "BTC", "USDC")
- token_out: output token symbol
- amount: numerical amount (if specified)
- amount_type: "absolute", "percentage", or "all"
- conditions: any conditions mentioned (as array of strings)
- urgency: "low", "normal", or "high"
- confidence: your confidence in the parsing (0.0 to 1.0)
- reasoning: brief explanation of your interpretation

Respond with valid JSON only. If the prompt is unclear or not trading-related, set action to "hold" and explain in reasoning.

Example response:
{{
    "action": "buy",
    "token_in": "ETH",
    "token_out": "USDC",
    "amount": 1.5,
    "amount_type": "absolute",
    "conditions": ["if price drops below $1600"],
    "urgency": "normal",
    "confidence": 0.9,
    "reasoning": "User wants to buy 1.5 ETH worth of USDC with a condition"
}}
"""
    
    def _parse_llm_response(self, response: str, original_prompt: str) -> Optional[TradingInstruction]:
        """
        Parse LLM response into TradingInstruction.
        
        Args:
            response: LLM response content
            original_prompt: Original user prompt
            
        Returns:
            TradingInstruction or None if parsing failed
        """
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            return TradingInstruction(
                action=data.get("action", "hold"),
                token_in=data.get("token_in"),
                token_out=data.get("token_out"),
                amount=data.get("amount"),
                amount_type=data.get("amount_type", "absolute"),
                conditions=data.get("conditions", []),
                urgency=data.get("urgency", "normal"),
                confidence=data.get("confidence", 0.0),
                reasoning=data.get("reasoning", ""),
                raw_prompt=original_prompt
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    async def generate_trade_summary(self, instruction: TradingInstruction, provider: str = None) -> str:
        """
        Generate human-readable summary of trading instruction.
        
        Args:
            instruction: Trading instruction
            provider: LLM provider to use (optional)
            
        Returns:
            Human-readable summary
        """
        if not self.clients:
            return f"Trade: {instruction.action} {instruction.amount} {instruction.token_in}"
        
        provider = provider or self.default_provider
        
        if provider not in self.clients:
            return f"Trade: {instruction.action} {instruction.amount} {instruction.token_in}"
        
        prompt = f"""
Create a brief, human-readable summary of this trading instruction:

Action: {instruction.action}
Token In: {instruction.token_in}
Token Out: {instruction.token_out}
Amount: {instruction.amount} ({instruction.amount_type})
Conditions: {instruction.conditions}
Urgency: {instruction.urgency}
Reasoning: {instruction.reasoning}

Provide a 1-2 sentence summary that a trader would understand.
"""
        
        try:
            client = self.clients[provider]
            response = await client.generate_response(prompt)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating trade summary: {e}")
            return f"Trade: {instruction.action} {instruction.amount} {instruction.token_in}"
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers."""
        return list(self.clients.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available."""
        return provider in self.clients


# Global LLM manager instance
llm_manager = LLMManager()

