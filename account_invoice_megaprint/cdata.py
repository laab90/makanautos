import xml.etree.ElementTree as ET

ET._original_serialize_xml = ET._serialize_xml


def serialize_xml_with_CDATA(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == 'CDATA':
        write("<![CDATA[{}]]>".format(elem.text))
        return
    return ET._original_serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs)


ET._serialize_xml = ET._serialize['xml'] = serialize_xml_with_CDATA


def CDATA(text):
   element =  ET.Element("CDATA")
   element.text = text
   return element
