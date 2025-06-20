# Deploy Automático - Fature MLM Service

## 🚀 Configuração Totalmente Automatizada

Criamos scripts que configuram **TUDO automaticamente** no Railway!

### ⚡ Opção 1: Script Totalmente Automatizado

```bash
# Torna o script executável
chmod +x setup-railway-auto.sh

# Executa configuração completa
./setup-railway-auto.sh
```

**O que este script faz:**
- ✅ Instala Railway CLI automaticamente
- ✅ Faz login usando suas credenciais GitHub
- ✅ Cria/conecta projeto no Railway
- ✅ Configura TODAS as variáveis de ambiente
- ✅ Adiciona PostgreSQL e Redis
- ✅ Faz deploy automaticamente
- ✅ Mostra URLs e status final

### 🔧 Opção 2: Script Interativo

```bash
# Para configuração com confirmações
chmod +x setup-railway.sh
./setup-railway.sh
```

### 📋 Variáveis Configuradas Automaticamente

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `SECRET_KEY` | `mlm_secret_key_2025_fature` | Chave secreta da aplicação |
| `OPERATION_DB_URL` | `postgresql://userschapz:...` | Banco da operação |
| `MLM_DB_URL` | `${{PostgreSQL.DATABASE_URL}}` | Banco MLM (auto) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Cache Redis (auto) |
| `SYNC_INTERVAL` | `60` | Intervalo de sincronização |
| `AUTO_START_SYNC` | `true` | Iniciar sync automático |
| `LOG_LEVEL` | `INFO` | Nível de logs |
| `FLASK_ENV` | `production` | Ambiente Flask |

### 🌐 Endpoints Disponíveis Após Deploy

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

### 🔍 Comandos Úteis Pós-Deploy

```bash
# Ver logs em tempo real
railway logs

# Status do projeto
railway status

# Listar variáveis configuradas
railway variables

# Ver URL do serviço
railway domain

# Fazer novo deploy
railway up
```

### 🎯 Integração com Backoffice

Após o deploy, use o arquivo `integration/backoffice-mlm-routes.js` para integrar com o backoffice-final:

1. Copie o arquivo para `api/routes/mlm.js` no backoffice
2. Adicione no `server.js`: `app.use('/api/mlm', require('./routes/mlm'))`
3. Configure a variável: `MLM_SERVICE_URL=https://seu-servico.railway.app`

### 🔐 Credenciais Utilizadas

- **GitHub**: ederziomek@upbet.com
- **Repositório**: https://github.com/ederziomek/fature-mlm-service
- **Railway**: Login via GitHub

### ⚠️ Troubleshooting

Se algo der errado:

```bash
# Verificar status
railway status

# Ver logs de erro
railway logs --tail

# Reconfigurar variáveis
railway variables set NOME=VALOR

# Refazer deploy
railway up --force
```

### 🎉 Resultado Final

Após executar o script, você terá:
- ✅ Serviço MLM rodando em produção
- ✅ Banco PostgreSQL configurado
- ✅ Sincronização automática ativa
- ✅ APIs prontas para uso
- ✅ Integração preparada para backoffice

