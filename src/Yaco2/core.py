"""
Yaco2 - a simple dictionary

Based on the UserDict
"""

import copy
import re
import sys
import types


class Yaco(object):

    """
    # >>> v= Yaco()
    # >>> v['a'] = 1
    # >>> assert(v['a'] == 1)
    # >>> v= Yaco({'a':2})
    # >>> assert(v['a'] == 2)

    """

    def __init__(self,
                 data=None,
                 branch='',
                 default="__RAISE_ERROR__"):


        self.default = default

        if data is None:
            self.data = {}
        elif isinstance(data, Yaco):
            self.data = data.data
        elif isinstance(data, dict):
            self.data = data
        else:
            raise Exception("unexpected Yaco init object: %s", data)

        self.check_key_name(branch)
        self.branch = branch.strip('.')

    def check_key_name(self, name):
        """
        branches/keys can't be anything.
        Keys may only contain:
            a-zA-Z0-9_.

        >>> f = Yaco()
        >>> assert(f.check_key_name('Aaz829387asdnvzjkdf__..'))
        >>> assert(not f.check_key_name('.#@#*()@(*&#'))
        """
        if len(name) == 0:
            return True
        return re.match(r'^[\w\.]+$', name)

    # allow with: use
    def __enter__(self):
        pass


    def __exit__(self):
        pass

    def get_branch(self, branch, absolute=False):
        """
        Return a branch

        >>> y = Yaco()
        >>> y['a'] = 1
        >>> y['a.b'] = 2
        >>> y['a.b.c'] = 3

        # get a branch:
        >>> z = y.get_branch('a')

        # make sure a branch has the proper structure
        >>> assert(z.data is y.data)
        >>> assert(z is not y)
        >>> assert(z.__class__ is y.__class__)
        >>> assert(dict(z) == {'b.c' : 3, 'b': 2})

        # branch of branchs
        >>> z2 = z.get_branch('b')
        >>> assert(dict(z2) == {'c' : 3})

        """
        new_branch = branch
        if not absolute:
            new_branch = "{}.{}".format(self.branch, new_branch)
        new_branch = new_branch.strip(".")

        return self.__class__(self, branch=new_branch)

    def __repr__(self):
        return repr(self.data)

    def __cmp__(self, other):
        """
        >>> a = Yaco({'a' : 1, 'b' : 2})
        >>> b = Yaco({'a' : 1, 'b' : 2})
        >>> assert(a == b)
        >>> c = Yaco({'a' : 1, 'b' : 3})
        >>> assert(a != c)
        """
        return cmp(dict(self), dict(other))


    __hash__ = None  # Avoid Py3k warning

    def __len__(self):
        """
        >>> a = Yaco({'a' : 1, 'b' : 2})
        >>> assert(len(a) == 2)
        """
        return len(self.data)

    def __getitem__(self, key):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> assert(a['a.a'] == 1)
        >>> assert(b['a'] == 1)
        >>> assert(a['a.b'] == 2)
        >>> assert(b['b'] == 2)
        """
        if self.branch:
            key = '{}.{}'.format(self.branch, key)

        try:
            return self.data[key]
        except KeyError:
            if self.default == "__RAISE_ERROR__":
                raise
            else:
                return self.default

    def __setitem__(self, key, item):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> b['c'] = 3
        >>> assert(a['a.c'] == 3)
        >>> assert(b['c'] == 3)
        """
        if self.branch:
            key = '{}.{}'.format(self.branch, key)
        self.data[key] = item

    def __delitem__(self, key):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> assert(a.has_key('a.a'))
        >>> assert(b.has_key('a'))
        >>> del b['a']
        >>> assert(not a.has_key('a.a'))
        >>> assert(not b.has_key('a'))
        """
        if self.branch:
            key = '{}.{}'.format(self.branch, key)
        del self.data[key]

    def has_key(self, key):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> assert(a.has_key('a.a'))
        >>> assert(b.has_key('a'))
        """
        if self.branch:
            key = '{}.{}'.format(self.branch, key)
        return key in self.data

    def clear(self):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> assert(len(a) == 2)
        >>> assert(len(b) == 2)
        >>> a.clear()
        >>> assert(len(a) == 0)
        >>> assert(len(b) == 0)
        """
        self.data.clear()

    def copy(self):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.copy()
        >>> assert(b.__class__ == a.__class__)
        >>> assert(b == a)
        >>> assert(not b is a)
        """
        new_data = copy.copy(self.data)
        c = self.__class__(new_data, branch=self.branch)
        return c

    def iteritems(self):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
        >>> ii = a.iteritems()
        >>> assert(isinstance(ii, types.GeneratorType))
        >>> assert(len(list(ii)) == 3)
        >>> b = a.get_branch('a')
        >>> ii = list(sorted(b.iteritems()))
        >>> assert(len(ii) == 2)
        >>> assert(ii == [('a', 1), ('b', 2)])
        """
        for k, v in self.data.iteritems():
            if not self.branch:
                yield k, v
            elif k.startswith('{}.'.format(self.branch)):
                yield (k[len(self.branch) + 1:], v)

    def iterkeys(self):
        for (k, v) in self.iteritems():
            yield k

    def itervalues(self):
        for (k, v) in self.iteritems():
            yield v

    def items(self):
        return self.iteritems()

    def values(self):
        return self.itervalues()

    def keys(self):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
        >>> assert(set(a.keys()) == set(['a.a', 'a.b', 'c.b']))
        >>> s = a.get_branch('a')
        >>> assert(set(s.keys()) == set(['a', 'b']))
        """
        return self.iterkeys()

    def update(self, dict=None):
        """
        >>> a = Yaco({'a.a' : 1})
        >>> a.update({'b.b' : 2, 'c.d' : 3})
        >>> assert(a['c.d'] == 3)
        >>> b = Yaco({'e.f' : 4})
        >>> a.update(b)
        >>> assert(a['e.f'] == 4)
        >>> c = b.get_branch('e')
        >>> a.update(c)
        >>> assert(a['f'] == 4)
        """
        for k, v in dict.iteritems():
            self[k] = v

    def __contains__(self, key):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
        >>> assert('a.a' in a)
        >>> assert('a.e' not in a)
        >>> b = a.get_branch('a')
        >>> assert('a' in b)
        >>> assert('e' not in b)
        """
        if self.branch:
            key = '{}.{}'.format(self.branch, key)
        return key in self.data

    def get(self, key, failobj=None):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
        >>> assert(a.get('a.a') == 1)
        >>> assert(a.get('a.c', 12) == 12)
        >>> b = a.get_branch('a')
        >>> assert(b.get('a', 12) == 1)
        """
        if key not in self:
            return failobj

        return self[key]

    def pretty(self, prefix=""):
        """
        >>> y = Yaco()
        >>> y['a'] = 1
        >>> y['b'] = 2
        >>> y['c.d'] = 3
        >>> y['c.d.e'] = 4
        >>> y['c.d.f'] = 5
        >>> y['g'] = 6
        >>> p = y.pretty()
        >>> assert(isinstance(p, str))
        """
        rv = []
        for k in sorted(self.keys()):
            v = self[k]
            rv.append("{}{}: '{}'".format(prefix, k, v))
        return "\n".join(rv)

    # def setdefault(self, key, failobj=None):
    #     if key not in self:
    #         self[key] = failobj
    #     return self[key]

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
