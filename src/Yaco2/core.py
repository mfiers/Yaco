"""
Yaco2 - a simple dictionary

Based on the UserDict
"""

import copy
import logging
import re
import sys
import types

lg = logging.getLogger(__name__)


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
            new_branch = "{0}.{1}".format(self.branch, new_branch)
        new_branch = new_branch.strip(".")
        rv = self.__class__(self, branch=new_branch)
        return rv

    def leaf(self):
        """
        Return the leaf name of the current branch

        >>> y = Yaco()
        >>> y['a.b.c.d'] = 1
        >>> b = y.get_branch('a.b.c')
        >>> assert(b.leaf() == 'c')
        """
        if not self.branch:
            return ""
        else:
            return self.branch.rsplit('.')[-1]

    def find_branch(self, pattern):
        """
        Find a pattern & return a series of branch names

        >>> y = Yaco()
        >>> y['a.b'] = 1
        >>> y['q.b'] = 1
        >>> y['a.c'] = 2
        >>> y['a.c.e'] = 2
        >>> y['a.d.c'] = 3
        >>> rv = set()
        >>> for y in y.find('a'):
        ...     rv.add(y.branch)
        >>> assert(rv == set(['a.c', 'a.d', 'a.b']))
        """

        regex = pattern.replace('*', r'[A-Za-z0-9_]+')
        regex = '^(' + regex + ')\.(.*)'
        rx = re.compile(regex)
        yielded = []
        for k in self.keys():
            mtch = rx.search(k)
            if not mtch:
                continue
            pre, to_yield = mtch.groups()
            to_yield = to_yield.split('.')[0]
            to_yield = '{0}.{1}'.format(pattern, to_yield)
            if to_yield in yielded:
                continue
            yielded.append(to_yield)
            yield self.get_branch(to_yield)

    find = find_branch

    def __str__(self):
        rv = ''
        if self.branch:
            rv = '[{0}]'.format(self.branch)

        rv += '{'

        keygen = self.keys()
        for i, k in enumerate(keygen):
            if i > 3:
                break
            if i > 0:
                rv += ','
            v = (" ".join(str(self[k]).split()))[:40]
            rv += "'{0}': {1}".format(k, v)

        try:
            nxt = keygen.next()
            rv += '...'
        except StopIteration:
            pass

        rv += '}'
        return rv

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        """
        >>> a = Yaco({'a' : 1, 'b' : 2})
        >>> b = Yaco({'a' : 1, 'b' : 2})
        >>> c = Yaco({'a' : 1, 'b' : 3})
        >>> assert(a == b)
        >>> assert(a != c)
        """
        ka = set(self.keys())
        if not hasattr(other, 'keys'):
            return False
        kb = set(other.keys())
        if ka != kb:
            return False

        for k in self.keys():
            if self[k] != other[k]:
                return False
        return True

    def __ne__(self, other):
        """ Use __eq__ """
        return not self == other

    def __cmp__(self, other):
        """ Use __eq__ """
        return self == other

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
            key = '{0}.{1}'.format(self.branch, key)

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
            key = '{0}.{1}'.format(self.branch, key)
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
            key = '{0}.{1}'.format(self.branch, key)
        del self.data[key]

    def has_key(self, key):
        """
        >>> a = Yaco({'a.a' : 1, 'a.b' : 2})
        >>> b = a.get_branch('a')
        >>> assert(a.has_key('a.a'))
        >>> assert(b.has_key('a'))
        """
        if self.branch:
            key = '{0}.{1}'.format(self.branch, key)
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
        for k, v in self.data.items():
            if not self.branch:
                yield k, v
            elif k.startswith('{0}.'.format(self.branch)):
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

    def keys(self, depth=0):
        """

        Return an iterator with the keys of this Yaco object.
        if depth != 0, it returns only keys of that specific depth,
        so for key 'a.b.c', depth=1 would return only a.


        >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
        >>> assert(set(a.keys()) == set(['a.a', 'a.b', 'c.b']))
        >>> s = a.get_branch('a')
        >>> assert(set(s.keys()) == set(['a', 'b']))

        >>> assert(set(a.keys(1)) == set(['a', 'c']))

        """
        if depth == 0:
            for k, v in self.iteritems():
                yield k
        else:
            yielded = []
            for k, v in self.iteritems():
                ks = k.split('.')
                if len(ks) < depth:
                    # no keys shorter than depth
                    continue
                rv = '.'.join(ks[:depth])
                if rv in yielded:
                    continue
                yielded.append(rv)
                yield rv

    def keys1(self):
        """
        shortcut for keys(depth=1)
        """
        for k in self.keys(1):
            yield k

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
        for k, v in dict.items():
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
            key = '{0}.{1}'.format(self.branch, key)
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
            rv.append("{0}{1}: '{2}'".format(prefix, k, v))
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
