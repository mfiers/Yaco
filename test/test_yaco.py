
import os
import logging
import tempfile
import unittest
import yaml
import collections


try:
    from sqlite3 import ProgrammingError
except ImportError:
    from pysqlite2.dbapi2 import ProgrammingError

import Yaco2

lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)


class BasicYacoTest(unittest.TestCase):

    def setUp(self):
        self.y = Yaco2.Yaco()
        self.z = Yaco2.Yaco()
        self.prepopulate()

    def prepopulate(self):
        self.y['a'] = 5
        self.z['a.a'] = 1
        self.z['a.b'] = 2
        self.z['b.c'] = 3

    def test_basic_asignment(self):
        self.y['a'] = 2
        self.y['b'] = 3
        self.assertEqual(self.y['a'], 2)
        self.assertEqual(self.y['b'], 3)

    def test_keys(self):
        kys = self.y.keys()
        self.assertTrue(isinstance(kys, collections.Iterable))
        self.assertEqual(set(kys), set(['a']))

        kys = self.z.keys()
        self.assertTrue(isinstance(kys, collections.Iterable))
        self.assertEqual(set(kys), set(['a.a', 'a.b', 'b.c']))

    def test_compare(self):
        self.assertEqual(self.y, {'a': 5})
        self.assertNotEqual(self.y, {'a': 2, 'b': 1})

    def test_vals(self):
        kys = self.y.values()
        self.assertTrue(isinstance(kys, collections.Iterable))
        self.assertEqual(set(kys), set([5]))
        kys = self.z.values()
        self.assertEqual(set(kys), set([1, 2, 3]))

    def test_in(self):
        self.assertTrue('a' in self.y)
        self.assertTrue('a.a' in self.z)
        self.assertTrue('a.b' in self.z)
        self.assertFalse('a.c' in self.z)
        self.assertTrue('b.c' in self.z)

    def test_clear_db(self):
        self.assertEqual(len(list(self.y.keys())), 1)
        self.y.clear()
        self.assertEqual(len(list(self.y.keys())), 0)

    def test_update(self):
        self.y['b'] = 2
        self.y.update({'a': 5, 'c': 3, 'd': 4})
        self.assertEqual(self.y, {'a': 5, 'b': 2, 'c': 3, 'd': 4})

    def test_to_dict(self):
        d = dict(self.y)
        self.assertEqual(type(d), type({}))

    #
    # branch tests
    #

    def test_branch_simple(self):
        s = self.y.get_branch('a')
        self.assertFalse('a' in s)
        kys = list(s.keys())
        self.assertEqual(len(kys), 0)

        t = self.z.get_branch('a')
        self.assertTrue('a' in t)
        kys = list(t.keys())
        self.assertEqual(len(kys), 2)

    def test_branch_keys(self):
        t = self.z.get_branch('a')
        kys = list(t.keys())
        self.assertEqual(set(kys), set(['a', 'b']))

    def test_branch_iterate_values(self):
        t = self.z.get_branch('a')
        rv = set()
        for i in t.values():
            rv.add(i)
        self.assertEqual(set([1, 2]), rv)

    def test_branch_to_dict(self):
        s = self.z.get_branch('a')
        #lg.critical("branch11 - %s", dict(s))
        self.assertEqual(dict(s), {'a': 1, 'b': 2})

    def test_branch_update(self):
        s = self.z.get_branch('a')
        s.update({'a': 5, 'c': 3})
        self.assertEqual(
            self.z, {'b.c': 3, 'a.a': 5, 'a.b': 2, 'a.c': 3})

    def test_update_with_a_branch(self):
        s = self.z.get_branch('a')
        self.y['c'] = 12
        self.y.update(s)
        self.assertEqual(self.y, {'a': 1, 'b': 2, 'c': 12})

    def test_update_a_branch_with_a_branch(self):
        s = self.z.get_branch('a')
        self.y['c'] = 12
        t = self.y.get_branch('a.b.c')
        t.update(s)
        self.assertEqual(
            self.y, {'a': 5, 'c': 12, 'a.b.c.a': 1, 'a.b.c.b': 2})


class DbYacoTest(BasicYacoTest):

    """
    All basic dictionary tests should also work for the
    db variant.

    """

    def setUp(self):
        self.dbloc_a = tempfile.NamedTemporaryFile(delete=False)
        self.dbloc_a.close()
        self.y = Yaco2.YacoDb(self.dbloc_a.name)

        self.dbloc_b = tempfile.NamedTemporaryFile(delete=False)
        self.dbloc_b.close()
        self.z = Yaco2.YacoDb(self.dbloc_b.name)
        self.prepopulate()

    def test_persistence(self):

        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.close()

        a = Yaco2.YacoDb(tf.name)
        a['q'] = 55
        a.close()

        b = Yaco2.YacoDb(tf.name)
        self.assertEqual(b['q'], 55)

        b.close(delete_db=True)

    def test_close_db(self):

        self.assertTrue(os.path.exists(self.y.datapath))
        self.y.close()

        self.assertRaises(ProgrammingError, lambda: self.y['a'])
        self.assertTrue(os.path.exists(self.y.datapath))

    def test_delete_db(self):
        self.assertTrue(os.path.exists(self.y.datapath))
        self.y.close(delete_db=True)
        self.assertRaises(ProgrammingError, lambda: self.y['a'])
        self.assertFalse(os.path.exists(self.y.datapath))

    def tearDown(self):
        try:
            self.y.close(delete_db=True)
        except OSError:
            pass
        try:
            self.z.close(delete_db=True)
        except OSError:
            pass

