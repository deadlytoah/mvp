import config
from sdb import Sdb
from key import Key

def find_all():
    """Finds all verses in the database."""
    with Sdb(config.translation + config.DB_EXT) as database:
        verse_table = [table for table in database.get_tables()
                       if table.name() == 'verse'][0]
        verse_table.create_manager()
        verse_table.verify()
        verse_table.service()
        return verse_table.select_all()

def find_by_book_and_chapter(book, chapter):
    """Finds verses by the given book and chapter."""

    with Sdb(config.translation + config.DB_EXT) as database:
        verse_table = [table for table in database.get_tables()
                       if table.name() == 'verse'][0]
        verse_table.create_manager()
        verse_table.verify()
        verse_table.service()

        return [rec for rec in verse_table.select_all()
                if rec['deleted'] == '0' and
                _key_starts_with(rec['key'], book, chapter)]

def insert(book, chapter, verseno, text):
    """Inserts a verse."""

    with Sdb(config.translation + config.DB_EXT) as database:
        verse_table = [table for table in database.get_tables()
                       if table.name() == 'verse'][0]
        verse_table.create_manager()
        verse_table.verify()
        verse_table.service()

        key = ' '.join([book, str(chapter)])
        key = ':'.join([key, str(verseno)])
        return verse_table.insert({
            'key': key,
            'text': text,
            'deleted': '0',
        })

def _key_starts_with(key_string, book, chapter):
    """Checks if the given record has book and chapter as the key."""
    key = Key.from_str(key_string)
    if key.book == book and key.chapter == str(chapter):
        return True
    else:
        return False
