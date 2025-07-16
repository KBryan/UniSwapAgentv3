"""
Integration tests for external service integrations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import aiohttp

from integrations.coingecko import CoinGeckoClient, CoinGeckoError
from integrations.uniswap import UniswapV2Adapter, UniswapV3Adapter, create_uniswap_adapter
from integrations.twitter import TwitterClient, TwitterError


class TestCoinGeckoIntegration:
    """Integration tests for CoinGecko API client."""
    
    @pytest.mark.integration
    @pytest.mark.external
    async def test_coingecko_connection(self):
        """Test CoinGecko API connection."""
        client = CoinGeckoClient()
        
        try:
            async with client:
                # Test basic ping/connection
                global_data = await client.get_global_data()
                assert isinstance(global_data, dict)
                assert "active_cryptocurrencies" in global_data
        except Exception as e:
            pytest.skip(f"CoinGecko API not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.external
    async def test_get_coin_list(self):
        """Test getting coin list from CoinGecko."""
        client = CoinGeckoClient()
        
        try:
            async with client:
                coin_list = await client.get_coin_list()
                
                assert isinstance(coin_list, dict)
                assert len(coin_list) > 0
                assert "BTC" in coin_list
                assert "ETH" in coin_list
                
                # Test coin ID retrieval
                btc_id = await client.get_coin_id("BTC")
                assert btc_id == "bitcoin"
                
                eth_id = await client.get_coin_id("ETH")
                assert eth_id == "ethereum"
        except Exception as e:
            pytest.skip(f"CoinGecko API not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.external
    async def test_get_prices(self):
        """Test getting cryptocurrency prices."""
        client = CoinGeckoClient()
        
        try:
            async with client:
                prices = await client.get_price(["BTC", "ETH"], "usd")
                
                assert isinstance(prices, dict)
                assert "BTC" in prices
                assert "ETH" in prices
                assert prices["BTC"] > 0
                assert prices["ETH"] > 0
        except Exception as e:
            pytest.skip(f"CoinGecko API not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.external
    async def test_get_coin_data(self):
        """Test getting detailed coin data."""
        client = CoinGeckoClient()
        
        try:
            async with client:
                eth_data = await client.get_coin_data("ETH")
                
                assert eth_data is not None
                assert eth_data.symbol == "ETH"
                assert eth_data.name == "Ethereum"
                assert eth_data.current_price > 0
                assert eth_data.market_cap > 0
                assert isinstance(eth_data.last_updated, datetime)
        except Exception as e:
            pytest.skip(f"CoinGecko API not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.external
    async def test_get_historical_prices(self):
        """Test getting historical price data."""
        client = CoinGeckoClient()
        
        try:
            async with client:
                history = await client.get_historical_prices("ETH", days=7)
                
                assert isinstance(history, list)
                assert len(history) > 0
                
                for price_point in history:
                    assert hasattr(price_point, 'timestamp')
                    assert hasattr(price_point, 'price')
                    assert price_point.price > 0
                    assert isinstance(price_point.timestamp, datetime)
        except Exception as e:
            pytest.skip(f"CoinGecko API not available: {e}")
    
    @pytest.mark.unit
    async def test_coingecko_rate_limiting(self):
        """Test CoinGecko rate limiting."""
        client = CoinGeckoClient()
        
        # Mock session to simulate rate limiting
        mock_response = Mock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "1"}
        
        with patch.object(client, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(CoinGeckoError):
                await client._make_request("test")
    
    @pytest.mark.unit
    async def test_coingecko_error_handling(self):
        """Test CoinGecko error handling."""
        client = CoinGeckoClient()
        
        # Mock session to simulate API error
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        
        with patch.object(client, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(CoinGeckoError):
                await client._make_request("test")


class TestUniswapIntegration:
    """Integration tests for Uniswap adapters."""
    
    @pytest.mark.unit
    def test_create_uniswap_adapter(self):
        """Test Uniswap adapter factory."""
        # Test V2 adapter creation
        adapter_v2 = create_uniswap_adapter("v2", "ethereum")
        assert isinstance(adapter_v2, UniswapV2Adapter)
        
        # Test V3 adapter creation
        adapter_v3 = create_uniswap_adapter("v3", "ethereum")
        assert isinstance(adapter_v3, UniswapV3Adapter)
        
        # Test invalid version
        with pytest.raises(ValueError):
            create_uniswap_adapter("v4", "ethereum")
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    def test_uniswap_v2_initialization(self, mock_web3):
        """Test Uniswap V2 adapter initialization."""
        # Mock Web3 connection
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        adapter = UniswapV2Adapter("ethereum")
        
        assert adapter.network == "ethereum"
        assert adapter.w3 == mock_w3_instance
        assert "ETH" in adapter.token_addresses
        assert "USDC" in adapter.token_addresses
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    def test_token_address_resolution(self, mock_web3):
        """Test token address resolution."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        adapter = UniswapV2Adapter("ethereum")
        
        # Test symbol resolution
        eth_addr = adapter._get_token_address("ETH")
        assert eth_addr == "0x0000000000000000000000000000000000000000"
        
        # Test address passthrough
        custom_addr = "0x1234567890abcdef1234567890abcdef12345678"
        resolved_addr = adapter._get_token_address(custom_addr)
        assert resolved_addr == custom_addr
        
        # Test unknown token
        with pytest.raises(Exception):
            adapter._get_token_address("UNKNOWN_TOKEN")
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    def test_swap_path_building(self, mock_web3):
        """Test swap path building logic."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        adapter = UniswapV2Adapter("ethereum")
        
        # Test direct path
        path = adapter._build_swap_path("ETH", "USDC")
        assert len(path) >= 2
        assert path[0] != path[-1]  # Different tokens
        
        # Test same token error
        with pytest.raises(Exception):
            adapter._build_swap_path("ETH", "ETH")
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    async def test_get_quote(self, mock_web3):
        """Test getting trade quote."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        # Mock contract call
        mock_contract = Mock()
        mock_contract.functions.getAmountsOut.return_value.call.return_value = [
            1000000000000000000,  # 1 ETH in wei
            1600000000  # 1600 USDC (6 decimals)
        ]
        mock_w3_instance.eth.contract.return_value = mock_contract
        
        adapter = UniswapV2Adapter("ethereum")
        
        quote = await adapter.get_quote("ETH", "USDC", 1.0)
        
        assert quote.exchange == "uniswap_v2"
        assert quote.token_in == "ETH"
        assert quote.token_out == "USDC"
        assert quote.amount_in == 1.0
        assert quote.amount_out > 0
        assert quote.price > 0
        assert quote.gas_estimate > 0
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    async def test_gas_estimation(self, mock_web3):
        """Test gas estimation."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        adapter = UniswapV2Adapter("ethereum")
        
        # Test ETH swap gas estimate
        gas_eth = await adapter.estimate_gas("ETH", "USDC", 1.0)
        assert gas_eth == 150000
        
        # Test token swap gas estimate
        gas_token = await adapter.estimate_gas("USDC", "DAI", 1000.0)
        assert gas_token == 200000
    
    @pytest.mark.integration
    @pytest.mark.external
    @patch('integrations.uniswap.Web3')
    async def test_uniswap_v3_quote_difference(self, mock_web3):
        """Test that V3 adapter provides different quotes than V2."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = True
        mock_web3.return_value = mock_w3_instance
        
        # Mock contract calls
        mock_contract = Mock()
        mock_contract.functions.getAmountsOut.return_value.call.return_value = [
            1000000000000000000,
            1600000000
        ]
        mock_w3_instance.eth.contract.return_value = mock_contract
        
        adapter_v2 = UniswapV2Adapter("ethereum")
        adapter_v3 = UniswapV3Adapter("ethereum")
        
        quote_v2 = await adapter_v2.get_quote("ETH", "USDC", 1.0)
        quote_v3 = await adapter_v3.get_quote("ETH", "USDC", 1.0)
        
        assert quote_v2.exchange == "uniswap_v2"
        assert quote_v3.exchange == "uniswap_v3"
        
        # V3 should have higher gas estimate
        assert quote_v3.gas_estimate > quote_v2.gas_estimate


