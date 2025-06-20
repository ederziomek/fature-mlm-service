# Fature MLM Service

Serviço de processamento de rede multinível (MLM) para o Sistema Fature.

## Funcionalidades

- ✅ Processamento de hierarquia MLM com 5 níveis
- ✅ Sincronização automática com banco da operação
- ✅ APIs RESTful para consultas e gerenciamento
- ✅ Cálculo de comissões por nível
- ✅ Cache otimizado para performance
- ✅ Logs detalhados e monitoramento

## Deploy no Railway

1. Conecte este repositório ao Railway
2. Configure as variáveis de ambiente:
   - `OPERATION_DB_URL`: URL do banco da operação
   - `MLM_DB_URL`: `${{PostgreSQL.DATABASE_URL}}`
   - `SECRET_KEY`: Chave secreta para a aplicação

3. O Railway detectará automaticamente o `railway.json` e fará o deploy

## Endpoints Principais

- `GET /health` - Health check do serviço
- `GET /api/v1/mlm/hierarchy/{affiliate_id}` - Hierarquia completa
- `GET /api/v1/mlm/stats/{affiliate_id}` - Estatísticas por nível
- `POST /api/v1/sync/manual` - Sincronização manual

## Integração com Backoffice

Use o arquivo `integration/backoffice-mlm-routes.js` para integrar com o backoffice-final.

## Tecnologias

- Python 3.11
- Flask
- PostgreSQL
- Docker

