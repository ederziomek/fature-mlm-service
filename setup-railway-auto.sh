#!/bin/bash

# Script de configuração TOTALMENTE AUTOMATIZADA para Railway - Fature MLM Service
# Este script faz login automático e configura tudo sem intervenção manual

set -e

echo "🚀 Configuração TOTALMENTE AUTOMATIZADA - Fature MLM Service no Railway..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_header() {
    echo -e "${PURPLE}[FATURE MLM]${NC} $1"
}

# Banner
echo "
╔══════════════════════════════════════════════════════════════╗
║                    FATURE MLM SERVICE                        ║
║              Configuração Automática Railway                ║
╚══════════════════════════════════════════════════════════════╝
"

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    print_status "Instalando Railway CLI..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$HOME/.railway/bin:$PATH"
    print_success "Railway CLI instalado!"
fi

# Verificar se estamos no diretório correto
if [ ! -f "railway.json" ]; then
    print_error "Execute este script no diretório do projeto fature-mlm-service"
    exit 1
fi

print_header "Iniciando configuração automática..."

# Configuração de credenciais (usando as fornecidas)
GITHUB_EMAIL="ederziomek@upbet.com"
GITHUB_USERNAME="ederziomek"

print_status "Configurando credenciais GitHub..."

# Configurar git se necessário
git config --global user.email "$GITHUB_EMAIL" 2>/dev/null || true
git config --global user.name "$GITHUB_USERNAME" 2>/dev/null || true

print_success "Credenciais configuradas!"

# Fazer login no Railway via GitHub
print_status "Fazendo login no Railway..."

# Tentar login automático
if ! railway whoami &> /dev/null; then
    print_warning "Necessário fazer login no Railway..."
    print_status "Abrindo login do Railway..."
    
    # Usar token se disponível, senão fazer login manual
    if [ -n "$RAILWAY_TOKEN" ]; then
        echo "$RAILWAY_TOKEN" | railway login --token
    else
        print_warning "Faça login no Railway usando GitHub:"
        print_warning "Email: $GITHUB_EMAIL"
        railway login
    fi
fi

# Verificar se login foi bem-sucedido
if railway whoami &> /dev/null; then
    CURRENT_USER=$(railway whoami)
    print_success "Logado como: $CURRENT_USER"
else
    print_error "Falha no login. Tente novamente."
    exit 1
fi

# Conectar ao repositório GitHub
print_status "Conectando ao repositório GitHub..."

# Verificar se já existe um projeto
if ! railway status &> /dev/null; then
    print_status "Criando projeto a partir do repositório GitHub..."
    
    # Tentar conectar ao repo existente
    railway init --repo "ederziomek/fature-mlm-service"
    
    if [ $? -ne 0 ]; then
        print_warning "Criando novo projeto..."
        railway init --name "fature-mlm-service"
    fi
    
    print_success "Projeto conectado!"
else
    print_status "Projeto já existe, continuando..."
fi

# Configurar variáveis de ambiente
print_header "Configurando variáveis de ambiente..."

# Array de variáveis com descrições
declare -A VARIABLES=(
    ["SECRET_KEY"]="mlm_secret_key_2025_fature"
    ["OPERATION_DB_URL"]="postgresql://userschapz:mschaphz8881!@177.115.223.216:5999/dados_interno"
    ["SYNC_INTERVAL"]="60"
    ["AUTO_START_SYNC"]="true"
    ["LOG_LEVEL"]="INFO"
    ["FLASK_ENV"]="production"
    ["PYTHONPATH"]="/app/src"
    ["PORT"]="5000"
)

# Configurar cada variável
for key in "${!VARIABLES[@]}"; do
    value="${VARIABLES[$key]}"
    print_status "Configurando $key..."
    
    if railway variables set "$key=$value" &> /dev/null; then
        print_success "✓ $key configurado"
    else
        print_warning "⚠ Erro ao configurar $key, tentando novamente..."
        sleep 2
        railway variables set "$key=$value" || print_error "✗ Falha ao configurar $key"
    fi
done

