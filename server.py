from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item
from flask import session as login_session
import random
import string
#from oauth2client.client import flow_from_clientsecrets
#from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

APPLICATION_NAME = "Catalog Application"

engine = create_engine('sqlite:///catalogs.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/catalog/')
def showCatalog():
    catalogs = session.query(Catalog).order_by(asc(Catalog.name))
    items = session.query(Item).order_by(Item.created_date.desc())
    return render_template('home.html', catalogs=catalogs, items=items)

@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/items')
def showItem(catalog_id):
    try:
        catalog = session.query(Catalog).filter_by(id=catalog_id).one()
        items = session.query(Item).filter_by(catalog_id=catalog_id)
        catalogs = session.query(Catalog).order_by(asc(Catalog.name))
        return render_template('category.html', catalogs=catalogs, items=items, catalog=catalog)
    except:
        flash("Oops! Invalid Catalog ID!")
        return redirect(url_for('showCatalog'))

@app.route('/catalog/<int:catalog_id>/item/<int:item_id>')
def menuItemDesc(catalog_id, item_id):
    try:
        item = session.query(Item).filter_by(id=item_id, catalog_id=catalog_id).one()
        return render_template('item.html', item=item)
    except:
        flash("Oops! Invalid Item Name!")
        return redirect(url_for('showCatalog'))

@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'], user_id=1)
        session.add(newCatalog)
        try:
            session.commit()
            flash('New Catalog %s Successfully Created' % newCatalog.name)
            return redirect(url_for('showCatalog'))
        except Exception as err:
            session.rollback()
            if "UNIQUE constraint failed" in str(err):
                flash("Oops! Catalog Name Already Exists!")
                return redirect(url_for('newCatalog'))
            else:
                flash("Oops! Something Went Wrong! Try Again!")
            return redirect(url_for('showCatalog'))
    else:
        return render_template('newCatalog.html')

@app.route('/catalog/<catalog_name>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_name):
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'], user_id=1)
        session.add(newCatalog)
        try:
            session.commit()
            flash('New Catalog %s Successfully Created' % newCatalog.name)
            return redirect(url_for('showCatalog'))
        except Exception as err:
            session.rollback()
            if "UNIQUE constraint failed" in str(err):
                flash("Oops! Catalog Name Already Exists!")
            else:
                flash("Oops! Something Went Wrong! Try Again!")
            return redirect(url_for('showCatalog'))
    else:
        catalog = session.query(Catalog).filter_by(name=catalog_name).one()
        return render_template('editCatalog.html', catalog=catalog)

@app.route('/catalog/items/new/', methods=['GET', 'POST'])
def newItem():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],catalog_id=request.form['catalog_id'], user_id=1)
        session.add(newItem)
        try:
            session.commit()
            flash('New Item %s Successfully Created' % newItem.name)
            return redirect(url_for('showCatalog'))
        except Exception as err:
            session.rollback()
            if "UNIQUE constraint failed" in str(err):
                flash("Oops! Item Name Already Exists!")
                return redirect(url_for('newItem'))
            else:
                flash("Oops! Something Went Wrong! Try Again!")
            return redirect(url_for('showCatalog'))
    else:
        catalogs = session.query(Catalog).order_by(asc(Catalog.name))
        return render_template('newItem.html', catalogs=catalogs)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='127.0.0.1', port=6789)
