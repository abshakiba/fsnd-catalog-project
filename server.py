from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']
APPLICATION_NAME = "Catalog Application"

engine = create_engine('sqlite:///catalogs.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    """ Directs Users to login page. Additionally,
        a random token is created to avouid CRSF attck.
     """
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Google API Client Connetion


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Function to connect to Google Email APIs to authenticate
        users. Users need to be logged in to apply any modifications.

        If the communication with Google APIs is successful, application
        will obtain username, email address, and picture of the user. All
        will be saved in the database. Additionally, all this info will
        saved in to the login_session so the user will have access to apply
        modifications.

        A new record will be saved in to the database for the first time users.
        otherwise, the user's data will be retrieved from database and will
        assigned to login_session.

        Thee user will be redirected to main page if login is successful.
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State token'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the auth code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    gid = credentials.id_token['sub']

    if result['user_id'] != gid:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID doesn't match given user ID."), 401)
        print("Token's client ID does not match app's")
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('access_token')
    stored_gid = login_session.get('gid')
    if stored_credentials is not None and gid == stored_gid:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'

    login_session['access_token'] = credentials.access_token
    login_session['gid'] = gid
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    flash("You are now logged in as %s" % login_session['username'])
    return "<h1> Welcome, %s" % login_session['username']
# User Helper Functions


def createUser(login_session):
    """ A new record will be created in to the USER table in the database.
        Args : Login session

        Return: User id of new user
    """
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """ Return a USER record
        Args: User id

        Return: A User record from USER table. class
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserId(email):
    """ Return a USER id
        Args: An email address

        Return: IF User in the database:
                    A User record from USER table. class
                otherwise:
                    None
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
# Logout and remove session


@app.route('/gdisconnect')
def gdisconnect():
    """ Revoke the token and delete user attributes in login_session.
        By removing info from login_session, the user will no longer has
        access to CUD functionality.
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gid']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully disconnected.")
        return redirect(url_for('showCatalog'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        flash("Failed to revoke token for given user.")
        return redirect(url_for('showCatalog'))


# Home Page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """ Shows all catalog and items in the application. Everyone has access
        to this page. If a user is logged in, their usernames will be passed to
        show the name and log out button.
    """

    catalogs = session.query(Catalog).order_by(asc(Catalog.name))
    items = session.query(Item).order_by(Item.created_date.desc())
    if 'username' in login_session:
        username = login_session['username']
        return render_template(
            'home.html',
            catalogs=catalogs,
            items=items,
            username=username)
    return render_template('home.html', catalogs=catalogs, items=items)


@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/items')
def showItem(catalog_id):
    """ Shows all items under a particular catalog. Additionally, all Catalogs
        will be shown. If user has created the catalog, additional buttons
        will be shown in the page to edit and delete the catalogself.

        Args: Catalog_id

        Return: Valid catalog_id : Redirects to category.html
                                    with or without user information.
                Invalid catalog_id: Redirects to main page with a message.
    """
    try:
        catalog = session.query(Catalog).filter_by(id=catalog_id).one()
        items = session.query(Item).filter_by(catalog_id=catalog_id)
        catalogs = session.query(Catalog).order_by(asc(Catalog.name))
        if 'username' in login_session:
            userid = getUserId(login_session['email'])
            username = getUserInfo(userid).name
            print(username)
            return render_template(
                'category.html',
                catalogs=catalogs,
                items=items,
                catalog=catalog,
                userid=userid,
                username=username)
        else:
            return render_template(
                'category.html',
                catalogs=catalogs,
                items=items,
                catalog=catalog)
    except BaseException:
        flash("Oops! Invalid Catalog ID!")
        return redirect(url_for('showCatalog'))


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>')
def menuItemDesc(catalog_id, item_id):
    """ Shows details about a particular item, if item id and catalog id
        match with a record in the database. IF the logged in user has
        created the item, options will be available for them to modify the
        item.

        Args: catalog_id, item_id

        Return: Valid catalog_id and item_id : Redirects to item.html
                                    with or without user information.
                Invalid args: Redirects to main page with a message.
    """
    try:
        item = session.query(Item).filter_by(
            id=item_id, catalog_id=catalog_id).one()
        if 'username' in login_session:
            userid = getUserId(login_session['email'])
            username = getUserInfo(userid).name
            print(username)
            return render_template(
                'item.html',
                item=item,
                userid=userid,
                username=username)
        else:
            return render_template('item.html', item=item)
    except BaseException:
        flash("Oops! Invalid Item Name!")
        return redirect(url_for('showCatalog'))


@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    """ Logged in users can create a new catalog.
        Only logged in users have access to this page.

        The primary key in the CATALOG table is catalog_id, However, Catalog
        names are unique. There will be a message for users in case
        they added a duplicate catalog name.

        Args:

        Return: A new record  with different catalog name will be added to
        the CATALOG talbe in the database.
    """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(
            name=request.form['name'],
            user_id=login_session['user_id'])
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
        userid = getUserId(login_session['email'])
        return render_template('newCatalog.html', userid=userid)


@app.route('/catalog/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    """ Logged in users can edit a catalog.
        Only logged in users have access to this page. Only the creator of
        catalogs are authorized to edit catalogs.

        Args: catalog_id

        Return: If any records with catalog_id found, an edit on a catalog
                record will be applied.
    """
    if 'username' not in login_session:
        return redirect('/login')

    editCatalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if editCatalog.user_id != login_session['user_id']:
        flash('You are not authorized to edir this Catalog.')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        if request.form['name']:
            editCatalog.name = request.form['name']
            flash('Catalog Successfully Edited %s' % editCatalog.name)
            return redirect(url_for('showCatalog'))
    else:

        return render_template(
            'editCatalog.html',
            catalog=editCatalog,
            username=login_session['username'])


@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    """ Logged in users can delete a catalog.
        Only logged in users have access to this page. Only the creator of
        catalogs are authorized to delete catalogs. Users will be redirected
        to another page for confirmation.

        Args: catalog_id

        Return: If any records with catalog_id found, it will be deleted.
    """
    if 'username' not in login_session:
        return redirect('/login')

    deleteCatalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if deleteCatalog.user_id != login_session['user_id']:
        flash('You are not authorized to delete this Catalog.')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        if request.form['delete_catalog']:
            if request.form['delete_catalog'] == "1":
                if session.query(Item).filter_by(
                        catalog_id=catalog_id).count() == 0:
                    session.delete(deleteCatalog)
                    flash('%s Successfully Deleted' % deleteCatalog.name)
                    session.commit()
                    return redirect(url_for('showCatalog'))
                else:
                    flash(
                        'You cannot delete %s. Remove %s Items First!' %
                        (deleteCatalog.name, deleteCatalog.name))
                    return redirect(url_for('showCatalog'))
            else:
                return redirect(url_for('showCatalog'))
    else:

        return render_template(
            'deleteCatalog.html',
            catalog=deleteCatalog,
            username=login_session['username'])


@app.route('/catalog/items/new/', methods=['GET', 'POST'])
def newItem():
    """ Logged in users can create a new item.
        Only logged in users have access to this page.
        Users have only access to add an item to their own category.
        Args:

        Return: A new item will be added to a category.
    """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            catalog_id=request.form['catalog_id'],
            user_id=login_session['user_id'])
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
        userid = getUserId(login_session['email'])
        catalogs = session.query(Catalog).filter_by(
            user_id=userid).order_by(asc(Catalog.name))
        username = getUserInfo(userid).name
        return render_template(
            'newItem.html',
            catalogs=catalogs,
            userid=userid,
            username=username)


@app.route(
    '/catalog/<int:catalog_id>/item/<int:item_id>/edit',
    methods=[
        'GET',
        'POST'])
def editItem(catalog_id, item_id):
    """ Logged in users can edit an item.
        Only logged in users have access to this page. Only the creator of
        items are authorized to edit items.

        Args: catalog_id, item_id

        Return: If any records with catalog_id and item_id found, an edit on
        an item will be applied.
    """
    if 'username' not in login_session:
        return redirect('/login')
    catalogs = session.query(Catalog).order_by(asc(Catalog.name))
    editItem = session.query(Item).filter_by(
        id=item_id, catalog_id=catalog_id).one()
    if editItem.user_id != login_session['user_id']:
        flash('You are not authorized to edit this Item.')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        if request.form['name'] and request.form['catalog_id']:
            editItem.name = request.form['name']
            editItem.description = request.form['description']
            editItem.catalog_id = request.form['catalog_id']
            flash('Item Successfully Edited %s' % editItem.name)
            return redirect(url_for('showCatalog'))
    else:

        return render_template(
            'editItem.html',
            item=editItem,
            catalogs=catalogs,
            username=login_session['username'])


@app.route(
    '/catalog/<int:catalog_id>/item/<int:item_id>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteItem(item_id, catalog_id):
    """ Logged in users can delete an item.
        Only logged in users have access to this page. Only the creator of
        items are authorized to delete items. Users will be redirected
        to another page for confirmation.

        Args: item_id, catalog_id

        Return: If any records with item_id and catalog_id found, it will be
                deleted.
    """
    if 'username' not in login_session:
        return redirect('/login')

    deleteItem = session.query(Item).filter_by(id=item_id).one()
    if deleteItem.user_id != login_session['user_id']:
        flash('You are not authorized to delete this Item.')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        if request.form['delete_item']:
            if request.form['delete_item'] == "1":
                session.delete(deleteItem)
                flash('Item %s Successfully Deleted' % deleteItem.name)
                session.commit()
                return redirect(url_for('showCatalog'))
            else:
                return redirect(url_for('showCatalog'))
    else:

        return render_template(
            'deleteItem.html',
            item=deleteItem,
            username=login_session['username'])


@app.route('/catalog/JSON')
def allCatalogsJSON():
    """
        Create a JSON file with all catalogs.
    """
    catalogs = session.query(Catalog)
    q = session.query(
        Catalog, Item).join(
        Item, Item.catalog_id == Catalog.id).all()
    return jsonify(Catalogs=[i.serialize for i in catalogs])


@app.route('/catalog/<int:catalog_id>/item/JSON')
def ItemsCatalogJSON(catalog_id):
    """
        Create a JSON file with all items belog to a particular catalog.
    """
    items = session.query(Item).filter_by(
        catalog_id=catalog_id).order_by(
        Item.created_date.desc())
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/item/JSON')
def allItemsJSON():
    """
        Create a JSON file with all items.
    """
    items = session.query(Item).order_by(Item.created_date.desc())
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def itemJSON(item_id, catalog_id):
    """
        Create a JSON file with information about a particular item.
    """
    item = session.query(Item).filter_by(id=item_id)
    return jsonify(Items=[i.serialize for i in item])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='127.0.0.1', port=6789)
