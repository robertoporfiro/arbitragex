FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src/
COPY config/ ./config/
COPY .env* ./

# Criar diretório para logs e dados
RUN mkdir -p /app/data /app/logs

# Definir variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor porta (se necessário para API futura)
EXPOSE 8000

# Comando padrão
CMD ["python", "src/main.py"]
