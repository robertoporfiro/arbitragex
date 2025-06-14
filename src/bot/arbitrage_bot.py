import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from ..exchanges.real_market_analyzer import RealMarketAnalyzer
from ..utils.logger import setup_logger

# Métricas Prometheus
OPPORTUNITIES_COUNTER = Counter('arbitragex_opportunities_total', 'Oportunidades encontradas')
TRADES_COUNTER = Counter('arbitragex_trades_total', 'Total de trades executados')
PROFIT_COUNTER = Counter('arbitragex_profit_total', 'Lucro total acumulado')
TRADE_DURATION = Histogram('arbitragex_trade_duration_seconds', 'Duração dos trades')
BALANCE_GAUGE = Gauge('arbitragex_balance', 'Balance atual')

class ArbitrageBot:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = setup_logger(__name__)
        self.market_analyzer = RealMarketAnalyzer()
        self.balance = float(config.get('INITIAL_BALANCE', 10000))
        self.min_profit_percent = float(config.get('MIN_PROFIT_PERCENT', 0.3))
        self.max_trade_amount = float(config.get('MAX_TRADE_AMOUNT', 1000))
        self.trading_symbols = config.get('TRADING_SYMBOLS', 'BTC/USDT,ETH/USDT').split(',')
        
        # Inicializar servidor de métricas
        try:
            start_http_server(8000)
            self.logger.info("📊 Servidor de métricas iniciado na porta 8000")
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao iniciar servidor de métricas: {e}")
    
    async def find_arbitrage_opportunities(self) -> List[Dict]:
        """Encontra oportunidades de arbitragem"""
        opportunities = []
        
        try:
            for symbol in self.trading_symbols:
                symbol = symbol.strip()
                self.logger.info(f"🔍 Analisando {symbol}...")
                
                # Buscar preços em múltiplas exchanges
                prices = await self.market_analyzer.get_prices_from_exchanges(symbol)
                
                if len(prices) >= 2:
                    # Encontrar maior e menor preço
                    sorted_prices = sorted(prices.items(), key=lambda x: x[1])
                    lowest_exchange, lowest_price = sorted_prices[0]
                    highest_exchange, highest_price = sorted_prices[-1]
                    
                    # Calcular diferença percentual
                    price_diff_percent = ((highest_price - lowest_price) / lowest_price) * 100
                    
                    if price_diff_percent >= self.min_profit_percent:
                        opportunity = {
                            'symbol': symbol,
                            'buy_exchange': lowest_exchange,
                            'sell_exchange': highest_exchange,
                            'buy_price': lowest_price,
                            'sell_price': highest_price,
                            'profit_percent': price_diff_percent,
                            'timestamp': datetime.now()
                        }
                        opportunities.append(opportunity)
                        
                        # ✅ CORREÇÃO: Incrementar contador de oportunidades
                        OPPORTUNITIES_COUNTER.inc()
                        
                        self.logger.info(f"🎯 Oportunidade encontrada: {symbol} - {price_diff_percent:.2f}% profit")
                        self.logger.info(f"   Comprar em {lowest_exchange}: ${lowest_price:.2f}")
                        self.logger.info(f"   Vender em {highest_exchange}: ${highest_price:.2f}")
                
                # Pequena pausa entre símbolos
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar oportunidades: {e}")
        
        return opportunities
    
    async def execute_arbitrage_trade(self, opportunity: Dict) -> bool:
        """Executa um trade de arbitragem (simulado)"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            symbol = opportunity['symbol']
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
            profit_percent = opportunity['profit_percent']
            
            # Calcular quantidade baseada no balance disponível
            trade_amount = min(self.max_trade_amount, self.balance * 0.1)
            quantity = trade_amount / buy_price
            
            # Simular execução do trade
            self.logger.info(f"🚀 Executando trade: {symbol}")
            self.logger.info(f"   💰 Quantidade: {quantity:.6f} {symbol.split('/')[0]}")
            self.logger.info(f"   📊 Valor: ${trade_amount:.2f}")
            
            # Simular latência de execução
            await asyncio.sleep(0.1)
            
            # Calcular lucro
            profit = (sell_price - buy_price) * quantity
            
            # Atualizar balance
            self.balance += profit
            
            # Atualizar métricas
            TRADES_COUNTER.inc()
            PROFIT_COUNTER.inc(profit)
            BALANCE_GAUGE.set(self.balance)
            
            # Registrar duração do trade
            duration = asyncio.get_event_loop().time() - start_time
            TRADE_DURATION.observe(duration)
            
            self.logger.info(f"✅ Trade executado com sucesso!")
            self.logger.info(f"   💵 Lucro: ${profit:.2f}")
            self.logger.info(f"   💰 Balance atual: ${self.balance:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao executar trade: {e}")
            return False
    
    async def run_paper_trading(self, duration_minutes: float = 60):
        """Executa paper trading por um período determinado"""
        self.logger.info(f"🚀 Iniciando paper trading por {duration_minutes} minutos...")
        self.logger.info(f"💰 Balance inicial: ${self.balance:.2f}")
        
        start_time = asyncio.get_event_loop().time()
        end_time = start_time + (duration_minutes * 60)
        
        trades_executed = 0
        opportunities_found = 0
        
        while asyncio.get_event_loop().time() < end_time:
            try:
                # Buscar oportunidades
                opportunities = await self.find_arbitrage_opportunities()
                opportunities_found += len(opportunities)
                
                # Executar trades para oportunidades válidas
                for opportunity in opportunities:
                    if await self.execute_arbitrage_trade(opportunity):
                        trades_executed += 1
                
                # Aguardar antes da próxima análise
                await asyncio.sleep(5)  # Análise a cada 5 segundos
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Paper trading interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"❌ Erro durante paper trading: {e}")
                await asyncio.sleep(1)
        
        # Relatório final
        total_time = (asyncio.get_event_loop().time() - start_time) / 60
        total_profit = self.balance - float(self.config.get('INITIAL_BALANCE', 10000))
        
        self.logger.info(f"📊 Paper Trading Finalizado!")
        self.logger.info(f"   ⏱️ Tempo total: {total_time:.1f} minutos")
        self.logger.info(f"   🎯 Oportunidades encontradas: {opportunities_found}")
        self.logger.info(f"   🚀 Trades executados: {trades_executed}")
        self.logger.info(f"   💵 Lucro total: ${total_profit:.2f}")
        self.logger.info(f"   💰 Balance final: ${self.balance:.2f}")
        
        return {
            'duration_minutes': total_time,
            'opportunities_found': opportunities_found,
            'trades_executed': trades_executed,
            'total_profit': total_profit,
            'final_balance': self.balance
        }
