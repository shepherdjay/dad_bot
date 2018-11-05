from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class SqlAlch(object):
    Base = declarative_base()

    class Items(Base):
        __tablename__ = "items"

        id = Column(Integer, primary_key=True)
        description = Column(String)
        owner_id = Column(String)
        owner_name = Column(String)
        category = Column(String)
        datetime = Column(DateTime)

    Index('itemIndex', Items.description.asc())
    Index('ownIndex', Items.owner_id.asc(), Items.category.asc())


class DBHelper:
    def __init__(self, dbname="dadinfo.sqlite"):
        self.dbname = dbname
        self.alchemyengine = create_engine("sqlite:///" + dbname)
        self.alchemybase = SqlAlch.Base
        self.conn = self.alchemyengine.raw_connection()
        self._session = sessionmaker(bind=self.alchemyengine)
        self.session = self._session()

    # standard items table
    def setup(self):
        self.alchemybase.metadata.bind = self.alchemyengine
        self.alchemybase.metadata.create_all(self.alchemyengine)

    def add_item(self, item_text, owner_id, category, owner_name, datetime):
        self.session.add(
            SqlAlch.Items(description=item_text, owner_id=owner_id, category=category, owner_name=owner_name,
                          datetime=datetime))
        self.session.commit()

    def delete_item(self, item_text, owner_id):
        stmt = "DELETE FROM items WHERE description = (?) AND owner_id = (?)"
        args = (item_text, owner_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items_by_owner_id(self, owner_id, datetime=False):
        stmt = "SELECT description FROM items WHERE owner_id = (?)"
        args = (owner_id,)
        if datetime:
            stmt = "SELECT description, datetime FROM items WHERE owner_id = (?)"
            args = (owner_id,)
            return self.conn.execute(stmt, args)
        else:
            return [x[0] for x in self.conn.execute(stmt, args)]
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_items_by_category(self, category, limit, datetime=False):
        stmt = "SELECT description FROM items WHERE category = (?) ORDER BY datetime LIMIT = (?)"
        args = (category, limit,)
        if datetime:
            return self.session.query(
                SqlAlch.Items.description, SqlAlch.Items.datetime).filter(
                SqlAlch.Items.category == category).order_by(
                SqlAlch.Items.datetime.desc())[:limit]
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_last_x_requested_items(self, number_of_events, datetime=False):
        stmt = "SELECT description FROM items ORDER BY datetime DESC LIMIT (?)"
        args = (number_of_events,)
        if datetime:
            stmt = "SELECT description, datetime FROM items ORDER BY datetime DESC LIMIT (?)"
            args = (number_of_events,)
            return self.conn.execute(stmt, args)
        else:
            return [x[0] for x in self.conn.execute(stmt, args)]

    # additional feeds table
    def setup_feed_table(self):
        tblstmt = "CREATE TABLE IF NOT EXISTS feeds (owner_id text, owner_name text)"
        self.conn.execute(tblstmt, )
        self.conn.commit()

    def add_feed_member(self, owner_id, owner_name):
        stmt = "INSERT INTO feeds (owner_id, owner_name) VALUES (?, ?)"
        args = (owner_id, owner_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def del_feed_member(self, owner_id):
        stmt = "DELETE FROM feeds WHERE owner_id = (?)"
        args = (owner_id,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_feed_chats(self):
        stmt = "SELECT owner_id FROM feeds"
        self.conn.execute(stmt)
        return [x[0] for x in self.conn.execute(stmt)]
