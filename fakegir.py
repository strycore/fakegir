#!/usr/bin/env python3
"""Build a fake python package from the information found in gir files"""
import glob
import keyword
import os
import re
import sys
import logging
from itertools import chain

from lxml.etree import XML, QName, XMLParser

LOGGER = logging.getLogger(__name__)
GIR_PATHS = ['/usr/share/gir-1.0/*.gir', '/usr/share/*/gir-1.0/*.gir']
FAKEGIR_PATH = os.path.expanduser('~/.cache/fakegir')
XMLNS = "http://www.gtk.org/introspection/core/1.0"
ADD_DOCSTRINGS = 'WITHDOCS' in os.environ

GIR_TO_NATIVE_TYPEMAP = {
    'gboolean': 'bool',
    'gint': 'int',
    'guint': 'int',
    'gint64': 'int',
    'guint64': 'int',
    'none': 'None',
    'gchar': 'str',
    'guchar': 'str',
    'gchar*': 'str',
    'guchar*': 'str',
    'glong': 'long',
    'gulong': 'long',
    'glong64': 'long',
    'gulong64': 'long',
    'gfloat': 'float',
    'gdouble': 'float',
    'string': 'str',
    'GString': 'str',
    'utf8': 'str',
}


def write_stderr(message, *args, **kwargs):
    """Write a message to standard error stream.
        If any extra positional or keyword arguments
        are given, call format() on the message
        with these arguments."""

    if args or kwargs:
        message = message.format(*args, **kwargs)

    sys.stderr.write(message + "\n")


def get_native_type(typename):
    """Convert a C type to a Python type"""
    typename = typename.replace("const ", "")
    return GIR_TO_NATIVE_TYPEMAP.get(typename, typename)


def get_docstring(callable_tag):
    """Return docstring text for a callable"""
    if ADD_DOCSTRINGS:
        for element in callable_tag:
            tag = QName(element)
            if tag.localname == 'doc':
                return element.text.replace("\\x", 'x')
    return ''


def get_parameter_type(element):
    """Returns the type of a parameter"""
    param_type = ""
    for elem_property in element:
        tag = QName(elem_property)
        if tag.localname == "type":
            try:
                param_type = elem_property.attrib['name']
            except KeyError:
                param_type = 'object'

            break
    return param_type


def get_parameter_doc(element):
    """Returns the doc of a parameter"""
    param_doc = ""
    if ADD_DOCSTRINGS:
        for elem_property in element:
            tag = QName(elem_property)
            if tag.localname == "doc":
                param_doc = (
                    element
                    .text
                    .replace("\\x", 'x')
                    .encode('utf-8')
                    .replace("\n", " ")
                    .strip()
                )
                break

    return param_doc


def get_parameters(element):
    """Return the parameters of a callable"""
    params = []
    for elem_property in element:
        tag = QName(elem_property)
        if tag.localname == 'parameters':
            for param in elem_property:
                subtag = QName(param)
                if subtag.localname == "instance-parameter":
                    param_name = 'self'
                else:
                    try:
                        param_name = param.attrib['name']
                    except KeyError:
                        continue

                param_type = get_parameter_type(param)
                param_doc = get_docstring(param).replace("\n", " ").strip()

                if keyword.iskeyword(param_name):
                    param_name = "_" + param_name

                if param_name == '...':
                    param_name = '*args'

                if param_name not in [p[0] for p in params]:
                    params.append((param_name, param_doc, param_type))
    return params


def indent(lines, depth):
    """Return a list of lines indented by depth"""
    return ['    ' * (depth + 1) + l for l in lines]


def make_safe(string):
    """Avoid having unicode characters in docstrings (such as uXXXX)"""
    return string.replace("\\u", "u").replace("\\U", "U")


def get_returntype(element):
    """Return the return-type of a callable"""
    for elem_property in element:
        tag = QName(elem_property)
        if tag.localname == 'return-value':
            return_doc = get_docstring(elem_property).replace("\n", " ").strip()
            for subelem in elem_property:
                try:
                    subtag = QName(subelem)
                    if subtag.localname == "type":
                        try:
                            return_type = subelem.attrib['name']
                        except KeyError:
                            return_type = 'object'

                        return (return_doc, return_type)

                except KeyError:
                    pass
    return ("", "None")


def prettify(string):
    return re.sub(r"([\s]{3,80})", r"\n\1", string)