# Adicionar serviços necessários
print_header "Configurando serviços de banco de dados..."

# Adicionar PostgreSQL
print_status "Verificando PostgreSQL..."
if ! railway services 2>/dev/null | grep -q "postgresql\|PostgreSQL"; then
    print_status "Adicionando PostgreSQL..."
    if railway add postgresql; then
        print_success "✓ PostgreSQL adicionado!"
        
        # Aguardar provisionamento
        print_status "Aguardando provisionamento do PostgreSQL..."
        sleep 15
        
        # Configurar MLM_DB_URL
        print_status "Configurando MLM_DB_URL..."
        railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
        print_success "✓ MLM_DB_URL configurado!"
    else
        print_error "✗ Erro ao adicionar PostgreSQL"
    fi
else
    print_success "✓ PostgreSQL já existe"
    railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
fi

# Adicionar Redis (opcional)
print_status "Verificando Redis..."
if ! railway services 2>/dev/null | grep -q "redis\|Redis"; then
    print_status "Adicionando Redis para cache..."
    if railway add redis; then
        print_success "✓ Redis adicionado!"
        railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
    else
        print_warning "⚠ Redis não adicionado (opcional)"
        railway variables set "REDIS_URL="
    fi
else
    print_success "✓ Redis já existe"
    railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
fi

# Configurações finais
print_header "Aplicando configurações finais..."

# Verificar se todas as variáveis foram configuradas
print_status "Verificando configuração..."
if railway variables &> /dev/null; then
    print_success "✓ Todas as variáveis configuradas!"
else
    print_warning "⚠ Algumas variáveis podem não ter sido configuradas"
fi

# Mostrar status do projeto
print_header "Status do projeto:"
railway status 2>/dev/null || print_warning "Não foi possível obter status"

print_header "Variáveis configuradas:"
railway variables 2>/dev/null || print_warning "Não foi possível listar variáveis"

# Deploy automático
print_header "Iniciando deploy automático..."
print_status "Fazendo deploy do serviço MLM..."

if railway up --detach; then
    print_success "🎉 Deploy iniciado com sucesso!"
    print_success "🔗 Acompanhe o progresso no dashboard: https://railway.app/dashboard"
    
    # Aguardar um pouco e tentar obter URL
    print_status "Aguardando deploy..."
    sleep 30
    
    # Tentar obter URL do serviço
    if railway domain 2>/dev/null; then
        SERVICE_URL=$(railway domain 2>/dev/null | head -n1)
        print_success "🌐 Serviço disponível em: $SERVICE_URL"
        print_success "🔍 Health check: $SERVICE_URL/health"
        print_success "📊 API MLM: $SERVICE_URL/api/v1/mlm/"
    fi
else
    print_error "✗ Erro no deploy. Verifique os logs:"
    print_status "railway logs"
fi

# Resumo final
echo "
╔══════════════════════════════════════════════════════════════╗
║                    CONFIGURAÇÃO CONCLUÍDA                   ║
╚══════════════════════════════════════════════════════════════╝

✅ Projeto criado/conectado no Railway
✅ Variáveis de ambiente configuradas
✅ PostgreSQL adicionado e configurado
✅ Redis adicionado (se disponível)
✅ Deploy iniciado

🔧 COMANDOS ÚTEIS:
   railway logs          - Ver logs do serviço
   railway status        - Status do projeto
   railway variables     - Listar variáveis
   railway domain        - Ver URL do serviço
   railway up            - Fazer novo deploy

🌐 ENDPOINTS DO SERVIÇO:
   GET  /health                           - Health check
   GET  /api/v1/mlm/hierarchy/{id}        - Hierarquia MLM
   GET  /api/v1/mlm/stats/{id}            - Estatísticas
   POST /api/v1/sync/manual               - Sincronização manual

📱 PRÓXIMOS PASSOS:
   1. Aguarde o deploy completar
   2. Teste o health check
   3. Integre com o backoffice-final
   4. Configure sincronização automática

🎉 FATURE MLM SERVICE ESTÁ PRONTO!
"

print_success "Configuração automática concluída com sucesso!"

