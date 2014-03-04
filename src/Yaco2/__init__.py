# -*- coding: utf-8 -*-
"""
Yaco2
-----

Yaco provides a `dict` like structure that can be serialized to & from
`yaml <http://www.yaml.org/>`_. Yaco objects behave as dictionaries
but also allow attribute access (loosely based on this `recipe <
http://code.activestate.com/recipes/473786/>`_). Sublevel dictionaries
are automatically converted to Yaco objects, allowing sublevel
attribute access, for example::

Note that sub-dictionaries do not need to be initialized. This has as
a consequence that requesting uninitialized items automatically return
an empty Yaco object (inherited from a dictionary).

Yaco can be `found <http://pypi.python.org/pypi/Yaco/0.1.1>`_ in the
`Python package index <http://pypi.python.org/pypi/>`_ and is also
part of the `Moa source distribution
<https://github.com/mfiers/Moa/tree/master/lib/python/Yaco>`_

"""

import logging
import sys

lg = logging.getLogger(__name__)

PY_2 = sys.version[0] == 2
PY_3 = sys.version[0] == 3

from Yaco2.core import Yaco
from Yaco2.ydb import YacoDb
from Yaco2.stack import YacoStack

from Yaco2.loader import dict_loader, yaml_string_loader, \
    yaml_file_loader, dir_loader, package_loader, \
    simple_package_loader, load

from Yaco2.loader import yaml_file_save


#    db    db  .d8b.   .o88b.  .d88b.
#    `8b  d8' d8' `8b d8P  Y8 .8P  Y8.
#     `8bd8'  88ooo88 8P      88    88
#       88    88~~~88 8b      88    88
#       88    88   88 Y8b  d8 `8b  d8'
#       YP    YP   YP  `Y88P'  `Y88P'


#     def __str__(self):
#         """
#         Map the structure to a string

#         >>> v= Yaco({'a':1})
#         >>> assert(str(v.a) == '1')
#         """
#         return str(self.get_data())


#     def has_key(self, key):
#         """
#         As the dict's has_key

#         >>> y = Yaco()
#         >>> y['a'] = 1
#         >>> y.b.c = 2

#         >>> assert(y.has_key('a'))
#         >>> assert(y.b.has_key('c'))
#         >>> assert(y.has_key('b.c'))
#         >>> assert(not y.has_key('d'))
#         >>> assert(not y.has_key('d.e'))

#         """
#         if '.' in key:
#             first, second = key.split('.', 1)
#             return self[first].has_key(second)
#         else:
#             return key in self.keys()

#     def __len__(self):
#         """
#         >>> y = Yaco()
#         >>> assert(len(y) == 0)
#         >>> y.a = 1
#         >>> assert(len(y) == 1)
#         >>> del y.a
#         >>> assert(len(y) == 0)
#         """
#         return super(Yaco, self).__len__()

#     def __repr__(self):
#         return super(Yaco, self).__repr__()

#     def __contains__(self, key):
#         """
#         makes:
#           if a in yacoobject
#         work

#         >>> y = Yaco()

#         >>> y.a = 1
#         >>> assert('a' in y)
#         >>> assert(not 'd' in y)

#         >>> y.b.c = 2
#         >>> assert('b' in y)
#         >>> assert('c' in y.b)
#         >>> assert('b.c' in y)
#         >>> assert(not 'e.f' in y)
#         """

#         if '.' in key:
#             first, second = key.split('.', 1)
#             return second in self[first]
#         else:
#             return super(Yaco, self).__contains__(key)

#     def __delattr__(self, name):
#         """
#         Remove an attribute

#         >>> y = Yaco()
#         >>> y.a = 1
#         >>> assert('a' in y)
#         >>> del y.a
#         >>> assert(not 'a' in y)

#         >>> y.b.c = 2
#         >>> y.d.e = 3
#         >>> assert('b' in y)
#         >>> assert('b.c' in y)
#         >>> del y.b
#         >>> assert(not 'b' in y)
#         >>> assert(not 'b.c' in y)
#         >>> del y.d.e
#         >>> assert('d' in y)
#         >>> assert(not 'd.e' in y)
#         >>> assert(not 'e' in y.d)
#         """

#         return super(Yaco, self).__delitem__(name)

