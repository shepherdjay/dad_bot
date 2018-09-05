import sqlite3


class DBHelper:
    def __init__(self, dbname="dadinfo.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

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

    def get_items_by_owner_id(self, owner_id):
        stmt = "SELECT description FROM items WHERE owner_id = (?)"
        args = (owner_id, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_items_by_category(self, category):
        stmt = "SELECT description FROM items WHERE category = (?)"
        args = (category,)
        return [x[0] for x in self.conn.execute(stmt, args)]
