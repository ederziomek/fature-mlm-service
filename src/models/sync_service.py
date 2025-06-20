import psycopg2
import psycopg2.extras
import threading
import time
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class MLMSyncService:
    """Serviço de sincronização entre banco da operação e banco MLM"""
    
    def __init__(self, operation_db_url, mlm_db_url, redis_url=None):
        self.operation_db_url = operation_db_url
        self.mlm_db_url = mlm_db_url
        self.redis_url = redis_url
        
        self.is_running = False
        self.last_sync = None
        self.sync_interval = 60  # segundos
        
        # Conexões de banco
        self.operation_conn = None
        self.mlm_conn = None
        
        # Cache para otimização
        self.hierarchy_cache = {}
        
        self.connect_databases()
    
    def connect_databases(self):
        """Conecta aos bancos de dados"""
        try:
            # Conexão com banco da operação
            self.operation_conn = psycopg2.connect(self.operation_db_url)
            self.operation_conn.autocommit = True
            logger.info("Conectado ao banco da operação")
            
            # Conexão com banco MLM
            self.mlm_conn = psycopg2.connect(self.mlm_db_url)
            self.mlm_conn.autocommit = True
            logger.info("Conectado ao banco MLM")
            
        except Exception as e:
            logger.error(f"Erro ao conectar bancos: {e}")
            raise
    
    def start_sync_worker(self):
        """Inicia worker de sincronização em background"""
        if not self.is_running:
            self.is_running = True
            worker_thread = threading.Thread(target=self._sync_worker)
            worker_thread.daemon = True
            worker_thread.start()
            logger.info("Worker de sincronização iniciado")
    
    def stop_sync_worker(self):
        """Para worker de sincronização"""
        self.is_running = False
        logger.info("Worker de sincronização parado")
    
    def _sync_worker(self):
        """Worker principal de sincronização"""
        while self.is_running:
            try:
                self.sync_data()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Erro na sincronização automática: {e}")
                time.sleep(30)  # Retry após 30 segundos em caso de erro
    
    def sync_data(self):
        """Sincroniza dados do banco da operação para o banco MLM"""
        start_time = datetime.now()
        logger.info("Iniciando sincronização de dados")
        
        try:
            # 1. Detectar mudanças no banco da operação
            tracked_data = self.get_tracked_data()
            
            if not tracked_data:
                logger.info("Nenhum dado encontrado para sincronização")
                return
            
            logger.info(f"Processando {len(tracked_data)} registros de afiliação")
            
            # 2. Construir hierarquia MLM
            hierarchy = self.build_mlm_hierarchy(tracked_data)
            
            # 3. Calcular estatísticas por nível
            level_stats = self.calculate_level_statistics(hierarchy)
            
            # 4. Persistir dados no banco MLM
            records_updated = self.persist_hierarchy(hierarchy)
            stats_updated = self.persist_level_stats(level_stats)
            
            # 5. Registrar log de sincronização
            self.log_sync_operation(
                sync_type='full_sync',
                records_processed=len(tracked_data),
                records_updated=records_updated,
                records_inserted=stats_updated,
                status='completed'
            )
            
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            
            logger.info(f"Sincronização concluída em {duration:.2f}s - {records_updated} hierarquias, {stats_updated} estatísticas")
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
            self.log_sync_operation(
                sync_type='full_sync',
                status='failed',
                error_message=str(e)
            )
            raise
    
    def get_tracked_data(self):
        """Obtém dados da tabela tracked do banco da operação"""
        try:
            with self.operation_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        id,
                        user_afil as affiliate_id,
                        user_id as referred_user_id,
                        tracked_type_id
                    FROM tracked 
                    WHERE tracked_type_id = 1 
                      AND user_afil IS NOT NULL 
                      AND user_id IS NOT NULL
                    ORDER BY user_afil, user_id;
                """)
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Erro ao buscar dados tracked: {e}")
            raise
    
    def build_mlm_hierarchy(self, tracked_data):
        """Constrói hierarquia MLM a partir dos dados tracked"""
        logger.info("Construindo hierarquia MLM")
        
        # Estrutura para armazenar relacionamentos
        relationships = defaultdict(list)  # affiliate_id -> [referred_users]
        user_to_affiliate = {}  # user_id -> affiliate_id
        
        # Processar dados tracked
        for record in tracked_data:
            affiliate_id = record['affiliate_id']
            referred_user_id = record['referred_user_id']
            
            relationships[affiliate_id].append(referred_user_id)
            user_to_affiliate[referred_user_id] = affiliate_id
        
        # Construir hierarquia com níveis
        hierarchy = {}
        
        # Identificar afiliados raiz (que não são referidos por ninguém)
        all_affiliates = set(relationships.keys())
        referred_users = set(user_to_affiliate.keys())
        root_affiliates = all_affiliates - referred_users
        
        logger.info(f"Encontrados {len(root_affiliates)} afiliados raiz")
        
        # Processar cada afiliado raiz
        for root_affiliate in root_affiliates:
            self._build_hierarchy_recursive(
                affiliate_id=root_affiliate,
                relationships=relationships,
                user_to_affiliate=user_to_affiliate,
                hierarchy=hierarchy,
                level=1,
                path=str(root_affiliate),
                parent_id=None
            )
        
        # Processar afiliados que são também usuários referidos
        for user_id, affiliate_id in user_to_affiliate.items():
            if user_id in relationships:  # Este usuário também é um afiliado
                if user_id not in hierarchy:
                    parent_affiliate = affiliate_id
                    parent_level = hierarchy.get(parent_affiliate, {}).get('level', 0)
                    
                    if parent_level < 5:  # Máximo 5 níveis
                        parent_path = hierarchy.get(parent_affiliate, {}).get('path', str(parent_affiliate))
                        
                        self._build_hierarchy_recursive(
                            affiliate_id=user_id,
                            relationships=relationships,
                            user_to_affiliate=user_to_affiliate,
                            hierarchy=hierarchy,
                            level=parent_level + 1,
                            path=f"{parent_path}.{user_id}",
                            parent_id=parent_affiliate
                        )
        
        logger.info(f"Hierarquia construída com {len(hierarchy)} afiliados")
        return hierarchy
    
    def _build_hierarchy_recursive(self, affiliate_id, relationships, user_to_affiliate, hierarchy, level, path, parent_id, max_level=5):
        """Constrói hierarquia recursivamente"""
        if level > max_level or affiliate_id in hierarchy:
            return
        
        # Adicionar afiliado à hierarquia
        hierarchy[affiliate_id] = {
            'affiliate_id': affiliate_id,
            'parent_id': parent_id,
            'level': level,
            'path': path,
            'direct_referrals': len(relationships.get(affiliate_id, [])),
            'children': []
        }
        
        # Processar referidos diretos
        for referred_user in relationships.get(affiliate_id, []):
            hierarchy[affiliate_id]['children'].append(referred_user)
            
            # Se o usuário referido também é um afiliado, processar recursivamente
            if referred_user in relationships and level < max_level:
                self._build_hierarchy_recursive(
                    affiliate_id=referred_user,
                    relationships=relationships,
                    user_to_affiliate=user_to_affiliate,
                    hierarchy=hierarchy,
                    level=level + 1,
                    path=f"{path}.{referred_user}",
                    parent_id=affiliate_id,
                    max_level=max_level
                )
    
    def calculate_level_statistics(self, hierarchy):
        """Calcula estatísticas por nível para cada afiliado"""
        logger.info("Calculando estatísticas por nível")
        
        level_stats = {}
        
        for affiliate_id, data in hierarchy.items():
            affiliate_stats = {}
            
            # Calcular estatísticas para cada nível (1-5)
            for level in range(1, 6):
                direct_count = 0
                indirect_count = 0
                
                if level == 1:
                    # Nível 1: referidos diretos
                    direct_count = data['direct_referrals']
                else:
                    # Níveis 2-5: contar descendentes no nível específico
                    descendants = self._get_descendants_at_level(affiliate_id, level, hierarchy)
                    indirect_count = len(descendants)
                
                if direct_count > 0 or indirect_count > 0:
                    affiliate_stats[level] = {
                        'affiliate_id': affiliate_id,
                        'level': level,
                        'direct_count': direct_count,
                        'indirect_count': indirect_count,
                        'total_volume': 0.0,  # Será calculado posteriormente com dados de transações
                        'commission_rate': self._get_commission_rate(level)
                    }
            
            if affiliate_stats:
                level_stats[affiliate_id] = affiliate_stats
        
        logger.info(f"Estatísticas calculadas para {len(level_stats)} afiliados")
        return level_stats
    
    def _get_descendants_at_level(self, affiliate_id, target_level, hierarchy, current_level=1):
        """Obtém descendentes em um nível específico"""
        descendants = []
        
        if current_level == target_level:
            return [affiliate_id]
        
        if current_level < target_level and affiliate_id in hierarchy:
            for child_id in hierarchy[affiliate_id]['children']:
                if child_id in hierarchy:
                    descendants.extend(
                        self._get_descendants_at_level(child_id, target_level, hierarchy, current_level + 1)
                    )
        
        return descendants
    
    def _get_commission_rate(self, level):
        """Obtém taxa de comissão para um nível"""
        commission_rates = {
            1: 0.10,  # 10% para nível 1
            2: 0.05,  # 5% para nível 2
            3: 0.03,  # 3% para nível 3
            4: 0.02,  # 2% para nível 4
            5: 0.01   # 1% para nível 5
        }
        return commission_rates.get(level, 0.0)
    
    def persist_hierarchy(self, hierarchy):
        """Persiste hierarquia no banco MLM"""
        logger.info("Persistindo hierarquia no banco MLM")
        
        records_updated = 0
        
        try:
            with self.mlm_conn.cursor() as cursor:
                for affiliate_id, data in hierarchy.items():
                    cursor.execute("""
                        INSERT INTO mlm_hierarchy (affiliate_id, parent_id, level, path, direct_referrals)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (affiliate_id) 
                        DO UPDATE SET 
                            parent_id = EXCLUDED.parent_id,
                            level = EXCLUDED.level,
                            path = EXCLUDED.path,
                            direct_referrals = EXCLUDED.direct_referrals,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        data['affiliate_id'],
                        data['parent_id'],
                        data['level'],
                        data['path'],
                        data['direct_referrals']
                    ))
                    
                    records_updated += 1
            
            logger.info(f"Hierarquia persistida: {records_updated} registros")
            return records_updated
            
        except Exception as e:
            logger.error(f"Erro ao persistir hierarquia: {e}")
            raise
    
    def persist_level_stats(self, level_stats):
        """Persiste estatísticas de nível no banco MLM"""
        logger.info("Persistindo estatísticas de nível")
        
        stats_updated = 0
        
        try:
            with self.mlm_conn.cursor() as cursor:
                for affiliate_id, affiliate_stats in level_stats.items():
                    for level, stats in affiliate_stats.items():
                        cursor.execute("""
                            INSERT INTO mlm_levels 
                            (affiliate_id, level, direct_count, indirect_count, total_volume, commission_rate)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (affiliate_id, level)
                            DO UPDATE SET 
                                direct_count = EXCLUDED.direct_count,
                                indirect_count = EXCLUDED.indirect_count,
                                total_volume = EXCLUDED.total_volume,
                                commission_rate = EXCLUDED.commission_rate,
                                last_calculated = CURRENT_TIMESTAMP;
                        """, (
                            stats['affiliate_id'],
                            stats['level'],
                            stats['direct_count'],
                            stats['indirect_count'],
                            stats['total_volume'],
                            stats['commission_rate']
                        ))
                        
                        stats_updated += 1
            
            logger.info(f"Estatísticas persistidas: {stats_updated} registros")
            return stats_updated
            
        except Exception as e:
            logger.error(f"Erro ao persistir estatísticas: {e}")
            raise
    
    def log_sync_operation(self, sync_type, records_processed=0, records_updated=0, records_inserted=0, status='completed', error_message=None):
        """Registra operação de sincronização"""
        try:
            with self.mlm_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO mlm_sync_log 
                    (sync_type, records_processed, records_updated, records_inserted, end_time, status, error_message)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s);
                """, (sync_type, records_processed, records_updated, records_inserted, status, error_message))
                
        except Exception as e:
            logger.error(f"Erro ao registrar log de sincronização: {e}")
    
    def get_sync_status(self):
        """Obtém status das sincronizações"""
        try:
            with self.mlm_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sync_type,
                        records_processed,
                        records_updated,
                        records_inserted,
                        start_time,
                        end_time,
                        status,
                        error_message
                    FROM mlm_sync_log 
                    ORDER BY start_time DESC 
                    LIMIT 10;
                """)
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Erro ao buscar status de sincronização: {e}")
            return []
    
    def close_connections(self):
        """Fecha conexões com bancos de dados"""
        if self.operation_conn and not self.operation_conn.closed:
            self.operation_conn.close()
            logger.info("Conexão com banco da operação fechada")
        
        if self.mlm_conn and not self.mlm_conn.closed:
            self.mlm_conn.close()
            logger.info("Conexão com banco MLM fechada")

