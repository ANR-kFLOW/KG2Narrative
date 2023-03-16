import uuid
from rdflib import URIRef


def node_creation(path, entity_mention, base_add=''):
    base = f"http://kflow.eurecom.fr{base_add}"
    uri = base + '/' + str(uuid.uuid5(uuid.NAMESPACE_DNS, path + entity_mention))
    return URIRef(uri)