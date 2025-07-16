"""
Configuration module for NFT-Gated AI Trading Bot.
Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings  # Fixed import
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(env="SECRET_KEY")
    bypass_nft_gate: bool = Field(default=False, env="BYPASS_NFT_GATE")
    real_data_mode: bool = Field(default=False, env="REAL_DATA_MODE")

    # Database Configuration
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(env="REDIS_URL")

    # AI/LLM API Keys
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    venice_api_key: Optional[str] = Field(default=None, env="VENICE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # Blockchain Configuration
    ethereum_rpc_url: str = Field(env="ETHEREUM_RPC_URL")
    skale_rpc_url: Optional[str] = Field(default=None, env="SKALE_RPC_URL")
    beam_rpc_url: Optional[str] = Field(default=None, env="BEAM_RPC_URL")
    private_key: str = Field(env="PRIVATE_KEY")
    private_key_beam: Optional[str] = Field(default=None, env="PRIVATE_KEY_BEAM")

    # Twitter Integration
    enable_twitter: bool = Field(default=False, env="ENABLE_TWITTER")
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    twitter_api_key: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = Field(default=None, env="TWITTER_API_SECRET")
    twitter_access_token: Optional[str] = Field(default=None, env="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: Optional[str] = Field(default=None, env="TWITTER_ACCESS_TOKEN_SECRET")
    twitter_username: Optional[str] = Field(default=None, env="TWITTER_USERNAME")

    # External APIs
    coingecko_api_key: Optional[str] = Field(default=None, env="COINGECKO_API_KEY")

    # Celery Configuration
    celery_broker_url: str = Field(env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND")

    # NFT Configuration
    nft_contract_address: Optional[str] = Field(default=None, env="NFT_CONTRACT_ADDRESS")
    nft_chain_id: int = Field(default=1, env="NFT_CHAIN_ID")

    # Trading Configuration
    default_slippage: float = Field(default=0.5, env="DEFAULT_SLIPPAGE")
    max_gas_price: int = Field(default=100, env="MAX_GAS_PRICE")
    min_trade_amount: float = Field(default=0.001, env="MIN_TRADE_AMOUNT")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # This allows extra environment variables without errors


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Rest of your constants...
SUPPORTED_NETWORKS = {
    "ethereum": {
        "chain_id": 1,
        "name": "Ethereum Mainnet",
        "rpc_key": "ethereum_rpc_url",
        "private_key": "private_key"
    },
    "skale": {
        "chain_id": 1351057110,
        "name": "SKALE Europa Hub",
        "rpc_key": "skale_rpc_url",
        "private_key": "private_key"
    },
    "beam": {
        "chain_id": 4337,
        "name": "Beam Mainnet",
        "rpc_key": "beam_rpc_url",
        "private_key": "private_key_beam"
    }
}

LLM_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "api_key": "anthropic_api_key",
        "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    },
    "openai": {
        "name": "OpenAI GPT",
        "api_key": "openai_api_key",
        "models": ["gpt-4", "gpt-3.5-turbo"]
    },
    "gemini": {
        "name": "Google Gemini",
        "api_key": "gemini_api_key",
        "models": ["gemini-pro", "gemini-pro-vision"]
    },
    "venice": {
        "name": "Venice AI",
        "api_key": "venice_api_key",
        "models": ["venice-1"]
    }
}

STRATEGY_TYPES = [
    "momentum",
    "arbitrage",
    "mean_reversion",
    "grid_trading",
    "dca",
    "custom"
]

SUPPORTED_EXCHANGES = {
    "uniswap_v2": {
        "name": "Uniswap V2",
        "type": "dex",
        "networks": ["ethereum"]
    },
    "uniswap_v3": {
        "name": "Uniswap V3",
        "type": "dex",
        "networks": ["ethereum"]
    },
    "sushiswap": {
        "name": "SushiSwap",
        "type": "dex",
        "networks": ["ethereum"]
    }
}