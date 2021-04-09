import math

import file_operations

def compute_log_term_freq(tf):
    return 1 + math.log(tf, 10) if tf != 0 else 0


def compute_idf(N, df):
    return math.log(N, 10) - math.log(df, 10) if N != 0 and df != 0 else 0 # Equivalent to log(N/df)


def compute_length_squared(wt):
    return sum(weight**2 for weight in wt)


def compute_term_score(doc_wt, doc_length_sqr, query_wt, query_length_sqr):
    return ((doc_wt * query_wt) / (doc_length_sqr * query_length_sqr)) if (doc_length_sqr != 0 and query_length_sqr != 0) else 0


def create_query_vector(query_array, valid_docs, dictionary, N):
    query_tf_dict = {}
    query_idf_dict = {}

    for term in query_array:
        if term in query_tf_dict:
            query_tf_dict[term] += 1
        else:
            query_tf_dict[term] = 1
        
        if term in dictionary and term not in query_idf_dict:
                query_idf_dict[term] = dictionary[term][2] # df
        else:
            query_idf_dict[term] = 0

    query_tfwt = {term: compute_log_term_freq(tf) for term, tf in query_tf_dict.items()}
    query_idf = {term: compute_idf(N, df) for term, df in query_idf_dict.items()}
    query_wt = {term: query_tfwt[term] * query_idf[term] for term in query_array}
    query_length = compute_length_squared(query_wt.values())

    return (query_wt, query_length)


def get_term_score(dictionary, doc_id, term, doc_length_sqr, query_wt, query_length_sqr):
    if term not in dictionary: return 0

    term_posting = file_operations.retrieve_posting_list(term, dictionary)
    if doc_id in term_posting:
        doc_tf = len(term_posting[doc_id])
        doc_wt = compute_log_term_freq(doc_tf)

        # Calculates the interim score of a term - see general notes in README.txt 
        return compute_term_score(float(doc_wt), float(doc_length_sqr), float(query_wt[term]), float(query_length_sqr))

    else: return 0