#     def __getitem__(self, key):
#         """
#         as getattr, expect for when there is a '.' in the key.

#         it is possible to ask for yacoobject[''] which returns
#         the root
#         """

#         if key == '':
#             return self

#         if not isinstance(key, str):
#             return self.__getattr__(key)
#         elif not '.' in key:
#             return self.__getattr__(key)
#         else:
#             k1, k2 = key.split('.', 1)
#             return self.__getattr__(k1)[k2]

#     def __setitem__(self, key, value):
#         """
#         as setattr, except for when there is a dot in the key

#         >>> y = Yaco()
#         >>> y['b'] = 1
#         >>> assert(y.b == 1)
#         >>> # no assignment over other objects
#         >>> y['b.c'] = 2
#         Traceback (most recent call last):
#             ...
#         TypeError: 'int' object does not support item assignment
#         >>> del y['b']
#         >>> y['b.c'] = 2
#         >>> assert(y.b.c == 2)

#         """
#         if not '.' in key:
#             return self.__setattr__(key, value)
#         else:
#             k1, k2 = key.split('.', 1)
#             self.__getattr__(k1)[k2] = value

#     __delitem__ = __delattr__

#     def empty(self):
#         """
#         Is this Yaco object empty?

#         >>> y = Yaco()
#         >>> assert(y.empty())
#         >>> y.a = 1
#         >>> assert(not y.empty())
#         >>> del y.a
#         >>> assert(y.empty())

#         """
#         return self == {}

#     def simple(self):
#         """
#         return a simplified representation of this
#         Yaco struct - remove Yaco from the equation - and
#         all object reference. Leave only bool, float, str,
#         lists, tuples and dicts

#         >>> x = Yaco()
#         >>> x.y.z = 1
#         >>> assert(isinstance(x.y, Yaco))
#         >>> s = x.simple()
#         >>> assert(s['y']['z'] == 1)
#         >>> assert(type(s) == dict)
#         >>> assert(type(s['y']) == dict)
#         """

#         def _returnSimple(item):
#             if isinstance(item, (str, bool, int, float)):
#                 return item
#             elif isinstance(item, list):
#                 return [_returnSimple(x) for x in item]
#             elif isinstance(item, tuple):
#                 return (_returnSimple(x) for x in item)
#             elif isinstance(item, dict):
#                 return dict([(k, _returnSimple(item[k]))
#                              for k in item])
#             else:
#                 return str(item)

#         return _returnSimple(self)

#     def _list_parser(self, old_list):
#         """
#         Recursively parse a list & replace all dicts with Yaco objects
#         """
#         for i, item in enumerate(old_list):
#             if isinstance(item, dict):
#                 old_list[i] = Yaco(item)
#             elif isinstance(item, list):
#                 old_list[i] = self._list_parser(item)
#             else:
#                 pass
#         return old_list

#     def soft_update(self, data):
#         """
#         As update - but only update keys that do not have a value.

#         Note - lists are completely ignored

#         >>> d1 = {'a' : [1,2,3,{'b': 12}], 'd' : {'e': 72}}
#         >>> d2 = {'a' : [2,3,4,{'b': 12}], 'd' : {'e': 73, 'f': 18}, 'c' : 18}
#         >>> v = Yaco(d1)
#         >>> assert(v.a[2] == 3)
#         >>> assert(v.d.e == 72)
#         >>> v.soft_update(d2)
#         >>> assert(v.d.e == 72)
#         >>> assert(v.d.f == 18)
#         >>> assert(v.a[2] == 3)

#         """
#         if not data:
#             return

#         for key, value in list(data.items()):

#             old_value = super(Yaco, self).get(key, None)

#             if isinstance(value, dict):
#                 if old_value and isinstance(old_value, Yaco):
#                     old_value.soft_update(value)
#                 if old_value:
#                     # there is an older value - not a dict - cannot overwrite
#                     continue
#                 else:
#                     # no old value - overwrite all you like
#                     super(Yaco, self).__setitem__(key, Yaco(value))
#             elif isinstance(value, list):
#                 # parse the list to see if there are dicts - which
#                 # need to be translated to Yaco objects
#                 if not old_value:
#                     new_value = self._list_parser(value)
#                     super(Yaco, self).__setitem__(key, new_value)
#             else:
#                 if not old_value:
#                     super(Yaco, self).__setitem__(key, value)

