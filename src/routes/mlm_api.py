from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

mlm_bp = Blueprint('mlm', __name__)

# Será inicializado no main.py
mlm_db = None
sync_service = None

def init_mlm_services(db_instance, sync_instance):
    """Inicializa instâncias dos serviços MLM"""
    global mlm_db, sync_service
    mlm_db = db_instance
    sync_service = sync_instance

@mlm_bp.route('/hierarchy/<int:affiliate_id>')
def get_hierarchy(affiliate_id):
    """Retorna hierarquia completa de um afiliado"""
    try:
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # Buscar hierarquia do banco
        hierarchy = mlm_db.get_affiliate_hierarchy(affiliate_id)
        
        if not hierarchy:
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'Nenhuma hierarquia encontrada para este afiliado'
            })
        
        # Organizar dados por nível
        levels_data = {}
        for record in hierarchy:
            level = record['depth']
            if level not in levels_data:
                levels_data[level] = []
            
            levels_data[level].append({
                'affiliate_id': record['affiliate_id'],
                'parent_id': record['parent_id'],
                'level': record['level'],
                'path': record['path'],
                'direct_count': record['direct_count'] or 0,
                'indirect_count': record['indirect_count'] or 0,
                'total_volume': float(record['total_volume'] or 0),
                'commission_earned': float(record['commission_earned'] or 0)
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'affiliate_id': affiliate_id,
                'levels': levels_data,
                'total_levels': len(levels_data),
                'total_downline': sum(len(affiliates) for affiliates in levels_data.values()) - 1  # Excluir o próprio afiliado
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
def get_stats(affiliate_id):
    """Retorna estatísticas MLM de um afiliado"""
    try:
        if not mlm_db:
            return jsonify({
                'status': 'error',
                'message': 'Serviço MLM não inicializado'
            }), 500
        
        # Buscar estatísticas do banco
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
        
        # Organizar dados por nível
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
            }\n            \n            levels_data.append(level_data)\n            total_downline += level_data['total_count']\n            total_volume += level_data['total_volume']\n            total_commissions += level_data['commission_earned']\n        \n        return jsonify({\n            'status': 'success',\n            'data': {\n                'affiliate_id': affiliate_id,\n                'levels': levels_data,\n                'summary': {\n                    'total_downline': total_downline,\n                    'total_volume': total_volume,\n                    'total_commissions': total_commissions,\n                    'active_levels': len(levels_data)\n                }\n            },\n            'timestamp': datetime.now().isoformat()\n        })\n        \n    except Exception as e:\n        logger.error(f\"Erro ao buscar estatísticas para {affiliate_id}: {e}\")\n        return jsonify({\n            'status': 'error',\n            'message': 'Erro interno do servidor',\n            'error': str(e)\n        }), 500\n\n@mlm_bp.route('/commissions/<int:affiliate_id>')\ndef get_commissions(affiliate_id):\n    \"\"\"Retorna comissões de um afiliado\"\"\"\n    try:\n        # Parâmetros de consulta\n        start_date = request.args.get('start_date')\n        end_date = request.args.get('end_date')\n        level = request.args.get('level', type=int)\n        status = request.args.get('status', 'all')\n        \n        # TODO: Implementar consulta de comissões\n        # Por enquanto, retornar dados mock\n        \n        return jsonify({\n            'status': 'success',\n            'data': {\n                'affiliate_id': affiliate_id,\n                'commissions': [],\n                'summary': {\n                    'total_amount': 0,\n                    'pending_amount': 0,\n                    'paid_amount': 0,\n                    'total_transactions': 0\n                },\n                'filters': {\n                    'start_date': start_date,\n                    'end_date': end_date,\n                    'level': level,\n                    'status': status\n                }\n            },\n            'message': 'Funcionalidade de comissões em desenvolvimento',\n            'timestamp': datetime.now().isoformat()\n        })\n        \n    except Exception as e:\n        logger.error(f\"Erro ao buscar comissões para {affiliate_id}: {e}\")\n        return jsonify({\n            'status': 'error',\n            'message': 'Erro interno do servidor',\n            'error': str(e)\n        }), 500\n\n@mlm_bp.route('/summary')\ndef get_summary():\n    \"\"\"Retorna resumo geral do sistema MLM\"\"\"\n    try:\n        if not mlm_db:\n            return jsonify({\n                'status': 'error',\n                'message': 'Serviço MLM não inicializado'\n            }), 500\n        \n        # TODO: Implementar consulta de resumo geral\n        # Por enquanto, retornar dados básicos\n        \n        return jsonify({\n            'status': 'success',\n            'data': {\n                'total_affiliates': 0,\n                'total_levels': 5,\n                'total_volume': 0,\n                'total_commissions': 0,\n                'active_affiliates': 0,\n                'last_sync': sync_service.last_sync.isoformat() if sync_service and sync_service.last_sync else None\n            },\n            'timestamp': datetime.now().isoformat()\n        })\n        \n    except Exception as e:\n        logger.error(f\"Erro ao buscar resumo MLM: {e}\")\n        return jsonify({\n            'status': 'error',\n            'message': 'Erro interno do servidor',\n            'error': str(e)\n        }), 500\n\n@mlm_bp.route('/levels/<int:affiliate_id>/<int:level>')\ndef get_level_details(affiliate_id, level):\n    \"\"\"Retorna detalhes de um nível específico\"\"\"\n    try:\n        if level < 1 or level > 5:\n            return jsonify({\n                'status': 'error',\n                'message': 'Nível deve estar entre 1 e 5'\n            }), 400\n        \n        if not mlm_db:\n            return jsonify({\n                'status': 'error',\n                'message': 'Serviço MLM não inicializado'\n            }), 500\n        \n        # Buscar dados do nível específico\n        stats = mlm_db.calculate_affiliate_stats(affiliate_id)\n        level_data = None\n        \n        for stat in stats:\n            if stat['level'] == level:\n                level_data = {\n                    'affiliate_id': affiliate_id,\n                    'level': stat['level'],\n                    'direct_count': stat['direct_count'] or 0,\n                    'indirect_count': stat['indirect_count'] or 0,\n                    'total_count': (stat['direct_count'] or 0) + (stat['indirect_count'] or 0),\n                    'total_volume': float(stat['total_volume'] or 0),\n                    'commission_rate': float(stat['commission_rate'] or 0),\n                    'commission_earned': float(stat['commission_earned'] or 0),\n                    'last_calculated': stat['last_calculated'].isoformat() if stat['last_calculated'] else None\n                }\n                break\n        \n        if not level_data:\n            return jsonify({\n                'status': 'success',\n                'data': None,\n                'message': f'Nenhum dado encontrado para o nível {level}'\n            })\n        \n        return jsonify({\n            'status': 'success',\n            'data': level_data,\n            'timestamp': datetime.now().isoformat()\n        })\n        \n    except Exception as e:\n        logger.error(f\"Erro ao buscar detalhes do nível {level} para {affiliate_id}: {e}\")\n        return jsonify({\n            'status': 'error',\n            'message': 'Erro interno do servidor',\n            'error': str(e)\n        }), 500

