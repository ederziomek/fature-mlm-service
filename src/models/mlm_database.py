import psycopg2
import psycopg2.extras
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MLMDatabase:
    """Classe para gerenciar conexões e operações do banco MLM"""
    
    def __init__(self, db_url):
        self.db_url = db_url
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Estabelece conexão com o banco MLM"""
        try:
            self.connection = psycopg2.connect(self.db_url)
            self.connection.autocommit = True
            logger.info("Conexão com banco MLM estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar com banco MLM: {e}")
            raise
    
    def check_connection(self):
        """Verifica se a conexão está ativa"""
        try:
            if self.connection.closed:
                self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Erro na verificação de conexão: {e}")
            return False
    
    def create_tables(self):
        """Cria tabelas do banco MLM se não existirem"""
        try:
            with self.connection.cursor() as cursor:
                # Tabela de hierarquia MLM
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mlm_hierarchy (
                        id SERIAL PRIMARY KEY,
                        affiliate_id INTEGER NOT NULL,
                        parent_id INTEGER,
                        level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
                        path TEXT NOT NULL,
                        total_downline INTEGER DEFAULT 0,
                        direct_referrals INTEGER DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        CONSTRAINT unique_affiliate UNIQUE (affiliate_id)
                    );
                """)
                
                # Tabela de níveis MLM
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mlm_levels (
                        id SERIAL PRIMARY KEY,
                        affiliate_id INTEGER NOT NULL,
                        level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
                        direct_count INTEGER DEFAULT 0,
                        indirect_count INTEGER DEFAULT 0,
                        total_volume DECIMAL(15,2) DEFAULT 0.00,
                        commission_rate DECIMAL(5,4) DEFAULT 0.0000,
                        commission_earned DECIMAL(15,2) DEFAULT 0.00,
                        last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        CONSTRAINT unique_affiliate_level UNIQUE (affiliate_id, level)
                    );
                """)
                
                # Tabela de comissões MLM
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mlm_commissions (
                        id SERIAL PRIMARY KEY,
                        transaction_id VARCHAR(100),
                        affiliate_id INTEGER NOT NULL,
                        level INTEGER NOT NULL,
                        commission_amount DECIMAL(15,2) NOT NULL,
                        commission_rate DECIMAL(5,4) NOT NULL,
                        base_amount DECIMAL(15,2) NOT NULL,
                        calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payment_status VARCHAR(20) DEFAULT 'pending',
                        payment_date TIMESTAMP
                    );
                """)
                
                # Tabela de sincronização
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mlm_sync_log (
                        id SERIAL PRIMARY KEY,
                        sync_type VARCHAR(50) NOT NULL,
                        records_processed INTEGER DEFAULT 0,
                        records_updated INTEGER DEFAULT 0,
                        records_inserted INTEGER DEFAULT 0,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'running',
                        error_message TEXT
                    );
                """)
                
                # Criar índices
                self.create_indexes()
                
                logger.info("Tabelas MLM criadas/verificadas com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
    
    def create_indexes(self):
        """Cria índices para otimização de performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_mlm_hierarchy_parent ON mlm_hierarchy(parent_id);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_hierarchy_level ON mlm_hierarchy(level);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_hierarchy_path ON mlm_hierarchy USING GIN (string_to_array(path, '.'));",
            "CREATE INDEX IF NOT EXISTS idx_mlm_levels_affiliate ON mlm_levels(affiliate_id);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_levels_level ON mlm_levels(level);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_commissions_affiliate ON mlm_commissions(affiliate_id);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_commissions_date ON mlm_commissions(calculation_date);",
            "CREATE INDEX IF NOT EXISTS idx_mlm_sync_log_date ON mlm_sync_log(start_time);"
        ]
        
        with self.connection.cursor() as cursor:
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
    
    def get_affiliate_hierarchy(self, affiliate_id, max_level=5):
        """Obtém hierarquia completa de um afiliado"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    WITH RECURSIVE affiliate_tree AS (
                        -- Caso base: afiliado raiz
                        SELECT 
                            affiliate_id,
                            parent_id,
                            level,
                            path,
                            1 as depth
                        FROM mlm_hierarchy 
                        WHERE affiliate_id = %s
                        
                        UNION ALL
                        
                        -- Recursão: descendentes
                        SELECT 
                            h.affiliate_id,
                            h.parent_id,
                            h.level,
                            h.path,
                            at.depth + 1
                        FROM mlm_hierarchy h
                        INNER JOIN affiliate_tree at ON h.parent_id = at.affiliate_id
                        WHERE at.depth < %s
                    )
                    SELECT 
                        at.*,
                        l.direct_count,
                        l.indirect_count,
                        l.total_volume,
                        l.commission_earned
                    FROM affiliate_tree at
                    LEFT JOIN mlm_levels l ON at.affiliate_id = l.affiliate_id 
                        AND l.level = at.depth
                    ORDER BY at.depth, at.affiliate_id;
                """, (affiliate_id, max_level))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Erro ao buscar hierarquia: {e}")
            raise
    
    def calculate_affiliate_stats(self, affiliate_id):
        """Calcula estatísticas MLM para um afiliado"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        level,
                        direct_count,
                        indirect_count,
                        total_volume,
                        commission_rate,
                        commission_earned,
                        last_calculated
                    FROM mlm_levels 
                    WHERE affiliate_id = %s
                    ORDER BY level;
                """, (affiliate_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            raise
    
    def insert_hierarchy_record(self, affiliate_id, parent_id, level, path):
        """Insere registro na hierarquia MLM"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO mlm_hierarchy (affiliate_id, parent_id, level, path)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (affiliate_id) 
                    DO UPDATE SET 
                        parent_id = EXCLUDED.parent_id,
                        level = EXCLUDED.level,
                        path = EXCLUDED.path,
                        updated_at = CURRENT_TIMESTAMP;
                """, (affiliate_id, parent_id, level, path))
                
        except Exception as e:
            logger.error(f"Erro ao inserir hierarquia: {e}")
            raise
    
    def update_level_stats(self, affiliate_id, level, direct_count, indirect_count, total_volume=0):
        """Atualiza estatísticas de nível"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO mlm_levels (affiliate_id, level, direct_count, indirect_count, total_volume)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (affiliate_id, level)
                    DO UPDATE SET 
                        direct_count = EXCLUDED.direct_count,
                        indirect_count = EXCLUDED.indirect_count,
                        total_volume = EXCLUDED.total_volume,
                        last_calculated = CURRENT_TIMESTAMP;
                """, (affiliate_id, level, direct_count, indirect_count, total_volume))
                
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}")
            raise
    
    def log_sync_operation(self, sync_type, records_processed=0, records_updated=0, records_inserted=0, status='completed', error_message=None):
        """Registra operação de sincronização"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO mlm_sync_log 
                    (sync_type, records_processed, records_updated, records_inserted, end_time, status, error_message)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s);
                """, (sync_type, records_processed, records_updated, records_inserted, status, error_message))
                
        except Exception as e:
            logger.error(f"Erro ao registrar log de sincronização: {e}")
    
    def get_sync_status(self):
        """Obtém status das últimas sincronizações"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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
    
    def close(self):
        """Fecha conexão com o banco"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Conexão com banco MLM fechada")

