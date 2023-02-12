from flask import Flask, request, render_template, session
import hashlib
import MySQLdb


def md5(vstup):
    return hashlib.md5(vstup.encode("utf-8")).hexdigest()

app = Flask(__name__)
app.secret_key = "123"

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/produkty/')
def produkty():
    return render_template("produkty.html")


def mojeDBconnect():
    db=MySQLdb.connect("kol39313.mysql.pythonanywhere-services.com","kol39313","Jablko31","kol39313$default")
    return db

@app.route('/databaze/')
def databaze():
    #db=MySQLdb.connect("kol39313.mysql.pythonanywhere-services.com","kol39313","Jablko31","kol39313$default")
    db = mojeDBconnect()
    cur = db.cursor()
    cur.execute("select * from student")

    txt = "vysledek obsahuje " + str(cur.rowcount)  + " radku"

    db.close
    return "práce s DB"+txt

import os

@app.route('/fotogalerie/')
def fotogalerie():
    fotky=os.listdir("./mysite/static/upload")
    return render_template("fotogalerie.html", fotky=fotky, zprava="")

@app.route('/nahrani-fotky/', methods=['GET', 'POST'])
def upload_foto():
    if request.method=="POST":

        try:
            f = request.files["soubor"]
            f.save("./mysite/static/upload/"+f.filename)
            return render_template("fotogalerie.html", zprava="Soubor úspěšně nahrán")
        except:
            pass
    return render_template("fotogalerie.html", zprava="Chyba při nahrávání souboru")

@app.route('/kontakt/')
def kontakt():
    return render_template("kontakt.html")


@app.route('/registrace', methods=['GET', 'POST'])
def registrace():
    uspech=""
    chybova_zprava=""
    jmeno=""

    if request.method=="POST":

        jm=request.form["jmeno"]
        hes=request.form["heslo"]
        phes=request.form["potvrdit_heslo"]
        em=request.form["email"]
        if len(jm)==0:
            chybova_zprava = "Jméno musí být vyplněno!"
        elif hes!=phes:
            jmeno=jm
            chybova_zprava = "Zadaná hesla si neodpovídají!"
        else:

            if chybova_zprava=="": #uzivatelske jmeno "jm" dosud v souboru nexistuje

                db = mojeDBconnect()
                cur = db.cursor()
                heslo=md5(jm+";"+hes)
                cur.execute(f'insert into uziv (login,heslo,email) values ("{jm}","{heslo}","{em}")')
                db.commit()


                if cur.rowcount >0:
                    chybova_zprava="Úspěšně jste se zaregistroval" +jm

                db.close()



    return render_template("registrace.html", chybova_zprava=chybova_zprava, uspech=uspech,jmeno=jmeno)

@app.route('/zmenahesla/', methods=['GET', 'POST'])
def zmenahesla():
    zprava1=""
    if request.method=='POST':
        jm=session["uziv"]
        st=md5(jm+";"+request.form["stare_heslo"])
        he=request.form["nove_heslo"]
        he2=request.form["nove_potvrdit_heslo"]
        db = mojeDBconnect()
        cur=db.cursor()
        cur.execute(f'select * from uziv where login="{jm}" and heslo="{st}"')
        if cur.rowcount !=0:
            if he == he2:
                heslo=md5(jm+";"+he)
                zprava1="HESLO byla změněna"
                cur.execute(f'update uziv set heslo="{heslo}" where login="{jm}"')
                db.commit()
            else:
                zprava1 = "vaše hesla se neshodují"
        else:
            zprava1 = "staré heslo bylo špatně zadané"
        db.close()
    return render_template("změnahesla.html",zprava1=zprava1)


@app.route('/prihlaseni/', methods=['GET', 'POST'])
def prihlaseni():

    chybova_zprava=""
    uspech=""
    jmeno=""
    nalezeno=0

    if "uziv" in session:
        uspech="Uživatel "+session["uziv"]+" byl odhlášen."
        del session["uziv"]

    if request.method=="POST":
        jm=request.form["jmeno"]
        hs=md5(jm+";"+request.form["heslo"])


        db = mojeDBconnect()
        cur = db.cursor()
        heslo=md5(jm+";"+hs)
        cur.execute(f'insert into uziv (login,heslo) values ("{jm}","{heslo}")')
        if cur.rowcount >0:
                nalezeno = 1
        db.close()

        if nalezeno>0:
          uspech="Úspěšné přihlášení :-) Uživatel: "+jm
          session["uziv"]=jm
        else:
          jmeno=jm
          chybova_zprava="Špatně zadané přihlašovací údaje :-("

    return render_template("prihlaseni.html", chybova_zprava=chybova_zprava, uspech=uspech, jmeno=jmeno)



@app.route('/zprava-uzivatelu/', methods=['GET','POST'])
def adm_uziv():

    uzivatele=""


    db = mojeDBconnect()
    cur=db.cursor()

    if request.method=="POST":

        akce=request.form["akce"]
        login=request.form["login"]

        if akce=="povolit":

            if request.form["povolen"]=="A":
                povolen="N"
            else:

                povolen="A"

            cur.execute(f'update uziv set povolen="{povolen}" where login="{login}";')
            db.commit()


        elif akce=="smazat":

            cur.execute(f'delete from uziv where login="{login}";')
            db.commit()

    cur.execute("select login, email, povolen from uziv")

    uzivatele=cur.fetchall()


    db.close()

    return render_template("uzivatele.html", uzivatele=uzivatele)

