#!/usr/bin/python3

import csv
import getopt
import sys
import time

import language_operations
import file_operations

csv.field_size_limit(100000000)


def usage():
    print("usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file")


def build_index(in_data, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    # This is an empty method
    # Pls implement your code in below

    indexing_start_time = time.process_time()
    file_operations.init_indexing(out_dict, out_postings)

    term_map = {}              # Contains postings list in python dict format
    block_map = {}             # Contains term - block_id mappings for merging
    lengths_map = {}           # Contains doc_id - doc_length mappings

    SPIMI_BLOCK_SIZE = 500     # Maximum number of documents to store in each block
    block_id = 1               # ID of current block
    doc_counter = 0            # Counter for block separation

    csvfile = open(in_data, 'r', encoding='utf-8')
    csvdata = csv.DictReader(csvfile, delimiter=',', quotechar='\"')
    # Columns: 'document_id', 'title', 'content', 'date_posted', 'court''

    for row in csvdata:
        doc_counter += 1

        doc_id = row["document_id"]
        content = row["content"]

        print('Processing document', doc_id)
        language_operations.process_document(doc_id, content, term_map, lengths_map)

        if doc_counter == SPIMI_BLOCK_SIZE:
            file_operations.write_block(block_id, term_map, block_map, lengths_map)
            block_id += 1
            doc_counter = 0
            term_map = {}

        # FOR DEBUGGING PURPOSES: RETURN A SMALL SUBSET OF THE COLLECTION
        # if block_id == 3: break

    csvfile.close()

    # WRITE THE LAST BLOCK
    file_operations.write_block(block_id, term_map, block_map, lengths_map)

    # MERGE THE BLOCKS
    print('Merging blocks...')
    file_operations.merge_blocks(block_map, lengths_map)

    # REMOVE TMP FOLDER
    file_operations.flush_temp_dirs()

    print('===================================')
    indexing_end_time = time.process_time()
    indexing_time_elapsed = indexing_end_time - indexing_start_time
    with open('indexing_log.txt', 'w') as f: f.write(str(indexing_time_elapsed) + '\n')
    print('Time Elapsed: ' + str(indexing_time_elapsed) + 's')


# ============================================================================


in_dataset = output_file_dictionary = output_file_postings = None

# ===================================================
# DEBUG
in_dataset = 'dataset/dataset.csv'
output_file_dictionary = 'dictionary.txt'
output_file_postings = 'postings.txt'
# END DEBUG
# ===================================================

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':
        in_dataset = a
    elif o == '-d':
        output_file_dictionary = a
    elif o == '-p':
        output_file_postings = a
    else:
        assert False, "unhandled option"

if in_dataset is None or output_file_postings is None or output_file_dictionary is None:
    usage()
    sys.exit(2)

build_index(in_dataset, output_file_dictionary, output_file_postings)