test_yaml = """
a:
  b1:
    c1: v1
    c2: v2
    c3: v3
  b2: v4
b: v5
"""

test_dict = yaml.load(test_yaml)


class LoaderTest(unittest.TestCase):

    def setUp(self):
        self.tf = tempfile.NamedTemporaryFile(delete=False)
        self.tf.write(test_yaml.encode('utf8'))
        self.tf.close()
        self.test_dir = os.path.join(
            os.path.dirname(__file__), 'data')

    def get_empty_yaco(self):
        return Yaco2.Yaco()

    def test_dict_loader(self):
        y = self.get_empty_yaco()
        Yaco2.dict_loader(y, test_dict)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')

    def test_simple_loader_yaml(self):
        y = self.get_empty_yaco()
        Yaco2.load(y, test_dict)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')

    def test_yaml_string_loader(self):
        y = self.get_empty_yaco()
        Yaco2.yaml_string_loader(y, test_yaml)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')
        z = self.get_empty_yaco()
        Yaco2.dict_loader(z, test_dict)
        self.assertEqual(y, z)


    def test_yaml_string_loader_simple(self):
        y = self.get_empty_yaco()
        Yaco2.load(y, test_yaml)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')
        z = self.get_empty_yaco()
        Yaco2.dict_loader(z, test_dict)
        self.assertEqual(y, z)

    def test_yaml_file_loader(self):
        y = self.get_empty_yaco()
        Yaco2.yaml_file_loader(y, self.tf.name)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')
        z = self.get_empty_yaco()
        Yaco2.dict_loader(z, test_dict)
        self.assertEqual(y, z)


    def test_yaml_file_save(self):
        y = self.get_empty_yaco()
        y['a.b.c'] = 1
        y['d.e'] = '2'

        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.close()
        Yaco2.yaml_file_save(y, tf.name)
        tf.close()

        z = Yaco2.Yaco()
        Yaco2.yaml_file_loader(z, tf.name)
        self.assertEqual(y, z)

    def test_yaml_file_loader_simple(self):
        y = self.get_empty_yaco()
        Yaco2.load(y, self.tf.name)
        self.assertEqual(y['a.b1.c2'], 'v2')
        self.assertEqual(y['b'], 'v5')
        z = self.get_empty_yaco()
        Yaco2.dict_loader(z, test_dict)
        self.assertEqual(y, z)

    def test_dir_loader(self):
        y = self.get_empty_yaco()
        Yaco2.dir_loader(y, self.test_dir)
        self.assertEqual(y['test.a'], 1)
        self.assertEqual(y['subdir.subtest.e.g'], 4)
        self.assertEqual(y['subdir.subsubdir.subsubtest.g'], 4)
        self.assertEqual(y['subdir.subtest.d'], 'overridden')
        self.assertEqual(y['subdir.raw'].strip(),
                         'multiline\ntext\nfield')

    def test_package_loader(self):
        y = self.get_empty_yaco()
        Yaco2.package_loader(y, "Yaco2", "etc")
        self.assertEqual(y['Mus'], 'musculus')
        self.assertEqual(y['subdir.Rattus'], 'norvegicus')
        self.assertEqual(y['subdir.Sus'], 'scrofa')
        self.assertEqual(y['subdir.test.Gallus'], 'Gallus')

    def test_simple_package_loader(self):
        y = self.get_empty_yaco()
        Yaco2.simple_package_loader(y, "pkg://Yaco2/etc")
        self.assertEqual(y['Mus'], 'musculus')
        self.assertEqual(y['subdir.Rattus'], 'norvegicus')
        self.assertEqual(y['subdir.Sus'], 'scrofa')
        self.assertEqual(y['subdir.test.Gallus'], 'Gallus')

    def test_simple_loader(self):
        y = self.get_empty_yaco()
        Yaco2.load(y, "pkg://Yaco2/etc")
        self.assertEqual(y['Mus'], 'musculus')
        self.assertEqual(y['subdir.Rattus'], 'norvegicus')
        self.assertEqual(y['subdir.Sus'], 'scrofa')
        self.assertEqual(y['subdir.test.Gallus'], 'Gallus')

    def tearDown(self):
        os.unlink(self.tf.name)


class LoaderDbTest(LoaderTest):

    def get_empty_yaco(self):
        self.ydb = tempfile.NamedTemporaryFile(delete=False)
        self.ydb.close()
        return Yaco2.YacoDb(self.ydb.name)

    def tearDown(self):
        os.unlink(self.tf.name)
        os.unlink(self.ydb.name)
