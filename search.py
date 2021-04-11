#!/usr/bin/python3

import getopt
import sys
import time

import boolean_retrieval
import file_operations
import list_operations
import language_operations
import vsm


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q query-file -o output-file-of-results")


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below

    start = time.process_time()

    file_operations.init_search(dict_file, postings_file, queries_file, results_file)

    # Load files
    dictionary = file_operations.load_dictionary()
    N, doc_lengths = file_operations.load_doc_lengths()
    query, valid_docs = file_operations.read_query_file()

    # Parse the query into a boolean query version and a free search version with query expansion
    # Then process boolean query to retrieve list of documents to perform VSM
    # Then use this list to compute VSM scores
    boolean_query, vsm_query = language_operations.parse_query(query, dictionary)

    # Prepare boolean query for evaluation
    rpn = boolean_retrival.create_rpn(boolean_query)

    # Evaluate boolean query
    boolean_result = boolean_retrival.eval_rpn(rpn, dictionary, N)
    boolean_result.sort()

    valid_docs = list_operations.union(valid_docs, boolean_result)

    print('Number of valid documents returned:', len(valid_docs))
    # ======================================================================

    # Create the query document
    query_wt, query_length_sqr = vsm.create_query_vector(vsm_query, valid_docs, dictionary, N)
    document_scores = []  # Document scores

    print('Calculating scores...')
    print('===================================')

    # Now calculate vector score between query and document
    for doc_id in valid_docs:
        print('Calculating score for document', doc_id)
        doc_length_sqr = doc_lengths[doc_id]  # returns -> doc_length_sqr

        term_scores = {term: vsm.get_term_score(dictionary, doc_id, term, doc_length_sqr, query_wt, query_length_sqr)
                       for term in vsm_query}
        # returns -> {<term> <score>}

        # Accumulates the scores on a term basis - see general notes in README.txt 
        this_score = (sum(term_scores[term] for term in term_scores)) ** 2 * float(doc_length_sqr) * float(
            query_length_sqr)
        document_scores.append((int(doc_id), this_score))

    sorted_scores = sorted(document_scores, key=lambda x: (-x[1], x[0]))

    print('===================================')
    print('Printing results to', results_file)
    file_operations.write_results(sorted_scores)

    print('===================================')
    time_elapsed = str(time.process_time() - start)
    print('Retrieved: ' + str(len(valid_docs)) + ' documents')
    print('Time Elapsed: ' + str(time_elapsed) + 's')


# ============================================================================


file_dictionary = file_postings = file_query = file_output = None

# ===================================================
# DEBUG
file_dictionary = 'dictionary.txt'
file_postings = 'postings.txt'
file_query = 'queries/q2.txt'
file_output = 'output-test.txt'
# END DEBUG
# ===================================================

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        file_dictionary = a
    elif o == '-p':
        file_postings = a
    elif o == '-q':
        file_query = a
    elif o == '-o':
        file_output = a
    else:
        assert False, "unhandled option"

if file_dictionary is None or file_postings is None or file_query is None or file_output is None:
    usage()
    sys.exit(2)

run_search(file_dictionary, file_postings, file_query, file_output)