#     def update(self, data):
#         """
#         As dict update, but with a dict, or Yaco, object. Also,
#         this function works in place.

#         >>> a = Yaco()
#         >>> b = Yaco()
#         >>> a.a = 1
#         >>> b.b = 2

#         >>> a.update(b)
#         >>> assert(a.b == 2)

#         >>> a.c.d = 3
#         >>> b.c.e = 4
#         >>> a.update(b)

#         >>> assert(a.c.d == 3)
#         >>> assert(a.c.e == 4)

#         >>> a.update({'c' : {'f' : 6}})
#         >>> assert(a.c.f == 6)

#         """

#         if not data:
#             return

#         for key, value in list(data.items()):

#             old_value = super(Yaco, self).get(key, None)

#             if isinstance(value, dict):
#                 if old_value and isinstance(old_value, Yaco):
#                     old_value.update(value)
#                 else:
#                     super(Yaco, self).__setitem__(key, Yaco(value))
#             elif isinstance(value, list):
#                 # parse the list to see if there are dicts - which
#                 # need to be translated to Yaco objects
#                 new_value = self._list_parser(value)
#                 super(Yaco, self).__setitem__(key, new_value)
#             else:
#                 super(Yaco, self).__setitem__(key, value)

#     def copy(self):
#         """

#         >>> a = Yaco()
#         >>> a.c = 1

#         >>> b = a.copy()
#         >>> assert(b == a)

#         >>> b.c = 2
#         >>> assert(b != a)
#         """
#         ch = Yaco(self)
#         return ch

#     def load(self, from_file, leaf=None):
#         """
#         Load this dict from_file

#         Note - it can load the file into a leaf, instead of the root
#         of this Yaco structure. Note - the leaf variable is a string,
#         but may contain dots, which are automatically interpreted.

#         >>> import tempfile
#         >>> tf = tempfile.NamedTemporaryFile(delete=True)
#         >>> tf.close()
#         >>> x = Yaco({'a': [1,2,3, [1,2,3, {'d' : 4}]],
#         ...           'b': 4, 'c': '5', 'uni' : "Aπ"})
#         >>> x.save(tf.name)
#         >>> y = Yaco()
#         >>> y.load(tf.name)
#         >>> assert(y.a[3][3].d == 4)
#         >>> assert(sys.version_info[0] == 2 or y.uni == "Aπ")
#         """
#         from_file = os.path.expanduser(
#             os.path.abspath(os.path.expanduser(from_file)))
#         if sys.version_info[0] == 2:
#             with codecs.open(from_file, encoding='utf-8') as F:
#                 data = yaml.load(F.read())
#         else:
#             with open(from_file, encoding='utf8') as F:
#                 data = yaml.load(F)

#         if not leaf:
#             self.update(data)
#         else:
#             self[leaf].update(data)

#     def pretty(self):
#         """
#         Return data as a pprint.pformatted string

#         >>> y = Yaco()
#         >>> y.a = 1
#         >>> s = y.pretty()
#         >>> if PY_2:
#         ...     assert(s == 'a: 1')
#         ...     assert(type(s) == str)
#         >>> if PY_3:
#         ...     assert(s == b'a: 1')
#         ...     assert(type(s) == bytes)
#         """
#         return yaml.dump(self.get_data(), encoding='utf-8',
#                          default_flow_style=False).rstrip()

#     def get_data(self):
#         """
#         Prepare & parse data for export.

#         This means, removing all fields starting with a '_'

#         >>> y = Yaco()
#         >>> y.a = 1
#         >>> y.b = 2
#         >>> y._c = 3
#         >>> assert(y._c == 3)
#         >>> d = y.get_data()
#         >>> assert('b' in d)
#         >>> assert(not 'c' in d)

#         >>> y._private = ['b']
#         >>> d = y.get_data()
#         >>> assert('a' in d)
#         >>> assert(not 'b' in d)
#         >>> assert(not '_c' in d)
#         """
#         data = {}
#         _priv = self.get('_private', [])

#         def check_data(v):
#             if isinstance(v, Yaco):
#                 v = v.get_data()
#             elif isinstance(v, list):
#                 v = [check_data(x) for x in v]
#             return v

