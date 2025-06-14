"""
Sistema de métricas do ArbitrageX
"""

import asyncio
import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        # Métricas Prometheus
        self.trades_total = Counter('arbitragex_trades_total', 'Total de trades executados')
        self.profit_total = Counter('arbitragex_profit_total', 'Lucro total acumulado')
        self.opportunities_found = Counter('arbitragex_opportunities_total', 'Oportunidades encontradas')
        self.trade_duration = Histogram('arbitragex_trade_duration_seconds', 'Duração dos trades')
        self.balance_gauge = Gauge('arbitragex_balance', 'Balance atual')
        
    async def start(self):
        """Iniciar servidor de métricas"""
        try:
            start_http_server(8000)
            logger.info("✅ Servidor de métricas iniciado na porta 8000")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar métricas: {e}")
    
    async def record_trade(self, profit: float):
        """Registrar trade executado"""
        self.trades_total.inc()
        self.profit_total.inc(profit)
        logger.debug(f"Métricas atualizadas - Profit: ${profit:.2f}")
    
    async def stop(self):
        """Parar coletor de métricas"""
        logger.info("Parando coletor de métricas...")
