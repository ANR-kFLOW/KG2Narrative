from collections import defaultdict
import pandas as pd
from rdflib import Graph, URIRef
from owlrl import DeductiveClosure
from rdflib.term import Variable
from owlrl import OWLRL_Semantics #This is needed to allow owl reasoning over the sameAs links
import random
from resources import convert_selected_triples_to_jointgt
import os
from resources import combine_jointgt_events

namespaces = {"faro": "https://purl.org/faro/",
              "sem": "http://semanticweb.cs.vu.nl/2009/11/sem/",
              "rnews": "http://iptc.org/std/rNews/2011-10-07#",
              "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#",
              "owl": "http://www.w3.org/2002/07/owl#",
              "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
              "schema": "http://schema.org/"}


def bulk_generate(graph_path, base_output_path, gen_four_w = True, events = None):
    """
    This can either extract all events with 4W, or a list with events can be given.
    It will then perfrom selction of nodes, and generates the JointGT format.
    :param graph_path: The path to the graph
    :param base_output_path: The folder where all the files are saved. Please select an empty folder
    :param gen_four_w: If the graph needs to be queried, to find all 4W events
    :param events: If a list of events of interest is already present, this can be given too
    :return:
    """

    graph = Graph()
    graph.parse(graph_path)
    print("Applying reasoning over graph...")
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    processed_files = []

    if gen_four_w == True and events == None:
        four_w_query = """
        select distinct ?event where { 
            ?event a sem:Event;
                sem:hasActor ?actor;
                sem:hasPlace ?place;
                rdf:value ?name
            OPTIONAL{?event sem:hasTime ?time}.
            OPTIONAL{?event sem:hasBeginTimeStamp ?begintime}.
            OPTIONAL{?event sem:hasEndTimeStamp ?endtime}.
            }"""


        qres = graph.query(four_w_query, initNs=namespaces)

        events = [row[0] for row in qres]

    print(f"{len(events)} events will be processed")

    for event in events:
        query = """
        SELECT ?event_name ?Time ?place ?actor ?beginTime ?endTime ?timeStamp where {
        	?event a  sem:Event;
        	    rdf:value ?event_name
            OPTIONAL{?event sem:hasTime ?time_uri.
                    ?time_uri rdf:value ?Time}.
            OPTIONAL{?event sem:hasPlace ?place_uri.
                    ?place_uri rdf:value ?place}.
            OPTIONAL{?event sem:hasActor ?actor_uri.
                    ?actor_uri rdf:value ?actor}.
            OPTIONAL{?event sem:hasBeginTimeStamp ?beginTime_uri.
                    ?beginTime_uri rdf:value ?beginTime}.
            OPTIONAL{?event sem:hasEndTimeStamp ?endTime_uri.
                    ?endTime_uri rdf:value ?endTime}.
            OPTIONAL{?event sem:hasTimeStamp ?time_uri.
                    ?time_uri rdf:value ?time}.
        }"""

        event = URIRef(event)

        qres = graph.query(query, initNs=namespaces, initBindings={"event": event})
        four_W = {}

        for row in qres.bindings:
            for key in row.keys():
                if key not in four_W.keys():
                    four_W[key] = [row[key]]
                else:
                    if row[key] not in four_W[key]:
                        four_W[key].append(row[key])

        query = """
        SELECT (COUNT(?i) as ?num_input) WHERE {
            ?i ?p2 ?uri
        } GROUP BY ?uri
        """

        def def_value():
            return 0

        four_W_scores = defaultdict(def_value)
        for values in four_W.values():
            for value in values:
                qres = graph.query(query, initNs=namespaces, initBindings={"uri": value})
                four_W_scores[value] = int(qres.bindings[0]['num_input'])

        selected_nodes = {"mentions": []}

        if ('beginTime' in str(four_W.keys()) and 'endTime' in str(four_W.keys())):  # Favour the more descriptive dates
            if (four_W[Variable('beginTime')] != four_W[
                Variable('endTime')]):  # If they are the same, it doesn't add any information
                try:
                    del four_W[Variable('Time')]
                except:
                    print("Key already removed")

            elif 'Time' in str(four_W.keys()):
                del four_W[Variable('beginTime')]
                del four_W[Variable('endTime')]

        for key in four_W:
            most_relevant_node = None
            for node in four_W[key]:
                if four_W_scores[node] > four_W_scores[most_relevant_node]:
                    most_relevant_node = node
            selected_nodes[str(key)] = str(most_relevant_node) if not 'Time' in str(key) else \
            str(most_relevant_node).split('T')[0]  # For now only take the date into account

        query = """
        PREFIX faro: <https://purl.org/faro/>
        PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
        PREFIX rnews: <http://iptc.org/std/rNews/2011-10-07#>
        PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix schema: <http://schema.org/>
        select distinct ?mention where {
        	?event a sem:Event;
                 schema:subjectOf ?article.
            ?article nif:sentence ?sentence.
            ?sentence nif:word ?mention.
            ?mention owl:sameAs ?o .

        }"""

        qres = graph.query(query, initNs=namespaces, initBindings={"event": event})
        mentions = [mention[0] for mention in qres]  # Save all mentions of this event

        # Now, find the biggest cluster
        query = """
        SELECT ?nodes where {
        	?mention a faro:Relata;
        	    owl:sameAs+ ?nodes
        }
        """
        clusters = {}  # the key will be one of the mentions in the set
        for mention in mentions:
            mention = URIRef(mention)
            qres = graph.query(query, initNs=namespaces, initBindings={"mention": mention})
            mention_cluster = set()
            for result in qres:
                mention_cluster.add(result[0])
            if not any(key in mention_cluster for key in clusters.keys()) and len(
                    mention_cluster) != 1:  # Only keep unique clusters, keep as key one of the elements in the cluster
                clusters[mention] = mention_cluster
        clusters = dict(sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True))

        # Find the text values for the clusters
        SELECT_MAX_MENTIONS = 3  # Select only the top x mentions

        subject_query = """
        SELECT ?subject_value ?predicate ?object_value where {
        	?mention a faro:Relata;
        	    rdf:value ?subject_value;
        	    ?predicate ?object.
        	?object rdf:value ?object_value
        }"""

        object_query = """
        SELECT ?subject_value ?predicate ?object_value where {
        	?mention a faro:Relata;
        	    rdf:value ?object_value.
        	?subject ?predicate ?mention;
        	    rdf:value ?subject_value
        }"""
        for i, cluster in enumerate(clusters.values()):
            mention = random.choice(list(cluster))  # Only pick one mention per cluster
            if 'subject' in str(mention):
                qres = graph.query(subject_query, initNs=namespaces, initBindings={"mention": mention})
            else:
                qres = graph.query(object_query, initNs=namespaces, initBindings={"mention": mention})

            for instance in qres.bindings:
                if 'faro' in str(instance['predicate']):
                    selected_nodes['mentions'].append(
                        [str(instance['subject_value']), instance['predicate'].split('/')[-1],
                         str(instance['object_value'])])
                    break
            if i + 1 == SELECT_MAX_MENTIONS:
                break


        output_path = os.path.join(base_output_path, selected_nodes['event_name'].replace(" ", "_"))
        convert_selected_triples_to_jointgt(selected_nodes, output_path + '.json')
        processed_files.append(output_path + '.json')

    filepaths = [os.path.join(base_output_path, file) for file in os.listdir(base_output_path)]
    combine_jointgt_events(filepaths, output_file= os.path.join(base_output_path, "event_combined.json"))
    print(f"Processed {len(filepaths)} events")
    print(f"Saved at: {os.path.join(base_output_path, 'event_combined.json')}")