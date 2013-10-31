
import os
import logging
import shutil
import tempfile
import unittest
import yaml

import Yaco

lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)

test_set_1 = {
    'a': 1,
    'b': 2,
    'c': {'d': 3,
          'e': 4,
          'f': 5},
    'g': [0, 1, 2, 3,
          {'h': 6,
           'i': 7,
           'j': 8,
           }]}

test_set_2 = {
    'a': 18,
    'b': {'k': 9,
          'm': 10
          },
    'g': [0, 1, 2, 3, 4, 5]
}


def d():
    return Yaco.Yaco(test_set_1)

class BasicYacoTest(unittest.TestCase):

    def test_load(self):
        Yaco.Yaco()

    def test_simpledict(self):
        y = Yaco.Yaco()
        y['a'] = 1
        y['b'] = 2
        self.assertEqual(y['a'], 1)
        self.assertEqual(y['b'], 2)

        self.assertTrue('b' in y)

        del(y.b)
        self.assertTrue(not 'b' in y)
        self.assertTrue('b' not in y)

    def test_dots_in_keys(self):
        y = Yaco.Yaco()
        y.a.b = 2
        assert(y['a.b'] == 2)
        y['a.c.e'] = 4
        assert(y.a.c.e == 4)

    def test_yaco_has_attribute_access(self):
        y = d()
        self.assertEqual(y.a, 1)
        self.assertEqual(y.b, 2)

    def test_yaco_can_do_multiple_levels(self):
        y = Yaco.Yaco()
        y['a'] = Yaco.Yaco()
        y['a']['b'] = 3
        self.assertEqual(y['a']['b'], 3)
        self.assertEqual(y.a.b, 3)

    def test_load_from_dict(self):
        y = Yaco.Yaco(test_set_1)
        self.assertEqual(y['a'], 1)
        self.assertEqual(y.c.e, 4)

    def test_implicit_branch_creation(self):
        y = Yaco.Yaco()
        y.a.b.c = 4
        self.assertEqual(y['a']['b']['c'], 4)
        self.assertEqual(y.a.b.c, 4)

    def test_list_integration(self):
        y = Yaco.Yaco()
        y.a.b.c = 4
        y.a.d = [0, 1, 2, Yaco.Yaco()]
        y.a.d[3].e = 'test'
        self.assertEqual(y.a.d[3].e, 'test')

    def test_update(self):
        y = Yaco.Yaco(test_set_1)
        self.assertEqual(y.b, 2)
        y.update(test_set_2)
        self.assertNotEqual(y.b, 2)
        self.assertEqual(y.b.m, 10)

    def test_leaf_update(self):
        y = Yaco.Yaco()
        y.a = 1
        y.b.c.d = 2

        z = Yaco.Yaco()
        z.c = 3
        z.e = 4
        self.assertEqual(y.b.c.d, 2)
        y[''].d = 5
        self.assertEqual(y.d, 5)

        y['b.c.d'] = 8
        self.assertEqual(y.b.c.d, 8)

        y['b.c'].update(z)
        self.assertEqual(y.b.c.c, 3)
        self.assertEqual(y.b.c.d, 8)
        self.assertEqual(y.b.c.e, 4)


    def test_save_and_yaml(self):
        y = Yaco.Yaco(test_set_1)
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        y.save(tmpfile.name)
        self.assertTrue(os.path.exists(tmpfile.name))
        with open(tmpfile.name) as F:
            YY = yaml.load(F)
        self.assertEqual(YY['a'], 1)
        self.assertEqual(YY['g'][4]['i'], 7)


class BasicYacoFileTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp("PolyYacoTest")
        self.filename = os.path.join(self.tmpdir, 'one.yaml')

        #save a testset to Yaco files
        y = Yaco.Yaco(test_set_1)
        y.save(self.filename)

    def test_load(self):
        y = Yaco.YacoFile(self.filename)
        self.assertEqual(y.b, 2)

    def test_load_leaf(self):
        y = Yaco.Yaco()
        y.load(self.filename, "leaf")
        self.assertEqual(y.leaf.b, 2)

    def test_load_leaf_2(self):
        y = Yaco.Yaco()
        y.load(self.filename, "deeply.nested.leaf")
        self.assertEqual(y.deeply.nested.leaf.b, 2)

    def test_loadsave(self):
        y = Yaco.YacoFile(self.filename)
        y.load()
        self.assertEqual(y.b, 2)
        y.b = 3
        y.save()
        z = Yaco.YacoFile(self.filename)
        self.assertEqual(y.b, 3)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class BasicYacoDirTest(unittest.TestCase):

    def setUp(self):

        self.tmpdir = tempfile.mkdtemp("PolyYacoTest")
        sa = os.path.join(self.tmpdir, 'sub_a', 'sub_c')
        sb = os.path.join(self.tmpdir, 'sub_b')

        os.makedirs(sa)
        os.makedirs(sb)

        self.filenameA = os.path.join(self.tmpdir, '_one.config')
        self.filenameB = os.path.join(self.tmpdir, 'two.config')

        #save two testsets to Yaco files
        y = Yaco.Yaco(test_set_1)
        x = Yaco.Yaco(test_set_2)

        y.save(self.filenameA)
        x.save(self.filenameB)

        y.save(os.path.join(sa, 'three.config'))
        x.save(os.path.join(sb, '_four.config'))

    def test_load(self):
        y = Yaco.YacoDir(self.tmpdir)
        #print y.pretty()
        self.assertEqual(y.sub_a.sub_c.three.c.d, 3)
        self.assertEqual(y.a, 1)
        self.assertEqual(y.two.a, 18)
        self.assertEqual(y.c.d, 3)
        self.assertEqual(y.c.d, 3)

        self.assertEqual(y.sub_a.sub_c.three.a, 1)

    def test_cache(self):
        y = Yaco.YacoDir(self.tmpdir)
        self.assertTrue(os.path.exists(
            os.path.join(self.tmpdir, Yaco.YACODIR_CACHEFILE)))
        #hmm - loading it twice should activate cache loading
        y = Yaco.YacoDir(self.tmpdir)


    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class BasicPolyYacoTest(unittest.TestCase):

    def setUp(self):

        self.tmpdir = tempfile.mkdtemp("PolyYacoTest")

        self.filenameA = os.path.join(self.tmpdir, 'one.yaml')
        self.filenameB = os.path.join(self.tmpdir, 'two.yaml')

        sb = os.path.join(self.tmpdir, 'subdir_b')
        self.subdir = sb
        os.makedirs(sb)

        #save two testsets to Yaco files
        y = Yaco.Yaco(test_set_1)
        x = Yaco.Yaco(test_set_2)

        y.save(self.filenameA)
        x.save(self.filenameB)
        x.save(os.path.join(sb, 'four.yaml'))


    def get_py_files(self):
        return Yaco.PolyYaco(files=[self.filenameA, self.filenameB])

    def get_py_filesanddirs(self):
        return Yaco.PolyYaco(files=[self.filenameA, self.subdir])

    def test_load(self):
        y = Yaco.PolyYaco()

    def test_load_files(self):
        y = self.get_py_files()
        self.assertEqual(y.c.e, 4)

    def test_load_filesanddirs(self):
        pkg = 'pkg://Yaco/etc/test.config'
        y = Yaco.PolyYaco(files=[pkg, self.filenameA, self.subdir])
        self.assertEqual(y.c.e, 4)

    def test_load_filespkgsanddirs_pattern(self):
        pkg = 'pkg://Yaco/etc/*.config'
        y = Yaco.PolyYaco(files=[pkg, self.filenameA, self.subdir])
        self.assertEqual(y.c.e, 4)
        self.assertEqual(y.Mus, 'musculus')
        #self.assertEqual(y.Sus, 'scrofa')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class BasicYacoPkgTest(unittest.TestCase):

    def test_get_basic(self):
        y = Yaco.YacoPkg("Yaco", "etc/__root__.config")
        self.assertEqual(y.Mus, 'musculus')
        self.assertNotEqual(y.subset_a.Sus, 'scrofa')

    def test_get_basic_subdir(self):
        y = Yaco.YacoPkg("Yaco", "etc/")
        self.assertEqual(y.Mus, 'musculus')
        self.assertEqual(y.subset_a.Sus, 'scrofa')

    def test_leaf_basic_loading(self):
        y = Yaco.YacoPkg("Yaco", "etc/", leaf='a.b.c')
        self.assertEqual(y.a.b.c.Mus, 'musculus')
        self.assertEqual(y.a.b.c.subset_a.Sus, 'scrofa')

    def test_get_custom_location(self):
        y = Yaco.YacoPkg("Yaco", 'etc/subset_a/')
        self.assertEqual(y.Sus, 'scrofa')


