"""
Configuração centralizada do ArbitrageX
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

@dataclass
class ExchangeConfig:
    name: str
    api_key: str
    secret_key: str
    sandbox: bool = True
    enabled: bool = True

@dataclass
class Config:
    # Trading
    initial_balance: float = float(os.getenv('INITIAL_BALANCE', '10000'))
    min_profit_percent: float = float(os.getenv('MIN_PROFIT_PERCENT', '0.3'))
    max_trade_amount: float = float(os.getenv('MAX_TRADE_AMOUNT', '1000'))
    
    # Sistema
    environment: str = os.getenv('ENVIRONMENT', 'development')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Database
    database_url: str = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'arbitrage_user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'arbitrage_pass')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'arbitrage_db')}"
    )
    
    # Redis
    redis_url: str = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}"
    
    # Monitoramento
    prometheus_port: int = int(os.getenv('PROMETHEUS_PORT', '8000'))
    
    # Notificações
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
    discord_webhook_url: str = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    # Usar field(default_factory) para listas mutáveis
    trading_symbols: List[str] = field(
        default_factory=lambda: os.getenv('TRADING_SYMBOLS', 'BTC/USDT,ETH/USDT').split(',')
    )
    
    # Exchanges como property para evitar problemas com dataclass
    @property
    def exchanges(self) -> Dict[str, ExchangeConfig]:
        return {
            'binance': ExchangeConfig(
                name='binance',
                api_key=os.getenv('BINANCE_API_KEY', ''),
                secret_key=os.getenv('BINANCE_SECRET_KEY', ''),
                sandbox=self.environment != 'production'
            ),
            'coinbase': ExchangeConfig(
                name='coinbase',
                api_key=os.getenv('COINBASE_API_KEY', ''),
                secret_key=os.getenv('COINBASE_SECRET_KEY', ''),
                sandbox=self.environment != 'production'
            ),
            'kraken': ExchangeConfig(
                name='kraken',
                api_key=os.getenv('KRAKEN_API_KEY', ''),
                secret_key=os.getenv('KRAKEN_SECRET_KEY', ''),
                sandbox=self.environment != 'production'
            )
        }
