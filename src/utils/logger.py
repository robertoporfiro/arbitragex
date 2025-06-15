"""
Sistema de logging do ArbitrageX
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import structlog

def setup_logging(level: str = "INFO"):
    """Configurar sistema de logging"""

    # Criar diretório de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configurar nível
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configurar formatação
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Handler para arquivo
    file_handler = RotatingFileHandler(
        log_dir / "arbitragex.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Evita handlers duplicados
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def setup_logger(name: str, level: str = "INFO"):
    """
    ✅ FUNÇÃO ADICIONADA: setup_logger
    Configurar logger para um módulo específico
    """
    # Configurar logging geral se ainda não foi feito
    setup_logging(level)
    
    # Retornar logger específico para o módulo
    logger = logging.getLogger(name)
    logger.propagate = True
    return logger

# Alias para compatibilidade
get_logger = setup_logger
