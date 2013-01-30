import os
from lxml import etree

GIR_PATH = '/usr/share/gir-1.0/'
FAKEGIR_PATH = os.path.join(os.path.expanduser('~'), '.cache/fakegir')


def extract_methods(class_tag):
    methods_content = ''
    for element in class_tag:
        tag = etree.QName(element)
        if tag.localname == 'method':
            methods_content += ("    def %s(self):\n        pass\n"
                                % element.attrib['name'])
    return methods_content


def extract_namespace(namespace):
    namespace_content = ""
    for element in namespace:
        tag = etree.QName(element)
        if tag.localname == 'class':
            class_content = "\nclass %s:\n    pass\n" % element.attrib['name']
            class_content += extract_methods(element)
            namespace_content += class_content
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
        if gir_file in ('Gtk-2.0.gir', 'Gdk-2.0.gir', 'GdkX11-2.0.gir'):
            continue
        module_name = gir_file[:gir_file.index('-')]
        gir_info = (module_name, gir_file)
        yield gir_info


if __name__ == "__main__":
    fakegir_repo_dir = os.path.join(FAKEGIR_PATH, 'gi/repository')
    if not os.path.exists(fakegir_repo_dir):
        os.makedirs(fakegir_repo_dir)
    for module_name, gir_file in iter_girs():
        gir_path = os.path.join(GIR_PATH, gir_file)
        fakegir_content = parse_gir(gir_path)
        fakegir_path = os.path.join(FAKEGIR_PATH, 'gi/repository',
                                    module_name + ".py")
        with open(fakegir_path, 'w') as fakegir_file:
            fakegir_file.write(fakegir_content)
