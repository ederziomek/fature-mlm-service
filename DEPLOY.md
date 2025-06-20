# Script de Deploy para Railway

# 1. Adicionar ao package.json do backoffice-final:
{
  "scripts": {
    "start": "node api/server.js",
    "dev": "nodemon api/server.js"
  },
  "dependencies": {
    "axios": "^1.6.0"
  }
}

# 2. Modificar api/server.js para incluir rotas MLM:
const mlmRoutes = require('./routes/mlm');
app.use('/api/mlm', mlmRoutes);

# 3. Copiar backoffice-mlm-routes.js para api/routes/mlm.js

# 4. Adicionar variável de ambiente no Railway:
MLM_SERVICE_URL=https://fature-mlm-service-production.up.railway.app

# 5. Para o serviço MLM, criar railway.json:
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python src/main.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 60,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}

# 6. Criar Dockerfile para o serviço MLM:
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 5000

CMD ["python", "src/main.py"]

# 7. Variáveis de ambiente no Railway para MLM service:
OPERATION_DB_URL=postgresql://userschapz:mschaphz8881!@177.115.223.216:5999/dados_interno
MLM_DB_URL=${{PostgreSQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=mlm_secret_key_2025_fature

