#uvozimo bottle
from ctypes import get_last_error
from bottle import *
from bottleext import *

#import sqlite3
import hashlib
import os

#uvozimo potrebne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2 - nalozi v ukaznem pozivu pip install psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

#privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

#conn_datoteka = 'HotelManagement.db'
# odkomentiraj, če želiš sporočila o napakah
debug(True)

def nastaviSporocilo(sporocilo = None):
    # global napakaSporocilo
    staro = request.get_cookie("sporocilo", secret=skrivnost)
    # idk zaki spodaj zakomentirano - iza ma tk
    if sporocilo is None:
        response.delete_cookie('sporocilo')
    else:
        response.set_cookie('sporocilo', sporocilo, path="/", secret=skrivnost)
    return staro

# Mapa za statične vire (slike, css, ...)
static_dir = "./static"

skrivnost = "rODX3ulHw3ZYRdbIVcp1IfJTDn8iQTH6TFaNBgrSkjIulr"

@get('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static')

def preveriUporabnika(): 
   username = request.get_cookie("username", secret=skrivnost)
   if username:
       cur = conn.cursor()    
       uporabnik = None
       try: 
           uporabnik = cur.execute("SELECT * FROM zaposleni WHERE username = %s", (username, )).fetchone()
       except:
           uporabnik = None
       if uporabnik: 
           return uporabnik
   redirect('/prijava')

#------------------------------------------------
#FUNKCIJE ZA IZGRADNJO STRANI
# @route("/static/<filename:path>")
# def static(filename):
#     return static_file(filename, root=static_dir)

#-----------------------------------------------
#ZAČETNA STRAN
#-----------------------------------------------
@get('/')
def index():
    return template('zacetna_stran.html')
#------------------------------------------------


#------------------------------------------------
# REGISTRACIJA, PRIJAVA, ODJAVA
#------------------------------------------------

def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

@get('/registracija')
def registracija_get():
    napaka = nastaviSporocilo()
    return template('registracija.html', napaka=napaka)

@post('/registracija')
def registracija_post():
    ime = request.forms.ime
    username = request.forms.username
    password = request.forms.password
    password2 = request.forms.password2

    print(ime, username, password, password2)

    if (ime == '') or (username == '') or (password == '') or (password2 == ''): 
        nastaviSporocilo('Registracija ni možna, ker dobim prazen string.') 
        #redirect('/registracija')
        redirect(url('registracija_get'))
        #return None #  brezveze
    # cur = conn.cursor()     # je že vspostavljen ne rabim še enkrat
    #uporabnik = None #  to je mal brezveze
    # try: 
    try:
        cur.execute(f"SELECT * FROM zaposleni WHERE ime = \'{ime}\'")
        uporabnik = cur.fetchone()
    except Exception:
        conn.rollback()
        # nared neki če ga ni
        nastaviSporocilo('Registracija ni možna, uporabnik ni v bazi.') 
        #redirect('/registracija')
        redirect(url('registracija_get'))
    #     print(e)
    #     uporabnik = None
    # if uporabnik is None:
    #     nastaviSporocilo('Registracija ni možna, uporabnik ni v bazi.') 
    #     #redirect('/registracija')
    #     redirect(url('registracija_get'))
    #     return
    if len(password) < 4:
        nastaviSporocilo('Geslo mora imeti vsaj 4 znake.') 
        #redirect('/registracija')
        redirect(url('registracija_get'))

    if password != password2:
        nastaviSporocilo('Gesli se ne ujemata.') 
        #redirect('/registracija')
        redirect(url('registracija_get'))

    zgostitev = hashGesla(password)
    #cur.execute("UPDATE zaposleni set username = %s, password = %s WHERE ime = %s", (username, zgostitev, ime))
    try:
        # cur.execute("""INSERT INTO zaposleni
        #             (ime, username, password)
        #             VALUES (%s, %s, %s)""", (ime, username, zgostitev))
        cur.execute(f"""UPDATE zaposleni
                        SET
                            username = \'{username}\',
                            password = \'{zgostitev}\'
                        WHERE
                            ime = \'{ime}\'""")
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
        #redirect('/registracija')
        redirect(url('registracija_get'))

    response.set_cookie('username', username, secret=skrivnost)
    print('vrzem vas na zaposlene')
    redirect('/prijava')



@get('/prijava')
def prijava_get():
   napaka = nastaviSporocilo()
   return template('prijava.html', napaka=napaka)

@post('/prijava')
def prijava_post():
   username = request.forms.username
   password = request.forms.password
   if (username=='') or (password==''):
       nastaviSporocilo('Uporabniško ima in geslo morata biti neprazna') 
       redirect('/prijava')

#    cur = conn.cursor()    
#    hashconn = None
   try: 
       cur.execute("SELECT password FROM zaposleni WHERE username = %s", (username, ))
       hashconn = cur.fetchone()
       hashconn = hashconn[-1]  # ne dodajaj kolon na desno
   except:
        conn.rollback()
        nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
        redirect('/prijava')

   if hashGesla(password) != hashconn:
       nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
       redirect('/prijava')
       

   response.set_cookie('username', username, secret=skrivnost)
   redirect('/hotelska_veriga')
    
@get('/odjava')
def odjava_get():
   response.delete_cookie('username')
   redirect('/')

