from flask import Flask, request, render_template, session, url_for, redirect, flash
import hashlib
import MySQLdb
import traceback



def md5(vstup):
    return hashlib.md5(vstup.encode("utf-8")).hexdigest()


app = Flask(__name__)
app.secret_key = "123"

@app.route('/')
@app.route('/home')
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
    db=mojeDBconnect()
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
                    uspech="Úspěšně jste se zaregistroval " +jm

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


    if "uziv" in session:
        uspech="Uživatel "+session["uziv"]+" byl odhlášen."
        del session["uziv"]

    if request.method=="POST":

        jm=request.form["jmeno"]
        hes=md5(jm+";"+request.form["heslo"])

        db = mojeDBconnect()
        cur=db.cursor()
        cur.execute(f'select * from uziv where login="{jm}" and heslo="{hes}"')
        if cur.rowcount > 0:
            uspech="OK"
        db.close()


        if len(uspech)>0:
          uspech="Úspěšné přihlášení :-) Uživatel: "+jm
          session["uziv"]=jm
        else:
          jmeno=jm
          chybova_zprava="Špatně zadané přihlašovací údaje :-("

    return render_template("prihlaseni.html", chybova_zprava=chybova_zprava, uspech=uspech, jmeno=jmeno)




@app.route('/sprava-uzivatelu/', methods=['GET','POST'])
def adm_uziv():

    uzivatele=""
    chyba=""
    tymy=""
    spolec=""

    db = mojeDBconnect()
    cur=db.cursor()
    cur2=db.cursor()
    cur3=db.cursor()
    cur4=db.cursor()


    if request.method == "POST":


        akce=request.form["akce"]
        login=request.form["login"]

        if akce == "smazat":

            cur.execute(f'delete from uziv where login="{login}";')
            db.commit()

        elif akce == "pridat_tym":

            try:


                tym_id=request.form["tymy"]

                cur3.execute(f'select id_uziv from uziv where login="{login}"')
                id_uziv = cur3.fetchone()[0]

                cur3.execute(f'insert into uziv_tym (id_uzivatele, id_tymu) values ({id_uziv}, {tym_id})')
                db.commit()

            except TypeError:
                pass



        elif akce == "smazat_z_tymu":

            cur.execute(f'delete from uziv_tym where id_uzivatele=(select id_uziv from uziv where login="{login}")')
            db.commit()



    cur.execute("select login, email from uziv")

    uzivatele=cur.fetchall()

    cur2.execute("select jmeno_tymu, id_tymu from tymy")

    tymy=cur2.fetchall()

    cur4.execute("SELECT  uziv.login, tymy.jmeno_tymu FROM uziv_tym JOIN uziv ON uziv_tym.id_uzivatele = uziv.id_uziv  JOIN tymy ON uziv_tym.id_tymu = tymy.id_tymu")

    spolec=cur4.fetchall()

    db.close()

    return render_template("uzivatele.html", uzivatele=uzivatele, tymy=tymy,chyba=chyba, spolec=spolec)





@app.route('/sprava-tymu', methods=['GET','POST'])
def adm_tymu():

    tymy=""


    db = mojeDBconnect()
    cur=db.cursor()



    if request.method == "POST":


        akce=request.form["akce"]
        jmeno_tymu=request.form["jmeno_tymu"]
        login=request.form["login"]

        if akce == "smazat":

            cur.execute(f'delete from tymy where jmeno_tymu="{jmeno_tymu}";')
            db.commit()


        elif akce == "pridat_roli":


            role = request.form["role"]

            if role == "1":


                jmeno_tymu=request.form["jmeno_tymu"]

                try:

                    cur.execute(f'select id_tymu from uziv_tym where id_uzivatele=(select id_uziv from uziv where login="{login}")')
                    id_tymu = cur.fetchone()[0]

                    cur.execute(f'update tymy set kapitan="{login}" where id_tymu={id_tymu}')
                    db.commit()

                except TypeError:
                    pass





    cur.execute("select jmeno_tymu, kapitan from tymy")

    tymy=cur.fetchall()

    db.close()

    return render_template("tymy.html", tymy=tymy)

@app.route('/tvoreni-tymu', methods=['GET', 'POST'])
def tvor_tym():

    chybova_zprava=""
    uspech=""

    if request.method=='POST':

        nz=request.form["nazev"]

        if nz=="":
            chybova_zprava="Pole musí být vyplněno"
        else:
            if chybova_zprava=="":

                db = mojeDBconnect()
                cur = db.cursor()
                cur.execute(f'insert into tymy (jmeno_tymu) values ("{nz}")')
                db.commit()

                db.close()

    return render_template("prihlastym.html", chybova_zprava=chybova_zprava, uspech=uspech)

@app.route('/tvoreni-ukolu', methods=['GET', 'POST'])
def tvor_ukol():

    tymy=""

    db = mojeDBconnect()
    cur = db.cursor()



    if request.method == 'POST':

        nazev = request.form['nazev']
        termin = request.form['termin']
        popis = request.form['popis']


        cur.execute(f"INSERT INTO ukoly (nazev, termin, popis) VALUES ('{nazev}', '{termin}', '{popis}')")
        db.commit()

    cur.execute("select jmeno_tymu from tymy")

    tymy=cur.fetchall()

    db.close()


    return render_template("vytvorukol.html",tymy=tymy)

@app.route('/prehled-ukolu', methods=['GET', 'POST'])
def prehled_ukolu():

    ukoly=""

    db = mojeDBconnect()
    cur = db.cursor()

    if request.method == "POST":


        akce = request.form["akce"]


        if akce == "smazat":

            try:

                login = request.form["login"]

                cur.execute("DELETE FROM ukoly WHERE nazev=%s", (login,))
                db.commit()

            except TypeError:
                pass


    cur.execute("select nazev, termin, popis from ukoly")

    ukoly=cur.fetchall()

    db.close()


    return render_template("ukoly.html", ukoly=ukoly)

@app.route('/uziv-ukoly', methods=['GET', 'POST'])
def uziv_ukoly():

    ukoly=""

    db = mojeDBconnect()
    cur = db.cursor()


    cur.execute("select nazev, termin, popis from ukoly")

    ukoly=cur.fetchall()

    db.close()



    return render_template("uzivukoly.html", ukoly=ukoly)




@app.route('/zarazeni', methods=['GET', 'POST'])
def zarazeni():

    zarazeni=""
    chyba=""

    db = mojeDBconnect()
    cur = db.cursor()


    if request.method == "POST":

        akce = request.form['akce']
        login = request.form['login']

        if akce == "smazat":


            cur.execute('delete uziv.login, tymy.jmeno_tymu FROM uziv_tym JOIN uziv ON uziv_tym.id_uzivatele = uziv.id_uziv JOIN tymy ON uziv_tym.id_tymu = tymy.id_tymu')
            #cur.execute(f"DELETE FROM uziv_tym WHERE id_uzivatele = '{login}'")
            db.commit()



    cur.execute('SELECT uziv.login, tymy.jmeno_tymu FROM uziv_tym JOIN uziv ON uziv_tym.id_uzivatele = uziv.id_uziv JOIN tymy ON uziv_tym.id_tymu = tymy.id_tymu')
    #cur.execute('select id_uzivatele, id_tymu from uziv_tym ')

    zarazeni=cur.fetchall()

    db.close()


    return render_template("zarazeni.html", zarazeni=zarazeni, chyba=chyba)

@app.route('/profil', methods=['GET', 'POST'])
def profil():


    return render_template("profil.html")






























