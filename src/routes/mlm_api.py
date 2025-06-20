from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Criar blueprint
mlm_bp = Blueprint('mlm', __name__, url_prefix='/api/v1/mlm')

# Variáveis globais para serviços
mlm_db = None
sync_service = None

def init_mlm_routes(mlm_database, sync_svc):
    """Inicializa as rotas MLM com as dependências"""
    global mlm_db, sync_service
    mlm_db = mlm_database
    sync_service = sync_svc
    logger.info("Rotas MLM inicializadas")

@mlm_bp.route('/health')
def health_check():
    """Health check do serviço MLM"""
    try:
        status = {
            'status': 'healthy',
            'service': 'fature-mlm-service',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'mlm_database': 'connected' if mlm_db else 'disconnected',
                'sync_service': 'active' if sync_service else 'inactive'
            }
        }
        
        if sync_service and sync_service.last_sync:
            status['last_sync'] = sync_service.last_sync.isoformat()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@mlm_bp.route('/hierarchy/<int:affiliate_id>')
def get_hierarchy(affiliate_id):
    """Retorna hierarquia MLM de um afiliado"""
    try:
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # Buscar hierarquia do afiliado
        hierarchy = mlm_db.get_affiliate_hierarchy(affiliate_id)
        
        if not hierarchy:
            return jsonify({
                'status': 'success',
                'data': {
                    'affiliate_id': affiliate_id,
                    'hierarchy': [],
                    'total_downline': 0
                },
                'message': 'Nenhuma hierarquia encontrada para este afiliado'
            })
        
        # Processar dados da hierarquia
        hierarchy_data = []
        total_downline = 0
        
        for record in hierarchy:
            level_data = {
                'level': record['level'],
                'affiliate_id': record['downline_affiliate_id'],
                'user_id': record['user_id'],
                'parent_affiliate_id': record['parent_affiliate_id'],
                'depth': record['depth'],
                'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
            }
            hierarchy_data.append(level_data)
            total_downline += 1
        
        return jsonify({
            'status': 'success',
            'data': {
                'affiliate_id': affiliate_id,
                'hierarchy': hierarchy_data,
                'total_downline': total_downline,
                'levels_count': len(set(record['level'] for record in hierarchy))
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar hierarquia para {affiliate_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@mlm_bp.route('/stats/<int:affiliate_id>')
def get_affiliate_stats(affiliate_id):
    """Retorna estatísticas de um afiliado"""
    try:
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # Buscar estatísticas do afiliado
        stats = mlm_db.calculate_affiliate_stats(affiliate_id)
        
        if not stats:
            return jsonify({
                'status': 'success',
                'data': {
                    'affiliate_id': affiliate_id,
                    'levels': [],
                    'summary': {
                        'total_downline': 0,
                        'total_volume': 0,
                        'total_commissions': 0,
                        'active_levels': 0
                    }
                },
                'message': 'Nenhuma estatística encontrada para este afiliado'
            })
        
        # Processar estatísticas por nível
        levels_data = []
        total_downline = 0
        total_volume = 0
        total_commissions = 0
        
        for record in stats:
            level_data = {
                'level': record['level'],
                'direct_count': record['direct_count'] or 0,
                'indirect_count': record['indirect_count'] or 0,
                'total_count': (record['direct_count'] or 0) + (record['indirect_count'] or 0),
                'total_volume': float(record['total_volume'] or 0),
                'commission_rate': float(record['commission_rate'] or 0),
                'commission_earned': float(record['commission_earned'] or 0),
                'last_calculated': record['last_calculated'].isoformat() if record['last_calculated'] else None
            }
            
            levels_data.append(level_data)
            total_downline += level_data['total_count']
            total_volume += level_data['total_volume']
            total_commissions += level_data['commission_earned']
        
        return jsonify({
            'status': 'success',
            'data': {
                'affiliate_id': affiliate_id,
                'levels': levels_data,
                'summary': {
                    'total_downline': total_downline,
                    'total_volume': total_volume,
                    'total_commissions': total_commissions,
                    'active_levels': len(levels_data)
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas para {affiliate_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@mlm_bp.route('/commissions/<int:affiliate_id>')
def get_commissions(affiliate_id):
    """Retorna comissões de um afiliado"""
    try:
        # Parâmetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        level = request.args.get('level', type=int)
        status = request.args.get('status', 'all')
        
        # TODO: Implementar consulta de comissões
        # Por enquanto, retornar dados mock
        
        return jsonify({
            'status': 'success',
            'data': {
                'affiliate_id': affiliate_id,
                'commissions': [],
                'summary': {
                    'total_amount': 0,
                    'pending_amount': 0,
                    'paid_amount': 0,
                    'total_transactions': 0
                },
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'level': level,
                    'status': status
                }
            },
            'message': 'Funcionalidade de comissões em desenvolvimento',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar comissões para {affiliate_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@mlm_bp.route('/summary')
def get_summary():
    """Retorna resumo geral do sistema MLM"""
    try:
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # TODO: Implementar consulta de resumo geral
        # Por enquanto, retornar dados básicos
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_affiliates': 0,
                'total_levels': 5,
                'total_volume': 0,
                'total_commissions': 0,
                'active_affiliates': 0,
                'last_sync': sync_service.last_sync.isoformat() if sync_service and sync_service.last_sync else None
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar resumo MLM: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

@mlm_bp.route('/levels/<int:affiliate_id>/<int:level>')
def get_level_details(affiliate_id, level):
    """Retorna detalhes de um nível específico"""
    try:
        if level < 1 or level > 5:
            return jsonify({
                'status': 'error',
                'message': 'Nível deve estar entre 1 e 5'
            }), 400
        
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # Buscar dados do nível específico
        stats = mlm_db.calculate_affiliate_stats(affiliate_id)
        level_data = None
        
        for stat in stats:
            if stat['level'] == level:
                level_data = {
                    'affiliate_id': affiliate_id,
                    'level': stat['level'],
                    'direct_count': stat['direct_count'] or 0,
                    'indirect_count': stat['indirect_count'] or 0,
                    'total_count': (stat['direct_count'] or 0) + (stat['indirect_count'] or 0),
                    'total_volume': float(stat['total_volume'] or 0),
                    'commission_rate': float(stat['commission_rate'] or 0),
                    'commission_earned': float(stat['commission_earned'] or 0),
                    'last_calculated': stat['last_calculated'].isoformat() if stat['last_calculated'] else None
                }
                break
        
        if not level_data:
            return jsonify({
                'status': 'success',
                'data': None,
                'message': f'Nenhum dado encontrado para o nível {level}'
            })
        
        return jsonify({
            'status': 'success',
            'data': level_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do nível {level} para {affiliate_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500

