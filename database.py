import sqlite3
import json
from datetime import datetime
from config import Config, encrypt_value, decrypt_value

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_URI)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create config table
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY DEFAULT 1,
            kilo_api_key TEXT,
            system_prompt TEXT,
            posting_time TEXT,
            jitter_minutes INTEGER DEFAULT 15,
            model_name TEXT DEFAULT 'openai/gpt-4o-mini',
            linkedin_rule TEXT,
            reddit_rule TEXT,
            threads_rule TEXT
        )
    ''')
    
    # Migration: Handle 'user_id' -> 'id' rename if necessary
    try:
        # Check if 'user_id' exists and 'id' doesn't
        cursor = c.execute('PRAGMA table_info(config)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'user_id' in columns and 'id' not in columns:
            c.execute('ALTER TABLE config RENAME COLUMN user_id TO id')
    except sqlite3.OperationalError:
        pass

    # Migration for jitter_minutes
    try:
        c.execute('ALTER TABLE config ADD COLUMN jitter_minutes INTEGER DEFAULT 15')
    except sqlite3.OperationalError:
        pass # Already exists

    # Migration for model_name
    try:
        c.execute('ALTER TABLE config ADD COLUMN model_name TEXT DEFAULT "openai/gpt-4o-mini"')
    except sqlite3.OperationalError:
        pass # Already exists

    # Migration for platform rules
    for platform in ['linkedin', 'reddit', 'threads']:
        try:
            c.execute(f'ALTER TABLE config ADD COLUMN {platform}_rule TEXT')
        except sqlite3.OperationalError:
            pass # Already exists
        
    # Auto-update old model names to new Kilo format
    c.execute("UPDATE config SET model_name = 'openai/gpt-4o-mini' WHERE model_name = 'gpt-4o-mini'")
    c.execute("UPDATE config SET model_name = 'openai/gpt-4o' WHERE model_name = 'gpt-4o'")
    c.execute("UPDATE config SET model_name = 'anthropic/claude-3-5-sonnet' WHERE model_name = 'claude-3-5-sonnet'")
    c.execute("UPDATE config SET model_name = 'anthropic/claude-3-haiku' WHERE model_name = 'claude-3-haiku'")
    c.execute("UPDATE config SET model_name = 'google/gemini-pro-1.5' WHERE model_name = 'gemini-1.5-pro'")
    c.execute("UPDATE config SET model_name = 'z-ai/glm-5:free' WHERE model_name = 'z-ai/glm-4:free'")
    c.execute("UPDATE config SET model_name = 'minimax/minimax-m2.5:free' WHERE model_name = 'minimax/minimax-m2.1:free'")
    
    # Ensure a single row exists in config
    c.execute('SELECT COUNT(*) FROM config')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO config (id, kilo_api_key, system_prompt, posting_time, jitter_minutes, model_name, linkedin_rule, reddit_rule, threads_rule) VALUES (1, "", "", "09:00", 15, "openai/gpt-4o-mini", "", "", "")')
    
    # Create accounts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            platform TEXT PRIMARY KEY,
            credentials TEXT,
            session_data TEXT,
            status TEXT
        )
    ''')
    
    # Migration: Add session_data col if missing
    try:
        c.execute('ALTER TABLE accounts ADD COLUMN session_data TEXT')
    except sqlite3.OperationalError:
        pass # Already exists
    
    # Create knowledge_base table
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            uploaded_at TIMESTAMP
        )
    ''')
    
    # Create trends_cache table
    c.execute('''
        CREATE TABLE IF NOT EXISTS trends_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            trending_topic TEXT,
            scraped_at TIMESTAMP
        )
    ''')
    
    # Create post_history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS post_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            content TEXT,
            status TEXT,
            timestamp TIMESTAMP,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            model_used TEXT
        )
    ''')

    # Migration: Add new columns to post_history if they don't exist
    for col, col_type in [("prompt_tokens", "INTEGER"), ("completion_tokens", "INTEGER"), ("model_used", "TEXT")]:
        try:
            c.execute(f'ALTER TABLE post_history ADD COLUMN {col} {col_type}')
        except sqlite3.OperationalError:
            pass # Already exists
    
    conn.commit()
    conn.close()

# --- Configuration Methods ---
def get_config():
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    conn.close()
    if row:
        return {
            'kilo_api_key': decrypt_value(row['kilo_api_key']) if row['kilo_api_key'] else '',
            'system_prompt': row['system_prompt'],
            'posting_time': row['posting_time'],
            'jitter_minutes': row['jitter_minutes'],
            'model_name': row['model_name'],
            'linkedin_rule': row['linkedin_rule'] or "",
            'reddit_rule': row['reddit_rule'] or "",
            'threads_rule': row['threads_rule'] or ""
        }
    return None

