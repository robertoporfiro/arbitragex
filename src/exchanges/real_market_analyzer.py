"""
Analisador de mercado real - Conexões com APIs das exchanges
"""

import asyncio
import logging
import aiohttp
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class RealTimePrice:
    symbol: str
    exchange: str
    bid: float
    ask: float
    volume_24h: float
    timestamp: datetime
    spread_percent: float

@dataclass
class MarketDepth:
    symbol: str
    exchange: str
    bids: List[Tuple[float, float]]  # [(price, volume), ...]
    asks: List[Tuple[float, float]]  # [(price, volume), ...]
    timestamp: datetime

class RealMarketAnalyzer:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.price_cache = {}
        self.last_update = {}
        
        # URLs das APIs públicas (sem necessidade de chaves)
        self.api_endpoints = {
            'binance': {
                'ticker': 'https://api.binance.com/api/v3/ticker/24hr',
                'orderbook': 'https://api.binance.com/api/v3/depth',
                'symbols_map': {
                    'BTC/USDT': 'BTCUSDT',
                    'ETH/USDT': 'ETHUSDT',
                    'ADA/USDT': 'ADAUSDT',
                    'SOL/USDT': 'SOLUSDT'
                }
            },
            'coinbase': {
                'ticker': 'https://api.exchange.coinbase.com/products/{}/ticker',
                'orderbook': 'https://api.exchange.coinbase.com/products/{}/book',
                'symbols_map': {
                    'BTC/USDT': 'BTC-USD',
                    'ETH/USDT': 'ETH-USD',
                    'ADA/USDT': 'ADA-USD',
                    'SOL/USDT': 'SOL-USD'
                }
            },
            'kraken': {
                'ticker': 'https://api.kraken.com/0/public/Ticker',
                'orderbook': 'https://api.kraken.com/0/public/Depth',
                'symbols_map': {
                    'BTC/USDT': 'XBTUSD',
                    'ETH/USDT': 'ETHUSD',
                    'ADA/USDT': 'ADAUSD',
                    'SOL/USDT': 'SOLUSD'
                }
            }
        }
    
    async def initialize(self):
        """Inicializar conexões HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'ArbitrageX/1.0'}
        )
        logger.info("🌐 Conexões HTTP inicializadas para análise real")
        return True
    
    async def close(self):
        """Fechar conexões"""
        if self.session:
            await self.session.close()
    
    async def fetch_binance_price(self, symbol: str) -> Optional[RealTimePrice]:
        """Buscar preço real da Binance"""
        try:
            binance_symbol = self.api_endpoints['binance']['symbols_map'].get(symbol)
            if not binance_symbol:
                return None
            
            url = f"{self.api_endpoints['binance']['ticker']}?symbol={binance_symbol}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    bid = float(data['bidPrice'])
                    ask = float(data['askPrice'])
                    volume = float(data['volume'])
                    
                    return RealTimePrice(
                        symbol=symbol,
                        exchange='binance',
                        bid=bid,
                        ask=ask,
                        volume_24h=volume,
                        timestamp=datetime.now(),
                        spread_percent=((ask - bid) / bid) * 100
                    )
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço Binance para {symbol}: {e}")
        return None
    
    async def fetch_coinbase_price(self, symbol: str) -> Optional[RealTimePrice]:
        """Buscar preço real da Coinbase"""
        try:
            coinbase_symbol = self.api_endpoints['coinbase']['symbols_map'].get(symbol)
            if not coinbase_symbol:
                return None
            
            url = self.api_endpoints['coinbase']['ticker'].format(coinbase_symbol)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    bid = float(data['bid'])
                    ask = float(data['ask'])
                    volume = float(data['volume'])
                    
                    return RealTimePrice(
                        symbol=symbol,
                        exchange='coinbase',
                        bid=bid,
                        ask=ask,
                        volume_24h=volume,
                        timestamp=datetime.now(),
                        spread_percent=((ask - bid) / bid) * 100
                    )
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço Coinbase para {symbol}: {e}")
        return None
    
    async def fetch_kraken_price(self, symbol: str) -> Optional[RealTimePrice]:
        """Buscar preço real da Kraken"""
        try:
            kraken_symbol = self.api_endpoints['kraken']['symbols_map'].get(symbol)
            if not kraken_symbol:
                return None
            
            url = f"{self.api_endpoints['kraken']['ticker']}?pair={kraken_symbol}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'result' in data and kraken_symbol in data['result']:
                        ticker_data = data['result'][kraken_symbol]
                        
                        bid = float(ticker_data['b'][0])  # Best bid price
                        ask = float(ticker_data['a'][0])  # Best ask price
                        volume = float(ticker_data['v'][1])  # 24h volume
                        
                        return RealTimePrice(
                            symbol=symbol,
                            exchange='kraken',
                            bid=bid,
                            ask=ask,
                            volume_24h=volume,
                            timestamp=datetime.now(),
                            spread_percent=((ask - bid) / bid) * 100
                        )
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço Kraken para {symbol}: {e}")
        return None
    
    async def fetch_all_prices(self, symbol: str) -> Dict[str, RealTimePrice]:
        """Buscar preços de todas as exchanges para um símbolo"""
        tasks = [
            self.fetch_binance_price(symbol),
            self.fetch_coinbase_price(symbol),
            self.fetch_kraken_price(symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        prices = {}
        
        for result in results:
            if isinstance(result, RealTimePrice):
                prices[result.exchange] = result
            elif isinstance(result, Exception):
                logger.warning(f"⚠️  Erro ao buscar preço: {result}")
        
        return prices
    
    async def get_market_snapshot(self) -> Dict[str, Dict[str, RealTimePrice]]:
        """Obter snapshot completo do mercado"""
        logger.info("📊 Coletando dados reais do mercado...")
        
        market_data = {}
        
        for symbol in self.config.trading_symbols:
            logger.info(f"🔍 Buscando preços para {symbol}...")
            prices = await self.fetch_all_prices(symbol)
            
            if prices:
                market_data[symbol] = prices
                logger.info(f"✅ {symbol}: {len(prices)} exchanges conectadas")
                
                # Log dos preços coletados
                for exchange, price_data in prices.items():
                    logger.info(f"   📈 {exchange.upper()}: "
                              f"Bid=${price_data.bid:,.8f} "
                              f"Ask=${price_data.ask:,.8f} "
                              f"Spread={price_data.spread_percent:.3f}%")
            else:
                logger.warning(f"⚠️  Nenhum preço obtido para {symbol}")
            
            # Pequena pausa entre símbolos para evitar rate limiting
            await asyncio.sleep(0.5)
        
        return market_data
    
    def find_real_arbitrage_opportunities(self, market_data: Dict[str, Dict[str, RealTimePrice]]) -> List:
        """Encontrar oportunidades reais de arbitragem"""
        opportunities = []
        
        for symbol, exchange_prices in market_data.items():
            exchanges = list(exchange_prices.keys())
            
            if len(exchanges) < 2:
                continue
            
            # Comparar todos os pares de exchanges
            for i, buy_exchange in enumerate(exchanges):
                for sell_exchange in exchanges[i+1:]:
                    buy_price_data = exchange_prices[buy_exchange]
                    sell_price_data = exchange_prices[sell_exchange]
                    
                    # Oportunidade 1: Comprar em buy_exchange, vender em sell_exchange
                    buy_price = buy_price_data.ask  # Preço que pagamos para comprar
                    sell_price = sell_price_data.bid  # Preço que recebemos para vender
                    
                    if sell_price > buy_price:
                        profit_percent = ((sell_price - buy_price) / buy_price) * 100
                        
                        if profit_percent >= self.config.min_profit_percent:
                            # Calcular volume baseado no menor volume disponível
                            max_volume = min(buy_price_data.volume_24h, sell_price_data.volume_24h) * 0.001  # 0.1% do volume diário
                            trade_volume = min(max_volume, self.config.max_trade_amount / buy_price)
                            
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': buy_exchange,
                                'sell_exchange': sell_exchange,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'profit_percent': profit_percent,
                                'profit_usd': (sell_price - buy_price) * trade_volume,
                                'volume': trade_volume,
                                'buy_spread': buy_price_data.spread_percent,
                                'sell_spread': sell_price_data.spread_percent,
                                'timestamp': datetime.now()
                            })
                    
                    # Oportunidade 2: Comprar em sell_exchange, vender em buy_exchange
                    buy_price = sell_price_data.ask
                    sell_price = buy_price_data.bid
                    
                    if sell_price > buy_price:
                        profit_percent = ((sell_price - buy_price) / buy_price) * 100
                        
                        if profit_percent >= self.config.min_profit_percent:
                            max_volume = min(buy_price_data.volume_24h, sell_price_data.volume_24h) * 0.001
                            trade_volume = min(max_volume, self.config.max_trade_amount / buy_price)
                            
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': sell_exchange,
                                'sell_exchange': buy_exchange,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'profit_percent': profit_percent,
                                'profit_usd': (sell_price - buy_price) * trade_volume,
                                'volume': trade_volume,
                                'buy_spread': sell_price_data.spread_percent,
                                'sell_spread': buy_price_data.spread_percent,
                                'timestamp': datetime.now()
                            })
        
        return sorted(opportunities, key=lambda x: x['profit_percent'], reverse=True)
    
    def log_market_analysis(self, market_data: Dict[str, Dict[str, RealTimePrice]], opportunities: List):
        """Log da análise de mercado"""
        logger.info("\n" + "📊"*50)
        logger.info("🌐 ANÁLISE REAL DO MERCADO")
        logger.info("📊"*50)
        
        total_exchanges = sum(len(prices) for prices in market_data.values())
        logger.info(f"🔗 Conexões ativas: {total_exchanges}")
        logger.info(f"💱 Pares monitorados: {len(market_data)}")
        logger.info(f"🎯 Oportunidades encontradas: {len(opportunities)}")
        
        # Resumo por símbolo
        for symbol, exchange_prices in market_data.items():
            logger.info(f"\n💰 {symbol}:")
            
            prices = [(ex, data.bid, data.ask) for ex, data in exchange_prices.items()]
            prices.sort(key=lambda x: x[1])  # Ordenar por bid price
            
            for exchange, bid, ask in prices:
                spread = ((ask - bid) / bid) * 100
                logger.info(f"   📈 {exchange.upper()}: ${bid:,.8f} / ${ask:,.8f} (spread: {spread:.3f}%)")
        
        # Top oportunidades
        if opportunities:
            logger.info(f"\n🏆 TOP {min(3, len(opportunities))} OPORTUNIDADES:")
            for i, opp in enumerate(opportunities[:3], 1):
                logger.info(f"   {i}. {opp['symbol']}: "
                          f"{opp['buy_exchange'].upper()} → {opp['sell_exchange'].upper()} "
                          f"({opp['profit_percent']:.3f}%, ${opp['profit_usd']:.2f})")
        
        logger.info("📊"*50)
