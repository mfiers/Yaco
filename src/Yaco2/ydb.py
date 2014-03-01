import logging
import os
import pickle
import re
import sqlite3
import tempfile
import types

from Yaco2.core import Yaco

lg = logging.getLogger(__name__)


class InvalidYacoSlice(Exception):
    pass


class InvalidYacoKey(Exception):
    pass


def _test_yacodb():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    return YacoDb(tf.name)


class YacoDb(Yaco):

    """
    Simple key value database, based on sqlite3.

    keys are hierarchical / levels are divided by dots.

    Extra possibilities: slicing - get instances that contain
    a subtree of the key/value database
    """

    def __init__(self, data, branch='',
                 default="__RAISE_ERROR__"):
        """
        Create the object & open the database

        >>> f = _test_yacodb()
        >>> assert(isinstance(f, YacoDb))
        """

        super(YacoDb, self).__init__(
            data={}, branch=branch,
            default=default)

        if isinstance(data, str) or isinstance(data, unicode):
            "assume this is a path to a database"
            self.datapath = data
            self.open()

        elif isinstance(data, YacoDb):
            self.data = data.data
            self.datapath = data.datapath
        else:
            raise Exception("unexpected Yaco init object: %s", data)


    def __exit__(self):
        self.data.close()

    def close(self, delete_db=False):
        """
        Close the database
        """
        self.data.close()
        if delete_db:
            os.remove(self.datapath)

    def open(self):
        """
        Open database file & create tables (if needed)

        >>> f = _test_yacodb()
        >>> assert(isinstance(f.data, sqlite3.Connection))
        >>> f.close(delete_db=True)
        """
        dbpath, dbname = os.path.split(self.datapath)
        if not os.path.exists(dbpath):
            os.makedirs(dbpath)
        lg.debug("opening Yaco2 database: {0}".format(self.datapath))
        self.data = sqlite3.connect(self.datapath)
        self.data.text_factory = bytes
        self.execute("""
            CREATE TABLE IF NOT EXISTS yaco(
                key text PRIMARY KEY,
                val text
            )""")

    def execute(self, sql, *data):
        """
        Execute a sql query & return
        the cursor

        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> c = f.execute('SELECT * FROM yaco LIMIT 5')
        >>> r = c.fetchall()
        >>> assert(len(r) == 5)
        >>> f.close(delete_db=True)
        """
        c = self.data.cursor()
        c.execute(sql, *data)
        self.data.commit()
        return c

    def __getitem__(self, key):
        """
        >>> f = _test_yacodb()
        >>> f['key'] = 'val'
        >>> assert(f['key'] == 'val')

        #test persistence
        >>> dbpath = f.datapath
        >>> f.close()
        >>> g = YacoDb(dbpath)
        >>> assert(g['key'] == 'val')

        #test slicing
        >>> g['a.b'] = 1
        >>> g['a.c'] = 2
        >>> a = g.get_branch('a')
        >>> assert(a['b'] == 1)
        >>> assert(a['c'] == 2)
        >>> f.close(delete_db=True)

        """

        # adapt key if branchbed
        if self.branch != '':
            key = '{0}.{1}'.format(self.branch, key)

        c = self.execute("""
            SELECT * from yaco
            WHERE key = ?""", (key,))
        r = c.fetchone()

        if r is None:
            if self.default == "__RAISE_ERROR__":
                raise KeyError(key)
            else:
                return self.default

        return pickle.loads(r[1])

    def __setitem__(self, key, val):
        """
        >>> f = _test_yacodb()
        >>> f['key'] = 'val'
        >>> assert(f['key'] == 'val')
        >>> assert(f['key2'] == 'val')
        Traceback (most recent call last):
        ...
        KeyError: 'key2'

        # test slicing
        >>> a = f.get_branch('a')
        >>> a['b'] = 1
        >>> assert('a.b' in f)
        >>> assert('b' in a)
        >>> f.close(delete_db=True)

        """
        vts = pickle.dumps(val)
        if self.branch:
            key = '{0}.{1}'.format(self.branch, key)
        self.execute("""
            INSERT OR REPLACE
            INTO yaco (key, val)
            VALUES (?, ?)""", (key, vts))

    def __delitem__(self, key):
        """
        >>> f = _test_yacodb()
        >>> f['a'] = 1
        >>> assert(f['a'] == 1)
        >>> del f['a']

        #test slicing
        >>> f['a.b'] = 1
        >>> f['a.c'] = 2
        >>> a = f.get_branch('a')
        >>> assert('b' in a)
        >>> del a['b']
        >>> assert('b' not in a)
        >>> assert('c' in a)
        >>> assert('a.b' not in f)
        >>> assert('a.c' in f)

        >>> f.close(delete_db=True)

        """
        if self.branch:
            key = '{0}.{1}'.format(self.branch, key)
            lg.critical(key)
        self.execute("""
            DELETE FROM yaco
            WHERE key = ?""", (key,))


    def clear(self):
        """
        Empty the database

        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> c = f.execute('SELECT * FROM yaco')
        >>> r = c.fetchall()
        >>> assert(len(r) == 10)

        >>> f.clear()

        >>> c = f.execute('SELECT * FROM yaco')
        >>> q = c.fetchall()
        >>> assert(len(q) == 0)
        >>> f.close(delete_db=True)
        >>>
        """
        c = self.execute("""
            DELETE FROM yaco""")

    def iteritems(self):
        """
        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> kys = f.iteritems()
        >>> assert(isinstance(kys, types.GeneratorType))
        >>> i = 0
        >>> for k, v in kys:
        ...     i += 1
        >>> assert(i == 10)

        # Test slicing
        >>> f['a.b'] = 1
        >>> f['a.c'] = 2
        >>> s = f.get_branch('a')
        >>> assert(set(s.iteritems()) == set([('b', 1), ('c', 2)]))

        >>> s.close()
        >>> f.close(delete_db=True)
        """

        step = 100
        offset = 0
        if self.branch == '':
            sql = """
                SELECT key,val from yaco
                LIMIT ? OFFSET ?"""
        else:
            sql = """
                SELECT key,val from yaco
                WHERE key LIKE '{0}.%'
                LIMIT ? OFFSET ?""".format(self.branch)

        while True:
            c = self.execute(sql, (step, offset))
            res = c.fetchall()
            if len(res) is 0:
                break
            for k, v in res:
                if self.branch != '':
                    k = k[len(self.branch) + 1:]
                yield (k.decode('ascii'), pickle.loads(v))
            offset += step

    def keys(self):
        """
        as dict.keys() - but returns an iterator -
        to make this work nicely. Note - do not change
        the contents of the database while iterating!

        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> kys = f.keys()
        >>> assert(isinstance(kys, types.GeneratorType))
        >>> i = 0
        >>> for k in kys:
        ...     i += 1
        >>> assert(i == 10)
        >>> f.close(delete_db=True)
        """
        for k, v in self.iteritems():
            yield k

    def iterkeys(self):
        """
        as keys()

        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> kys = f.iterkeys()
        >>> assert(isinstance(kys, types.GeneratorType))
        >>> i = 0
        >>> for k in kys:
        ...     i += 1
        >>> assert(i == 10)
        >>> f.close(delete_db=True)
        """
        return self.keys()

    def items(self):
        return self.iteritems()

    def itervalues(self):
        """
        >>> f = _test_yacodb()
        >>> for i in range(10):
        ...     f[i] = i
        >>> kys = f.itervalues()
        >>> assert(isinstance(kys, types.GeneratorType))
        >>> i = 0
        >>> for k in kys:
        ...     i += 1
        >>> assert(i == 10)
        >>> f.close(delete_db=True)
        """
        for k, v in self.iteritems():
            yield v

    def values(self):
        return self.itervalues()

    def has_key(self, key):
        """
        check if the key is in the database

        >>> f = _test_yacodb()
        >>> f['a'] = 1
        >>> assert(f.has_key('a'))
        >>> assert(not f.has_key('b'))
        >>> f.close(delete_db=True)
        """

        if self.branch:
            key = '{0}.{1}'.format(self.branch, key)

        c = self.execute("""
            SELECT * from yaco
            WHERE key = ?""", (key,))

        return not c.fetchone() is None

    def __contains__(self, key):
        """
        Makes 'a' in yacoobject work

        """
        return self.has_key(key)

    # def pop(self, key, *args):
    #     return self.data.pop(key, *args)

    # def popitem(self):
    #     return self.data.popitem()

    # @classmethod
    # def fromkeys(cls, iterable, value=None):
    #     d = cls()
    #     for key in iterable:
    #         d[key] = value
    #     return d
