from sdb.sdb import Sdb

if __name__ == '__main__':
    Sdb.create('nkjv.sdb')

    with Sdb('nkjv.sdb') as sdb:
        sdb.create_table('verse.mjson')