#         for k in list(self.keys()):
#             if k in _priv:
#                 continue
#             if isinstance(k, (str)) and k and k[0] == '_':
#                 continue
#             data[k] = check_data(self[k])
#         return data

#     def dump(self):
#         if sys.version_info[0] == 2:
#             return yaml.safe_dump(self.get_data(),
#                                   default_flow_style=False)
#         elif sys.version_info[0] == 3:
#             return yaml.dump(self.get_data(), default_flow_style=False)


#     def save(self, to_file, doNotSave=[]):
#         """
#         Save data to file

#         >>> import tempfile
#         """

#         data = self.get_data()
#         to_file = os.path.expanduser(to_file)
#         for k in list(data.keys()):
#             if k in doNotSave:
#                 del data[k]
#         with open(to_file, 'w') as F:
#             F.write(self.dump())


# # #    db    db  .d8b.   .o88b.  .d88b.  d88888b d888888b db      d88888b
# # #    `8b  d8' d8' `8b d8P  Y8 .8P  Y8. 88'       `88'   88      88'
# # #     `8bd8'  88ooo88 8P      88    88 88ooo      88    88      88ooooo
# # #       88    88~~~88 8b      88    88 88~~~      88    88      88~~~~~
# # #       88    88   88 Y8b  d8 `8b  d8' 88        .88.   88booo. 88.
# # #       YP    YP   YP  `Y88P'  `Y88P'  YP      Y888888P Y88888P Y88888P


# # class YacoFile(Yaco):

# #     """
# #     As Yaco, but loads from a file - or returns an emtpy object if it
# #     cannot find the file
# #     """

#     def __init__(self, filename):
#         """
#         Constructor

#         :param filename: filename to load
#         :type filename: string
#         """

#         dict.__init__(self)
#         self._filename = filename
#         self.load()

#     def load(self):
#         """
#         Load from the defined filename
#         """
#         super(YacoFile, self).load(self._filename)

#     def save(self):
#         """
#         Load from the defined filename
#         """
#         super(YacoFile, self).save(self._filename)


# def _get_leaf(leaf, d, pattern):
#     """
#     Helper function to determine the leaf name
#     """
#     xleaf = d.rsplit('/', 1)[-1].strip()
#     check_pattern = re.match('\*(\.[a-zA-Z0-9]+)$', pattern)
#     if check_pattern:
#         xten = check_pattern.groups()[0]
#         if xleaf[-len(xten):] == xten:
#             xleaf = xleaf[:-len(xten)].strip()
#     if xleaf.find(ROOT_LEAF_PREFIX) == 0:
#         return leaf
#     elif leaf.strip():
#         return '{0}.{1}'.format(leaf, xleaf)
#     else:
#         return xleaf

# #    db    db  .d8b.   .o88b.  .d88b.  d8888b. d888888b d8888b.
# #    `8b  d8' d8' `8b d8P  Y8 .8P  Y8. 88  `8D   `88'   88  `8D
# #     `8bd8'  88ooo88 8P      88    88 88   88    88    88oobY'
# #       88    88~~~88 8b      88    88 88   88    88    88`8b
# #       88    88   88 Y8b  d8 `8b  d8' 88  .8D   .88.   88 `88.
# #       YP    YP   YP  `Y88P'  `Y88P'  Y8888D' Y888888P 88   YD


# class YacoDir(Yaco):

#     """
#     As Yaco, but load all files in a directory on top of each other.

#     Order of loading is the alphanumerical sort of filenames

#     files in subdirectories are loaded into leaves

#     e.g. a file in /tmp/test/sub/a.yaml with only (x=1) will end up
#     as follows:

#         y = YacoDir('/tmp/test')
#         y.sub.x == 1


#     Note, YacoDir will try to cache itself in a .yacodir.cache file in
#     the root of the dirname if the modification date of this file is
#     the same as the directory - that will be loaded instead.
#     """

#     def __init__(self, dirname, pattern='*.config'):
#         """
#         Constructor

#         :param dirname: directory to load
#         :type dirname: string
#         :param glob: a glob describing what files to load
#         :type glob: string
#         """
#         dict.__init__(self)
#         #print("loading", dirname, pattern)
#         self.load(dirname, pattern)

#     def load(self, dirname, pattern):
#         """
#         Load from the defined directory
#         """

