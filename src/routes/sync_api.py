from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

sync_bp = Blueprint('sync', __name__)

# Será inicializado no main.py
sync_service = None
mlm_db = None

def init_sync_services(sync_instance, db_instance):
    """Inicializa instâncias dos serviços de sincronização"""
    global sync_service, mlm_db
    sync_service = sync_instance
    mlm_db = db_instance

@sync_bp.route('/manual', methods=['POST'])
def manual_sync():
    """Executa sincronização manual"""
    try:
        if not sync_service:
            return jsonify({
                'status': 'error',
                'message': 'Serviço de sincronização não inicializado'
            }), 500
        
        logger.info("Iniciando sincronização manual")
        start_time = datetime.now()
        
        # Executar sincronização
        sync_service.sync_data()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return jsonify({
            'status': 'success',
            'message': 'Sincronização manual concluída',
            'data': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na sincronização manual: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro na sincronização manual',
            'error': str(e)
        }), 500

@sync_bp.route('/status')
def sync_status():
    """Retorna status das sincronizações"""
    try:
        if not sync_service or not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviços não inicializados'
            }), 500
        
        # Buscar histórico de sincronizações
        sync_history = mlm_db.get_sync_status()
        
        # Informações do serviço
        service_info = {
            'is_running': sync_service.is_running,
            'sync_interval': sync_service.sync_interval,
            'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
        }
        
        # Processar histórico
        history_data = []
        for record in sync_history:
            history_item = {
                'sync_type': record['sync_type'],
                'records_processed': record['records_processed'],
                'records_updated': record['records_updated'],
                'records_inserted': record['records_inserted'],
                'start_time': record['start_time'].isoformat() if record['start_time'] else None,
                'end_time': record['end_time'].isoformat() if record['end_time'] else None,
                'status': record['status'],
                'error_message': record['error_message']
            }
            
            # Calcular duração se disponível
            if record['start_time'] and record['end_time']:
                duration = (record['end_time'] - record['start_time']).total_seconds()
                history_item['duration_seconds'] = duration
            
            history_data.append(history_item)
        
        return jsonify({
            'status': 'success',
            'data': {
                'service': service_info,
                'history': history_data,
                'total_records': len(history_data)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar status de sincronização: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@sync_bp.route('/start', methods=['POST'])
def start_sync():
    """Inicia worker de sincronização automática"""
    try:
        if not sync_service:
            return jsonify({
                'status': 'error',
                'message': 'Serviço de sincronização não inicializado'
            }), 500
        
        if sync_service.is_running:
            return jsonify({
                'status': 'info',
                'message': 'Worker de sincronização já está em execução'
            })
        
        sync_service.start_sync_worker()
        
        return jsonify({
            'status': 'success',
            'message': 'Worker de sincronização iniciado',
            'data': {
                'is_running': sync_service.is_running,
                'sync_interval': sync_service.sync_interval
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar worker de sincronização: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro ao iniciar worker de sincronização',
            'error': str(e)
        }), 500

@sync_bp.route('/stop', methods=['POST'])
def stop_sync():
    """Para worker de sincronização automática"""
    try:
        if not sync_service:
            return jsonify({
                'status': 'error',
                'message': 'Serviço de sincronização não inicializado'
            }), 500
        
        if not sync_service.is_running:
            return jsonify({
                'status': 'info',
                'message': 'Worker de sincronização já está parado'
            })
        
        sync_service.stop_sync_worker()
        
        return jsonify({
            'status': 'success',
            'message': 'Worker de sincronização parado',
            'data': {
                'is_running': sync_service.is_running
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao parar worker de sincronização: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro ao parar worker de sincronização',
            'error': str(e)
        }), 500

@sync_bp.route('/config', methods=['GET', 'POST'])
def sync_config():
    """Obtém ou atualiza configurações de sincronização"""
    try:
        if not sync_service:
            return jsonify({
                'status': 'error',
                'message': 'Serviço de sincronização não inicializado'
            }), 500
        
        if request.method == 'GET':
            # Retornar configurações atuais
            return jsonify({
                'status': 'success',
                'data': {
                    'sync_interval': sync_service.sync_interval,
                    'is_running': sync_service.is_running,
                    'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
                }
            })
        
        elif request.method == 'POST':
            # Atualizar configurações
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'Dados JSON não fornecidos'
                }), 400
            
            # Atualizar intervalo de sincronização se fornecido
            if 'sync_interval' in data:
                new_interval = data['sync_interval']
                
                if not isinstance(new_interval, int) or new_interval < 30:
                    return jsonify({
                        'status': 'error',
                        'message': 'Intervalo de sincronização deve ser um inteiro >= 30 segundos'
                    }), 400
                
                sync_service.sync_interval = new_interval
                logger.info(f"Intervalo de sincronização atualizado para {new_interval} segundos")
            
            return jsonify({
                'status': 'success',
                'message': 'Configurações atualizadas',
                'data': {
                    'sync_interval': sync_service.sync_interval,
                    'is_running': sync_service.is_running
                }
            })
        
    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@sync_bp.route('/health')
def sync_health():
    """Verifica saúde do serviço de sincronização"""
    try:
        if not sync_service:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Serviço de sincronização não inicializado'
            }), 500
        
        # Verificar conexões de banco
        operation_db_ok = False
        mlm_db_ok = False
        
        try:
            # Testar conexão com banco da operação
            with sync_service.operation_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                operation_db_ok = True
        except:
            pass
        
        try:
            # Testar conexão com banco MLM
            with sync_service.mlm_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                mlm_db_ok = True
        except:
            pass
        
        # Determinar status geral
        if operation_db_ok and mlm_db_ok and sync_service.is_running:
            overall_status = 'healthy'
        elif operation_db_ok and mlm_db_ok:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        return jsonify({
            'status': overall_status,
            'data': {
                'sync_service_running': sync_service.is_running,
                'operation_db_connected': operation_db_ok,
                'mlm_db_connected': mlm_db_ok,
                'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None,
                'sync_interval': sync_service.sync_interval
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no health check de sincronização: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

