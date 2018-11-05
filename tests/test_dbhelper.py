import datetime

import pytest

from dbhelper import DBHelper


@pytest.fixture(scope='module')
def testdb():
    database = DBHelper(dbname=":memory:")
    database.setup()
    return database


def test_add_item_and_basic_retrieve(testdb):
    #     def add_item(self, item_text, owner_id, category, owner_name, datetime):
    testdb.add_item(item_text="This is a test item", owner_id="123456789", category="Medication", owner_name="Nobody",
                    datetime=datetime.datetime.now())
    testdb.add_item(item_text="This is a test item 2", owner_id="666", category="Medication", owner_name="Somebody",
                    datetime=datetime.datetime.now())
    item_count = testdb.conn.execute("SELECT COUNT(*) from items").fetchone()[0]
    assert ["This is a test item"] == testdb.get_items_by_owner_id(owner_id=123456789)
    assert 2 == item_count