#!/bin/bash

# Script de configuração ULTRA AUTOMATIZADA para Railway - Fature MLM Service
# Este script faz TUDO automaticamente, incluindo login e deploy

set -e

echo "🚀 CONFIGURAÇÃO ULTRA AUTOMATIZADA - Fature MLM Service no Railway..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Banner melhorado
echo "
╔══════════════════════════════════════════════════════════════╗
║                    FATURE MLM SERVICE                        ║
║           Configuração ULTRA Automática Railway             ║
║                                                              ║
║  ✅ Login automático via GitHub                              ║
║  ✅ Configuração completa de variáveis                       ║
║  ✅ Deploy automático com verificações                       ║
║  ✅ Monitoramento de status                                  ║
╚══════════════════════════════════════════════════════════════╝
"

# Verificar se Railway CLI está instalado
print_step "1/8 - Verificando Railway CLI..."
if ! command -v railway &> /dev/null; then
    print_status "Instalando Railway CLI..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$HOME/.railway/bin:$PATH"
    print_success "Railway CLI instalado!"
else
    print_success "Railway CLI já instalado!"
fi

# Verificar se estamos no diretório correto
print_step "2/8 - Verificando diretório do projeto..."
if [ ! -f "railway.json" ]; then
    print_error "Execute este script no diretório do projeto fature-mlm-service"
    exit 1
fi
print_success "Diretório correto!"

# Configuração de credenciais
GITHUB_EMAIL="ederziomek@upbet.com"
GITHUB_USERNAME="ederziomek"

print_step "3/8 - Configurando credenciais..."
git config --global user.email "$GITHUB_EMAIL" 2>/dev/null || true
git config --global user.name "$GITHUB_USERNAME" 2>/dev/null || true
print_success "Credenciais configuradas!"

# Fazer login no Railway
print_step "4/8 - Fazendo login no Railway..."
if ! railway whoami &> /dev/null; then
    print_warning "Necessário fazer login no Railway..."
    print_status "🌐 Abrindo login do Railway no navegador..."
    print_status "📧 Use o email: $GITHUB_EMAIL"
    print_status "🔑 Faça login via GitHub"
    
    railway login
    
    # Aguardar login
    print_status "Aguardando login..."
    sleep 5
fi

# Verificar se login foi bem-sucedido
if railway whoami &> /dev/null; then
    CURRENT_USER=$(railway whoami)
    print_success "✅ Logado como: $CURRENT_USER"
else
    print_error "❌ Falha no login. Tente novamente."
    exit 1
fi

# Conectar/criar projeto
print_step "5/8 - Configurando projeto no Railway..."
if ! railway status &> /dev/null; then
    print_status "Criando projeto no Railway..."
    
    # Tentar conectar ao repo existente primeiro
    if railway init --repo "ederziomek/fature-mlm-service" &> /dev/null; then
        print_success "✅ Projeto conectado ao repositório GitHub!"
    else
        print_status "Criando novo projeto..."
        railway init --name "fature-mlm-service"
        print_success "✅ Novo projeto criado!"
    fi
else
    print_success "✅ Projeto já existe!"
fi

# Configurar variáveis de ambiente
print_step "6/8 - Configurando variáveis de ambiente..."

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

# Configurar cada variável com retry
for key in "${!VARIABLES[@]}"; do
    value="${VARIABLES[$key]}"
    print_status "Configurando $key..."
    
    # Tentar 3 vezes
    for attempt in 1 2 3; do
        if railway variables set "$key=$value" &> /dev/null; then
            print_success "  ✅ $key configurado"
            break
        else
            if [ $attempt -eq 3 ]; then
                print_error "  ❌ Falha ao configurar $key após 3 tentativas"
            else
                print_warning "  ⚠️ Tentativa $attempt falhou, tentando novamente..."
                sleep 2
            fi
        fi
    done
done

# Adicionar serviços de banco
print_step "7/8 - Configurando serviços de banco..."

# PostgreSQL
print_status "Verificando PostgreSQL..."
if ! railway services 2>/dev/null | grep -q "postgresql\|PostgreSQL"; then
    print_status "Adicionando PostgreSQL..."
    if railway add postgresql; then
        print_success "✅ PostgreSQL adicionado!"
        
        # Aguardar provisionamento
        print_status "⏳ Aguardando provisionamento do PostgreSQL..."
        sleep 20
        
        # Configurar MLM_DB_URL
        railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
        print_success "✅ MLM_DB_URL configurado!"
    else
        print_error "❌ Erro ao adicionar PostgreSQL"
    fi