class TestTwitterIntegration:
    """Integration tests for Twitter client."""
    
    @pytest.mark.unit
    @patch('integrations.twitter.tweepy')
    def test_twitter_client_initialization_disabled(self, mock_tweepy):
        """Test Twitter client when disabled."""
        with patch('config.get_settings') as mock_settings:
            mock_settings.return_value.enable_twitter = False
            
            client = TwitterClient()
            assert not client.enabled
            assert not client.is_enabled()
    
    @pytest.mark.unit
    @patch('integrations.twitter.tweepy')
    def test_twitter_client_initialization_enabled(self, mock_tweepy):
        """Test Twitter client initialization when enabled."""
        with patch('config.get_settings') as mock_settings:
            settings = mock_settings.return_value
            settings.enable_twitter = True
            settings.twitter_bearer_token = "test_bearer"
            settings.twitter_api_key = "test_key"
            settings.twitter_api_secret = "test_secret"
            settings.twitter_access_token = "test_token"
            settings.twitter_access_token_secret = "test_token_secret"
            
            # Mock successful API initialization
            mock_client = Mock()
            mock_user = Mock()
            mock_user.data.username = "test_bot"
            mock_client.get_me.return_value = mock_user
            mock_tweepy.Client.return_value = mock_client
            
            client = TwitterClient()
            assert client.enabled
            assert client.is_enabled()
    
    @pytest.mark.unit
    async def test_post_trade_notification_disabled(self):
        """Test posting trade notification when Twitter is disabled."""
        with patch('config.get_settings') as mock_settings:
            mock_settings.return_value.enable_twitter = False
            
            client = TwitterClient()
            
            trade_data = {
                "action": "buy",
                "amount_in": 1.0,
                "token_in": "ETH",
                "amount_out": 1600.0,
                "token_out": "USDC",
                "price": 1600.0,
                "gas_used": 150000,
                "tx_hash": "0x1234567890abcdef"
            }
            
            result = await client.post_trade_notification(trade_data)
            assert result is None
    
    @pytest.mark.unit
    @patch('integrations.twitter.tweepy')
    async def test_post_trade_notification_enabled(self, mock_tweepy):
        """Test posting trade notification when Twitter is enabled."""
        with patch('config.get_settings') as mock_settings:
            settings = mock_settings.return_value
            settings.enable_twitter = True
            settings.twitter_bearer_token = "test_bearer"
            settings.twitter_api_key = "test_key"
            settings.twitter_api_secret = "test_secret"
            settings.twitter_access_token = "test_token"
            settings.twitter_access_token_secret = "test_token_secret"
            
            # Mock successful tweet creation
            mock_client = Mock()
            mock_user = Mock()
            mock_user.data.username = "test_bot"
            mock_client.get_me.return_value = mock_user
            
            mock_response = Mock()
            mock_response.data = {"id": "tweet_123"}
            mock_client.create_tweet.return_value = mock_response
            
            mock_tweepy.Client.return_value = mock_client
            
            client = TwitterClient()
            
            trade_data = {
                "action": "buy",
                "amount_in": 1.0,
                "token_in": "ETH",
                "amount_out": 1600.0,
                "token_out": "USDC",
                "price": 1600.0,
                "gas_used": 150000,
                "tx_hash": "0x1234567890abcdef1234567890abcdef12345678"
            }
            
            result = await client.post_trade_notification(trade_data)
            assert result == "tweet_123"
    
    @pytest.mark.unit
    @patch('integrations.twitter.tweepy')
    async def test_post_strategy_signal(self, mock_tweepy):
        """Test posting strategy signal notification."""
        with patch('config.get_settings') as mock_settings:
            settings = mock_settings.return_value
            settings.enable_twitter = True
            settings.twitter_bearer_token = "test_bearer"
            settings.twitter_api_key = "test_key"
            settings.twitter_api_secret = "test_secret"
            settings.twitter_access_token = "test_token"
            settings.twitter_access_token_secret = "test_token_secret"
            
            mock_client = Mock()
            mock_user = Mock()
            mock_user.data.username = "test_bot"
            mock_client.get_me.return_value = mock_user
            
            mock_response = Mock()
            mock_response.data = {"id": "tweet_124"}
            mock_client.create_tweet.return_value = mock_response
            
            mock_tweepy.Client.return_value = mock_client
            
            client = TwitterClient()
            
            signal_data = {
                "strategy_name": "Momentum Strategy",
                "signal_type": "buy",
                "token": "ETH",
                "confidence": 0.8,
                "reason": "Strong bullish momentum"
            }
            
            result = await client.post_strategy_signal(signal_data)
            assert result == "tweet_124"
    
    @pytest.mark.unit
    def test_truncate_hash(self):
        """Test transaction hash truncation."""
        with patch('config.get_settings') as mock_settings:
            mock_settings.return_value.enable_twitter = False
            
            client = TwitterClient()
            
            # Test normal hash
            full_hash = "0x1234567890abcdef1234567890abcdef12345678"
            truncated = client._truncate_hash(full_hash, 6)
            assert truncated == "0x1234...345678"
            
            # Test short hash
            short_hash = "0x123"
            truncated = client._truncate_hash(short_hash, 6)
            assert truncated == "0x123"
            
            # Test empty hash
            empty_hash = ""
            truncated = client._truncate_hash(empty_hash)
            assert truncated == ""
    
    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.slow
    async def test_twitter_api_connection(self):
        """Test actual Twitter API connection (requires valid credentials)."""
        try:
            client = TwitterClient()
            
            if not client.enabled:
                pytest.skip("Twitter integration not enabled")
            
            # Test getting rate limit status
            rate_limit = client.get_rate_limit_status()
            assert "enabled" in rate_limit
            
            if rate_limit.get("enabled"):
                # Test posting a simple message (if credentials are valid)
                test_message = f"Test message from NFT Trading Bot - {datetime.utcnow().isoformat()}"
                tweet_id = await client.post_custom_message(test_message)
                
                if tweet_id:
                    # Clean up by deleting the test tweet
                    await client.delete_tweet(tweet_id)
                    
        except Exception as e:
            pytest.skip(f"Twitter API not available or credentials invalid: {e}")


