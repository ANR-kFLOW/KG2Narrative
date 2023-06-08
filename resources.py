import uuid
from rdflib import URIRef
from urllib.parse import urlparse


def node_creation(path, entity_mention, base_add=''):
    """
    :param path: A path that has to be added to the generated URI e.g. /sentence/
    :param entity_mention: The entity for which the generation is done
    :param base_add: Allows for more information to be added to the generated URI
    :return:
    """
    base = f"http://kflow.eurecom.fr{base_add}"
    uri = base + '/' + str(uuid.uuid5(uuid.NAMESPACE_DNS, path + entity_mention))
    return URIRef(uri)


def uri_validator(x):
    """
    :param x: The URI/ URL to check
    :return:
    """
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


def mapping_dict(words):
    """
    :param words: The words for which an encoding has to be made
    :return: A dictionary that performs the translation
    """

    mapping_dict = dict([(y, x + 1) for x, y in enumerate(sorted(set(words)))])

    return mapping_dict