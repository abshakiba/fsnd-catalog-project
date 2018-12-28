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

@app.route('/catalog/<catalog_name>/')
@app.route('/catalog/<catalog_name>/items')
def showItem(catalog_name):
    try:
        session.query(Catalog).filter_by(name=catalog_name).one()
        items = session.query(Item).filter_by(catalog_name=catalog_name)
        catalogs = session.query(Catalog).order_by(asc(Catalog.name))
        return render_template('category.html', catalogs=catalogs, items=items, catalog_name=catalog_name)
    except:
        flash("Oops! Invalid Catalog Name!")
        return redirect(url_for('showCatalog'))

@app.route('/catalog/<catalog_name>/<item_name>')
def menuItemDesc(catalog_name, item_name):
    try:
        item = session.query(Item).filter_by(name=item_name, catalog_name=catalog_name).one()
        return render_template('item.html', item=item)
    except:
        flash("Oops! Invalid Item Name!")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='127.0.0.1', port=6789)
