
import sqlite3

def setup():
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS wallet(id INTEGER PRIMARY KEY, info TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS nfts(contract TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS erc20s(contract TEXT)")
    con.commit()