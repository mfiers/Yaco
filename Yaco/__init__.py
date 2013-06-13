# -*- coding: utf-8 -*-
"""
Yaco
----

Yaco provides a `dict` like structure that can be serialized to & from
`yaml <http://www.yaml.org/>`_. Yaco objects behave as dictionaries
but also allow attribute access (loosely based on this `recipe <
http://code.activestate.com/recipes/473786/>`_). Sublevel dictionaries
are automatically converted to Yaco objects, allowing sublevel
attribute access, for example::

    >>> x = Yaco()
    >>> x.test = 1
    >>> x.sub.test = 2
    >>> x.sub.test
    2

Note that sub-dictionaries do not need to be initialized. This has as
a consequence that requesting uninitialized items automatically return
an empty Yaco object (inherited from a dictionary).

Yaco can be `found <http://pypi.python.org/pypi/Yaco/0.1.1>`_ in the
`Python package index <http://pypi.python.org/pypi/>`_ and is also
part of the `Moa source distribution
<https://github.com/mfiers/Moa/tree/master/lib/python/Yaco>`_

Autogenerating keys
===================

An important feature (or annoyance) of Yaco is the auto generation of
keys that are not present (yet). For example::

    >>> x = Yaco()
    >>> x.a.b.c.d = 1
    >>> assert(x.a.b.c.d == 1)

works - `a`, `b` and `c` are assumed to be `Yaco` dictionaries and d
is give value `1`. This makes populating data structures easy.

It might also generate some confusion when querying for keys in the
Yaco structure - if a key does not exists, it automatically comes back
as an empy `dict` or `Yaco` object (renders as `{}`). This means that
if it is easy to check if a certain 'branch' of a Yaco datastructure
exists::

   >>> x = Yaco()
   >>> assert (not x.a.b)

but now the following works as well:

   >>> assert('a' in x)
   >>> assert('b' in x.a )

So, a safe way to test a data structure, without introducing extra
branches is:

   >>> x = Yaco()
   >>> assert(not 'a' in x)

Todo: Need to find a more elegant way of testing without introducing
data structures

"""

import os
import sys
import yaml
import logging
lg = logging.getLogger(__name__)
#lg.setLevel(logging.DEBUG)

if sys.version_info[0] == 2:
    import codecs


