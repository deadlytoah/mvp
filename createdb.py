# coding: utf-8
""" Creates and initialises one or more databases """

import argparse
import config
from sdb.sdb import Sdb

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Creates a new database by the given name.')
    parser.add_argument('name', nargs='+', help='name of the database')
    opts = parser.parse_args()

    for name in opts.name:
        Sdb.create(name + config.DB_EXT)

        with Sdb(name + config.DB_EXT) as sdb:
            sdb.create_table('verse.mjson')
