import re

from nltk.corpus import wordnet
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

import vsm

stemmer = PorterStemmer()
def process_document(doc_id, content, term_map, lengths_map):
    # Opens a file, processes the file and returns a term mapping and document length mapping:

    doc_terms = {}
    # K: term
    # V: (tf, [pos_idx])
    
    stripped_content = re.sub('[^a-zA-Z]',   # Search for all non-letters
                              ' ',           # Replace all non-letters with space
                              str(content))
                           
    sentences = sent_tokenize(stripped_content)

    position_idx = 1
    for sentence in sentences:
        tokens = word_tokenize(sentence)
        for token in tokens:
            term = stemmer.stem(token.lower())
            if term in doc_terms:
                doc_terms[term][0] += 1
                doc_terms[term][1].append(position_idx)
            else:
                doc_terms[term] = [1, [position_idx]]
                
                # term_map:
                # K: term
                # V: Element 0: df
                #    Element 1:
                #        [  Element 0: doc_id
                #           Element 1: (tf, [pos_idx]) ]
                if term in term_map:
                    term_map[term][0] += 1
                    term_map[term][1].append((doc_id, doc_terms[term]))
                else:
                    term_map[term] = [1, [(doc_id, doc_terms[term])]]
            
            position_idx += 1

    lengths_map[doc_id] = vsm.compute_length_squared([vsm.compute_log_term_freq(val[0]) for val in doc_terms.values()])



# Assume that the given input string is a boolean query.
# Insert OR operators between two words if it is not part of a phrasal query,
# Otherwise insert AND operator.
# Phrases will be returned as a list to be processed first in the
# boolean evaluation later.
# Then create a free search version for VSM.

def parse_boolean_query(string):
    line = string.split() # The input line as a list

    boolean_query = []
    ptr = 0
    while ptr < len(line):
        if line[ptr][0] == '\"':
            phrase = ''
            if line[ptr][-1] == '\"':
                # If phrase only consists of one word, remove quotes
                boolean_query.append(stemmer.stem(line[ptr][1:-1]))
            else:
                phrase = stemmer.stem(line[ptr][1:])
                ptr += 1
                # Append all terms in the phrase to a separate list until a matching '"' is found,
                # then treat this list as a single token in the boolean query
                while ptr < len(line) and line[ptr][-1] != '\"':
                    phrase += (' AND ' + stemmer.stem(line[ptr]))
                    ptr += 1
                phrase += (' AND ' + stemmer.stem(line[ptr][:-1]))
                if boolean_query == [] or boolean_query[-1] == 'AND':
                    boolean_query.append(phrase.split())
                else:
                    boolean_query.append('OR')
                    boolean_query.append(phrase.split())
        elif line[ptr] == 'AND':
            boolean_query.append(line[ptr])
        else:
            if boolean_query == [] or boolean_query[-1] == 'AND':
                boolean_query.append(stemmer.stem(line[ptr]))
            else:
                boolean_query.append('OR')
                boolean_query.append(stemmer.stem(line[ptr]))
        ptr += 1

    return boolean_query


def parse_free_query(string):
    vsm_query = ' '.join(string.replace('AND', '').replace('\"', '').split())
    return [stemmer.stem(term) for term in vsm_query.split()]


# # UNCOMMENT THE FOLLOWING IF DOING THESAURUS-BASED QUERY EXPANSION
# def query_expand(boolean_query, vsm_query, dictionary):
#     boolean_query_expanded = []

#     for term in boolean_query:
#         if isinstance(term, list) or term == 'OR' or term == 'AND':
#             boolean_query_expanded.append(term)
#             continue
#         new_term = [term]

#         # Get synonyms of term
#         term_syns = {stemmer.stem(l.name()) for syn in wordnet.synsets(term) for l in syn.lemmas()}

#         # Add synonyms to new_term: append 'OR', append synonym
#         for syn in term_syns:
#             if syn in dictionary:
#                 new_term.append('OR')
#                 new_term.append(syn)
#                 vsm_query.append(syn)
        
#         boolean_query_expanded.append('(')
#         boolean_query_expanded += new_term
#         boolean_query_expanded.append(')')
    
#     return boolean_query_expanded, vsm_query


def parse_query(string, dictionary):
    print('Before query expansion:')
    boolean_query = parse_boolean_query(string)
    print('boolean_query:', boolean_query)

    vsm_query = parse_free_query(string)
    print('vsm_query:', vsm_query)

    # UNCOMMENT THE FOLLOWING IF DOING THESAURUS-BASED QUERY EXPANSION
    # boolean_query, vsm_query = query_expand(boolean_query, vsm_query, dictionary)
    # print('After query expansion:')
    # print('boolean_query:', boolean_query)
    # print('vsm_query:', vsm_query)

    return(boolean_query, vsm_query)

