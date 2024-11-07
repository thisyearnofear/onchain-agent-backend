import sqlite3

def get_wallet_info():
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM wallet")
    return cur.fetchone()