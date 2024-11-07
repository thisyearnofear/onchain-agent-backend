import sqlite3

def add_token(contract_address: str):
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("INSERT INTO erc20s(contract) VALUES (?)", (contract_address,))
    con.commit()

def get_tokens() -> list[str]:
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM erc20s")
    return cur.fetchall()