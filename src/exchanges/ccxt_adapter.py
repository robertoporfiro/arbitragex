"""
Adapter para integração com exchanges via CCXT
"""

import ccxt
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class CCXTPrice:
    symbol: str
    exchange: str
    bid: float
    ask: float
    volume_24h: float
    timestamp: datetime
    spread_percent: float

class CCXTExchangeAdapter:
    def __init__(self, exchanges: list):
        import logging
        self.exchanges = {}
        logger = logging.getLogger(__name__)
        for ex in exchanges:
            try:
                ccxt_ex = getattr(__import__('ccxt'), ex)()
                try:
                    ccxt_ex.load_markets()
                except Exception as e:
                    logger.warning(f"[CCXT] Falha ao carregar mercados para '{ex}': {e}")
                self.exchanges[ex] = ccxt_ex
            except Exception as e:
                logger.warning(f"[CCXT] Falha ao inicializar exchange '{ex}': {e}")

    def fetch_price(self, exchange: str, symbol: str) -> Optional[CCXTPrice]:
        import logging
        logger = logging.getLogger(__name__)
        try:
            ex = self.exchanges.get(exchange)
            if not ex:
                logger.debug(f"[CCXT] Exchange '{exchange}' não encontrado no adapter.")
                return None
            if not hasattr(ex, 'symbols') or ex.symbols is None:
                logger.warning(f"[CCXT] Exchange '{exchange}' não carregou lista de símbolos (symbols=None).")
                return None
            if symbol not in ex.symbols:
                logger.debug(f"[CCXT] Símbolo '{symbol}' não suportado em '{exchange}'. Exemplos: {list(ex.symbols)[:5]}...")
                return None
            market = ex.market(symbol)
            ticker = ex.fetch_ticker(symbol)
            bid = ticker.get('bid') or 0.0
            ask = ticker.get('ask') or 0.0
            volume = ticker.get('baseVolume') or 0.0
            spread = ((ask - bid) / bid) * 100 if bid else 0.0
            return CCXTPrice(
                symbol=symbol,
                exchange=exchange,
                bid=bid,
                ask=ask,
                volume_24h=volume,
                timestamp=datetime.utcfromtimestamp(ticker['timestamp']/1000) if ticker.get('timestamp') else datetime.utcnow(),
                spread_percent=spread
            )
        except Exception as e:
            logger.warning(f"[CCXT] Erro ao buscar preço para {symbol} em {exchange}: {e}")
            return None
