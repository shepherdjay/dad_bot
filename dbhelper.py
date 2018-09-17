import sqlite3


class DBHelper:
    def __init__(self, dbname="dadinfo.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

# standard items table
    def setup(self):
        tblstmt = "CREATE TABLE IF NOT EXISTS items (description text, owner_id text, category text, owner_name text," \
                  " datetime datetime)"
        itemidx = "CREATE INDEX IF NOT EXISTS itemIndex ON items (description ASC)"
        ownidx = "CREATE INDEX IF NOT EXISTS ownIndex ON items (owner_id ASC)"
        catidx = "CREATE INDEX IF NOT EXISTS ownIndex ON items (category ASC)"
        self.conn.execute(tblstmt)
        self.conn.execute(itemidx)
        self.conn.execute(ownidx)
        self.conn.execute(catidx)
        self.conn.commit()

    def add_item(self, item_text, owner_id, category, owner_name, datetime):
        stmt = "INSERT INTO items (description, owner_id, category, owner_name, datetime) VALUES (?, ?, ?, ?, ?)"
        args = (item_text, owner_id, category, owner_name, datetime)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, item_text, owner_id):
        stmt = "DELETE FROM items WHERE description = (?) AND owner_id = (?)"
        args = (item_text, owner_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items_by_owner_id(self, owner_id, datetime=False):
        stmt = "SELECT description FROM items WHERE owner_id = (?)"
        args = (owner_id, )
        if datetime:
            stmt = "SELECT description, datetime FROM items WHERE owner_id = (?)"
            args = (owner_id, )
            return self.conn.execute(stmt, args)
        else:
            return [x[0] for x in self.conn.execute(stmt, args)]
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_items_by_category(self, category, datetime=False):
        stmt = "SELECT description FROM items WHERE category = (?)"
        args = (category, )
        if datetime:
            stmt = "SELECT description, datetime FROM items WHERE category = (?)"
            args = (category, )
            return self.conn.execute(stmt, args)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_last_x_requested_items(self, number_of_events, datetime=False):
        stmt = "SELECT description FROM items ORDER BY datetime DESC LIMIT (?)"
        args = (number_of_events, )
        if datetime:
            stmt = "SELECT description, datetime FROM items ORDER BY datetime DESC LIMIT (?)"
            args = (number_of_events, )
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
        args = (owner_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_feed_chats(self):
        stmt = "SELECT owner_id FROM feeds"
        self.conn.execute(stmt)
        return [x[0] for x in self.conn.execute(stmt)]
