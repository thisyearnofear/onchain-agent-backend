import sqlite3

def add_nft(contract_address: str):
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("INSERT INTO nfts(contract) VALUES (?)", (contract_address,))
    con.commit()

def get_nfts() -> list[str]:
    con = sqlite3.connect("agent.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM nfts")
    return cur.fetchall()