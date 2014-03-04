
import logging

from Yaco2 import Yaco

lg = logging.getLogger(__name__)


def _get_test_stack():
    s = YacoStack()
    y = Yaco({'a': 1, 'b.c': 2, 'b.d': 3})
    z = Yaco({'e': 4, 'b.f': 5, 'b.d': 6})
    s.append(y)
    s.append(z)

    return s


class YacoEmptyStack(Exception):
    pass


class YacoStack(Yaco):

    def __init__(self, data=None, default="__RAISE_ERROR__"):

        self.default = default

        self.mode = "merge"

        if data is None:
            self.stack = []
        elif isinstance(data, Yaco):
            self.stack = [data]
        elif isinstance(data, list):
            self.stack = data
        else:
            raise Exception("unexpected Yaco init object: %s", data)

    def append(self, *args, **kwargs):
        return self.stack.append(*args, **kwargs)

    def insert(self, *args, **kwargs):
        return self.stack.insert(*args, **kwargs)

    def get_branch(self, branch, absolute=False):
        """
        Return a branch

        >>> s = _get_test_stack()
        >>> assert(s['a'] == 1)
        >>> assert(s['b.d'] == 3)

        >>> b = s.get_branch('b')
        >>> assert(b['d'] == 3)
        >>> assert('a' not in b)

        """
        new_stack = []
        for s in self.stack:
            new_stack.append(s.get_branch(branch, absolute))
        return self.__class__(new_stack, self.default)

    def __repr__(self):
        return repr(self.stack)


    def __len__(self):
        """
        """
        return len(dict(self))


    def __getitem__(self, key):
        """

        >>> a = _get_test_stack()
        >>> assert(a['a'] == 1)
        >>> assert(a['b.c'] == 2)
        >>> assert(a['e'] == 4)
        >>> assert(a['e'] == 4)

        """
        for s in self.stack:
            if key in s:
                return s[key]

        if self.default == "__RAISE_ERROR__":
            raise KeyError(key)
        else:
            return self.default

    def __setitem__(self, key, item):
        """
        >>> a = _get_test_stack()
        >>> assert('q' not in a)
        >>> a['q'] = 42
        >>> assert(a['q'] == 42)
        >>> assert(a.stack[0]['q'] == 42)
        >>> assert('q' not in a.stack[1])

        >>> b = a.get_branch('r')
        >>> b['c'] = 3
        >>> assert(a['r.c'] == 3)
        """
        if len(self.stack) == 0:
            raise YacoEmptyStack()

        self.stack[0][key] = item

    def __delitem__(self, key):
        """
        Dangerous? Should not do this - manipulate the objects
        in the stack directly!

        """
        raise NotImplementedError("dangerous - manipulate the stack directly")

    def has_key(self, key):
        """
        >>> a = _get_test_stack()
        >>> b = a.get_branch('b')
        >>> assert(a.has_key('b.c'))
        >>> assert(b.has_key('c'))
        """
        return key in self

    def clear(self):
        raise NotImplementedError("dangerous - manipulate the stack directly")

    def __str__(self):
        rv = "[YacoStack]"
        for s in self.stack[:3]:
            if isinstance(s, YacoStack):
                rv += '[[YacoStack]],'
            else:
                rv += str(s.branch) + ','
            rv += '...'
        rv += "}"
        return rv
    # def iteritems(self):
    #     """
    #     >>> a = Yaco({'a.a' : 1, 'a.b' : 2, 'c.b' : 3})
    #     >>> ii = a.iteritems()
    #     >>> assert(isinstance(ii, types.GeneratorType))
    #     >>> assert(len(list(ii)) == 3)
    #     >>> b = a.get_branch('a')
    #     >>> ii = list(sorted(b.iteritems()))
    #     >>> assert(len(ii) == 2)
    #     >>> assert(ii == [('a', 1), ('b', 2)])
    #     """
    #     for k, v in self.data.iteritems():
    #         if not self.branch:
    #             yield k, v
    #         elif k.startswith('{}.'.format(self.branch)):
    #             yield (k[len(self.branch) + 1:], v)

    # def iterkeys(self):
    #     for (k, v) in self.iteritems():
    #         yield k

    # def itervalues(self):
    #     for (k, v) in self.iteritems():
    #         yield v

    # def items(self):
    #     return self.iteritems()

    # def values(self):
    #     return self.itervalues()

    def keys(self, depth=0):
        """

        TODO: make this more efficient

        >>> a = _get_test_stack()
        >>> assert(set(a.keys()) == \
                set('a b.c b.d e b.f'.split()))
        >>> s = a.get_branch('b')
        >>> assert(set(s.keys()) == set(['c', 'd', 'f']))
        """

        all_keys = set()
        for s in self.stack:
            all_keys.update(set(s.keys()))

        if depth == 0:
            for k in all_keys:
                yield k
        else:
            yielded = []
            for k in all_keys:
                ks = k.split('.')
                if len(ks) < depth:
                    # no keys shorter than depth
                    continue
                rv = '.'.join(ks[:depth])
                if rv in yielded:
                    continue
                yielded.append(rv)
                yield rv


    def update(self, dict=None):
        """
        >>> a = _get_test_stack()
        >>> a.update({'b.b' : 2, 'c.d' : 3})
        >>> assert(a['c.d'] == 3)
        >>> b = Yaco({'e.f' : 4})
        >>> a.update(b)
        >>> assert(a['e.f'] == 4)
        >>> c = b.get_branch('e')
        >>> a.update(c)
        >>> assert(a['f'] == 4)
        """
        if len(self.stack) == 0:
            raise YacoEmptyStack()
        self.stack[0].update(dict)


    def __contains__(self, key):
        """
        >>> a = _get_test_stack()
        >>> assert('b.c' in a)
        >>> assert('b.q' not in a)
        >>> b = a.get_branch('b')
        >>> assert('c' in b)
        >>> assert('q' not in b)
        """
        for s in self.stack:
            if key in s:
                return True
        return False

    def get(self, key, failobj=None):
        """
        >>> a = _get_test_stack()
        >>> assert(a.get('a') == 1)
        >>> assert(a.get('a.c', 12) == 12)
        """
        if key in self:
            return self[key]
        return failobj
