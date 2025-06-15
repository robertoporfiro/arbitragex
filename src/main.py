#!/usr/bin/env python3
"""
ArbitrageX - Advanced Cryptocurrency Arbitrage Trading Bot
Main entry point for the application
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from bot.arbitrage_bot import ArbitrageBot
from utils.config import Config
from utils.logger import setup_logging
from database.connection import DatabaseManager
from monitoring.metrics import MetricsCollector

# Configurar logging
logger = logging.getLogger(__name__)

class ArbitrageXApp:
    def __init__(self):
        self.config = Config()
        self.bot = None
        self.db_manager = None
        self.metrics = None
        self.running = False
        
    async def initialize(self):
        """Inicializar todos os componentes"""
        try:
            # Setup logging
            setup_logging(self.config.log_level)
            logger.info("🚀 Iniciando ArbitrageX...")
            
            # Inicializar database
            self.db_manager = DatabaseManager(self.config.database_url)
            await self.db_manager.initialize()
            logger.info("✅ Database conectado")
            
            # Inicializar métricas
            self.metrics = MetricsCollector()
            await self.metrics.start()
            logger.info("✅ Métricas iniciadas")
            
            # Inicializar bot
            self.bot = ArbitrageBot(
                config=self.config,
                db_manager=self.db_manager,
                metrics=self.metrics
            )
            await self.bot.initialize()
            logger.info("✅ Bot inicializado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            return False
    
    async def run(self, mode='paper', duration=None):
        """Executar o bot"""
        if not await self.initialize():
            return False
            
        self.running = True
        
        try:
            if mode == 'paper':
                logger.info("📝 Iniciando Paper Trading...")
                await self.bot.run_paper_trading(duration or 60)
            elif mode == 'live':
                logger.warning("⚠️  Iniciando Live Trading - DINHEIRO REAL!")
                await self.bot.run_live_trading()
            else:
                logger.error(f"❌ Modo inválido: {mode}")
                return False
                
        except KeyboardInterrupt:
            logger.info("⏹️  Parando bot...")
        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown graceful"""
        logger.info("🛑 Fazendo shutdown...")
        self.running = False
        
        if self.bot:
            await self.bot.shutdown()
        
        if self.metrics:
            await self.metrics.stop()
            
        if self.db_manager:
            await self.db_manager.close()
            
        logger.info("✅ Shutdown completo")

def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    logger.info(f"Recebido sinal {signum}, parando...")
    sys.exit(0)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='ArbitrageX - Crypto Arbitrage Bot')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Modo de execução (default: paper)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duração em minutos para paper trading (default: 60)')
    parser.add_argument('--config', type=str, default='.env',
                       help='Arquivo de configuração (default: .env)')
    
    args = parser.parse_args()
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Criar e executar aplicação
    app = ArbitrageXApp()
    
    try:
        asyncio.run(app.run(mode=args.mode, duration=args.duration))
    except KeyboardInterrupt:
        print("\n👋 ArbitrageX finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
