import uuid
from rdflib import URIRef
from urllib.parse import urlparse
import re


def node_creation(path, entity_mention, base_add=''):
    """
    This function generates a URI for an entity
    :param path: A path that has to be added to the generated URI e.g. /sentence/
    :param entity_mention: The entity for which the generation is done
    :param base_add: Allows for more information to be added to the generated URI
    :return:
    """
    base = f"http://kflow.eurecom.fr{base_add}"
    uri = base + '/' + str(uuid.uuid5(uuid.NAMESPACE_DNS, path + entity_mention))
    return URIRef(uri)

def clean_text(text):
    '''
    This is used to remove the html codes from the text
    :param text: The text to clean
    :return: Cleaned text
    '''

    # Strip the last part of the text
    index_of_last_occurence = text.rfind('</p><p>')
    if index_of_last_occurence != -1:
        text = text[:index_of_last_occurence]

    text = re.sub(r"<.*?>", " ", text) # Strip all the special characters in the text

    text = text.strip() #Remove the whitespace at the beginning, due to deletion

    return text


def uri_validator(x):
    """
    This function checks if a string is a URI/URI
    :param x: The URI/ URL to check
    :return:
    """
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


class MappingDict:

    def __init__(self, encoding_dict = {}):
        """
        This function generates a dictionary used to lookup the unique ID's for words
        :param encoding_dict: A dictionary which already contains a mapping
        """
        self.encoding_dict = encoding_dict
        self.max_key = self.get_max_key()

    def get_max_key(self):
        if len(self.encoding_dict) != 0:
            values = [int(value[1:]) for value in self.encoding_dict.values()]
            return max(values)
        else:
            return 0

    def increment_max_key(self):
        self.max_key +=1

    def add_words(self, words):

        for word in words:
            if word not in self.encoding_dict.keys():
                self.encoding_dict[word] = f"W{str(self.max_key +1)}"
                self.increment_max_key()


def gen_mapping_dict(*args):
    import json
    total_instances = 0
    """
    This function generates a dictionary containing all the unique keys for the objects in the JointGT files
    :param args: paths to the jointGT files
    :return: the mapping dictionary
    """
    encoding_dict = {}
    filepaths = [*args]
    for dataset in filepaths:
        dataset = json.load(open(dataset))
        total_instances += len(dataset)

        for instance in dataset:

            for key, value in instance['kbs'].items():
                encoding_dict[value[0]] = key

    encoding_dict = MappingDict(encoding_dict)
    print(f"Processed {total_instances} instances")

    return encoding_dict, total_instances

