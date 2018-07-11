# coding: utf-8
""" Creates and initialises one or more databases """

import argparse
from sdb.sdb import Sdb

DB_EXT='.sdb'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Creates a new database by the given name.')
    parser.add_argument('name', nargs='+', help='name of the database')
    opts = parser.parse_args()

    for name in opts.name:
        Sdb.create(name + DB_EXT)

        with Sdb(name + DB_EXT) as sdb:
            sdb.create_table('verse.mjson')