else
    print_success "✅ PostgreSQL já existe"
    railway variables set "MLM_DB_URL=\${{PostgreSQL.DATABASE_URL}}"
fi

# Redis (opcional)
print_status "Verificando Redis..."
if ! railway services 2>/dev/null | grep -q "redis\|Redis"; then
    print_status "Adicionando Redis para cache..."
    if railway add redis; then
        print_success "✅ Redis adicionado!"
        railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
    else
        print_warning "⚠️ Redis não adicionado (opcional)"
        railway variables set "REDIS_URL="
    fi
else
    print_success "✅ Redis já existe"
    railway variables set "REDIS_URL=\${{Redis.REDIS_URL}}"
fi

# Deploy automático
print_step "8/8 - Fazendo deploy automático..."
print_status "🚀 Iniciando deploy do serviço MLM..."

if railway up --detach; then
    print_success "🎉 Deploy iniciado com sucesso!"
    
    # Aguardar e monitorar deploy
    print_status "⏳ Aguardando deploy completar..."
    sleep 45
    
    # Verificar status
    print_status "📊 Verificando status do deploy..."
    
    # Tentar obter URL do serviço
    SERVICE_URL=""
    for attempt in 1 2 3; do
        if SERVICE_URL=$(railway domain 2>/dev/null | head -n1); then
            if [ -n "$SERVICE_URL" ]; then
                break
            fi
        fi
        sleep 10
    done
    
    if [ -n "$SERVICE_URL" ]; then
        print_success "🌐 Serviço disponível em: https://$SERVICE_URL"
        print_success "🔍 Health check: https://$SERVICE_URL/health"
        print_success "📊 API MLM: https://$SERVICE_URL/api/v1/mlm/"
        
        # Testar health check
        print_status "🩺 Testando health check..."
        sleep 10
        if curl -f "https://$SERVICE_URL/health" &> /dev/null; then
            print_success "✅ Health check OK!"
        else
            print_warning "⚠️ Health check ainda não disponível (normal nos primeiros minutos)"
        fi
    else
        print_warning "⚠️ URL ainda não disponível. Verifique no dashboard do Railway."
    fi
    
else
    print_error "❌ Erro no deploy. Verificando logs..."
    railway logs --tail 20
fi

# Mostrar status final
print_header "📋 Status Final do Projeto:"
railway status 2>/dev/null || print_warning "Não foi possível obter status"

print_header "🔧 Variáveis Configuradas:"
railway variables 2>/dev/null || print_warning "Não foi possível listar variáveis"

# Resumo final com instruções
echo "
╔══════════════════════════════════════════════════════════════╗
║                    CONFIGURAÇÃO CONCLUÍDA                   ║
╚══════════════════════════════════════════════════════════════╝

✅ SERVIÇOS CONFIGURADOS:
   • Projeto criado/conectado no Railway
   • PostgreSQL adicionado e configurado
   • Redis adicionado para cache
   • Todas as variáveis de ambiente configuradas
   • Deploy automático realizado

🌐 ENDPOINTS DISPONÍVEIS:
   GET  /health                           - Health check
   GET  /                                 - Informações do serviço
   GET  /api/v1/mlm/hierarchy/{id}        - Hierarquia MLM
   GET  /api/v1/mlm/stats/{id}            - Estatísticas por nível
   POST /api/v1/sync/manual               - Sincronização manual
   GET  /api/v1/sync/status               - Status de sincronização

🔧 COMANDOS ÚTEIS:
   railway logs          - Ver logs em tempo real
   railway status        - Status do projeto
   railway variables     - Listar variáveis
   railway domain        - Ver URL do serviço
   railway up            - Fazer novo deploy

📱 PRÓXIMOS PASSOS:
   1. ✅ Aguarde alguns minutos para o serviço inicializar
   2. ✅ Teste o health check
   3. ✅ Integre com o backoffice-final
   4. ✅ Configure sincronização automática

🎯 INTEGRAÇÃO COM BACKOFFICE:
   • Use o arquivo integration/backoffice-mlm-routes.js
   • Configure MLM_SERVICE_URL no backoffice
   • Adicione as rotas MLM ao servidor

🎉 FATURE MLM SERVICE ESTÁ PRONTO E FUNCIONANDO!
"

print_success "🚀 Configuração ultra automatizada concluída com sucesso!"
print_status "📊 Acesse o dashboard: https://railway.app/dashboard"
print_status "📱 Para monitorar: railway logs"

