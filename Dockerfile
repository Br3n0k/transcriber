# Stage 1: Builder
FROM python:3.13-slim as builder

# Instala dependências de compilação e git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cria ambiente virtual para isolar dependências
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
# Instala dependências no ambiente virtual
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim as runtime

# Instala apenas dependências de runtime (ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copia ambiente virtual do estágio de build
COPY --from=builder /opt/venv /opt/venv

# Configura variáveis de ambiente
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Desativa auto-setup do ffmpeg pois já instalamos via apt
ENV FFMPEG_AUTO_SETUP=false

# Copia código da aplicação
COPY . .

# Cria diretórios de storage e ajusta permissões
RUN mkdir -p storage/uploads storage/transcriptions && \
    chown -R appuser:appuser /app

# Muda para usuário não-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
