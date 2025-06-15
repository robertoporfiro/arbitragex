import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from prometheus_client import start_http_server

from exchanges.real_market_analyzer import RealMarketAnalyzer
from utils.logger import setup_logger
from src.monitoring.metrics import MetricsCollector

class ArbitrageBot:
    def __init__(self, config, db_manager=None, metrics=None):
        self.config = config
        self.db_manager = db_manager
        self.metrics = metrics or MetricsCollector()
        self.logger = setup_logger(__name__)
        self.market_analyzer = RealMarketAnalyzer(config)
        # Suporte tanto para dict quanto para objeto Config
        if hasattr(config, 'initial_balance'):
            self.balance = float(getattr(config, 'initial_balance', 10000))
            self.min_profit_percent = float(getattr(config, 'min_profit_percent', 0.3))
            self.max_trade_amount = float(getattr(config, 'max_trade_amount', 1000))
            # Corrige: aceita lista OU string para trading_symbols
            trading_symbols = getattr(config, 'trading_symbols', 'BTC/USDT,ETH/USDT')
            if isinstance(trading_symbols, list):
                self.trading_symbols = trading_symbols
            else:
                self.trading_symbols = trading_symbols.split(',')
        else:
            self.balance = float(config.get('INITIAL_BALANCE', 10000))
            self.min_profit_percent = float(config.get('MIN_PROFIT_PERCENT', 0.3))
            self.max_trade_amount = float(config.get('MAX_TRADE_AMOUNT', 1000))
            trading_symbols = config.get('TRADING_SYMBOLS', 'BTC/USDT,ETH/USDT')
            if isinstance(trading_symbols, list):
                self.trading_symbols = trading_symbols
            else:
                self.trading_symbols = trading_symbols.split(',')

        # Inicializar servidor de métricas (apenas uma vez)
        self._metrics_server_started = False
        self._start_metrics_server()

    def _start_metrics_server(self):
        """Iniciar servidor de métricas apenas uma vez"""
        if not self._metrics_server_started:
            try:
                start_http_server(8000)
                self.logger.info("📊 Servidor de métricas iniciado na porta 8000")
                self._metrics_server_started = True
            except OSError as e:
                if "Address already in use" in str(e):
                    self.logger.info("📊 Servidor de métricas já está rodando na porta 8000")
                    self._metrics_server_started = True
                else:
                    self.logger.warning(f"⚠️ Erro ao iniciar servidor de métricas: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao iniciar servidor de métricas: {e}")

    async def find_arbitrage_opportunities(self) -> List[Dict]:
        """Encontra oportunidades de arbitragem e simula ação ao identificar uma oportunidade"""
        opportunities = []

        try:
            for symbol in self.trading_symbols:
                symbol = symbol.strip()
                self.logger.info(f"🔍 Analisando {symbol}...")

                # Buscar preços em múltiplas exchanges
                prices = await self.market_analyzer.fetch_all_prices(symbol)

                # Log detalhado: preço por exchange
                for ex, price in prices.items():
                    self.logger.info(f"   📈 {symbol} @ {ex}: Bid=${price.bid:.8f} Ask=${price.ask:.8f} Vol24h={price.volume_24h:.2f} Spread={price.spread_percent:.3f}%")

                price_dict = {ex: price.ask for ex, price in prices.items()}

                if len(price_dict) >= 2:
                    # Encontrar maior e menor preço
                    sorted_prices = sorted(price_dict.items(), key=lambda x: x[1])
                    lowest_exchange, lowest_price = sorted_prices[0]
                    highest_exchange, highest_price = sorted_prices[-1]

                    # Calcular diferença percentual
                    price_diff_percent = ((highest_price - lowest_price) / lowest_price) * 100

                    if price_diff_percent >= self.min_profit_percent:
                        trade_volume = 1  # Simulação: 1 unidade
                        opportunity = {
                            'symbol': symbol,
                            'buy_exchange': lowest_exchange,
                            'sell_exchange': highest_exchange,
                            'buy_price': lowest_price,
                            'sell_price': highest_price,
                            'profit_percent': price_diff_percent,
                            'profit_usd': (highest_price - lowest_price) * trade_volume,
                            'volume': trade_volume,
                            'timestamp': datetime.now()
                        }
                        opportunities.append(opportunity)

                        # Incrementar contador de oportunidades
                        self.metrics.opportunities_found.inc()

                        self.logger.info(f"🎯 Oportunidade encontrada: {symbol} - {price_diff_percent:.2f}% profit")
                        self.logger.info(f"   Comprar em {lowest_exchange}: ${lowest_price:.2f}")
                        self.logger.info(f"   Vender em {highest_exchange}: ${highest_price:.2f}")

                        # Simulação de ação: executar trade simulado
                        await self.simulate_action(opportunity)

                # Pequena pausa entre símbolos
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar oportunidades: {e}")

        return opportunities

    async def simulate_action(self, opportunity: Dict):
        """Simula a execução de uma ação de arbitragem ao identificar uma oportunidade"""
        self.logger.info(f"🟢 Simulando ação: Comprando {opportunity['symbol']} em {opportunity['buy_exchange']} por ${opportunity['buy_price']:.8f} e vendendo em {opportunity['sell_exchange']} por ${opportunity['sell_price']:.8f}")
        # Simular latência
        await asyncio.sleep(0.2)
        # Simular resultado
        simulated_profit = (opportunity['sell_price'] - opportunity['buy_price']) * 1  # 1 unidade
        self.logger.info(f"🟢 Simulação concluída: Lucro estimado = ${simulated_profit:.2f} para 1 unidade de {opportunity['symbol']}")

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
            self.metrics.trades_total.inc()
            self.metrics.profit_total.inc(profit)
            self.metrics.balance_gauge.set(self.balance)

            # Registrar duração do trade
            duration = asyncio.get_event_loop().time() - start_time
            self.metrics.trade_duration.observe(duration)

            self.logger.info(f"✅ Trade executado com sucesso!")
            self.logger.info(f"   💵 Lucro: ${profit:.8f}")
            self.logger.info(f"   💰 Balance atual: ${self.balance:.8f}")

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

        while True:
            now = asyncio.get_event_loop().time()
            if now >= end_time:
                break
            try:
                # Buscar oportunidades
                opportunities = await self.find_arbitrage_opportunities()
                opportunities_found += len(opportunities)

                # Log detalhado de mercado (snapshot + análise)
                market_data = await self.market_analyzer.get_market_snapshot()
                self.market_analyzer.log_market_analysis(market_data, opportunities)

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
        if hasattr(self.config, 'initial_balance'):
            total_profit = self.balance - float(getattr(self.config, 'initial_balance', 10000))
        else:
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

    async def initialize(self):
        await self.market_analyzer.initialize()

    async def shutdown(self):
        """Shutdown do bot"""
        self.logger.info("\n🛑 Fazendo shutdown do ArbitrageBot...")
        self.running = False
        # Fechar conexões HTTP se existirem
        if hasattr(self, 'market_analyzer') and hasattr(self.market_analyzer, 'close'):
            await self.market_analyzer.close()
        self.logger.info("✅ Bot finalizado com sucesso")