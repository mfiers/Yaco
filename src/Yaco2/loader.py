"""
Load a dict from disk & populate a YacoDict

"""

import logging
import os
import pkg_resources

import yaml

lg = logging.getLogger(__name__)

_demo_object = yaml.load(
"""
a:
  b1:
    c1: v1
    c2: v2
    c3: v3
  b2: v4
""")


def dict_loader(yaco_object, dictionary):
    """
    Populate a yaco object from a dictionary
    """
    for k, v in dictionary.iteritems():
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
                branch_name += '.{}'.format(file_name)
            branch_name.lstrip('.')  # no dots at the end allowed
            branch = yaco_object.get_branch(branch_name)

            if file_ext in ['yaml', 'conf', 'config']:
                yaml_file_loader(branch, full_file_name)
            elif file_ext == 'txt':
                with open(full_file_name) as F:
                    val = F.read()
                yaco_object[branch_name] = val


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

        if filename[0] != '_':
            branch_name += ".{}".format(file_base)

        data = pkg_resources.resource_string(pkg_name, path)
        b = yaco_object.get_branch(branch_name, absolute=True)
        yaml_string_loader(b, data)
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

