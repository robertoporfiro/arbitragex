-- ArbitrageX Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    profit_usd DECIMAL(15, 2) NOT NULL,
    profit_percent DECIMAL(8, 4) NOT NULL,
    fees_paid DECIMAL(15, 2) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    profit_percent DECIMAL(8, 4) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    bid DECIMAL(20, 8) NOT NULL,
    ask DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 8) NOT NULL,
    spread_percent DECIMAL(8, 4) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_opportunities_symbol ON opportunities(symbol);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_exchange ON market_data(symbol, exchange);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

-- Insert initial data
INSERT INTO trades (symbol, buy_exchange, sell_exchange, buy_price, sell_price, quantity, profit_usd, profit_percent, fees_paid, execution_time_ms)
VALUES ('BTC/USDT', 'binance', 'coinbase', 43250.50, 43275.80, 0.001, 25.30, 0.058, 0.86, 245)
ON CONFLICT DO NOTHING;
