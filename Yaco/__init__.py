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

import fnmatch
import logging
import os
import pkg_resources
import re
import sys
import yaml

lg = logging.getLogger(__name__)
#lg.setLevel(logging.DEBUG)

if sys.version_info[0] == 2:
    import codecs

ITEM_INVALID = 0
ITEM_FILE = 1
ITEM_WEB = 2
ITEM_STRING = 3

ROOT_LEAF_PREFIX = "_"
YACODIR_CACHEFILE = '.yacodir_cache'

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

    def __init__(self, data={}, leaf=None):
        """
        Constructor

        :param data: data to initialize the Yaco structure with
        :type data: dict or yaml formatted string
        """

        dict.__init__(self)

        if not data == {}:
            to_update = None
            if isinstance(data, dict):
                to_update = data
            elif isinstance(data, str) or isinstance(data, bytes):
                to_update = yaml.load(data)
            else:
                raise Exception('cannot parse %s' % type(data))

            if leaf is None or leaf == '':
                self.update(to_update)
            else:
                self[leaf].update(to_update)

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

    def __getitem__(self, key):
        """
        as getattr, expect for when there is a '.' in the key.

        it is possible to ask for yacoobject[''] - this is a form
        of leaf loading - but means, give me the root. So - checking for
        that
        """
        #print(  key)
        if key == '':
            return self

        if not '.' in key:
            return self.__getattr__(key)
        else:
            k1, k2 = key.split('.', 1)
            return self.__getattr__(k1)[k2]

    def __setitem__(self, key, value):
        """
        as setattr, except for when there is a dot in the key
        """
        if not '.' in key:
            return self.__setattr__(key, value)
        else:
            k1, k2 = key.split('.', 1)
            self.__getattr__(k1)[k2] = value

    __delitem__ = __delattr__

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

    def copy(self):
        ch = Yaco(self)
        return ch

    def load(self, from_file, leaf=None):
        """
        Load this dict from_file

        Note - it can load the file into a leaf, instead of the root
        of this Yaco structure. Note - the leaf variable is a string,
        but may contain dots (which are automatically interpreted)

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

        if leaf is None or leaf == '':
            self.update(data)
        else:
            self[leaf].update(data)

    def pretty(self):
        """
        Return data as a pprint.pformatted string
        """
        return yaml.dump(self.get_data(), encoding='utf-8',
                         default_flow_style=False).rstrip()

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
            #print self.keys()
            #print k, 'x' * 30
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
            with open(to_file, 'w', 0) as F:
                F.write(self.dump())
        else:
            with open(to_file, 'w', 0, encoding='utf-8') as F:
                F.write(self.dump())


class YacoFile(Yaco):
    """
    As Yaco, but loads from a file - or returns an emtpy object if it
    cannot find the file
    """

    def __init__(self, filename):
        """
        Constructor

        :param filename: filename to load
        :type filename: string
        """

        dict.__init__(self)

        self._filename = filename
        self.load()

    def load(self):
        """
        Load from the defined filename
        """
        super(YacoFile, self).load(self._filename)

    def save(self):
        """
        Load from the defined filename
        """
        super(YacoFile, self).save(self._filename)


def _get_leaf(leaf, d, pattern):
    """
    Helper function to determine the leaf name
    """
#    print('12312341234', leaf, d, pattern)
    xleaf = d.rsplit('/', 1)[-1].strip()
    check_pattern = re.match('\*(\.[a-zA-Z0-9]+)$', pattern)
    if check_pattern:
        xten = check_pattern.groups()[0]
        if xleaf[-len(xten):] == xten:
            xleaf = xleaf[:-len(xten)].strip()
    if xleaf.find(ROOT_LEAF_PREFIX) == 0:
        return leaf
    elif leaf.strip():
        return '{}.{}'.format(leaf, xleaf)
    else:
        return xleaf


class YacoDir(Yaco):
    """
    As Yaco, but load all files in a directory on top of each other.

    Order of loading is the alphanumerical sort of filenames

    files in subdirectories are loaded into leaves
    e.g. a file in /tmp/test/sub/a.yaml with only (x=1) will end up as follows:

        y = YacoDir('/tmp/test')
        y.sub.x == 1


    Note, YacoDir will try to cache itself in a .yacodir.cache file in the root
    of the dirname if the modification date of this file is the same as the
    directory - that will be loaded instead.
    """

    def __init__(self, dirname, pattern='*.config'):
        """
        Constructor

        :param dirname: directory to load
        :type dirname: string
        :param glob: a glob describing what files to load
        :type glob: string
        """
        dict.__init__(self)
        #print("loading", dirname, pattern)
        self.load(dirname, pattern)

    def load(self, dirname, pattern):
        """
        Load from the defined directory
        """

        cachefile = os.path.join(dirname, YACODIR_CACHEFILE)

        # TODO: get caching to work properly :(
        # if os.path.exists(cachefile):
        #     if os.path.getmtime(dirname) == \
        #             os.path.getmtime(cachefile):
        #         #load cache
        #         super(YacoDir, self).load(cachefile)
        #         return

        for root, dirs, files in os.walk(dirname):
            #print('-' * 80)
            ##import sh
            #print(sh.ls("-l", dirname))
            #print(root, dirs, files, pattern)
            to_parse = sorted(fnmatch.filter(files, pattern))
            base = root.replace(dirname, '').strip('/')
            base = base.replace('/', '.')
            #lg.critical("{0} {1}".format(root, dirs))
            for filename in to_parse:
                fullname = os.path.join(root, filename)
                lg.debug("YacoDir loading {0}".format(fullname))
                #print ("loadlaod", filename, fullname)
                nleaf = _get_leaf(base, filename, pattern)

                with open(fullname) as F:
                    y = yaml.load(F.read())

                if nleaf == '':
                    self.update(y)
                else:
                    self[nleaf].update(y)
        #print('*' * 80)
        #print self.pretty()
        if self:
            #after loading - save to cache!
            super(YacoDir, self).save(cachefile)

    def save(self):
        """
        Save is disabled.
        """
        raise Exception("Cannot save to a YacoDir")


class YacoPkg(Yaco):

    def __init__(self, pkg_name, path,
                 pattern='*.config', leaf="",
                 base_path=None, prefix=None):


        #lg.setLevel(logging.DEBUG)
        lg.debug("pkg loading {} {} {}".format(pkg_name, path, pattern))

        if not base_path is None:
            if leaf:
                leaf = leaf.strip('.') + '.'
            leaf = path.replace(base_path, '').strip('/').replace('/', '.')
            lg.debug("leaf: ({}) {}".format(base_path, leaf))

        if not pkg_resources.resource_isdir(pkg_name, path):
            #asssume a file:
            lg.debug("loading file {} {}".format(pkg_name, path))
            #print("loading file {} {}".format(pkg_name, path))
            y = pkg_resources.resource_string(pkg_name, path)
            self[leaf].update(yaml.load(y))

        else:
            for d in pkg_resources.resource_listdir(pkg_name, path):
                nres = os.path.join(path, d)
                #print('nn', nres, leaf)
                lg.debug("checking for pkg load: {}".format(nres))
                if pkg_resources.resource_isdir(pkg_name, nres):
                    lg.debug("pkg load: is directory: {}".format(nres))
                    if base_path == None:
                        base_path = path
                    #print('d', leaf, pkg_name, nres)
                    y = YacoPkgDir(pkg_name, nres,
                                   pattern=pattern,
                                   base_path=base_path)
                    self[leaf].update(y)
                else:
                    if not fnmatch.fnmatch(d, pattern):
                        lg.debug('ignoring {}'.format(nres))
                        continue
                    else:
                        lg.debug("pkg load: loading file: {}".format(nres))
                        y =  yaml.load(pkg_resources.resource_string(pkg_name, nres))
                        lg.debug("pkg load: got: {}".format(str(y)))
                        this_leaf = _get_leaf(leaf, d, pattern)
                        #print('f', leaf, path, nres, d, this_leaf)
                        self[this_leaf].update(y)


YacoPkgDir = YacoPkg

class PolyYaco(Yaco):
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

    def __init__(self, name="PY", files=[],
                 pattern='*.config',
                 leaf=""):
        """

        """

        #if not items - set a default
        if files is None:
            files = [
                '/etc/{0}.config'.format(name),
                '~/.config/{0}/'.format(name) ]

        super(PolyYaco, self).__init__()
        self.load(leaf, files, pattern)

    def load(self, leaf, files, pattern):
        """

        """

        for filename in files:
            filename = os.path.expanduser(filename)

            y  = None
            if filename[:6] == 'pkg://':
                #expecting pkg://Yaco/etc/config.yaml
                base = filename[6:]
                pkg, loc = base.split('/', 1)
                this_pattern=pattern
                if '*' in loc:
                    if '/' in loc:
                        loc, this_pattern = loc.rsplit('/', 1)
                    else:
                        loc, this_pattern = '/', loc

                try:
                    y = YacoPkg(pkg, loc, pattern=this_pattern)
                except IOError:
                    #file does probably not exists - ignore
                    lg.debug("cannot load file {}".format(loc))
                    pass
                except ImportError:
                    #or the complete package does not exists - one of script? ignore
                    lg.debug("cannot find package {}".format(pkg))

                    pass

            elif os.path.isdir(filename):
                y = YacoDir(filename, pattern = pattern)

            elif os.path.isfile(filename):
                y = Yaco()
                y.load(filename)
            else:
                #nothing to load
                continue

            if not y is None:
                self[leaf].update(y)
        #print self.pretty()

    def save(self):
        lg.warning("PolyYaco save is disabled")
        #cfn, cyc = self._getTop()
        #if cfn == '_base':
        #    raise Exception("Cannot save to 'base' configuration")
        #cyc.save(cfn)


if __name__ == "__main__":
    if 'x' in sys.argv:
        y = Yaco()
        y.x.z = 1
        print(y.x.z)
    else:
        import doctest
        doctest.testmod()

