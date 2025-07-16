-- NFT Trading Bot Database Initialization
-- This script is run by PostgreSQL Docker container on first startup

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE nft_trading_bot_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nft_trading_bot_dev')\gexec

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE nft_trading_bot_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nft_trading_bot_test')\gexec

-- Connect to the main database
\c nft_trading_bot_dev;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TEXT AS $$
BEGIN
    RETURN 'Database is healthy at ' || NOW();
END;
$$ LANGUAGE plpgsql;

