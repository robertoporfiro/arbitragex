# ArbitrageX - Cryptocurrency Arbitrage Trading Bot
.PHONY: help setup build up down logs clean paper-trading monitoring

help:
	@echo "🚀 ArbitrageX - Cryptocurrency Arbitrage Trading Bot"
	@echo ""
	@echo "Available commands:"
	@echo "  setup          - Initial project setup"
	@echo "  build          - Build Docker images"
	@echo "  up             - Start core services (bot, db, redis)"
	@echo "  up-monitoring  - Start with monitoring (prometheus, grafana)"
	@echo "  down           - Stop all services"
	@echo "  logs           - View bot logs"
	@echo "  paper-trading  - Run paper trading with real market data"
	@echo "  clean          - Clean up containers and volumes"

setup:
	@echo "🔧 Setting up ArbitrageX..."
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	@echo "✅ Setup complete!"
	@echo "📝 Edit .env file if needed"
	@echo "🚀 Run 'make build && make up' to start"

build:
	@echo "🏗️  Building ArbitrageX..."
	docker-compose build --no-cache

up:
	@echo "🚀 Starting ArbitrageX (core services)..."
	docker-compose up -d arbitragex postgres redis
	@echo "✅ Core services started!"
	@echo "🔍 Bot metrics: http://localhost:8000/metrics"

up-monitoring:
	@echo "🚀 Starting ArbitrageX with monitoring..."
	docker-compose --profile monitoring up -d
	@echo "✅ All services started!"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin)"
	@echo "📈 Prometheus: http://localhost:9090"
	@echo "🔍 Bot metrics: http://localhost:8000/metrics"

down:
	@echo "🛑 Stopping ArbitrageX..."
	docker-compose --profile monitoring down

logs:
	@echo "📋 Viewing ArbitrageX logs..."
	docker-compose logs -f arbitragex

paper-trading:
	@echo "📝 Starting Paper Trading with REAL market data..."
	@echo "🌐 Connecting to live exchanges (Binance, Coinbase, Kraken)..."
	docker-compose exec arbitragex python src/main.py --mode paper --duration 60

paper-trading-custom:
	@read -p "Enter duration in minutes: " duration; \
	echo "📝 Starting Paper Trading for $$duration minutes..."; \
	docker-compose exec arbitragex python src/main.py --mode paper --duration $$duration

clean:
	@echo "🧹 Cleaning up..."
	docker-compose --profile monitoring down -v
	docker system prune -f
	@echo "✅ Cleanup complete"

restart:
	@echo "🔄 Restarting ArbitrageX..."
	docker-compose restart arbitragex

status:
	@echo "📊 ArbitrageX Status:"
	docker-compose ps

shell:
	@echo "🐚 Accessing ArbitrageX shell..."
	docker-compose exec arbitragex /bin/bash

debug-metrics:
	@echo "🔍 DEBUG: Verificando sistema de métricas..."
	@echo ""
	@echo "📊 1. Status dos containers:"
	@docker-compose ps
	@echo ""
	@echo "📊 2. Testando endpoint de métricas:"
	@curl -s http://localhost:8000/metrics | grep arbitragex || echo "❌ Nenhuma métrica encontrada"
	@echo ""
	@echo "📊 3. Logs recentes do bot:"
	@docker-compose logs --tail=20 arbitragex
	@echo ""
	@echo "📊 4. Testando conexão com exchanges:"
	@docker-compose exec arbitragex python -c "import aiohttp; print('aiohttp OK')" || echo "❌ aiohttp não disponível"

debug-full:
	@echo "🔍 DEBUG COMPLETO do ArbitrageX..."
	@echo ""
	@echo "🐳 Containers:"
	@docker-compose ps
	@echo ""
	@echo "📊 Métricas disponíveis:"
	@curl -s http://localhost:8000/metrics | head -30
	@echo ""
	@echo "📈 Prometheus targets:"
	@curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="arbitragex")' 2>/dev/null || echo "❌ Prometheus não acessível"
	@echo ""
	@echo "🤖 Logs do bot (últimas 50 linhas):"
	@docker-compose logs --tail=50 arbitragex
