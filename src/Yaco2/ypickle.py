import logging
import os
import pickle
import re
import tempfile
import types
import cPickle

from Yaco2.core import Yaco

lg = logging.getLogger(__name__)


class InvalidYacoSlice(Exception):
    pass


class InvalidYacoKey(Exception):
    pass


def _test_yacopickle():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    return YacoPickle(tf.name)

class YacoPickle(Yaco):

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

        >>> f = _test_yacopickle()
        >>> assert(isinstance(f, YacoPickle))
        """

        super(YacoPickle, self).__init__(
            data={}, branch=branch,
            default=default)

        if isinstance(data, str) or isinstance(data, unicode):
            "assume this is a path to a database"
            self.datapath = data
            self.open()

        elif isinstance(data, YacoPickle):
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
        if delete_db:
            os.remove(self.datapath)

    def open(self):
        """
        Open database file & create tables (if needed)

        >>> f = _test_yacopickle()
        >>> f.close(delete_db=True)
        """
        dbpath, dbname = os.path.split(self.datapath)

        if not os.path.exists(dbpath):
            os.makedirs(dbpath)

        if not os.path.exists(self.datapath):
            return

        if os.path.getsize(self.datapath) == 0:
            return

        with open(self.datapath, 'rb') as F:
            d = pickle.load(F)
            self.update(d)

    def _save(self, closing=False):
        with open(self.datapath, 'wb') as F:
            pickle.dump(dict(self), F)


    def __setitem__(self, key, item):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> b['c'] = 3
        >>> assert(a['a.c'] == 3)
        >>> assert(b['c'] == 3)
        """
        super(YacoPickle, self).__setitem__(key, item)
        self._save()

    def __delitem__(self, key):
        """
        >>> f = _test_yacopickle()
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
        super(YacoPickle, self).__delitem__(key)
        self._save()

    def clear(self):
        """
        Empty the database


        """
        super(YacoPickle, self).clear()
        self._save()

