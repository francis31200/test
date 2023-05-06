import sqlite3
import click
import re
import os
import os
from datetime import datetime
from time import time
import csv
from . import moon_utils
from flask import current_app, g
from flask.cli import with_appcontext
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(): 
    return #already initialized, return is here for performance reasons
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
        with open("mobility/ugly_csv.csv","r", encoding="utf-8") as ugly_csv:
            csvlines=csv.reader(ugly_csv)
            next(csvlines)
            for y in csvlines:
                db.execute("INSERT OR IGNORE INTO ville(nom,code_postal,population) VALUES(?, ?, ?)", (y[0], y[1],0))
                db.execute("INSERT OR IGNORE INTO rue(nom,rue_id,code_postal) VALUES(?, ?, ?)", (y[2], y[3], y[1]))
                db.execute("INSERT INTO trafic(rue_id,date,lourd,voiture,velo,pieton,v85) VALUES(?, ?, ?, ?, ?, ?, ?)", (y[3], y[4], y[5], y[6], y[7], y[8], y[11]))
                values = y[10][1:-1].split(',')
                for z in range(len(values)):
                    db.execute("INSERT INTO vitesse(rue_id,date,tranche_de_vitesse,proportion) VALUES(?, ?, ?, ?)", (y[3], y[4], z*5, values[z]))
                db.commit()
                print("done")
            db.execute("UPDATE ville SET population=183287 WHERE nom='Bruxelles'")
            db.execute("UPDATE ville SET population=195278 WHERE nom='Liege'")
            db.execute("UPDATE ville SET population=111000 WHERE nom='Namur'")
            db.execute("UPDATE ville SET population=202421 WHERE nom='Charleroi'")
            db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)


def table_entry():
    #compte le nombre d'entrées de chaque type et le retourne
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT COUNT(*) FROM ville")
    entreesville = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM rue")
    entreesrue = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM vitesse")
    entreesvitesse = db.fetchone()[0]
    db.execute("SELECT COUNT(*) FROM trafic")
    entreestrafic = db.fetchone()[0]
    db.close()
    dbb.close()
    print(entreesville)
    return entreesville, entreesrue, entreesvitesse, entreestrafic

    

def nombre_rues():
    #compte le nombre de rues pour chaque ville, et le retourne
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    ruesbx = db.execute("SELECT COUNT(*) FROM rue WHERE code_postal='1000'")
    ruesbx = db.fetchone()[0]
    ruesliege = db.execute("SELECT COUNT(*) FROM rue WHERE code_postal='4000'")
    ruesliege = db.fetchone()[0]
    ruesnamur = db.execute("SELECT COUNT(*) FROM rue WHERE code_postal='5000'")
    ruesnamur = db.fetchone()[0]
    ruescharleroi = db.execute("SELECT COUNT(*) FROM rue WHERE code_postal='6000'")
    ruescharleroi = db.fetchone()[0]
    db.close()
    dbb.close()
    return ruesbx, ruesnamur, ruesliege, ruescharleroi

def total_velo(code):
    #retourne une moyenne des cyclistes pour une ville donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT rue_id FROM rue WHERE code_postal = ?", (code,))
    results=db.fetchall()
    values = [result[0] for result in results]
    print(values)
    counter = 0
    total_velo = 0
    for x in values:
        db.execute("SELECT SUM(velo) FROM trafic  WHERE rue_id= ?", (x,))
        total_velo+=db.fetchone()[0]
        counter += 1
    db.close()
    dbb.close()
    return total_velo / counter


def rues_cyclables():
    #retourne une valeur représentant la cyclabilité d'une ville par rapport à sa population
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    velobxl = (total_velo(1000) / 183287) * 100
    velonamur = (total_velo(5000) / 111000) * 100
    veloliege = (total_velo(4000) / 195278) * 100
    velocharleroi = (total_velo(6000) / 202421) * 100
    db.close()
    dbb.close()
    return round(velobxl,2), round(velonamur,2), round(veloliege,2), round(velocharleroi,2)
    


    