#         cachefile = os.path.join(dirname, YACODIR_CACHEFILE)

#         # TODO: get caching to work properly :(
#         # if os.path.exists(cachefile):
#         #     if os.path.getmtime(dirname) == \
#         #             os.path.getmtime(cachefile):
#         # load cache
#         #         super(YacoDir, self).load(cachefile)
#         #         return

#         for root, dirs, files in os.walk(dirname):
#             to_parse = sorted(fnmatch.filter(files, pattern))
#             base = root.replace(dirname, '').strip('/')
#             base = base.replace('/', '.')
#             for filename in to_parse:
#                 fullname = os.path.join(root, filename)
#                 lg.debug("YacoDir loading {0}".format(fullname))
#                 nleaf = _get_leaf(base, filename, pattern)

#                 with open(fullname) as F:
#                     y = yaml.load(F.read())

#                 if nleaf == '':
#                     self.update(y)
#                 else:
#                     self[nleaf].update(y)
#         #print('*' * 80)
#         # print self.pretty()
#         if self:
#             # after loading - save to cache!
#            super(YacoDir, self).save(cachefile)

#     def save(self):
#         """
#         Save is disabled.
#         """
#         raise Exception("Cannot save to a YacoDir")


# #    db    db  .d8b.   .o88b.  .d88b.  d8888b. db   dD  d888b
# #    `8b  d8' d8' `8b d8P  Y8 .8P  Y8. 88  `8D 88 ,8P' 88' Y8b
# #     `8bd8'  88ooo88 8P      88    88 88oodD' 88,8P   88
# #       88    88~~~88 8b      88    88 88~~~   88`8b   88  ooo
# #       88    88   88 Y8b  d8 `8b  d8' 88      88 `88. 88. ~8~
# #       YP    YP   YP  `Y88P'  `Y88P'  88      YP   YD  Y888P

# class YacoPkg(Yaco):

#     def __init__(self, pkg_name, path,
#                  pattern='*.config',
#                  txt_pattern='*.txt',
#                  leaf="",
#                  base_path=None,
#                  prefix=None):

#         # lg.setLevel(logging.DEBUG)
#         thisleaf = None
#         if False:
#             lg.warning("pkg loading name: {0}".format(pkg_name))
#             lg.warning("            path: {0} {1}".format(path, pattern))
#             lg.warning("       base_path: {0}".format(base_path))

#             lg.warning("           isdir: {0}".format(
#                 pkg_resources.resource_isdir(pkg_name, path)))
#             lg.warning("            leaf: {0}".format(leaf))

#         if leaf:
#             leaf = leaf.strip('.')

#         # if base_path is None:
#         # leave leaf as iss
#         #     pass
#         # else:
#         #     leaf =  leaf + path.replace(base_path, '')\
#         #                     .strip('/')\
#         #                     .replace('/', '.')

#         lg.debug("leaf: ({0}) {1}".format(base_path, leaf))

#         if not pkg_resources.resource_isdir(pkg_name, path):
#             # this must be a file:
#             lg.debug("loading file {0} {1}".format(pkg_name, path))
#             #print("loading file {} {}".format(pkg_name, path))
#             y = pkg_resources.resource_string(pkg_name, path)

#             self[leaf].update(yaml.load(y))

#         else:
#             lg.debug("loading from package {0} {1}".format(pkg_name, path))

#             for d in pkg_resources.resource_listdir(pkg_name, path):
#                 nres = os.path.join(path, d)

#                 lg.debug("checking for pkg load: {0}".format(nres))
#                 if pkg_resources.resource_isdir(pkg_name, nres):
#                     if leaf:
#                         newleaf = leaf + '.' + d.replace('/', '.')
#                     else:
#                         newleaf = d.replace('/', '.').strip('.')

#                     lg.debug("pkg load: is directory: {0}".format(nres))

#                     if base_path is None:
#                         base_path = path
#                     if False:
#                         lg.warning("loading subpackage")
#                         lg.warning("       leaf: %s", leaf)
#                         lg.warning("   new_leaf: %s", newleaf)
#                         lg.warning("    pkgname: %s", pkg_name)
#                         lg.warning("    newpath: %s", nres)
#                         lg.warning("   basepath: %s", base_path)

