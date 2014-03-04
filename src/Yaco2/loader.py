"""
Load a dict from disk & populate a YacoDict

"""

import logging
import os
import pkg_resources

import yaml

lg = logging.getLogger(__name__)
#lg.setLevel(logging.DEBUG)

_demo_object = yaml.load(
"""
a:
  b1:
    c1: v1
    c2: v2
    c3: v3
  b2: v4
""")

#['pkg://leip/etc/*.config', u'/Users/u0089478/.config/leip/', '/etc/leip/']


def guess_loader(data):
    if isinstance(data, dict):
        return dict_loader
    elif not isinstance(data, basestring):
        raise Exception("Invalid data type {0} ({1}".format(
            str(data)[:50], type(data)))
    elif os.path.isdir(data):
        return dir_loader
    elif data[:6] == 'pkg://':
        return simple_package_loader
    elif os.path.isfile(data):
        try:
            name, ext = data.rsplit('.', 1)
            if ext.lower() in ['yaml', 'config', 'conf']:
                return yaml_file_loader
            else:
                raise Exception("unknown file type: {0}".format(data))
        except:
            # just go for it :/
            return yaml_file_loader
    elif data[0] == '/' or data[0] == '~':
        # looks like a file or dir - but may not exists..
        return dummy_loader
    else:
        # assume it's just plain yaml
        return yaml_string_loader


def dummy_loader(yaco_object, data):
    """
    Do not do anything - just pretend
    """
    pass


def load(yaco_object, data):
    """
    Generic loader - tries to be smart
    """
    guess_loader(data)(yaco_object, data)


def dict_loader(yaco_object, dictionary):
    """
    Populate a yaco object from a dictionary
    """
    if isinstance(dictionary, str):
        raise Exception("invalid dictionary: {}".format(
            str(dictionary)[:80]))
        exit(-1)
    for k, v in dictionary.items():
        if isinstance(v, dict):
            dict_loader(yaco_object.get_branch(k), v)
        else:
            yaco_object[k] = v


def yaml_string_loader(yaco_object, data):
    """
    Populate a yaco object from a yaml string
    """
    parsed = yaml.load(data)
    return dict_loader(yaco_object, parsed)


def yaml_file_loader(yaco_object, filename):
    """
    Populate a yaco object from a yaml string
    """
    with open(filename) as F:
        parsed = yaml.load(F)
    return dict_loader(yaco_object, parsed)


def yaml_file_save(yaco_object, filename):
    """
    Save a file to yaml
    """
    lg.debug("saving to %s", filename)
    with open(filename, 'w') as F:
        F.write(yaml.dump(dict(yaco_object),
                          encoding=('ascii'),
                          default_flow_style=False))


def dir_loader(yaco_object, path):
    """
    Populate a yaco object from a directory of yaml files

    * loading is depth first - this results in values in a
      directory being overwritten by overlapping definitions
      in a file higher in the tree
    * directory names are interpreted as keys in the tree

    """
    start_path = path
    for path, dirs, files in os.walk(start_path, topdown=False):
        branch_base = os.path.relpath(path, start_path).replace('/', '.')

        for f in files:
            file_name, file_ext = f.rsplit('.', 1)
            full_file_name = os.path.join(path, f)

            # get the proper branch
            branch_name = branch_base
            if f[0] != '_':
                branch_name += '.{0}'.format(file_name)
            branch_name.lstrip('.')  # no dots at the end allowed
            branch = yaco_object.get_branch(branch_name)

            if file_ext in ['yaml', 'conf', 'config']:
                yaml_file_loader(branch, full_file_name)
            elif file_ext == 'txt':
                with open(full_file_name) as F:
                    val = F.read()
                yaco_object[branch_name] = val


def simple_package_loader(yaco_object, data):
    assert(data[:6] == 'pkg://')
    name, path = data[6:].split('/', 1)
    path = '/' + path
    return package_loader(yaco_object, name, path)


def package_loader(yaco_object, pkg_name, path, start_path=None):

    if start_path is None:
        start_path = path

    # check if we're looking at a single file in a package -
    # if so - load that.
    if not pkg_resources.resource_isdir(pkg_name, path):

        base_path, filename = os.path.split(path)
        file_base, file_ext = filename.rsplit('.', 1)

        branch_name = os.path.relpath(base_path, start_path)\
            .replace('/', '.').strip('.')

        data = pkg_resources.resource_string(pkg_name, path)

        if filename[0] != '_':
            branch_name += ".{0}".format(file_base)

        if file_ext in ['yaml', 'conf', 'config']:
            b = yaco_object.get_branch(branch_name, absolute=True)
            yaml_string_loader(b, data)
        elif file_ext in ['txt']:
            r = yaco_object.get_branch("", absolute=True)
            r[branch_name] = data
        return

    # It's a directory
    # base branch name - from path
    branch_name = os.path.relpath(path, start_path)\
        .replace('/', '.').strip('.')

    # start loading - depth first - so do directories
    for obj in pkg_resources.resource_listdir(pkg_name, path):
        new_path = os.path.join(path, obj)
        if pkg_resources.resource_isdir(pkg_name, new_path):
            package_loader(yaco_object.get_branch(branch_name),
                           pkg_name, new_path, start_path)

    # and now files
    for obj in pkg_resources.resource_listdir(pkg_name, path):
        new_path = os.path.join(path, obj)
        if not pkg_resources.resource_isdir(pkg_name, new_path):
            package_loader(yaco_object.get_branch(branch_name),
                           pkg_name, new_path, start_path)
