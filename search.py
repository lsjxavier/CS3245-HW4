#!/usr/bin/python3

import getopt
import multiprocessing as mp
import sys
import time

import boolean_retrieval
import config
import filenames
import file_operations
import language_operations
import list_operations
import vsm


def worker(boolean_document_scores, input_files, boolean_result, doc_lengths, dictionary, query_wt, query_length_sqr, vsm_query):
    # Reinitialize for this process
    file_operations.init_search(input_files[0], input_files[1], input_files[3], input_files[4])

    for doc_id in boolean_result:
        boolean_document_scores.append(language_operations.calculate_doc_score(doc_id, doc_lengths, dictionary, query_wt, query_length_sqr, vsm_query))

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q query-file -o output-file-of-results")


if __name__ == '__main__':
    # ===================================================
    dict_file = postings_file = queries_file = results_file = None
    # ===================================================
    # DEBUG
    # dict_file = 'dictionary.txt'
    # postings_file = 'postings.txt'
    # queries_file = '../queries/q2.txt'
    # results_file = 'output-test.txt'
    # END DEBUG
    # ===================================================

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-d':
            dict_file = a
        elif o == '-p':
            postings_file = a
        elif o == '-q':
            queries_file = a
        elif o == '-o':
            results_file = a
        else:
            assert False, "unhandled option"

    if dict_file is None or postings_file is None or queries_file is None or results_file is None:
        usage()
        sys.exit(2)

    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below

    # ===========================================================================

    start = time.perf_counter()

    file_operations.init_search(dict_file, postings_file, queries_file, results_file)

    # Load files
    dictionary = file_operations.load_dictionary()
    N, doc_lengths = file_operations.load_doc_lengths()
    query, relevant_docs = file_operations.read_query_file()

    # Parse the query into a boolean query version and a free search version with query expansion
    # Then process boolean query to retrieve list of documents to perform VSM
    # Then use this list to compute VSM scores
    boolean_query, vsm_query = language_operations.parse_query(query, dictionary)

    # Prepare boolean query for evaluation
    rpn = boolean_retrieval.create_rpn(boolean_query)

    # Evaluate boolean query
    boolean_result = boolean_retrieval.eval_rpn(rpn, dictionary, N, vsm_query)
    boolean_result.sort()
    
    # ======================================================================

    # Create the query document
    query_wt, query_length_sqr = vsm.create_query_vector(vsm_query, dictionary, N)
    boolean_document_scores = []  # Document scores
    relevant_document_scores = []

    print('Calculating scores...')
    print('===================================')

    # Compute boolean scores with multiprocessing
    boolean_result_len = len(boolean_result)
    boolean_result_split = [ boolean_result[
        i * boolean_result_len // config.NUM_WORKER_PROCESSES : (i + 1) * boolean_result_len // config.NUM_WORKER_PROCESSES]
        for i in range(config.NUM_WORKER_PROCESSES) ]

    input_files = [filenames.dict_file, filenames.postings_file, filenames.lengths_file, filenames.query_file, filenames.results_file]

    with mp.Manager() as manager:
        boolean_document_scores = manager.list()
        jobs = []
        for i in range(config.NUM_WORKER_PROCESSES):
            p = mp.Process(target=worker, args=(
                boolean_document_scores, input_files, boolean_result_split[i], doc_lengths, dictionary, query_wt, query_length_sqr, vsm_query))
            jobs.append(p)
        
        for p in jobs: p.start()
        for p in jobs: p.join()

        # End multiprocessing.
        # Now cleanup and sort scores

        for doc_id in relevant_docs:
            relevant_document_scores.append(
                language_operations.calculate_doc_score(doc_id, doc_lengths, dictionary, query_wt, query_length_sqr, vsm_query))

        boolean_document_sorted_scores = sorted(boolean_document_scores, key=lambda x: (-x[1], x[0]))
        document_scores = relevant_document_scores + boolean_document_sorted_scores

    # REMOVE TMP FOLDER
    file_operations.flush_temp_dirs()

    print('===================================')
    print('Printing results to', results_file)
    file_operations.write_results(document_scores)

    print('===================================')
    time_elapsed = str(time.perf_counter() - start)
    print('Retrieved: ' + str(len(document_scores)) + ' documents')
    print('Time Elapsed: ' + str(time_elapsed) + 's')
