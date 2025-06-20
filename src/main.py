import os
import sys
import threading
import time
from datetime import datetime, timedelta
import logging

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos do MLM
from src.models.mlm_database import MLMDatabase
from src.models.sync_service import MLMSyncService
from src.routes.mlm_api import mlm_bp
from src.routes.sync_api import sync_bp

app = Flask(__name__)
CORS(app)

# Configurações
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mlm_secret_key_2025')

# Configurações de banco de dados
app.config['OPERATION_DB_URL'] = os.getenv(
    'OPERATION_DB_URL',
    'postgresql://userschapz:mschaphz8881!@177.115.223.216:5999/dados_interno'
)

app.config['MLM_DB_URL'] = os.getenv(
    'MLM_DB_URL',
    'postgresql://localhost:5432/fature_mlm'
)

app.config['REDIS_URL'] = os.getenv(
    'REDIS_URL',
    'redis://localhost:6379/0'
)

# Registrar blueprints
app.register_blueprint(mlm_bp, url_prefix='/api/v1/mlm')
app.register_blueprint(sync_bp, url_prefix='/api/v1/sync')

# Inicializar serviços
mlm_db = None
sync_service = None

def initialize_services():
    """Inicializa serviços MLM"""
    global mlm_db, sync_service
    
    try:
        # Inicializar banco MLM
        mlm_db = MLMDatabase(app.config['MLM_DB_URL'])
        logger.info("Banco MLM inicializado")
        
        # Inicializar serviço de sincronização
        sync_service = MLMSyncService(
            operation_db_url=app.config['OPERATION_DB_URL'],
            mlm_db_url=app.config['MLM_DB_URL'],
            redis_url=app.config['REDIS_URL']
        )
        
        # Iniciar worker de sincronização
        sync_service.start_sync_worker()
        logger.info("Serviço de sincronização iniciado")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise

@app.route('/')
def index():
    """Endpoint de informações do serviço"""
    return jsonify({
        'service': 'fature-mlm-service',
        'message': 'Serviço MLM do Sistema Fature - Processamento de Rede Multinível',
        'version': '1.0.0',
        'features': [
            'MLM Hierarchy Processing',
            'Multi-level Commission Calculation',
            'Real-time Data Synchronization',
            'Performance Optimized Queries',
            'Comprehensive Audit Trail'
        ],
        'endpoints': {
            'health': '/health',
            'mlm_hierarchy': '/api/v1/mlm/hierarchy/{affiliate_id}',
            'mlm_stats': '/api/v1/mlm/stats/{affiliate_id}',
            'mlm_commissions': '/api/v1/mlm/commissions/{affiliate_id}',
            'sync_manual': '/api/v1/sync/manual',
            'sync_status': '/api/v1/sync/status'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexão com banco MLM
        mlm_status = mlm_db.check_connection() if mlm_db else False
        
        # Verificar status do sync service
        sync_status = sync_service.is_running if sync_service else False
        
        status = 'healthy' if mlm_status and sync_status else 'degraded'
        
        return jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'services': {
                'mlm_database': 'connected' if mlm_status else 'disconnected',
                'sync_service': 'running' if sync_status else 'stopped'
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para endpoints não encontrados"""
    return jsonify({
        'error': 'Endpoint not found',
        'service': 'fature-mlm-service',
        'path': request.path,
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    logger.error(f"Internal error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'service': 'fature-mlm-service',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    try:
        # Inicializar serviços
        initialize_services()
        
        # Iniciar aplicação
        logger.info("Iniciando Fature MLM Service...")
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        logger.error(f"Falha ao iniciar aplicação: {e}")
        sys.exit(1)