def insert_function(name, parameters, returntype, depth, docstring='', annotation=''):
    """Returns a function as a string"""
    if keyword.iskeyword(name) or name == 'print':
        name = "_" + name

    function_params = []
    for parameter in parameters:
        parameter_name = parameter[0]
        if not parameter_name.startswith('*') and parameter_name != 'self':
            function_params.append('%s=None' % parameter_name)
        else:
            function_params.append(parameter_name)

    arglist = ", ".join([p for p in function_params])

    full_docstrings = ""
    if ADD_DOCSTRINGS:
        param_docstrings = [
            "@param {}: {}".format(pname, make_safe(pdoc))
            if (pdoc and pname != "self") else ""
            for (pname, pdoc, ptype) in parameters
        ]

        type_docstrings = [
            "@type %s: %s" % (pname, get_native_type(ptype))
            if (ptype and pname != "self") else ""
            for (pname, pdoc, ptype) in parameters
        ]

        return_docstrings = []
        if returntype[1] == 'None':
            return_docstrings = ["@rtype: None"]
        else:
            return_docstrings = [
                "@returns: {}".format(prettify(returntype[0])),
                "@rtype: {}".format(get_native_type(returntype[1]))
            ]

        full_docstrings = "\n".join(
            indent(chain(
                docstring.split("\n"),
                [p for p in param_docstrings if p],
                [t for t in type_docstrings if t],
                return_docstrings,
                [""]
            ), depth)
        )
    indent_level = '    ' * depth
    return "%s\n%sdef %s(%s):\n%s    \"\"\"%s\"\"\"\n%s    return object\n" % (
        indent_level + annotation,
        indent_level,
        name,
        arglist,
        indent_level,
        full_docstrings,
        indent_level
    )


def insert_enum(element):
    """Returns an enum (class with attributes only) as text"""
    enum_name = element.attrib['name']
    docstring = get_docstring(element)
    enum_content = "\n\nclass {}:\n    \"\"\"{}\"\"\"\n".format(
        enum_name, docstring
    )
    members = element.findall("{%s}member" % XMLNS)
    for member in members:
        enum_name = member.attrib['name']
        if not enum_name:
            enum_name = "_"
        if enum_name and enum_name[0].isdigit():
            enum_name = '_' + enum_name
        enum_value = member.attrib['value']
        enum_value = enum_value.replace('\\', '\\\\')
        enum_content += "    %s = '%s'\n" % (enum_name.upper(), enum_value)
    return enum_content


def extract_methods(class_tag):
    """Return methods from a class element"""
    methods_content = ''
    for element in class_tag:
        tag = QName(element)
        if tag.localname in ('function', 'method', 'virtual-method'):
            method_name = element.attrib['name']
            if method_name == 'print':
                method_name += "_"
            docstring = get_docstring(element)
            params = get_parameters(element)
            annotation = "" if any(p[0] == "self" for p in params) else "@staticmethod"
            returntype = get_returntype(element)
            methods_content += insert_function(method_name,
                                               params,
                                               returntype,
                                               1,
                                               docstring,
                                               annotation)
    return methods_content


def extract_constructors(class_tag):
    """return the constructor methods for this class"""
    class_name = class_tag.attrib["name"]
    methods_content = ''
    for element in class_tag:
        tag = QName(element)
        if tag.localname == 'constructor':
            method_name = element.attrib['name']
            docstring = get_docstring(element)
            params = get_parameters(element)
            returntype = ("Newly created " + class_name, class_name)

            if method_name == "new":
                params_init = list(params)
                params_init.insert(0, ("self", "", ""))
                methods_content += insert_function("__init__", params_init,
                                                   returntype, 1, docstring)

            methods_content += insert_function(method_name,
                                               params,
                                               returntype,
                                               1,
                                               docstring,
                                               annotation="@staticmethod")
    return methods_content


def build_classes(classes):
    """Order classes with correct dependency order
    also return external imports
    """
    classes_text = ""
    imports = set()
    local_parents = set()
    written_classes = set()
    all_classes = set([class_info[0] for class_info in classes])
    for class_info in classes:
        parents = class_info[1]
        local_parents = local_parents.union(set([class_parent
                                                 for class_parent in parents
                                                 if '.' not in class_parent]))
    while written_classes != all_classes:
        for class_name, parents, class_content in classes:
            skip = False
            for parent in parents:
                if '.' not in parent and parent not in written_classes:
                    skip = True
            if class_name in written_classes:
                skip = True
            if skip:
                continue
            classes_text += class_content
            written_classes.add(class_name)
            for parent_class in parents:
                if '.' in parent_class:
                    imports.add(parent_class[:parent_class.index('.')])
    return classes_text, imports


