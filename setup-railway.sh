#!/bin/bash

# Script de configuração automática para Railway - Fature MLM Service
# Este script configura automaticamente todas as variáveis de ambiente necessárias

set -e

echo "🚀 Configurando Fature MLM Service no Railway..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    print_error "Railway CLI não encontrado. Instalando..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$HOME/.railway/bin:$PATH"
fi

# Verificar se estamos no diretório correto
if [ ! -f "railway.json" ]; then
    print_error "Arquivo railway.json não encontrado. Execute este script no diretório do projeto."
    exit 1
fi

print_status "Verificando autenticação no Railway..."

# Verificar se está logado no Railway
if ! railway whoami &> /dev/null; then
    print_warning "Não está logado no Railway. Fazendo login..."
    print_status "Abrindo navegador para login..."
    railway login
fi

print_success "Autenticado no Railway!"

# Verificar se já existe um projeto
PROJECT_EXISTS=$(railway status 2>/dev/null | grep -c "Project:" || echo "0")

if [ "$PROJECT_EXISTS" -eq "0" ]; then
    print_status "Criando novo projeto no Railway..."
    railway init --name "fature-mlm-service"
    print_success "Projeto criado!"
else
    print_status "Projeto já existe, continuando..."
fi

# Configurar variáveis de ambiente
print_status "Configurando variáveis de ambiente..."

# Variáveis principais
VARIABLES=(
    "SECRET_KEY=mlm_secret_key_2025_fature"
    "OPERATION_DB_URL=postgresql://userschapz:mschaphz8881!@177.115.223.216:5999/dados_interno"
    "SYNC_INTERVAL=60"
    "AUTO_START_SYNC=true"
    "LOG_LEVEL=INFO"
    "FLASK_ENV=production"
    "PYTHONPATH=/app/src"
)

# Configurar cada variável
for var in "${VARIABLES[@]}"; do
    key=$(echo "$var" | cut -d'=' -f1)
    value=$(echo "$var" | cut -d'=' -f2-)
    
    print_status "Configurando $key..."
    railway variables set "$key=$value"
done

print_success "Variáveis de ambiente configuradas!"

# Adicionar PostgreSQL se não existir
print_status "Verificando serviços..."

# Verificar se PostgreSQL já está adicionado
if ! railway services | grep -q "PostgreSQL"; then
    print_status "Adicionando PostgreSQL..."
    railway add postgresql
    print_success "PostgreSQL adicionado!"
    
    # Aguardar um pouco para o serviço ser provisionado
    print_status "Aguardando provisionamento do PostgreSQL..."
    sleep 10
    
    # Configurar MLM_DB_URL para usar o PostgreSQL
    print_status "Configurando MLM_DB_URL..."
    railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
else
    print_status "PostgreSQL já existe, configurando MLM_DB_URL..."
    railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
fi

# Adicionar Redis (opcional, para cache)
if ! railway services | grep -q "Redis"; then
    print_warning "Redis não encontrado. Deseja adicionar Redis para cache? (y/n)"
    read -r add_redis
    if [[ $add_redis =~ ^[Yy]$ ]]; then
        print_status "Adicionando Redis..."
        railway add redis
        railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
        print_success "Redis adicionado!"
    else
        print_status "Pulando Redis..."
        railway variables set "REDIS_URL="
    fi
else
    print_status "Redis já existe, configurando REDIS_URL..."
    railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
fi

print_success "Configuração concluída!"

# Mostrar status final
print_status "Status do projeto:"
railway status

print_status "Variáveis configuradas:"
railway variables

# Opção de fazer deploy imediatamente
print_warning "Deseja fazer deploy agora? (y/n)"
read -r deploy_now

if [[ $deploy_now =~ ^[Yy]$ ]]; then
    print_status "Iniciando deploy..."
    railway up
    print_success "Deploy iniciado! Acompanhe o progresso no dashboard do Railway."
else
    print_status "Deploy não iniciado. Para fazer deploy manualmente, execute:"
    echo "railway up"
fi

print_success "🎉 Configuração automática concluída!"
print_status "Acesse o dashboard: https://railway.app/dashboard"
print_status "Para ver logs: railway logs"
print_status "Para fazer deploy: railway up"

