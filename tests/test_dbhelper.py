import datetime

import pytest

from dbhelper import DBHelper


@pytest.fixture
def testdb():
    database = DBHelper(dbname=":memory:")
    database.setup()
    database.alchemyengine.echo = True
    return database


@pytest.fixture
def populated_testdb(testdb):
    item1 = {"item_text": "This is a test item", "owner_id": "1", "category": "Medication",
             "owner_name": "Nobody"}
    item2 = {"item_text": "This is a second test item", "owner_id": "2", "category": "Medication",
             "owner_name": "Somebody"}
    item3 = {"item_text": "This is a special test item", "owner_id": "1", "category": "Special",
             "owner_name": "Somebody"}
    item4 = {"item_text": "This is a second special test item", "owner_id": "2", "category": "Special",
             "owner_name": "Somebody"}
    testdb.add_item(**item1, datetime=datetime.datetime.now())
    testdb.add_item(**item2, datetime=datetime.datetime.now())
    testdb.add_item(**item3, datetime=datetime.datetime.now())
    testdb.add_item(**item4, datetime=datetime.datetime.now())
    return testdb


def test_add_item_and_basic_retrieve(testdb):
    #     def add_item(self, item_text, owner_id, category, owner_name, datetime):
    testdb.add_item(item_text="This is a test item", owner_id="123456789", category="Medication", owner_name="Nobody",
                    datetime=datetime.datetime.now())
    testdb.add_item(item_text="This is a second test item", owner_id="666", category="Medication", owner_name="Somebody",
                    datetime=datetime.datetime.now())
    item_count = testdb.conn.execute("SELECT COUNT(*) from items").fetchone()[0]
    assert ["This is a test item"] == testdb.get_items_by_owner_id(owner_id=123456789)
    assert 2 == item_count


def test_get_items_by_category_with_datetime(populated_testdb):
    category_items = [_[0] for _ in list(populated_testdb.get_items_by_category("Medication", limit=5, datetime=True))]
    assert 2 == len(category_items)
    assert "This is a test item" in category_items
    assert "This is a second test item" in category_items

def test_get_items_by_owner_id(populated_testdb):
    owner_items = list(populated_testdb.get_items_by_owner_id(1))
    assert 2 == len(owner_items)
    assert "This is a test item" in owner_items