def reqs1(code):
    #retourne les proportions d'usagers de la route pour une ville donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()

    db.execute("SELECT rue_id FROM rue WHERE code_postal = ?", (code,))
    results=db.fetchall()
    values = [result[0] for result in results]
    print(values)
    additionlourd=0
    additionvoiture=0
    additionvelo=0
    additionpieton=0
    for x in values:
        db.execute("SELECT SUM(lourd) FROM trafic  WHERE rue_id= ?", (x,))
        additionlourd+=db.fetchone()[0]
        db.execute("SELECT SUM(voiture) FROM trafic  WHERE rue_id= ?", (x,))
        additionvoiture+=db.fetchone()[0]
        db.execute("SELECT SUM(velo) FROM trafic  WHERE rue_id= ?", (x,))
        additionvelo+=db.fetchone()[0]
        db.execute("SELECT SUM(pieton) FROM trafic  WHERE rue_id= ?", (x,))
        additionpieton+=db.fetchone()[0]
    additiontotal=additionpieton+additionvelo+additionlourd+additionvoiture
    prclourd=(additionlourd/additiontotal)*100
    prcvoiture=(additionvoiture/additiontotal)*100
    prcvelo=(additionvelo/additiontotal)*100
    prcpieton=(additionpieton/additiontotal)*100

    db.close()
    dbb.close()
    return round(prclourd, 2),round(prcvoiture, 2),round(prcvelo, 2),round(prcpieton, 2)

def ruesville(code):
    #retourne la liste des rues d'une ville donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT rue_id,nom FROM rue WHERE code_postal = ?", (code,))
    results=db.fetchall()
    rue_id = [(result[0], result[1]) for result in results]
    print(rue_id)
    db.close()
    dbb.close()
    return rue_id

def villes():
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT code_postal,nom FROM ville")
    results=db.fetchall()
    rue_id = [(result[0], result[1]) for result in results]
    print(rue_id)
    db.close()
    dbb.close()
    return rue_id


def ruesjours(rue_id,jour):
    #retourne les proportions de vélos, voitures, etc.. pour une rue donnée et un jour de la semaine donné
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    roundedlist=[]
    additiontotal=0
    db.execute("SELECT SUM(lourd),SUM(voiture),SUM(velo),SUM(pieton) FROM trafic WHERE strftime('%w', date) = ? AND rue_id = ?",(str(jour),str(rue_id)))
    result = db.fetchall()
    for x in result[0]:
        additiontotal+=x
    
    for x in result[0]:
        roundedlist.append(round(((x/additiontotal)*100),2))

    db.close()
    return roundedlist

def ruesgraphe(rue_id,starttime,endtime):
    print(starttime)
    print(endtime)
    #retourne les proportions de vélos, voitures, etc.. pour une rue donnée et une heure donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()

    db.execute("SELECT SUM(lourd),SUM(voiture),SUM(velo),SUM(pieton) FROM trafic WHERE rue_id = ? AND strftime(date) BETWEEN ? AND ?",(str(rue_id),str(starttime)+"Z",str(endtime)+"Z"))
    result = db.fetchall()
   
    roundedlist=[]
    for x in result[0]:
        if x==None:
            roundedlist.append(0.00)
        else:
            roundedlist.append(round(x,2))
    db.close()
    return roundedlist
    

def velopleinelune(annee):
    #retourne la proportion de vélos les jours de pleine lune pendant une année donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("""SELECT date,velo,voiture,lourd,pieton FROM trafic WHERE strftime('%Y', date) = ? AND (voiture,lourd,velo,pieton)!=(0,0,0,0)""", (str(annee),))
    results = db.fetchall()
    db.close()
    dbb.close()
    pleinelunedates=[]
    for row in results:
        date = row[0]
        if str(moon_utils.phase(moon_utils.age(date))) == "MoonPhase.FULL_MOON":
            pleinelunedates.append(row)
    pleineluneprops=[]
    for row in pleinelunedates:
        pleineluneprops.append((row[1]/sum(row[1:]))*100)
    print(pleineluneprops)
    if pleineluneprops == []:
        return "Pas de données pour cette année!"


    return round(sum(pleineluneprops)/len(pleineluneprops),2)


def frequentation(rue_id,jour):
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT lourd,voiture,velo,pieton FROM trafic WHERE rue_id = ? AND strftime('%Y-%m-%d',date) = ?",(str(rue_id),str(jour)))
    result = db.fetchall()
    print(result)
    db.close()
    return result

def selectrues():
    #retourne la liste des rues d'une ville donnée
    dbb = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    db = dbb.cursor()
    db.execute("SELECT rue_id,nom FROM rue")
    results=db.fetchall()
    rue_id = [(result[0], result[1]) for result in results]
    db.close()
    dbb.close()
    return rue_id