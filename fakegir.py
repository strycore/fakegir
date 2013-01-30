"""Build a fake python package from the information found in gir files"""
import os
import keyword
from lxml import etree

GIR_PATH = '/usr/share/gir-1.0/'
FAKEGIR_PATH = os.path.join(os.path.expanduser('~'), '.cache/fakegir')


def get_docstring(callable_tag):
    for element in callable_tag:
        tag = etree.QName(element)
        if tag.localname == 'doc':
            return element.text.encode('utf-8') + "\n"
    return ''


def insert_function(name, args, depth, docstring=''):
    if keyword.iskeyword(name):
        name = "_" + name
    arglist = ", ".join(args)
    return "%sdef %s(%s):\n%s\"\"\"%s\"\"\"\n" % ('    ' * depth,
                                                  name,
                                                  arglist,
                                                  '    ' * (depth + 1),
                                                  docstring)


def extract_methods(class_tag):
    methods_content = ''
    for element in class_tag:
        tag = etree.QName(element)
        if tag.localname == 'method':
            method_name = element.attrib['name']
            docstring = get_docstring(element)
            methods_content += insert_function(method_name, ['self'], 1,
                                               docstring)
    return methods_content


def extract_namespace(namespace):
    namespace_content = ""
    for element in namespace:
        tag = etree.QName(element)
        tag_name = tag.localname
        if tag_name == 'class':
            class_name = element.attrib['name']
            docstring = get_docstring(element)
            class_content = ("\nclass %s:\n    \"\"\"%s\"\"\"\n"
                             % (class_name, docstring))
            class_content += extract_methods(element)
            namespace_content += class_content
        if tag_name == 'function':
            function_name = element.attrib['name']
            docstring = get_docstring(element)
            namespace_content += insert_function(function_name, [], 0,
                                                 docstring)
        if tag_name == 'constant':
            constant_name = element.attrib['name']
            constant_value = element.attrib['value'] or 'None'
            namespace_content += ("%s = '%s'\n"
                                  % (constant_name, constant_value))
    return namespace_content


def parse_gir(gir_path):
    tree = etree.parse(gir_path)
    root = tree.getroot()
    elements = root.findall('./')
    namespace_content = ""
    for element in elements:
        if 'namespace' in element.tag:
            namespace_content = extract_namespace(element)
    return namespace_content


def iter_girs():
    for gir_file in os.listdir(GIR_PATH):
        # Don't know what to do with those, guess nobody uses PyGObject
        # for Gtk 2.0 anyway
        if gir_file in ('Gtk-2.0.gir', 'Gdk-2.0.gir', 'GdkX11-2.0.gir'):
            continue
        module_name = gir_file[:gir_file.index('-')]
        gir_info = (module_name, gir_file)
        yield gir_info


if __name__ == "__main__":
    fakegir_repo_dir = os.path.join(FAKEGIR_PATH, 'gi/repository')
    if not os.path.exists(fakegir_repo_dir):
        os.makedirs(fakegir_repo_dir)

    gi_init_path = os.path.join(FAKEGIR_PATH, 'gi/__init__.py')
    with open(gi_init_path, 'w') as gi_init_file:
        gi_init_file.write('')
    repo_init_path = os.path.join(FAKEGIR_PATH, 'gi/repository/__init__.py')
    with open(repo_init_path, 'w') as repo_init_file:
        repo_init_file.write('')

    for module_name, gir_file in iter_girs():
        gir_path = os.path.join(GIR_PATH, gir_file)
        fakegir_content = parse_gir(gir_path)
        fakegir_path = os.path.join(FAKEGIR_PATH, 'gi/repository',
                                    module_name + ".py")
        with open(fakegir_path, 'w') as fakegir_file:
            fakegir_file.write("# -*- coding: utf-8 -*-\n")
            fakegir_file.write(fakegir_content)
