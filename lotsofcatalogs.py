from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Catalog, Item

engine = create_engine('sqlite:///catalogs.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="Robert Deniro", email="rob@de.niro",
             picture='https://pmcdeadline2.files.wordpress.com/2016/10/robert-de-niro1.jpg')
session.add(User1)
session.commit()

# Catalog 1 and items
catalog1 = Catalog(user_id=1, name="Soccer")

session.add(catalog1)
session.commit()

item1 = Item(user_id=1, name="Two shinguards", description="A shin guard or shin pad is a piece of equipment worn on the front of a player’s shin to protect them from injury.",
                catalog_id=catalog1.id)

session.add(item1)
session.commit()


item2 = Item(user_id=1, name="Shinguards", description="The shin guard was inspired by the concept of a greave. A greave is a piece of armor used to protect the shin.",
                catalog_id=catalog1.id)

session.add(item2)
session.commit()


item3 = Item(user_id=1, name="Jersey", description="The Jersey official football team represents the British Crown Dependency of Jersey in non-FIFA International matches.",
                catalog_id=catalog1.id)

session.add(item3)
session.commit()


item4 = Item(user_id=1, name="Soccer Cleats", description="Football shoes have studs on their soles Cleats or studs are protrusions on the sole of a shoe, or on an external attachment to a shoe, that provide additional traction on a soft or slippery surface.",
                catalog_id=catalog1.id)

session.add(item4)
session.commit()

# Catalog 2

catalog2 = Catalog(user_id=1, name="Bascketball")

session.add(catalog2)
session.commit()

# Catalog 3 and items

catalog3 = Catalog(user_id=1, name="Baseball")

session.add(catalog3)
session.commit()

item5 = Item(user_id=1, name="Bat", description="A baseball bat is a smooth wooden or metal club used in the sport of baseball to hit the ball after it is thrown by the pitcher.",
                catalog_id=catalog3.id)

session.add(item5)
session.commit()

# Catalog 4 and items

catalog4 = Catalog(user_id=1, name="Frisbee")

session.add(catalog4)
session.commit()

item6 = Item(user_id=1, name="Frisbee", description="A frisbee, also called a flying disc, is a gliding toy or sporting item that is generally plastic and roughly 20 to 25 centimetres in diameter with a pronounced lip.",
                catalog_id=catalog4.id)

session.add(item6)
session.commit()

# Catalog 5

catalog5 = Catalog(user_id=1, name="Snowboarding")

session.add(catalog5)
session.commit()

item7 = Item(user_id=1, name="Goggles", description="Goggles, or safety glasses, are forms of protective eyewear that usually enclose or protect the area surrounding the eye in order to prevent particulates, water or chemicals from striking the eyes.",
                catalog_id=catalog5.id)

session.add(item7)
session.commit()

item8 = Item(user_id=1, name="Snowboard", description="Snowboards are boards where both feet are secured to the same board, which are wider than skis, with the ability to glide on snow.",
                catalog_id=catalog5.id)

session.add(item8)
session.commit()

# Catalog 6

catalog6 = Catalog(user_id=1, name="Rock Climbing")

session.add(catalog6)
session.commit()

# Catalog 7

catalog7 = Catalog(user_id=1, name="Foosball")

session.add(catalog7)
session.commit()

# Catalog 8

catalog8 = Catalog(user_id=1, name="Skating")

session.add(catalog8)
session.commit()

# Catalog 9 and items

catalog9 = Catalog(user_id=1, name="Hockey")

session.add(catalog9)
session.commit()

item9 = Item(user_id=1, name="Stick", description="An ice hockey stick is a piece of equipment used in ice hockey to shoot, pass, and carry the puck across the ice.",
                catalog_id=catalog9.id)

session.add(item9)
session.commit()

print("Catalogs and Items added!")
