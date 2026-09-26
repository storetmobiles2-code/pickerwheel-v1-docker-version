"""
PickerWheel Database Module
PostgreSQL connection pool and session management
"""

import json
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Global database engine and session factory
engine = None
Session = None


def init_db(app):
    """Initialize database connection pool"""
    global engine, Session
    
    database_url = app.config['DATABASE_URL']
    pool_size = app.config.get('DB_POOL_SIZE', 10)
    max_overflow = app.config.get('DB_MAX_OVERFLOW', 20)
    pool_timeout = app.config.get('DB_POOL_TIMEOUT', 30)
    
    logger.info(f"Initializing database connection to {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True,  # Enable connection health checks
        echo=app.config.get('DEBUG', False)
    )
    
    # Create scoped session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    logger.info("Database connection pool initialized successfully")
    
    return engine


def get_session():
    """Get a database session"""
    if Session is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return Session()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        session.close()


def execute_sql(sql, params=None):
    """Execute raw SQL and return results"""
    with session_scope() as session:
        result = session.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return None


def execute_transaction(operations):
    """
    Execute several (sql, params) statements in a single transaction.
    All statements commit together or none do - use this instead of
    multiple execute_sql() calls whenever a route needs more than one
    write to land atomically.
    Returns a list of results (list[dict] or None) in the same order
    as `operations`.
    """
    with session_scope() as session:
        results = []
        for sql, params in operations:
            result = session.execute(text(sql), params or {})
            if result.returns_rows:
                results.append([dict(row._mapping) for row in result])
            else:
                results.append(None)
        return results


def run_in_transaction(fn):
    """
    Run fn(session) inside a single transaction and return its result.
    Use this (instead of execute_transaction) when a later write needs a
    value produced by an earlier one in the same transaction - e.g.
    inserting child rows that reference the id a preceding INSERT just
    generated - so the whole sequence commits or rolls back together.
    """
    with session_scope() as session:
        return fn(session)


def log_audit(action, entity_type, entity_id=None, performed_by=None,
              old_value=None, new_value=None):
    """
    Write one row to audit_log.

    performed_by should be the human-readable actor name captured once
    per admin session (see admin.py's _actor() helper) - now that the
    admin panel is used from multiple devices/people at once, hardcoding
    'admin' everywhere means an incident can never be traced back to who
    (or which device) actually made a change. Falls back to 'unknown'
    rather than a fixed literal, so a genuinely missing actor is visible
    as such instead of looking like a real, attributed action.
    """
    execute_sql("""
        INSERT INTO audit_log (action, entity_type, entity_id, old_value, new_value, performed_by)
        VALUES (:action, :entity_type, :entity_id, :old_value, :new_value, :performed_by)
    """, {
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'old_value': json.dumps(old_value, default=str) if old_value is not None else None,
        'new_value': json.dumps(new_value, default=str) if new_value is not None else None,
        'performed_by': performed_by or 'unknown',
    })


def execute_function(func_name, *args):
    """Execute a PostgreSQL function"""
    with session_scope() as session:
        placeholders = ', '.join([f':arg{i}' for i in range(len(args))])
        params = {f'arg{i}': arg for i, arg in enumerate(args)}
        
        sql = f"SELECT * FROM {func_name}({placeholders})"
        result = session.execute(text(sql), params)
        
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return None


class DatabaseManager:
    """Database manager for direct queries"""
    
    @staticmethod
    def get_connection():
        """Get a raw connection from the pool"""
        if engine is None:
            raise RuntimeError("Database not initialized")
        return engine.connect()
    
    @staticmethod
    def execute_with_transaction(queries):
        """Execute multiple queries in a single transaction"""
        with session_scope() as session:
            results = []
            for sql, params in queries:
                result = session.execute(text(sql), params or {})
                if result.returns_rows:
                    results.append([dict(row._mapping) for row in result])
                else:
                    results.append(None)
            return results

