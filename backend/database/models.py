"""
Modelos de Base de Datos SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """Gestor de base de datos SQLite"""

    def __init__(self, db_path: str = 'data/database.db'):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return conn

    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Tabla de generaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    target_length INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    strategy_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    seo_score REAL NOT NULL,
                    ctr REAL NOT NULL,
                    time_on_page REAL NOT NULL,
                    search_position REAL NOT NULL,
                    bounce_rate REAL NOT NULL,
                    reward REAL NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    generation_time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Índices para búsquedas rápidas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON generations(created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategy
                ON generations(strategy_id)
            """)

            conn.commit()
            conn.close()

            logger.info(f"Database initialized successfully at {self.db_path}")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_generation(self, generation: Dict) -> bool:
        """
        Guarda una generación en la base de datos

        Args:
            generation: Dict con los datos de la generación

        Returns:
            True si se guardó correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO generations (
                    id, topic, keywords, target_length, strategy_id, strategy_name,
                    content, seo_score, ctr, time_on_page, search_position,
                    bounce_rate, reward, tokens_used, generation_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                generation['id'],
                generation['topic'],
                json.dumps(generation['keywords']),
                generation.get('target_length', 600),
                generation['strategy_id'],
                generation['strategy_name'],
                generation['content'],
                generation['seo_score'],
                generation['engagement_metrics']['ctr'],
                generation['engagement_metrics']['time_on_page'],
                generation['engagement_metrics']['search_position'],
                generation['engagement_metrics']['bounce_rate'],
                generation['reward'],
                generation['tokens_used'],
                generation['generation_time'],
                generation['timestamp']
            ))

            conn.commit()
            conn.close()

            logger.info(f"Generation {generation['id']} saved to database")
            return True

        except Exception as e:
            logger.error(f"Error saving generation to database: {e}")
            return False

    def get_all_generations(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Obtiene todas las generaciones de la base de datos

        Args:
            limit: Número máximo de resultados
            offset: Offset para paginación

        Returns:
            Lista de generaciones
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generations
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            rows = cursor.fetchall()
            conn.close()

            generations = []
            for row in rows:
                generations.append({
                    'id': row['id'],
                    'topic': row['topic'],
                    'keywords': json.loads(row['keywords']),
                    'target_length': row['target_length'],
                    'strategy_id': row['strategy_id'],
                    'strategy_name': row['strategy_name'],
                    'content': row['content'],
                    'seo_score': row['seo_score'],
                    'engagement_metrics': {
                        'ctr': row['ctr'],
                        'time_on_page': row['time_on_page'],
                        'search_position': row['search_position'],
                        'bounce_rate': row['bounce_rate']
                    },
                    'reward': row['reward'],
                    'tokens_used': row['tokens_used'],
                    'generation_time': row['generation_time'],
                    'timestamp': row['created_at']
                })

            return generations

        except Exception as e:
            logger.error(f"Error getting generations from database: {e}")
            return []

    def get_generation_by_id(self, generation_id: str) -> Optional[Dict]:
        """
        Obtiene una generación específica por ID

        Args:
            generation_id: ID de la generación

        Returns:
            Dict con la generación o None si no existe
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM generations WHERE id = ?
            """, (generation_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                'id': row['id'],
                'topic': row['topic'],
                'keywords': json.loads(row['keywords']),
                'target_length': row['target_length'],
                'strategy_id': row['strategy_id'],
                'strategy_name': row['strategy_name'],
                'content': row['content'],
                'seo_score': row['seo_score'],
                'engagement_metrics': {
                    'ctr': row['ctr'],
                    'time_on_page': row['time_on_page'],
                    'search_position': row['search_position'],
                    'bounce_rate': row['bounce_rate']
                },
                'reward': row['reward'],
                'tokens_used': row['tokens_used'],
                'generation_time': row['generation_time'],
                'timestamp': row['created_at']
            }

        except Exception as e:
            logger.error(f"Error getting generation by ID: {e}")
            return None

    def get_total_count(self) -> int:
        """Obtiene el total de generaciones en la base de datos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM generations")
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 0

    def get_stats_by_strategy(self) -> Dict:
        """Obtiene estadísticas por estrategia"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    strategy_id,
                    strategy_name,
                    COUNT(*) as count,
                    AVG(seo_score) as avg_seo,
                    AVG(reward) as avg_reward
                FROM generations
                GROUP BY strategy_id
                ORDER BY avg_reward DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            stats = {}
            for row in rows:
                stats[row['strategy_id']] = {
                    'name': row['strategy_name'],
                    'count': row['count'],
                    'avg_seo': round(row['avg_seo'], 2),
                    'avg_reward': round(row['avg_reward'], 4)
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting stats by strategy: {e}")
            return {}
