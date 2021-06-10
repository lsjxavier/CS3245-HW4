import re

from nltk.corpus import wordnet
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

import vsm

stemmer = PorterStemmer()

def process_document(doc_id, content):
    # Opens a file, processes the file and returns a tuple:
    # Element 0: dict -> K: term
    #                    V: (tf, [pos_idx])
    # Element 1: doc_length_squared
    doc_terms = [{}, 0]
    stripped_content = re.sub('[^a-zA-Z]',   # Search for all non-letters
                              ' ',           # Replace all non-letters with space
                              str(content))
                           
    sentences = sent_tokenize(stripped_content)

    position_idx = 1
    for sentence in sentences:
        tokens = word_tokenize(sentence)
        for token in tokens:
            term = stemmer.stem(token.lower())
            if term in doc_terms[0]:
                doc_terms[0][term][0] += 1
                doc_terms[0][term][1].append(position_idx)
            else:
                doc_terms[0][term] = [1, [position_idx]]

            position_idx += 1
    
    doc_terms[1] = vsm.compute_length_squared([vsm.compute_log_term_freq(val[0]) for val in doc_terms[0].values()])
    return doc_terms

def get_term_postings(doc_id_map):
    # Convert a doc_id-orientated array of dictionaries to a term-orientated dictionary
    # doc_id_map:
    #     K: doc_id
    #     V: doc_id_tuple (see below)

    term_map = {}
    # K: term
    # V: Element 0: df
    #    Element 1:
    #        [  Element 0: doc_id
    #           Element 1: (tf, [pos_idx]) ]
    
    for doc_id in sorted(doc_id_map): # doc_id_map is now unsorted due to parallelization
        doc_id_tuple = doc_id_map[doc_id]
        # doc_id_tuple:
        #     Element 0: dict -> K: term 
        #                        V: (tf, [pos_idx])
        #     Element 1: doc_length_squared

        for term in doc_id_tuple[0]:
            if term in term_map:
                term_map[term][0] += 1
                term_map[term][1].append((doc_id, doc_id_tuple[0][term]))
            else:
                term_map[term] = [1, [(doc_id, doc_id_tuple[0][term])]]
    
    return term_map

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

def calculate_doc_score(doc_id, doc_lengths, dictionary, query_wt, query_length_sqr, vsm_query):
    print('Calculating score for document', doc_id)
    doc_length_sqr = doc_lengths[doc_id]  # returns -> doc_length_sqr

    term_scores = {term: vsm.get_term_score(dictionary, doc_id, term, doc_length_sqr, query_wt, query_length_sqr)
                    for term in vsm_query}
    # returns -> {<term> <score>}

    # Accumulates the squared lnc-ltc score on a term basis - see general notes in README.txt 
    this_score = (sum(term_scores[term] for term in term_scores)) ** 2 * float(doc_length_sqr) * float(query_length_sqr)

    return (int(doc_id), this_score)
