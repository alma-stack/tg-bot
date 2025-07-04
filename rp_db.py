import sqlite3

conn = sqlite3.connect("rp.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS rp_commands (
    command TEXT PRIMARY KEY,
    emoji TEXT,
    template TEXT
)
""")
conn.commit()

def add_custom_command(cmd, emoji, template):
    cur.execute("REPLACE INTO rp_commands (command, emoji, template) VALUES (?, ?, ?)", (cmd, emoji, template))
    conn.commit()

def get_custom_command(cmd):
    cur.execute("SELECT emoji, template FROM rp_commands WHERE command = ?", (cmd,))
    return cur.fetchone()
