#!/usr/bin/python3

import csv
import getopt
import itertools as itt
import multiprocessing as mp
import sys
import time

import config
import file_operations
import language_operations

csv.field_size_limit(100000000)


def usage():
    print("usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file")


def process_block(doc_id_map, mini_block):
    for row in mini_block:
        doc_id = int(row["document_id"])
        content = row["title"] + row["court"] + row["content"]

        print('Processing document', doc_id)
        
        doc_id_map[doc_id] = language_operations.process_document(doc_id, content)


if __name__ == '__main__':
    # ============================================================================
    in_data = out_dict = out_postings = None
    # ===================================================
    # DEBUG
    # in_data = '../dataset/dataset.csv'
    # out_dict = 'dictionary.txt'
    # out_postings = 'postings.txt'
    # END DEBUG
    # ===================================================

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-i':
            in_data = a
        elif o == '-d':
            out_dict = a
        elif o == '-p':
            out_postings = a
        else:
            assert False, "unhandled option"

    if in_data is None or out_postings is None or out_dict is None:
        usage()
        sys.exit(2)

    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    # This is an empty method
    # Pls implement your code in below

    # ===========================================================================

    indexing_start_time = time.perf_counter()
    file_operations.init_indexing(out_dict, out_postings)

    block_map = {}       # Contains term - block_id mappings for merging
    lengths_map = {}     # Contains doc_id - doc_length mappings

    block_id = 0         # ID of current block

    csvfile = open(in_data, 'r', encoding='utf-8')
    csvdata = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    # Columns: 'document_id', 'title', 'content', 'date_posted', 'court'

    # Split iterator into blocks
    split_every = (lambda n, it: itt.takewhile(bool, (list(itt.islice(it, n)) for _ in itt.repeat(None))))
    blocks_iter = split_every(config.SPIMI_BLOCK_SIZE, csvdata)

    for block_iter in blocks_iter:
        block_iter_len = len(block_iter)
        
        # Each worker will take one of the mini blocks to process
        mini_blocks = [ block_iter[
                i * block_iter_len // config.NUM_WORKER_PROCESSES : (i + 1) * block_iter_len // config.NUM_WORKER_PROCESSES] 
                for i in range(config.NUM_WORKER_PROCESSES) ]
        
        with mp.Manager() as manager:
            doc_id_map = manager.dict() # The initial dictionary housing documents in its condensed form
            
            jobs = []
            for i in range(config.NUM_WORKER_PROCESSES):
                p = mp.Process(target=process_block, args=(doc_id_map, mini_blocks[i]))
                jobs.append(p)

            for p in jobs: p.start()
            for p in jobs: p.join()
            
            # Write block to file
            block_id += 1
            file_operations.write_block(block_id, doc_id_map, block_map, lengths_map)

    csvfile.close()

    # MERGE THE BLOCKS
    file_operations.merge_blocks(block_map, lengths_map)

    # REMOVE TMP FOLDER
    file_operations.flush_temp_dirs()

    print('===================================')
    indexing_end_time = time.perf_counter()
    indexing_time_elapsed = indexing_end_time - indexing_start_time
    with open('indexing_log.txt', 'w') as f: f.write(str(indexing_time_elapsed) + '\n')
    print('Time Elapsed: ' + str(indexing_time_elapsed) + 's')
