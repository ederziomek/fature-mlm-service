# Deploy Automático - Fature MLM Service

## 🚀 PROBLEMA RESOLVIDO!

✅ **Dockerfile corrigido** - Não depende mais do arquivo `.env`
✅ **Arquivo `.env` criado** - Para desenvolvimento local
✅ **Scripts ultra automatizados** - Deploy 100% automático

## ⚡ DEPLOY TOTALMENTE AUTOMATIZADO

### Opção 1: Script Ultra Automatizado (RECOMENDADO)

```bash
# Clone o repositório (se ainda não fez)
git clone https://github.com/ederziomek/fature-mlm-service.git
cd fature-mlm-service

# Execute o script ultra automatizado
chmod +x setup-railway-ultra.sh
./setup-railway-ultra.sh
```

**Este script faz TUDO automaticamente:**
- ✅ Instala Railway CLI
- ✅ Faz login via GitHub (abre navegador)
- ✅ Cria/conecta projeto automaticamente
- ✅ Configura TODAS as variáveis de ambiente
- ✅ Adiciona PostgreSQL e Redis
- ✅ Faz deploy e monitora status
- ✅ Testa health check
- ✅ Mostra URLs finais

### Opção 2: Script Automatizado Original

```bash
chmod +x setup-railway-auto.sh
./setup-railway-auto.sh
```

## 🔧 CORREÇÕES IMPLEMENTADAS

### 1. Dockerfile Corrigido
```dockerfile
# ANTES (com erro):
COPY .env .

# DEPOIS (corrigido):
# Removida linha problemática
# Variáveis configuradas via Railway
```

### 2. Arquivo .env Criado
- ✅ Para desenvolvimento local
- ✅ Não interfere no Railway
- ✅ Configurações padrão incluídas

### 3. Scripts Melhorados
- ✅ Retry automático para falhas
- ✅ Monitoramento de status
- ✅ Verificação de health check
- ✅ Logs detalhados

## 🎯 PROCESSO TOTALMENTE AUTOMÁTICO

**Você NÃO precisa fazer NADA manualmente no Railway!**

1. **Execute o script**: `./setup-railway-ultra.sh`
2. **Faça login** quando o navegador abrir
3. **Aguarde** - tudo será configurado automaticamente
4. **Pronto!** - Serviço funcionando

## 📊 VARIÁVEIS CONFIGURADAS AUTOMATICAMENTE

| Variável | Valor | Status |
|----------|-------|--------|
| `SECRET_KEY` | `mlm_secret_key_2025_fature` | ✅ |
| `OPERATION_DB_URL` | `postgresql://userschapz:...` | ✅ |
| `MLM_DB_URL` | `${{PostgreSQL.DATABASE_URL}}` | ✅ |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | ✅ |
| `SYNC_INTERVAL` | `60` | ✅ |
| `AUTO_START_SYNC` | `true` | ✅ |
| `LOG_LEVEL` | `INFO` | ✅ |
| `FLASK_ENV` | `production` | ✅ |
| `PYTHONPATH` | `/app/src` | ✅ |
| `PORT` | `5000` | ✅ |

## 🌐 ENDPOINTS DISPONÍVEIS

Após o deploy automático:

```
GET  /health                           - Health check
GET  /                                 - Informações do serviço
GET  /api/v1/mlm/hierarchy/{id}        - Hierarquia completa
GET  /api/v1/mlm/stats/{id}            - Estatísticas por nível
GET  /api/v1/mlm/commissions/{id}      - Comissões
GET  /api/v1/mlm/summary               - Resumo geral
POST /api/v1/sync/manual               - Sincronização manual
GET  /api/v1/sync/status               - Status de sincronização
```

## 🔍 MONITORAMENTO

```bash
# Ver logs em tempo real
railway logs

# Status do projeto
railway status

# URL do serviço
railway domain

# Testar health check
curl https://seu-servico.railway.app/health
```

## 🎯 INTEGRAÇÃO COM BACKOFFICE

Após o deploy automático:

1. **Copie** o arquivo `integration/backoffice-mlm-routes.js`
2. **Cole** em `api/routes/mlm.js` no backoffice
3. **Configure** no backoffice: `MLM_SERVICE_URL=https://seu-servico.railway.app`
4. **Adicione** no `server.js`: `app.use('/api/mlm', require('./routes/mlm'))`

## 🚀 RESULTADO FINAL

Após executar `./setup-railway-ultra.sh`:

- ✅ **Serviço MLM rodando** em produção
- ✅ **Banco PostgreSQL** configurado
- ✅ **Cache Redis** otimizado
- ✅ **Sincronização automática** ativa
- ✅ **APIs funcionando** para hierarquia e estatísticas
- ✅ **Monitoramento** e logs disponíveis

## ⚠️ TROUBLESHOOTING

Se algo der errado:

```bash
# Ver logs de erro
railway logs --tail

# Reconfigurar variáveis
railway variables set NOME=VALOR

# Refazer deploy
railway up --force

# Verificar status
railway status
```

## 🎉 PRONTO!

**Execute apenas:**
```bash
./setup-railway-ultra.sh
```

**E em poucos minutos terá todo o sistema MLM funcionando automaticamente!** 🚀