#                     y = YacoPkgDir(pkg_name, nres,
#                                    pattern=pattern,
#                                    base_path=base_path,
#                                    leaf=newleaf)
#                     self.update(y)
#                 else:
#                     if fnmatch.fnmatch(d, pattern):
#                         this_leaf = _get_leaf(leaf, d, pattern)
#                         lg.debug("pkg load: loading file: {0}".format(nres))
#                         y = yaml.load(
#                             pkg_resources.resource_string(pkg_name, nres))
#                         lg.debug("pkg load: got: {0}".format(str(y)))
#                         #print('f', leaf, nres, this_leaf, str(y)[:50])
#                         self[this_leaf].update(y)
#                     elif fnmatch.fnmatch(d, txt_pattern):
#                         dl = d.replace('.txt', '')
#                         this_leaf = _get_leaf(leaf, dl, pattern)
#                         lg.debug("loading: %s", d)
#                         lg.debug("   into: %s", this_leaf)
#                         val = pkg_resources.resource_string(
#                             pkg_name, nres)
#                         self[this_leaf] = val

#                     else:
#                         lg.debug("Ignoring - file pattern mismatch: %s",
#                                  d)


# #    d8888b.  .d88b.  db      db    db
# #    88  `8D .8P  Y8. 88      `8b  d8'
# #    88oodD' 88    88 88       `8bd8'
# #    88~~~   88    88 88         88
# #    88      `8b  d8' 88booo.    88
# #    88       `Y88P'  Y88888P    YP


# YacoPkgDir = YacoPkg


# class PolyYaco(Yaco):

#     """
#     A meta object that allows a composite Yaco object to be loaded
#     from any number of different files which are kept as a stack of
#     Yaco objects. If looking for a value, this object will check each
#     of the layers in the stack and return the first value that it
#     comes across.

#     Changes are only made to the toplevel object.

#     The goal is to have multiple configuration files, for example in::

#         /location/to/python/package/etc/config.yaml
#         /etc/APPLICATION.yaml
#         ~/.config/APPLICATION/config.yaml

#     and have values in the latter file override those in the
#     former. Saving changed values will also be done to the latter, but
#     system and application wide settings can be maintained as well
#     (manually for the time being).
#     """

#     def __init__(self, name="PY", files=[],
#                  pattern='*.config',
#                  leaf=""):
#         """

#         """

#         # if not items - set a default
#         if files is None:
#             files = [
#                 '/etc/{0}.config'.format(name),
#                 '~/.config/{0}/'.format(name)]

#         super(PolyYaco, self).__init__()
#         self.load(leaf, files, pattern)

#     def load(self, leaf, files, pattern):
#         """

#         """
#         for filename in files:
#             filename = os.path.expanduser(filename)
#             lg.debug("Loading {0}".format(filename))
#             y = None
#             if filename[:6] == 'pkg://':
#                 # expecting pkg://Yaco/etc/config.yaml
#                 base = filename[6:]
#                 pkg, loc = base.split('/', 1)
#                 this_pattern = pattern
#                 if '*' in loc:
#                     if '/' in loc:
#                         loc, this_pattern = loc.rsplit('/', 1)
#                     else:
#                         loc, this_pattern = '/', loc

#                 try:
#                     y = YacoPkg(pkg, loc, pattern=this_pattern)
#                 except IOError:
#                     # file does probably not exists - ignore
#                     lg.debug("cannot load file {0}".format(loc))
#                     pass
#                 except ImportError:
#                     # or the complete package does not exists - one of script?
#                     # ignore
#                     lg.debug("cannot find package {0}".format(pkg))

#                     pass

#             elif os.path.isdir(filename):
#                 y = YacoDir(filename, pattern=pattern)
#                 #print('load dir')
#             elif os.path.isfile(filename):
#                 y = Yaco()
#                 y.load(filename)
#             else:
#                 # nothing to load
#                 continue

#             if not y is None:
#                 #print("update", filename, leaf)
#                 # print(y.plugin.plugin)
#                 self[leaf].update(y)
#         # print(self.pretty())

#     def save(self):
#         lg.warning("PolyYaco save is disabled")


# if __name__ == "__main__":
#     if 'x' in sys.argv:
#         y = Yaco()
#         y.x.z = 1
#         print(y.x.z)
#     else:
#         import doctest
#         doctest.testmod()