### ZAPOSLENI
@get('/zaposleni')
def zaposleni():
    cur = conn.cursor()
    zaposleni = cur.execute("SELECT zaposleni_id,ime,priimek,naziv,telefonska_stevilka,email,oddelek_id,naslov_id,hotel_id FROM zaposleni")
    return template('zaposleni.html', zaposleni=zaposleni)

@get('/dodaj_zaposlenega')
def dodaj_agenta():
    return template('dodaj_zaposlenega.html', zaposleni_id='', ime='', priimek='', naziv='', telefonska_stevilka='', email='', oddelek_id='', naslov_id='', hotel_id='', username='', password='', napaka=None)

@post('/dodaj_zaposlenega')
def dodaj_zaposlenega_post():
    zaposleni_id = request.forms.zaposleni_id
    ime = request.forms.ime
    priimek = request.forms.priimek
    naziv = request.forms.naziv
    telefonska_stevilka = request.forms.telefonska_stevilka
    email = request.forms.email
    oddelek_id = request.forms.oddelek_id
    naslov_id = request.forms.naslov_id
    hotel_id = request.forms.hotel_id
    username = request.forms.username
    password = request.forms.password
    password2 = hashGesla(password2)

    cur.execute("""INSERT INTO zaposleni
                (zaposleni_id,ime,priimek,naziv,telefonska_stevilka,email,oddelek_id,naslov_id,hotel_id, username, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (zaposleni_id,ime,priimek,naziv,telefonska_stevilka,email,oddelek_id,naslov_id,hotel_id, username, password2))
    redirect(url('zaposleni'))

#@get('/zaposleni/dodaj')
#def dodaj_komitenta_get():
#    return template('zaposleni-edit.html')

#@post('/zaposleni/dodaj') 
#def dodaj_zaposleni():
#    zaposleni_id = request.forms.zaposleni_id
#    ime = request.forms.ime
#    priimek = request.forms.priimek
#    email = request.forms.email
#    naziv = request.forms.naziv
#    telefonska_stevilka = request.forms.telefonska_stevilka
#    naslov_id = request.forms.naslov_id
#    hotel_id = request.forms.hotel_id
#    oddelek_id = request.forms.oddelek_id
#    cur = conn.cursor()
#    cur.execute("INSERT INTO zaposleni (zaposleni_id, ime, priimek, naziv, telefonska_stevilka, email,oddelek_id, naslov_id, hotel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (zaposleni_id, ime, priimek, naziv, telefonska_stevilka, email,oddelek_id, naslov_id, hotel_id))
#    redirect('/zaposleni')

### HOTELSKA VERIGA

@get('/hotelska_veriga')
def hotelska_veriga():
    # cur = conn.cursor()
    cur.execute("SELECT ime_hotelske_verige, naslov_glavne_pisarne, email_hotelske_verige, spletna_stran FROM hotelska_veriga")
    return template('hotelska_veriga.html', hotelska_veriga=cur)

### HOTEL

@get('/hotel')
def hotel():
    cur = conn.cursor()
    hotel = cur.execute("""SELECT ime_hotela, naslov.mesto, naslov.posta, naslov.drzava, telefonska_stevilka, email, hotelska_veriga.ime_hotelske_verige FROM hotel_podatki
    JOIN naslov ON hotel_podatki.naslov_id=naslov.naslov_id
    JOIN hotelska_veriga ON hotel_podatki.hotelska_veriga_id=hotelska_veriga.hotelska_veriga_id
    ORDER BY hotel_podatki.ime_hotela""")
    return template('hotel.html', hotel=hotel)

### GOST

@get('/gostje')
def gostje():
    cur = conn.cursor()
    gostje = cur.execute("""SELECT ime,priimek,telefonska_stevilka,email,naslov.mesto, naslov.posta, naslov.drzava FROM gostje
    JOIN naslov ON gostje.naslov_id=naslov.naslov_id
    ORDER BY gostje.priimek""")
    return template('gostje.html', gostje=gostje)

@get('/gostje/dodaj')
def naslov():
    cur = conn.cursor()
    naslovi = cur.execute("SELECT mesto,posta,drzava from naslov")

def dodaj_gosta_get():
    naslovi = cur.execute("SELECT mesto,posta,drzava FROM naslov")
    return template('gost_edit.html', naslovi=naslovi)

# @post('/gostje/dodaj') 
# def dodaj_gosta_post():
#     ime = request.forms.ime
#     priimek = request.forms.priimek
#     telefonska_stevilka = request.forms.telefonska_stevilka
#     email = request.forms.email
#     naslov_id = request.forms.naslov_id
#     cur = conn.cursor()
#     cur.execute("INSERT INTO gostje (ime,priimek,telefonska_stevilka,email,naslov_id) VALUES (?, ?, ?, ?, ?)", 
#          (ime,priimek,telefonska_stevilka,email,naslov_id))
#     redirect('/gostje')

# ### SOBA

# @get('/sobe')
# def sobe():
#     cur = conn.cursor()
#     sobe = cur.execute("""SELECT stevilka_sobe,tip_sobe_id,hotel_podatki.ime_hotela FROM sobe
#     JOIN hotel_podatki ON sobe.hotel_id=hotel_podatki.ime_hotela""")
#     return template('sobe.html', sobe=sobe)


# ### OSTALO

# # conn = sqlite3.connect(conn_datoteka, isolation_level=None)
# # conn.set_trace_callback(print)
# # cur = conn.cursor()
# # cur.execute("PRAGMA foreign_keys = ON;")
# # run(host='localhost', port=8080, reloader=True)


# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) #za pogovarjanje z bazo

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
    print('test')