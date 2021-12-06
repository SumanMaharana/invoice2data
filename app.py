from flask import Flask, render_template ,flash, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from datetime import datetime
import random
import string
import re
import os

UPLOAD_FOLDER = os.getcwd()+'\\uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key="Qwerty2702"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///invoice.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

class Invoice(db.Model):
    invno=db.Column(db.String(100), primary_key=True)
    sinvno=db.Column(db.String(100), primary_key=True)
    supname=db.Column(db.String(200), nullable=False)
    ownname=db.Column(db.String(200), nullable=False)
    Quantity=db.Column(db.Integer, nullable=False)
    Unitprice=db.Column(db.String(100), nullable=False)
    invdate=db.Column(db.String(100), nullable=False)
    amount=db.Column(db.String(100), nullable=False)
    itemnum=db.Column(db.String(100), nullable=False)
    itendesc=db.Column(db.String(200), nullable=False)
    data_ent=db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self)->str:
        return f"{self.invno} - {self.amount}"

class Admin(db.Model):
    username=db.Column(db.String(100), primary_key=True)
    password=db.Column(db.String(200), nullable=False)
    lastlogin=db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self)->str:
        return f"{self.username} - {self.password}"

@app.route("/",methods=['GET', 'POST'])
def invoice_extract(data=None):
    if "user" not in session:
        return redirect(url_for('login'))
    inv = Invoice.query.all()
    return render_template('index.html',data=data,allinv=inv)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/Ext",methods=['GET', 'POST'])
def uploader():
    if "user" not in session:
        return redirect(url_for('login'))
    x=0
    datadict={"Invoice Number":"","Supplier Invoice Number":"","Owner Name":"","Supplier Name":"","Invoice Date":"","Invoice Amount":"","Quantity":"","Unit Price":"","Item Number":"","Item Description":""}
    if (request.method=='POST'):
        f=request.files['invoicefile']
        if f and allowed_file(f.filename):
            newf=os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(''.join(random.choices(string.ascii_uppercase + string.digits, k=4))+"_"+f.filename))
            f.save(newf)
            datadict["Invoice Number"]=''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
            for page_layout in extract_pages(newf):
                for element in page_layout:
                    if isinstance(element, LTTextContainer) :
                        if x==5:
                            datadict["Supplier Invoice Number"]=element.get_text()[11:-1]
                        if x==32:
                            datadict["Invoice Amount"]=element.get_text()[:-1]
                        if x==22:
                            datadict["Quantity"]=element.get_text()[:-1]
                        if x==24:
                            datadict["Item Number"]=element.get_text()[:-1]
                        if x==30:
                            datadict["Unit Price"]=element.get_text()[:-1]
                        if x==45:
                            datadict["Supplier Name"]=str(re.sub(' +', ' ', element.get_text()))[:-1]
                        if x==34:
                            datadict["Owner Name"]=element.get_text()[18:-1].split('\n')[0]
                        if x==25:
                            datadict["Item Description"]=element.get_text()[:-1]
                        if x==31:
                            datadict["Invoice Date"]=element.get_text()[:8]
                    x+=1
            os.remove(newf)
            return render_template('index.html',data=datadict)
        else:
            msg="file format not supported Upload invoice in pdf Format only"
            flash(msg,category='upd1')
            return redirect(url_for('invoice_extract'))
    return redirect(url_for('invoice_extract'))

@app.route("/Ins",methods=['GET', 'POST'])
def datains():
    if "user" not in session:
        return redirect(url_for('login'))
    if request.method=="POST":
        inv = Invoice(invno=request.form['invno'],sinvno=request.form['sinvno'],supname=request.form['supname'],ownname=request.form['ownname'],Quantity=request.form['Quantity']
        ,Unitprice=request.form['Unitprice'],invdate=request.form['invdate'],amount=request.form['amount'],itemnum=request.form['itemnum'],itendesc=request.form['itendesc'])
        db.session.add(inv)
        db.session.commit()
        msg='Invoice Details inserted SuccessfUlly !'
        flash(msg,category='ins1')
    return redirect(url_for('invoice_extract'))

@app.route("/Update",methods=['GET', 'POST'])
def Update():
    if "user" not in session:
        return redirect(url_for('login'))
    if request.method=="POST":
        inv =Invoice.query.filter_by(invno=request.form['invno']).first()
        if inv is None :
            msg='Invoice Number Cannot be Changed ! Dont Inspect us'
            flash(msg,category='Update0')
        else :
            inv.invno=request.form['invno']
            inv.sinvno=request.form['sinvno']
            inv.supname=request.form['supname']
            inv.ownname=request.form['ownname']
            inv.Quantity=request.form['Quantity']
            inv.Unitprice=request.form['Unitprice']
            inv.invdate=request.form['invdate']
            inv.amount=request.form['amount']
            inv.itemnum=request.form['itemnum']
            inv.itendesc=request.form['itendesc']
            db.session.add(inv)
            db.session.commit()
            msg='Invoice Details Updated Successfully !'
            flash(msg,category='Update1')
    return redirect(url_for('invoice_extract'))

@app.route("/Delete/<string:invno>",methods=['GET', 'POST'])
def Delete(invno):
    if "user" not in session:
        return redirect(url_for('login'))
    inv =Invoice.query.filter_by(invno=invno).first()
    db.session.delete(inv)
    db.session.commit()
    msg='Invoice Details Deleted SuccessfUlly !'
    flash(msg,category='Delete1')
    return redirect(url_for('invoice_extract'))

@app.route("/Login",methods=['GET', 'POST'])
def login():
    cred = Admin.query.all()
    if len(cred)==0:
        addadmin = Admin(username="admin",password="admin")
        db.session.add(addadmin)
        db.session.commit()
    if request.method=="POST":
        creds =Admin.query.filter_by(username=request.form['username']).first()
        if creds is None:
            flash("Credentials mismatch Success ! Try again")
            return redirect(url_for('login'))
        elif creds.password == request.form['password']:
            session['user']=True
            return redirect(url_for('invoice_extract'))
    return render_template('login.html')

@app.route("/Logout",methods=['GET', 'POST'])
def Logout():
    session.pop('user',None)
    return redirect(url_for('login'))

if __name__=="__main__":
    app.run(debug=True)