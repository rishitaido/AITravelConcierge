import sqlite3


def init_cache_db():
    conn = sqlite3.connect("cache.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS prompt_cache (
              prompt TEXT PRIMARY KEY,
              response TEXT)""")
    conn.commit()
    conn.close()


def get_cached_response(prompt):
    conn = sqlite3.connect("cache.db")
    c = conn.cursor()
    c.execute("SELECT response FROM prompt_cache WHERE prompt = ? ", (prompt,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def save_response_to_cache(prompt, response):
    conn = sqlite3.connect("cache.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO prompt_cache (prompt, response) VALUES (?,?)", (prompt, response))
    conn.commit()
    conn.close()
