# Sistema MLM Corrigido - Hierarquia Infinita com Total N1-N5
# sync_service_final.py

import psycopg2
import psycopg2.extras
import threading
import time
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class MLMSyncService:
    """Serviço MLM com hierarquia infinita e total limitado a N1-N5 por afiliado"""
    
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
                time.sleep(30)

    def sync_data(self):
        """Sincroniza dados do banco da operação para o banco MLM"""
        start_time = datetime.now()
        logger.info("Iniciando sincronização MLM com hierarquia infinita")
        
        try:
            # 1. Obter TODOS os dados tracked (614.944 registros)
            tracked_data = self.get_tracked_data()
            
            if not tracked_data:
                logger.info("Nenhum dado encontrado para sincronização")
                return
            
            logger.info(f"Processando {len(tracked_data)} registros de afiliação")
            
            # 2. Construir hierarquia INFINITA (todos os registros presentes)
            global_hierarchy = self.build_infinite_hierarchy(tracked_data)
            
            # 3. Calcular perspectivas individuais N1-N5 para cada afiliado
            individual_stats = self.calculate_individual_n1_to_n5_stats(global_hierarchy)
            
            # 4. Persistir dados
            records_updated = self.persist_hierarchy(global_hierarchy)
            stats_updated = self.persist_level_stats(individual_stats)
            
            # 5. Log
            self.log_sync_operation(
                sync_type='infinite_hierarchy_n1_to_n5',
                records_processed=len(tracked_data),
                records_updated=records_updated,
                records_inserted=stats_updated,
                status='completed'
            )
            
            self.last_sync = datetime.now()
            duration = (self.last_sync - start_time).total_seconds()
            
            logger.info(f"Sincronização concluída em {duration:.2f}s - {len(global_hierarchy)} afiliados processados")
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
            self.log_sync_operation(
                sync_type='infinite_hierarchy_n1_to_n5',
                status='failed',
                error_message=str(e)
            )
            raise

    def get_tracked_data(self):
        """Obtém TODOS os dados da tabela tracked"""
        try:
            with self.operation_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id,
                        user_afil as affiliate_id,
                        user_id as referred_user_id,
                        tracked_type_id,
                        created_at
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

    def build_infinite_hierarchy(self, tracked_data):
        """Constrói hierarquia INFINITA - TODOS os 614.944 registros devem estar presentes"""
        logger.info("Construindo hierarquia infinita com todos os registros")
        
        # Estruturas de dados
        relationships = defaultdict(list)  # affiliate_id -> [referred_users]
        user_to_affiliate = {}  # user_id -> affiliate_id
        all_affiliates = set()
        all_users = set()
        
        # Processar TODOS os dados tracked
        for record in tracked_data:
            affiliate_id = record['affiliate_id']
            referred_user_id = record['referred_user_id']
            
            relationships[affiliate_id].append(referred_user_id)
            user_to_affiliate[referred_user_id] = affiliate_id
            all_affiliates.add(affiliate_id)
            all_users.add(referred_user_id)
        
        # Identificar afiliados raiz
        referred_users = set(user_to_affiliate.keys())
        root_affiliates = all_affiliates - referred_users
        
        logger.info(f"Total de registros tracked: {len(tracked_data)}")
        logger.info(f"Afiliados únicos: {len(all_affiliates)}")
        logger.info(f"Usuários referidos únicos: {len(all_users)}")
        logger.info(f"Afiliados raiz: {len(root_affiliates)}")
        
        # Construir hierarquia global INFINITA
        global_hierarchy = {}
        
        # Processar afiliados raiz
        for root_affiliate in root_affiliates:
            self._build_infinite_recursive(
                affiliate_id=root_affiliate,
                relationships=relationships,
                user_to_affiliate=user_to_affiliate,
                hierarchy=global_hierarchy,
                global_level=1,
                path=str(root_affiliate),
                parent_id=None
            )
        
        # Processar afiliados que são também usuários referidos
        # SEM LIMITAÇÃO DE NÍVEL - hierarquia infinita
        for user_id, affiliate_id in user_to_affiliate.items():
            if user_id in relationships and user_id not in global_hierarchy:
                parent_data = global_hierarchy.get(affiliate_id, {})
                parent_level = parent_data.get('global_level', 0)
                parent_path = parent_data.get('path', str(affiliate_id))
                
                self._build_infinite_recursive(
                    affiliate_id=user_id,
                    relationships=relationships,
                    user_to_affiliate=user_to_affiliate,
                    hierarchy=global_hierarchy,
                    global_level=parent_level + 1,
                    path=f"{parent_path}.{user_id}",
                    parent_id=affiliate_id
                )
        
        logger.info(f"Hierarquia infinita construída: {len(global_hierarchy)} afiliados mapeados")
        
        # Verificar se todos os registros estão presentes
        total_relationships = sum(len(refs) for refs in relationships.values())
        logger.info(f"Total de relacionamentos mapeados: {total_relationships}")
        
        if total_relationships != len(tracked_data):
            logger.warning(f"Discrepância: {len(tracked_data)} registros vs {total_relationships} relacionamentos")
        
        return global_hierarchy

    def _build_infinite_recursive(self, affiliate_id, relationships, user_to_affiliate, hierarchy, global_level, path, parent_id):
        """Constrói hierarquia recursivamente SEM limitação de nível"""
        
        # Adicionar afiliado à hierarquia
        hierarchy[affiliate_id] = {
            'affiliate_id': affiliate_id,
            'parent_id': parent_id,
            'global_level': global_level,
            'path': path,
            'direct_referrals': len(relationships.get(affiliate_id, [])),
            'children': relationships.get(affiliate_id, []).copy(),
            'affiliate_children': []  # Apenas filhos que também são afiliados
        }
        
        # Processar referidos diretos
        for referred_user in relationships.get(affiliate_id, []):
            # Se o usuário referido também é um afiliado, processar recursivamente
            if referred_user in relationships:
                hierarchy[affiliate_id]['affiliate_children'].append(referred_user)
                
                # Continuar recursivamente SEM limitação de nível
                self._build_infinite_recursive(
                    affiliate_id=referred_user,
                    relationships=relationships,
                    user_to_affiliate=user_to_affiliate,
                    hierarchy=hierarchy,
                    global_level=global_level + 1,
                    path=f"{path}.{referred_user}",
                    parent_id=affiliate_id
                )

    def calculate_individual_n1_to_n5_stats(self, global_hierarchy):
        """Calcula estatísticas N1-N5 para cada afiliado (TOTAL = N1+N2+N3+N4+N5)"""
        logger.info("Calculando estatísticas individuais N1-N5")
        
        individual_stats = {}
        
        for affiliate_id in global_hierarchy.keys():
            stats = self._calculate_affiliate_n1_to_n5(affiliate_id, global_hierarchy)
            individual_stats[affiliate_id] = stats
        
        logger.info(f"Estatísticas calculadas para {len(individual_stats)} afiliados")
        return individual_stats

    def _calculate_affiliate_n1_to_n5(self, affiliate_id, global_hierarchy):
        """Calcula N1-N5 de um afiliado específico"""
        
        stats = {
            'affiliate_id': affiliate_id,
            'levels': {1: [], 2: [], 3: [], 4: [], 5: []},
            'level_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'total_n1_to_n5': 0,  # APENAS N1+N2+N3+N4+N5
            'beyond_n5': 0  # N6+ (não conta no total, mas existe)
        }
        
        def map_levels_recursive(current_id, relative_level, visited=None):
            if visited is None:
                visited = set()
            
            if current_id in visited:
                return  # Evitar loops
            visited.add(current_id)
            
            current_data = global_hierarchy.get(current_id, {})
            affiliate_children = current_data.get('affiliate_children', [])
            all_children = current_data.get('children', [])
            
            for child_id in all_children:
                if relative_level <= 5:
                    # Contar no nível apropriado (N1-N5)
                    if child_id in global_hierarchy:
                        # Filho que também é afiliado
                        stats['levels'][relative_level].append(child_id)
                    
                    stats['level_counts'][relative_level] += 1
                    stats['total_n1_to_n5'] += 1
                    
                    # Continuar para próximo nível se o filho é afiliado
                    if child_id in global_hierarchy:
                        map_levels_recursive(child_id, relative_level + 1, visited.copy())
                else:
                    # N6+ - não conta no total do afiliado pai
                    stats['beyond_n5'] += 1
                    
                    # Mas continuar mapeando para outros afiliados
                    if child_id in global_hierarchy:
                        map_levels_recursive(child_id, relative_level + 1, visited.copy())
        
        # Executar mapeamento
        map_levels_recursive(affiliate_id, 1)
        
        return stats

    def persist_hierarchy(self, global_hierarchy):
        """Persiste hierarquia infinita no banco"""
        try:
            with self.mlm_conn.cursor() as cursor:
                # Limpar dados existentes
                cursor.execute("DELETE FROM mlm_hierarchy")
                
                # Inserir hierarquia completa
                for affiliate_id, data in global_hierarchy.items():
                    cursor.execute("""
                        INSERT INTO mlm_hierarchy (
                            affiliate_id, parent_id, level, path, 
                            total_downline, direct_referrals, status, 
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        affiliate_id,
                        data.get('parent_id'),
                        data.get('global_level'),
                        data.get('path'),
                        len(data.get('children', [])),  # Total de filhos diretos
                        data.get('direct_referrals', 0),
                        'active',
                        datetime.now(),
                        datetime.now()
                    ))
                
                logger.info(f"Persistidos {len(global_hierarchy)} registros na hierarquia")
                return len(global_hierarchy)
                
        except Exception as e:
            logger.error(f"Erro ao persistir hierarquia: {e}")
            raise

    def persist_level_stats(self, individual_stats):
        """Persiste estatísticas N1-N5 por afiliado"""
        try:
            with self.mlm_conn.cursor() as cursor:
                # Limpar dados existentes
                cursor.execute("DELETE FROM mlm_levels")
                
                # Inserir estatísticas por nível
                count = 0
                for affiliate_id, stats in individual_stats.items():
                    # Inserir estatísticas para cada nível (N1-N5)
                    for level in range(1, 6):
                        level_count = stats['level_counts'].get(level, 0)
                        cursor.execute("""
                            INSERT INTO mlm_levels (
                                affiliate_id, level, direct_count, indirect_count,
                                total_volume, commission_rate, last_calculated
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            affiliate_id,
                            level,
                            level_count,
                            0,  # indirect_count pode ser calculado separadamente
                            0.0,  # total_volume baseado em transações
                            self._get_commission_rate(level),
                            datetime.now()
                        ))
                        count += 1
                    
                    # Inserir total geral (N1+N2+N3+N4+N5)
                    cursor.execute("""
                        INSERT INTO mlm_levels (
                            affiliate_id, level, direct_count, indirect_count,
                            total_volume, commission_rate, last_calculated
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        affiliate_id,
                        0,  # level 0 = total
                        stats['total_n1_to_n5'],
                        stats['beyond_n5'],  # N6+ vai para indirect_count
                        0.0,
                        0.0,
                        datetime.now()
                    ))
                    count += 1
                
                logger.info(f"Persistidas {count} estatísticas de níveis")
                return count
                
        except Exception as e:
            logger.error(f"Erro ao persistir estatísticas: {e}")
            raise

    def _get_commission_rate(self, level):
        """Taxa de comissão por nível"""
        rates = {1: 0.05, 2: 0.03, 3: 0.02, 4: 0.01, 5: 0.005}
        return rates.get(level, 0.0)

    def log_sync_operation(self, **kwargs):
        """Log de sincronização"""
        try:
            with self.mlm_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO mlm_sync_log (
                        sync_type, records_processed, records_updated, 
                        records_inserted, start_time, end_time, status, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    kwargs.get('sync_type', 'unknown'),
                    kwargs.get('records_processed', 0),
                    kwargs.get('records_updated', 0),
                    kwargs.get('records_inserted', 0),
                    datetime.now(),
                    datetime.now(),
                    kwargs.get('status', 'unknown'),
                    kwargs.get('error_message')
                ))
                
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

    def get_affiliate_total_indicacoes(self, affiliate_id):
        """Retorna total de indicações do afiliado (N1+N2+N3+N4+N5)"""
        try:
            with self.mlm_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT direct_count as total_n1_to_n5
                    FROM mlm_levels 
                    WHERE affiliate_id = %s AND level = 0
                """, (affiliate_id,))
                
                result = cursor.fetchone()
                return result['total_n1_to_n5'] if result else 0
                
        except Exception as e:
            logger.error(f"Erro ao obter total de indicações: {e}")
            return 0

    def get_affiliate_level_breakdown(self, affiliate_id):
        """Retorna breakdown por nível (N1, N2, N3, N4, N5)"""
        try:
            with self.mlm_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT level, direct_count
                    FROM mlm_levels 
                    WHERE affiliate_id = %s AND level BETWEEN 1 AND 5
                    ORDER BY level
                """, (affiliate_id,))
                
                results = cursor.fetchall()
                breakdown = {}
                for result in results:
                    breakdown[f"N{result['level']}"] = result['direct_count']
                
                return breakdown
                
        except Exception as e:
            logger.error(f"Erro ao obter breakdown por nível: {e}")
            return {}

# Exemplo de uso e teste
if __name__ == "__main__":
    # Configurações de teste
    operation_db_url = "postgresql://user:pass@host:port/operation_db"
    mlm_db_url = "postgresql://user:pass@host:port/mlm_db"
    
    # Inicializar serviço
    mlm_service = MLMSyncService(operation_db_url, mlm_db_url)
    
    # Executar sincronização
    mlm_service.sync_data()
    
    # Testar consultas
    affiliate_id = 839691
    total = mlm_service.get_affiliate_total_indicacoes(affiliate_id)
    breakdown = mlm_service.get_affiliate_level_breakdown(affiliate_id)
    
    print(f"Afiliado {affiliate_id}:")
    print(f"Total de indicações (N1-N5): {total}")
    print(f"Breakdown por nível: {breakdown}")
    print(f"Soma do breakdown: {sum(breakdown.values())}")
    print(f"Deve ser igual ao total: {total == sum(breakdown.values())}")

