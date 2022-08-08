# uvozimo ustrezne podatke za povezavo
from . import auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv

def ustvari_tabelo():
    cur.execute("""
    CREATE TABLE sobe
    (
    soba_id SERIAL PRIMARY KEY NOT NULL,
    stevilka_sobe INT NOT NULL,
    tip_sobe_id INT REFERENCES Tipi_Sob(Tip_sobe_id),
    hotel_id INT REFERENCES hotel_podatki(Hotel_id) 
    );
    """) 
    conn.commit() #ko delam poizvedbe, da se potrdijo 

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE sobe;
    """)
    conn.commit()

def uvozi_podatke():
    with open("Podatki/sobe.csv", encoding="UTF-8") as f:
        rd = csv.reader(f)
        next(rd) # izpusti naslovno vrstico
        for r in rd:
            cur.execute("""
                INSERT INTO sobe
                (soba_id,stevilka_sobe,tip_sobe_id,hotel_id)
                VALUES (%s, %s, %s, %s)
            """, r)
            #rid, = cur.fetchone()
            #print("Uvožen naslov %s" % (r[0], rid))
    conn.commit()


conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 