class Yaco(dict):
    """
    Rather loosely based on http://code.activestate.com/recipes/473786/ (R1)

    >>> v= Yaco()
    >>> v.a = 1
    >>> assert(v.a == 1)
    >>> assert(v['a'] == 1)
    >>> v= Yaco({'a':1})
    >>> assert(v.a == 1)
    >>> assert(v['a'] == 1)

    """

    def __init__(self, data={}):
        """
        Constructor

        :param data: data to initialize the Yaco structure with
        :type data: dict or yaml formatted string
        """

        dict.__init__(self)

        if isinstance(data, dict):
            self.update(data)
        elif isinstance(data, str) or isinstance(data, bytes):
            self.update(yaml.load(data))
        else:
            raise Exception('cannot parse %s' % type(data))

    def __str__(self):
        """
        Map the structure to a string

        >>> v= Yaco({'a':1})
        >>> assert(str(v.a) == '1')
        """
        return str(self.get_data())

    def __setattr__(self, key, value):
        """
        Set the value of a key

        >>> v= Yaco()
        >>> v.a = 18
        >>> assert(v.a == 18)

        >>> v.a = 72
        >>> assert(v.a == 72)

        >>> v.a = {'b' : 5}
        >>> assert(v.a.b == 5)

        >>> v.a = {'c' : {'d' : 19}}
        >>> assert(v.a.b == 5)
        >>> assert(v.a.c.d == 19)
        >>> assert(v.a['c'].d == 19)

        >>> #create new instances on the fly
        >>> v.e = 1

        >>> v.f.g = 14
        >>> assert(v.f.g == 14)

        >>> v.f.h.i.j.k.l = 14
        >>> assert(v.f.h.i.j.k.l == 14)

        :param key: The key to set
        :param value: The value to assign to key
        """

        #print "setting %s to %s" % (key, value)
        old_value = super(Yaco, self).get(key, None)

        if isinstance(value, dict):
            #setting a dict
            if isinstance(old_value, Yaco):
                old_value.update(value)
            elif isinstance(value, Yaco):
                super(Yaco, self).__setitem__(key, value)
            else:
                super(Yaco, self).__setitem__(key, Yaco(value))
        elif isinstance(value, list):
            # parse the list to see if there are dicts - which need to
            # be translated to Yaco objects
            new_value = self._list_parser(value)
            super(Yaco, self).__setitem__(key, new_value)
        else:
            super(Yaco, self).__setitem__(key, value)

    def has_key(self, key):
        return key in list(super(Yaco, self).keys())

    def __getattr__(self, key):
        """
        >>> v= Yaco()
        >>> v.a = 18
        >>> assert(v.a == 18)
        >>> assert(isinstance(v.a, int))
        """
        try:
            return super(Yaco, self).__getitem__(key)
        except KeyError:
            rv = Yaco()
            super(Yaco, self).__setitem__(key, rv)
            return rv

    def __delattr__(self, name):
        return super(Yaco, self).__delitem__(name)

    def simple(self):
        """
        return a simplified representation of this
        Yaco struct - remove Yaco from the equation - and
        all object reference. Leave only bool, float, str,
        lists, tuples and dicts

        >>> x = Yaco()
        >>> x.y.z = 1
        >>> assert(isinstance(x.y, Yaco))
        >>> s = x.simple()
        >>> assert(s['y']['z'] == 1)
        >>> assert(isinstance(s['y'], dict))
        >>> assert(not isinstance(s['y'], Yaco))
        """

        def _returnSimple(item):
            if isinstance(item, (str, bool, int, float)):
                return item
            elif isinstance(item, list):
                return [_returnSimple(x) for x in item]
            elif isinstance(item, tuple):
                return (_returnSimple(x) for x in item)
            elif isinstance(item, dict):
                return dict([(k, _returnSimple(item[k]))
                             for k in item])
            else:
                return str(item)

        return _returnSimple(self)

    def _list_parser(self, old_list):
        """
        Recursively parse a list & replace all dicts with Yaco objects
        """
        for i, item in enumerate(old_list):
            if isinstance(item, dict):
                old_list[i] = Yaco(item)
            elif isinstance(item, list):
                old_list[i] = self._list_parser(item)
            else:
                pass
        return old_list


    def soft_update(self, data):
        """
        As update - but only update keys that do not have a value.

        Note - lists are completely

        >>> d1 = {'a' : [1,2,3,{'b': 12}], 'd' : {'e': 72}}
        >>> d2 = {'a' : [2,3,4,{'b': 12}], 'd' : {'e': 73, 'f': 18}, 'c' : 18}
        >>> v = Yaco(d1)
        >>> assert(v.a[2] == 3)
        >>> assert(v.d.e == 72)
        >>> v.soft_update(d2)
        >>> assert(v.d.e == 72)
        >>> assert(v.d.f == 18)
        >>> assert(v.a[2] == 3)

        """
        if not data:
            return

        for key, value in list(data.items()):

            old_value = super(Yaco, self).get(key, None)

            if isinstance(value, dict):
                if old_value and isinstance(old_value, Yaco):
                    old_value.soft_update(value)
                if old_value:
                    #there is an older value - not a dict - cannot overwrite
                    continue
                else:
                    #no old value - overwrite all you like
                    super(Yaco, self).__setitem__(key, Yaco(value))
            elif isinstance(value, list):
                # parse the list to see if there are dicts - which
                # need to be translated to Yaco objects
                if not old_value:
                    new_value = self._list_parser(value)
                    super(Yaco, self).__setitem__(key, new_value)
            else:
                if not old_value:
                    super(Yaco, self).__setitem__(key, value)

    def update(self, data):
        """
        >>> v = Yaco({'a' : [1,2,3,{'b' : 12}]})
        >>> assert(v.a[3].b == 12)

        >>> v = Yaco({'a' : [1,2,3,[1,{'b' : 12}]]})
        >>> assert(v.a[3][1].b == 12)

        """

        if not data:
            return

        for key, value in list(data.items()):

            old_value = super(Yaco, self).get(key, None)

            if isinstance(value, dict):
                if old_value and isinstance(old_value, Yaco):
                    old_value.update(value)
                else:
                    super(Yaco, self).__setitem__(key, Yaco(value))
            elif isinstance(value, list):
                # parse the list to see if there are dicts - which
                # need to be translated to Yaco objects
                new_value = self._list_parser(value)
                super(Yaco, self).__setitem__(key, new_value)
            else:
                super(Yaco, self).__setitem__(key, value)

    __getitem__ = __getattr__
    __setitem__ = __setattr__
    __delitem__ = __delattr__

    def copy(self):
        ch = Yaco(self)
        return ch

    def load(self, from_file):
        """
        Load this dict from_file

        >>> import yaml
        >>> import tempfile
        >>> tf = tempfile.NamedTemporaryFile(delete=True)
        >>> tf.close()
        >>> x = Yaco({'a': [1,2,3, [1,2,3, {'d' : 4}]],
        ...           'b': 4, 'c': '5', 'uni' : "Aπ"})
        >>> x.save(tf.name)
        >>> y = Yaco()
        >>> y.load(tf.name)
        >>> assert(y.a[3][3].d == 4)
        >>> assert(sys.version_info[0] == 2 or y.uni == "Aπ")
        """
        from_file = os.path.expanduser(
                os.path.abspath(os.path.expanduser(from_file)))
        if sys.version_info[0] == 2:
            with codecs.open(from_file, encoding='utf-8') as F:
                data = yaml.load(F.read())
        else:
            with open(from_file, encoding='utf8') as F:
                data = yaml.load(F)

        self.update(data)

    def pretty(self):
        """
        Return data as a pprint.pformatted string
        """
        return yaml.dump(self.get_data(), encoding='utf-8',
                         default_flow_style=False)

    def get_data(self):
        """
        Prepare & parse data for export

        >>> y = Yaco()
        >>> y.a = 1
        >>> y.b = 2
        >>> y._c = 3
        >>> assert(y._c == 3)
        >>> d = y.get_data()
        >>> assert('a' in d)
        >>> assert('b' in d)
        >>> assert(not 'c' in d)
        >>> y._private = ['b']
        >>> d = y.get_data()
        >>> assert('a' in d)
        >>> assert(not 'b' in d)
        >>> assert(not '_c' in d)
        """
        data = {}
        _priv = self.get('_private', [])

        def check_data(v):
            if isinstance(v, Yaco):
                v = v.get_data()
            elif isinstance(v, list):
                v = [check_data(x) for x in v]
            return v

        for k in list(self.keys()):
            if k in _priv:
                continue
            if isinstance(k, (str)) and k and k[0] == '_':
                continue
            data[k] = check_data(self[k])
        return data

    def dump(self):
        if sys.version_info[0] == 2:
            return yaml.safe_dump(self.get_data(),
                    default_flow_style=False)
        elif sys.version_info[0] == 3:
            return yaml.dump(self.get_data(), default_flow_style=False)

    def save(self, to_file, doNotSave=[]):
        """
        """

        data = self.get_data()
        to_file = os.path.expanduser(to_file)
        for k in list(data.keys()):
            if k in doNotSave:
                del data[k]
        if sys.version_info[0] == 2:
            with open(to_file, 'w') as F:
                F.write(self.dump())
        else:
            with open(to_file, 'w', encoding='utf-8') as F:
                F.write(self.dump())


