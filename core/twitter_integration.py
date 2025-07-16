"""
Twitter integration for NFT-Gated AI Trading Bot.
Handles automated tweeting of trading insights, market analysis, and notifications.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import tweepy

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TweetTemplate:
    """Template for different types of tweets."""
    template_type: str
    message_template: str
    hashtags: List[str]
    include_metrics: bool = True


class TwitterError(Exception):
    """Custom exception for Twitter API errors."""
    pass


class TwitterClient:
    """
    Twitter API client for posting notifications and engaging with community.

    Handles trade notifications, market updates, and social media engagement
    for the NFT-Gated AI Trading Bot.
    """

    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.enable_twitter
        self.api_v1: Optional[tweepy.API] = None
        self.api_v2: Optional[tweepy.Client] = None
        self.username = self.settings.twitter_username or "trading_bot"

        # Tweet templates for different notification types
        self.templates = {
            "trade_executed": TweetTemplate(
                template_type="trade_executed",
                message_template="🚀 Trade Executed!\n\n💱 {action}: {amount_in} {token_in} → {amount_out} {token_out}\n💰 Price: ${price:.4f}\n⛽ Gas: {gas_used:,} units\n🔗 TX: {tx_hash}\n\n#DeFi #Trading #NFTGated #AI",
                hashtags=["DeFi", "Trading", "NFTGated", "AI"]
            ),
            "strategy_signal": TweetTemplate(
                template_type="strategy_signal",
                message_template="📊 Strategy Alert: {strategy_name}\n\n🎯 Signal: {signal_type} {token}\n📈 Confidence: {confidence:.1%}\n💡 Reason: {reason}\n\n#TradingBot #AI #DeFi #Strategy",
                hashtags=["TradingBot", "AI", "DeFi", "Strategy"]
            ),
            "market_update": TweetTemplate(
                template_type="market_update",
                message_template="📈 Market Update\n\n{token}: ${price:.4f} ({change:+.2%})\n📊 24h Volume: ${volume:,.0f}\n🏆 Market Cap: ${market_cap:,.0f}\n\n#Crypto #MarketUpdate #Price",
                hashtags=["Crypto", "MarketUpdate", "Price"]
            ),
            "system_status": TweetTemplate(
                template_type="system_status",
                message_template="🤖 System Status: {status}\n\n✅ Active Strategies: {active_strategies}\n📊 24h Trades: {trades_24h}\n💰 24h Volume: ${volume_24h:,.0f}\n\n#TradingBot #Status #NFTGated",
                hashtags=["TradingBot", "Status", "NFTGated"]
            )
        }

        if self.enabled:
            self._initialize_clients()

    def _initialize_clients(self):
        """Initialize Twitter API clients."""
        try:
            # Validate required credentials
            required_creds = [
                self.settings.twitter_api_key,
                self.settings.twitter_api_secret,
                self.settings.twitter_access_token,
                self.settings.twitter_access_token_secret
            ]

            if not all(required_creds):
                logger.error("Missing required Twitter credentials")
                self.enabled = False
                return

            # Twitter API v2 client (primary)
            self.api_v2 = tweepy.Client(
                bearer_token=self.settings.twitter_bearer_token,
                consumer_key=self.settings.twitter_api_key,
                consumer_secret=self.settings.twitter_api_secret,
                access_token=self.settings.twitter_access_token,
                access_token_secret=self.settings.twitter_access_token_secret,
                wait_on_rate_limit=True
            )

            # Twitter API v1.1 client (for legacy features)
            auth = tweepy.OAuth1UserHandler(
                self.settings.twitter_api_key,
                self.settings.twitter_api_secret,
                self.settings.twitter_access_token,
                self.settings.twitter_access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

            # Test the connection
            user = self.api_v2.get_me()
            if user.data:
                self.username = user.data.username
                logger.info(f"Twitter client initialized successfully for @{self.username}")
            else:
                raise TwitterError("Failed to verify Twitter credentials")

        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            self.enabled = False
            raise TwitterError(f"Twitter initialization failed: {e}")

    def is_enabled(self) -> bool:
        """Check if Twitter integration is enabled and working."""
        return self.enabled and self.api_v2 is not None

    async def post_trade_notification(self, trade_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a trade execution notification.

        Args:
            trade_data: Trade execution data

        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            logger.info("Twitter notifications disabled")
            return None

        try:
            template = self.templates["trade_executed"]

            # Format the message
            message = template.message_template.format(
                action=trade_data.get("action", "SWAP").upper(),
                amount_in=trade_data.get("amount_in", 0),
                token_in=trade_data.get("token_in", "TOKEN"),
                amount_out=trade_data.get("amount_out", 0),
                token_out=trade_data.get("token_out", "TOKEN"),
                price=trade_data.get("price", 0),
                gas_used=trade_data.get("gas_used", 0),
                tx_hash=self._truncate_hash(trade_data.get("tx_hash", ""))
            )

            # Post tweet
            response = await asyncio.to_thread(self.api_v2.create_tweet, text=message)

            if response.data:
                tweet_id = response.data["id"]
                logger.info(f"Posted trade notification tweet: {tweet_id}")
                return tweet_id

        except Exception as e:
            logger.error(f"Failed to post trade notification: {e}")

        return None

    async def post_strategy_signal(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a strategy signal notification.

        Args:
            signal_data: Strategy signal data

        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            template = self.templates["strategy_signal"]

            message = template.message_template.format(
                strategy_name=signal_data.get("strategy_name", "Unknown"),
                signal_type=signal_data.get("signal_type", "SIGNAL").upper(),
                token=signal_data.get("token", "TOKEN"),
                confidence=signal_data.get("confidence", 0),
                reason=signal_data.get("reason", "Analysis complete")
            )

            response = await asyncio.to_thread(self.api_v2.create_tweet, text=message)

            if response.data:
                tweet_id = response.data["id"]
                logger.info(f"Posted strategy signal tweet: {tweet_id}")
                return tweet_id

        except Exception as e:
            logger.error(f"Failed to post strategy signal: {e}")

        return None

    async def post_market_update(self, market_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a market update notification.

        Args:
            market_data: Market data for update

        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            template = self.templates["market_update"]

            message = template.message_template.format(
                token=market_data.get("token", "TOKEN"),
                price=market_data.get("price", 0),
                change=market_data.get("price_change_24h", 0),
                volume=market_data.get("volume_24h", 0),
                market_cap=market_data.get("market_cap", 0)
            )

            response = await asyncio.to_thread(self.api_v2.create_tweet, text=message)

            if response.data:
                tweet_id = response.data["id"]
                logger.info(f"Posted market update tweet: {tweet_id}")
                return tweet_id

        except Exception as e:
            logger.error(f"Failed to post market update: {e}")

        return None

    async def post_system_status(self, status_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a system status update.

        Args:
            status_data: System status data

        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            template = self.templates["system_status"]

            message = template.message_template.format(
                status=status_data.get("status", "OPERATIONAL").upper(),
                active_strategies=status_data.get("active_strategies", 0),
                trades_24h=status_data.get("trades_24h", 0),
                volume_24h=status_data.get("volume_24h", 0)
            )

            response = await asyncio.to_thread(self.api_v2.create_tweet, text=message)

            if response.data:
                tweet_id = response.data["id"]
                logger.info(f"Posted system status tweet: {tweet_id}")
                return tweet_id

        except Exception as e:
            logger.error(f"Failed to post system status: {e}")

        return None

    async def post_custom_message(self, message: str, hashtags: List[str] = None) -> Optional[str]:
        """
        Post a custom message.

        Args:
            message: Custom message text
            hashtags: Optional hashtags to include

        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            logger.info(f"Would tweet: {message} with hashtags: {hashtags}")
            return None

        try:
            # Add hashtags if provided
            if hashtags:
                hashtag_text = " " + " ".join(f"#{tag}" for tag in hashtags)
                if len(message + hashtag_text) <= 280:
                    message += hashtag_text

            # Ensure message is within Twitter's character limit
            if len(message) > 280:
                message = message[:277] + "..."

            response = await asyncio.to_thread(self.api_v2.create_tweet, text=message)

            if response.data:
                tweet_id = response.data["id"]
                logger.info(f"Posted custom tweet: {tweet_id}")
                return tweet_id

        except Exception as e:
            logger.error(f"Failed to post custom message: {e}")

        return None

    async def get_mentions(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent mentions of the bot account.

        Args:
            max_results: Maximum number of mentions to retrieve

        Returns:
            List of mention data
        """
        if not self.is_enabled():
            logger.info(f"Would get {max_results} mentions")
            return []

        try:
            user = await asyncio.to_thread(self.api_v2.get_me)
            if not user.data:
                return []

            mentions = await asyncio.to_thread(
                self.api_v2.get_users_mentions,
                user.data.id,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "referenced_tweets"]
            )

            if not mentions.data:
                return []

            mention_list = []
            for tweet in mentions.data:
                mention_list.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "public_metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else None,
                    "referenced_tweets": tweet.referenced_tweets if hasattr(tweet, 'referenced_tweets') else None
                })

            return mention_list

        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []

    async def reply_to_tweet(self, tweet_id: str, message: str) -> Optional[str]:
        """
        Reply to a specific tweet.

        Args:
            tweet_id: ID of tweet to reply to
            message: Reply message

        Returns:
            Reply tweet ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None

        try:
            response = await asyncio.to_thread(
                self.api_v2.create_tweet,
                text=message,
                in_reply_to_tweet_id=tweet_id
            )

            if response.data:
                reply_id = response.data["id"]
                logger.info(f"Posted reply {reply_id} to tweet {tweet_id}")
                return reply_id

        except Exception as e:
            logger.error(f"Failed to reply to tweet {tweet_id}: {e}")

        return None

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Rate limit information
        """
        if not self.is_enabled():
            return {"enabled": False, "message": "Twitter integration disabled"}

        try:
            # Get rate limit status from API v1.1
            rate_limit = self.api_v1.get_rate_limit_status()
            return {
                "enabled": True,
                "username": self.username,
                "rate_limits": {
                    "tweets": rate_limit.get("statuses", {}).get("/statuses/update", {}),
                    "user_timeline": rate_limit.get("statuses", {}).get("/statuses/user_timeline", {}),
                    "mentions": rate_limit.get("statuses", {}).get("/statuses/mentions_timeline", {})
                }
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"enabled": True, "error": str(e)}

    def _truncate_hash(self, tx_hash: str, length: int = 8) -> str:
        """
        Truncate transaction hash for display.

        Args:
            tx_hash: Full transaction hash
            length: Number of characters to show from start and end

        Returns:
            Truncated hash
        """
        if not tx_hash or len(tx_hash) <= length * 2:
            return tx_hash

        return f"{tx_hash[:length]}...{tx_hash[-length:]}"

    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available tweet templates."""
        templates = {}
        for name, template in self.templates.items():
            templates[name] = {
                "type": template.template_type,
                "message_template": template.message_template,
                "hashtags": template.hashtags,
                "include_metrics": template.include_metrics
            }
        return templates


# Global Twitter client instance
twitter_client = TwitterClient()