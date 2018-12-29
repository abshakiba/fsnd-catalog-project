# Item catalog

## How to run?

* Make sure you have all required packages installed in your machine. This application is working on port `6789`. Make sure no other applications is listening on this port.

* Setup the database and tables: `python database_setup.py`

* Optional: Fill dummy records to the database: `python lotsofcatalogs.py`

* Run the application: `python server.py`

## How does it work?

Publicly, you can view all the catalogs and items in the application. If you want to add/edit/delete data, you need to login to the application using your google account. You can securely use Google Authentication APIs to login.

When You are logged in, you can add, edit, and delete your own catalogs and items. You do not have access to modify others data.

## Does this app have any APIs?

Yes. You can use these links to get access to JSON formatted records:

* `/catalog/JSON`, gives you all Catalogs
* `/catalog/catalog_id/item/JSON`, gives you all items under a particular catalog
* `/catalog/item/JSON`, gives you all items
* `/catalog/catalog_id/item/item_id/JSON` gives you all information about a particular item.