if __name__ == "__main__":
    if 'x' in sys.argv:
        y = Yaco()
        y.x.z = 1
        print(y.x.z)
    else:
        import doctest
        doctest.testmod()

class PolyYaco():
    """
    A meta object that allows a composite Yaco object to be loaded
    from any number of different files which are kept as a stack of
    Yaco objects. If looking for a value, this object will check each
    of the layers in the stack and return the first value that it
    comes across.

    Changes are only made to the toplevel object.

    The goal is to have multiple configuration files, for example in::

        /location/to/python/package/etc/config.yaml
        /etc/APPLICATION.yaml
        ~/.config/APPLICATION/config.yaml

    and have values in the latter file override those in the
    former. Saving changed values will also be done to the latter, but
    system and application wide settings can be maintained as well
    (manually for the time being).
    """

    def __init__(self, name, base = None, files=None):
        """

        """

        if files is None:
            self._PolyYaco_files = (
                ('system', '/etc/{0}.yaml'.format(name)),
                ('user', '~/.config/{0}/config.yaml'.format(name)),
                )
        else:
            self._PolyYaco_files = files

        if base is not None:
            self._PolyYaco_files = (('_base', True), ) +  \
                tuple(self._PolyYaco_files)

        self._PolyYaco_yaco = {}

        for cid, cfn in self._PolyYaco_files:
            if cid == '_base':
                self._PolyYaco_yaco[cid] = Yaco(base)
            else:
                self._PolyYaco_yaco[cid] = Yaco()
        self.load()

    def load(self):
        for cid, cfn in self._PolyYaco_files:
            if cid == '_base':
                continue
            cfn = os.path.expanduser(cfn)
            self._PolyYaco_yaco[cid] = Yaco()
            if os.path.exists(cfn):
                lg.debug("Loading {0}".format(cfn))
                self._PolyYaco_yaco[cid].load(cfn)
            else:
                lg.debug("Not found {0}".format(cfn))
                self._PolyYaco_yaco[cid] = Yaco()

    def _getTop(self):
        top_cid, top_cfn = self._PolyYaco_files[-1]
        return top_cid, top_cfn, self._PolyYaco_yaco[top_cid]

    def save(self):
        cid, cfn, cyc = self._getTop()
        cyc.save(cfn)

    def merge(self):
        for i, (cid, cfn) in enumerate((self._PolyYaco_files)):
            if i == 0:
                y = self._PolyYaco_yaco[cid].copy()
            else:
                y.update(self._PolyYaco_yaco[cid])
        return y

    def simple(self):
        return self.merge().simple()

    def __str__(self):
        return str(self.merge())

    def has_key(self, key):
        return key in self.merge()

    def __setattr__(self, key, value):
        #see if this is an instance variable
        if key[:9] == '_PolyYaco':
            self.__dict__[key] = value
            return
        cid, cfn, cyc = self._getTop()
        cyc.__setattr__(key, value)

    def get(self, key, default=None):
        try:
            rv = self.__getattr__(key)
        except KeyError:
            return default

        if rv == {}:
            return default
        return rv


    def __contains__(self, key):
        return self.merge().__contains__(key)

    def __getattr__(self, key):
        if isinstance(key, int):
            print( 'intkey', key)
            sys.exit(-1)
        if key[:9] == '_PolyYaco':
            try:
                return self.__dict__[key]
            except KeyError:
                raise AttributeError()

        return self.merge().__getattr__(key)

    __setitem__ = __setattr__
    __getitem__ = __getattr__