def extract_class(element):
    """Extract information from a class"""
    class_name = element.attrib['name']
    docstring = get_docstring(element)
    parents = []
    parent = element.attrib.get('parent')
    if parent:
        parents.append(parent)
    implements = element.findall('{%s}implements' % XMLNS)
    for implement in implements:
        parents.append(implement.attrib['name'])
    class_content = ("\n\nclass %s(%s):\n    \"\"\"%s\"\"\"\n"
                     % (class_name, ", ".join(parents), docstring))
    class_content += extract_constructors(element)
    class_content += extract_methods(element)
    return class_name, parents, class_content


def extract_namespace(namespace):
    """Extract all information from a gir namespace"""
    namespace_content = ""
    classes = []
    for element in namespace:
        tag = QName(element)
        tag_name = tag.localname
        if tag_name in ('class', 'interface', 'record'):
            classes.append(extract_class(element))
        if tag_name in ('enumeration', 'bitfield'):
            namespace_content += insert_enum(element)
        if tag_name == 'function':
            namespace_content += insert_function(
                element.attrib['name'],
                get_parameters(element),
                get_returntype(element),
                0,
                get_docstring(element)
            )
        if tag_name == 'constant':
            constant_name = element.attrib['name']
            if constant_name[0].isdigit():
                constant_name = "_" + constant_name
            constant_value = element.attrib['value'] or 'None'
            constant_value = constant_value.replace("\\", "\\\\")
            namespace_content += "{} = r\"\"\"{}\"\"\"\n".format(constant_name,
                                                                 constant_value)
    classes_content, imports = build_classes(classes)
    namespace_content += classes_content
    imports_text = ""
    for _import in imports:
        imports_text += "from gi.repository import %s\n" % _import

    namespace_content = imports_text + namespace_content
    return namespace_content


def parse_gir(gir_path):
    """Extract everything from a gir file"""
    print("Parsing {}".format(gir_path))
    parser = XMLParser(encoding='utf-8', recover=True)
    with open(gir_path, 'rt', encoding='utf-8') as gir_file:
        content = gir_file.read()
    root = XML(content, parser)
    namespace = root.findall('{%s}namespace' % XMLNS)[0]
    namespace_content = extract_namespace(namespace)
    return namespace_content


def iter_girs():
    """Return a generator of all available gir files"""
    gir_files = []
    for gir_path in GIR_PATHS:
        gir_files.extend(glob.glob(gir_path))

    for gir_file in gir_files:
        # Don't know what to do with those, guess nobody uses PyGObject
        # for Gtk 2.0 anyway
        basename = os.path.basename(gir_file)
        if basename in ('Gtk-2.0.gir', 'Gdk-2.0.gir', 'GdkX11-2.0.gir'):
            continue

        try:
            module_name = basename[:basename.index('-')]

        except ValueError:
            # file name contains no dashes
            write_stderr("Warning: unrecognized file in gir directory: {}", gir_file)
            continue

        gir_info = (module_name, gir_file)
        yield gir_info


def generate_fakegir():
    """Main function"""
    fakegir_repo_dir = os.path.join(FAKEGIR_PATH, 'gi/repository')
    if not os.path.exists(fakegir_repo_dir):
        os.makedirs(fakegir_repo_dir)

    gi_init_path = os.path.join(FAKEGIR_PATH, 'gi/__init__.py')
    with open(gi_init_path, 'w') as gi_init_file:
        gi_init_file.write('')
    repo_init_path = os.path.join(FAKEGIR_PATH, 'gi/repository/__init__.py')
    with open(repo_init_path, 'w') as repo_init_file:
        repo_init_file.write('')

    for module_name, gir_path in iter_girs():
        fakegir_content = parse_gir(gir_path)
        fakegir_path = os.path.join(FAKEGIR_PATH, 'gi/repository',
                                    module_name + ".py")
        with open(fakegir_path, 'w') as fakegir_file:
            fakegir_file.write("# -*- coding: utf-8 -*-\n")
            fakegir_file.write(fakegir_content)


if __name__ == "__main__":
    generate_fakegir()