def update_config(kilo_api_key=None, system_prompt=None, posting_time=None, jitter_minutes=None, model_name=None, linkedin_rule=None, reddit_rule=None, threads_rule=None):
    conn = get_db_connection()
    updates = []
    params = []
    
    if kilo_api_key is not None:
        updates.append("kilo_api_key = ?")
        params.append(encrypt_value(kilo_api_key))
    if system_prompt is not None:
        updates.append("system_prompt = ?")
        params.append(system_prompt)
    if posting_time is not None:
        updates.append("posting_time = ?")
        params.append(posting_time)
    if jitter_minutes is not None:
        updates.append("jitter_minutes = ?")
        params.append(jitter_minutes)
    if model_name is not None:
        updates.append("model_name = ?")
        params.append(model_name)
    if linkedin_rule is not None:
        updates.append("linkedin_rule = ?")
        params.append(linkedin_rule)
    if reddit_rule is not None:
        updates.append("reddit_rule = ?")
        params.append(reddit_rule)
    if threads_rule is not None:
        updates.append("threads_rule = ?")
        params.append(threads_rule)
        
    if updates:
        query = f"UPDATE config SET {', '.join(updates)} WHERE id = 1"
        conn.execute(query, params)
        conn.commit()
    conn.close()

# --- Accounts Methods ---
def get_account(platform):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM accounts WHERE platform = ?', (platform,)).fetchone()
    conn.close()
    if row:
        # Prioritize new session_data column
        session_data = row['session_data']
        if session_data:
            try:
                # Decrypt if it looks like it's encrypted (base64 check or just try-catch)
                decoded = decrypt_value(session_data)
                return {
                    'platform': row['platform'],
                    'credentials': {'session_state': decoded},
                    'status': row['status']
                }
            except:
                return {
                    'platform': row['platform'],
                    'credentials': {'session_state': session_data},
                    'status': row['status']
                }
                
        # Fallback to old credentials blob
        creds = decrypt_value(row['credentials'])
        return {
            'platform': row['platform'],
            'credentials': json.loads(creds) if creds else {},
            'status': row['status']
        }
    return None

def update_account(platform, credentials_dict, status="active"):
    conn = get_db_connection()
    
    # If it's a cookie paste, it will have 'session_state'
    session_data = credentials_dict.get('session_state')
    encrypted_session = encrypt_value(session_data) if session_data else None
    
    # Still keep credentials blob for compatibility
    creds_str = json.dumps(credentials_dict)
    encrypted_creds = encrypt_value(creds_str)
    
    conn.execute('''
        INSERT INTO accounts (platform, credentials, session_data, status) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(platform) DO UPDATE SET 
        credentials=excluded.credentials,
        session_data=excluded.session_data,
        status=excluded.status
    ''', (platform, encrypted_creds, encrypted_session, status))
    conn.commit()
    conn.close()

# --- Knowledge Base Methods ---
def add_knowledge(filename, content):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO knowledge_base (filename, content, uploaded_at)
        VALUES (?, ?, ?)
    ''', (filename, content, datetime.now()))
    conn.commit()
    conn.close()

def get_all_knowledge():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM knowledge_base ORDER BY uploaded_at DESC').fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize DB on import
init_db()

# --- Analytics Methods ---
def get_analytics_summary():
    conn = get_db_connection()
    
    total = conn.execute('SELECT COUNT(*) FROM post_history').fetchone()[0]
    success = conn.execute('SELECT COUNT(*) FROM post_history WHERE status = "success"').fetchone()[0]
    
    reddit_count = conn.execute('SELECT COUNT(*) FROM post_history WHERE platform = "reddit"').fetchone()[0]
    linkedin_count = conn.execute('SELECT COUNT(*) FROM post_history WHERE platform = "linkedin"').fetchone()[0]
    threads_count = conn.execute('SELECT COUNT(*) FROM post_history WHERE platform = "threads"').fetchone()[0]
    
    conn.close()
    
    success_rate = (success / total * 100) if total > 0 else 0
    
    return {
        'total_posts': total,
        'success_rate': round(success_rate, 1),
        'platforms': {
            'reddit': reddit_count,
            'linkedin': linkedin_count,
            'threads': threads_count
        }
    }

def get_recent_posts(limit=10):
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM post_history ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_posting_trends(days=7):
    conn = get_db_connection()
    query = '''
        SELECT 
            strftime('%Y-%m-%d', timestamp) as date,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as failure_count
        FROM post_history
        WHERE timestamp >= date('now', ?)
        GROUP BY date
        ORDER BY date ASC
    '''
    rows = conn.execute(query, (f'-{days} days',)).fetchall()
    conn.close()
    
    return {
        'labels': [row['date'] for row in rows],
        'success': [row['success_count'] for row in rows],
        'failure': [row['failure_count'] for row in rows]
    }
