"""Build a fake python package from the information found in gir files"""
import os
import sys
import keyword
from lxml import etree

GIR_PATH = '/usr/share/gir-1.0/'
FAKEGIR_PATH = os.path.join(os.path.expanduser('~'), '.cache/fakegir')
XMLNS = "http://www.gtk.org/introspection/core/1.0"


def get_docstring(callable_tag):
    """Return docstring text for a callable"""
    for element in callable_tag:
        tag = etree.QName(element)
        if tag.localname == 'doc':
            return element.text.replace("\\x", 'x').encode('utf-8') + b"\n"
    return ''


def get_parameter_type(element):
    """Returns the type of a parameter"""
    parm_type = ""
    for elem_property in element:
        tag = etree.QName(elem_property)
        if tag.localname == "type":
            parm_type = elem_property.attrib['name']
            break

    return parm_type


def get_parameter_doc(element):
    """Returns the doc of a parameter"""
    parm_doc = ""
    for elem_property in element:
        tag = etree.QName(elem_property)
        if tag.localname == "doc":
            parm_doc = element.text.replace("\\x", 'x').encode('utf-8').replace("\n", " ").strip()
            break

    return parm_doc


def get_parameters(element):
    """Return the parameters of a callable"""
    params = []
    for elem_property in element:
        tag = etree.QName(elem_property)
        if tag.localname == 'parameters':
            for param in elem_property:
                try:
                    subtag = etree.QName(param)
                    if subtag.localname == "instance-parameter":
                        param_name = 'self'
                    else:
                        param_name = param.attrib['name']

                    parm_type = get_parameter_type(param)
                    parm_doc = get_docstring(param).replace("\n", " ").strip()

                    if keyword.iskeyword(param_name):
                        param_name = "_" + param_name

                    if not param_name in params:
                        params.append((param_name, parm_doc, parm_type))
                except KeyError:
                    pass
    return params


def insert_function(name, args, depth, docstring=''):
    """Returns a function as a string"""
    if keyword.iskeyword(name):
        name = "_" + name
    arglist = ", ".join([arg[0] for arg in args])

    epydoc_doc_strs = ["@param %s: %s" % (pname, pdoc)
                       if (len(pdoc) > 0 and pname != "self") else ""
                       for (pname, pdoc, ptype) in args]

    epydoc_type_strs = ["@type %s: %s" % (pname, ptype)
                        if (len(ptype) > 0 and pname != "self") else ""
                        for (pname, pdoc, ptype) in args]

    def do_indent(lines):
        return ['    '*(depth+1) + l for l in lines]

    from itertools import chain
    full_docstr = "\n".join(
                  do_indent(chain(docstring.split("\n"),
                                  filter(lambda s: len(s) > 0, epydoc_doc_strs),
                                  filter(lambda s: len(s) > 0, epydoc_type_strs),
                                  [""])))

    return "%sdef %s(%s):\n%s\"\"\"\n%s\"\"\"\n" % ('    ' * depth,
                                                    name,
                                                    arglist,
                                                    '    ' * (depth + 1),
                                                    full_docstr)


def insert_enum(element):
    """returns an enum (class with attributes only) as text"""
    enum_name = element.attrib['name']
    docstring = get_docstring(element)
    enum_content = "class %s:\n    \"\"\"%s\"\"\"\n" % (enum_name, docstring)
    members = element.findall("{%s}member" % XMLNS)
    for member in members:
        enum_name = member.attrib['name']
        if enum_name[0].isdigit():
            enum_name = '_' + enum_name
        enum_value = member.attrib['value']
        enum_value = enum_value.replace('\\', '\\\\')
        enum_content += "    %s = '%s'\n" % (enum_name.upper(), enum_value)
    return enum_content


def extract_methods(class_tag):
    """return methods from a class element"""
    methods_content = ''
    for element in class_tag:
        tag = etree.QName(element)
        if tag.localname == 'method':
            method_name = element.attrib['name']
            docstring = get_docstring(element)
            params = get_parameters(element)
            methods_content += insert_function(method_name, params, 1,
                                               docstring)
    return methods_content


def build_classes(classes):
    """order classes with correct dependency order also return external
    imports"""
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


def extract_namespace(namespace):
    """extract all information from a gir namespace"""
    namespace_content = ""
    classes = []
    for element in namespace:
        tag = etree.QName(element)
        tag_name = tag.localname
        if tag_name in ('class', 'interface'):
            class_name = element.attrib['name']
            docstring = get_docstring(element)
            parents = []
            parent = element.attrib.get('parent')
            if parent:
                parents.append(parent)
            implements = element.findall('{%s}implements' % XMLNS)
            for implement in implements:
                parents.append(implement.attrib['name'])
            class_content = ("\nclass %s(%s):\n    \"\"\"%s\"\"\"\n"
                             % (class_name, ", ".join(parents), docstring))
            class_content += extract_methods(element)
            classes.append((class_name, parents, class_content))
        if (tag_name == 'enumeration') or (tag_name == "bitfield"):
            namespace_content += insert_enum(element)
        if tag_name == 'function':
            function_name = element.attrib['name']
            docstring = get_docstring(element)
            params = get_parameters(element)
            namespace_content += insert_function(function_name, params, 0,
                                                 docstring)
        if tag_name == 'constant':
            constant_name = element.attrib['name']
            constant_value = element.attrib['value'] or 'none'
            constant_value = constant_value.replace("\\", "\\\\")
            namespace_content += ("%s = r\"\"\"%s\"\"\"\n"
                                  % (constant_name, constant_value))
    classes_content, imports = build_classes(classes)
    namespace_content += classes_content
    imports_text = ""
    for _import in imports:
        imports_text += "import %s\n" % _import

    namespace_content = imports_text + namespace_content
    return namespace_content


def parse_gir(gir_path):
    """Extract everything from a gir file"""
    parser = etree.XMLParser(encoding='utf-8', recover=True)
    content = open(gir_path).read()
    root = etree.XML(content, parser)
    namespace = root.findall('{%s}namespace' % XMLNS)[0]
    namespace_content = extract_namespace(namespace)
    return namespace_content


def iter_girs():
    """Return a generator of all available gir files"""
    for gir_file in os.listdir(GIR_PATH):
        # Don't know what to do with those, guess nobody uses PyGObject
        # for Gtk 2.0 anyway
        if gir_file in ('Gtk-2.0.gir', 'Gdk-2.0.gir', 'GdkX11-2.0.gir'):
            continue
        module_name = gir_file[:gir_file.index('-')]
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

    for module_name, gir_file in iter_girs():
        gir_path = os.path.join(GIR_PATH, gir_file)
        fakegir_content = parse_gir(gir_path)
        fakegir_path = os.path.join(FAKEGIR_PATH, 'gi/repository',
                                    module_name + ".py")
        with open(fakegir_path, 'w') as fakegir_file:
            fakegir_file.write("# -*- coding: utf-8 -*-\n")
            fakegir_file.write(fakegir_content)

if __name__ == "__main__":
    generate_fakegir()