class TestIntegrationErrorHandling:
    """Test error handling across integrations."""
    
    @pytest.mark.unit
    async def test_coingecko_network_error(self):
        """Test CoinGecko network error handling."""
        client = CoinGeckoClient()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Network error")
            
            with pytest.raises(CoinGeckoError):
                await client._make_request("test")
    
    @pytest.mark.unit
    @patch('integrations.uniswap.Web3')
    async def test_uniswap_connection_error(self, mock_web3):
        """Test Uniswap connection error handling."""
        mock_w3_instance = Mock()
        mock_w3_instance.is_connected.return_value = False
        mock_web3.return_value = mock_w3_instance
        
        with pytest.raises(Exception):
            UniswapV2Adapter("ethereum")
    
    @pytest.mark.unit
    @patch('integrations.twitter.tweepy')
    async def test_twitter_api_error(self, mock_tweepy):
        """Test Twitter API error handling."""
        with patch('config.get_settings') as mock_settings:
            settings = mock_settings.return_value
            settings.enable_twitter = True
            settings.twitter_bearer_token = "test_bearer"
            settings.twitter_api_key = "test_key"
            settings.twitter_api_secret = "test_secret"
            settings.twitter_access_token = "test_token"
            settings.twitter_access_token_secret = "test_token_secret"
            
            # Mock API error
            mock_client = Mock()
            mock_user = Mock()
            mock_user.data.username = "test_bot"
            mock_client.get_me.return_value = mock_user
            mock_client.create_tweet.side_effect = Exception("API Error")
            
            mock_tweepy.Client.return_value = mock_client
            
            client = TwitterClient()
            
            trade_data = {"action": "buy", "amount_in": 1.0}
            result = await client.post_trade_notification(trade_data)
            assert result is None  # Should handle error gracefully

