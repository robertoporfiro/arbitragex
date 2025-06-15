-- Inicialização do banco de dados para o Crypto Arbitrage Bot

-- Tabela para histórico de preços
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    bid DECIMAL(20, 8),
    ask DECIMAL(20, 8),
    last DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para oportunidades de arbitragem
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    profit_percent DECIMAL(10, 4) NOT NULL,
    trade_amount DECIMAL(20, 8),
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para histórico de trades
CREATE TABLE IF NOT EXISTS trades_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    trade_amount DECIMAL(20, 8) NOT NULL,
    gross_profit DECIMAL(20, 8),
    total_fees DECIMAL(20, 8),
    net_profit DECIMAL(20, 8),
    profit_percent DECIMAL(10, 4),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para configurações do bot
CREATE TABLE IF NOT EXISTS bot_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir configurações padrão
INSERT INTO bot_config (key, value, description) VALUES
('min_profit_percent', '0.3', 'Percentual mínimo de lucro para executar trade'),
('max_trade_amount', '1000', 'Valor máximo por trade em USDT'),
('trading_enabled', 'false', 'Se o trading está habilitado'),
('paper_trading', 'true', 'Se está em modo paper trading')
ON CONFLICT (key) DO NOTHING;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_price_history_symbol_timestamp ON price_history(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_arbitrage_opportunities_timestamp ON arbitrage_opportunities(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_history_timestamp ON trades_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_history_symbol ON trades_history(symbol);

-- View para estatísticas rápidas
CREATE OR REPLACE VIEW trading_stats AS
SELECT 
    COUNT(*) as total_trades,
    SUM(net_profit) as total_profit,
    AVG(net_profit) as avg_profit,
    MAX(net_profit) as max_profit,
    MIN(net_profit) as min_profit,
    AVG(profit_percent) as avg_profit_percent,
    COUNT(DISTINCT symbol) as symbols_traded,
    COUNT(DISTINCT buy_exchange) as exchanges_used
FROM trades_history
WHERE status = 'completed';
