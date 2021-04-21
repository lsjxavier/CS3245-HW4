import os

import vbcode as vb

import filenames
import language_operations


WORKING_DIR = os.getcwd()
FILE_EXT = '.txt'

TMP_DIR = os.path.join(WORKING_DIR, 'tmp')
if not os.path.exists(TMP_DIR): os.mkdir(TMP_DIR)

TMP_DICT_DIR = os.path.join(TMP_DIR, 'dict')
TMP_POST_DIR = os.path.join(TMP_DIR, 'post')
if not os.path.exists(TMP_DICT_DIR): os.mkdir(TMP_DICT_DIR)
if not os.path.exists(TMP_POST_DIR): os.mkdir(TMP_POST_DIR)


def init_indexing(out_dict, out_post):
    filenames.dict_file = out_dict
    filenames.postings_file = out_post
    filenames.lengths_file = 'lengths.txt'


def init_search(dict_file, postings_file, queries_file, results_file):
    filenames.dict_file = dict_file
    filenames.postings_file = postings_file
    filenames.lengths_file = 'lengths.txt'
    filenames.query_file = queries_file
    filenames.results_file = results_file


def load_dictionary():
    dictionary = {} # <term>: <seek ptr to posting> <bytes_to_read> <doc freq>
    with open(filenames.dict_file, 'r') as df:
        for li in df:
            line = li.strip().split()
            
            dictionary[line[0]] = [int(line[1]), int(line[2]), int(line[3])]
    return dictionary


def load_doc_lengths():
    lengths = {} # <doc id> <doc lengths squared>
    N = 0
    lf = open(filenames.lengths_file, 'r')
    for li in lf:
        line = li.strip().split()
        if len(line) == 1: N = int(line[0])
        else: lengths[int(line[0])] = float(line[1])

    lf.close()
    return (N, lengths)


def read_query_file():
    valid_docs = []
    qf = open(filenames.query_file, 'r')
    q = [(line.strip()) for line in qf]
    qf.close()

    query = q[0]
    if len(q) > 1: valid_docs = [int(doc_id) for doc_id in q[1:]]
    valid_docs.sort()
    return query, valid_docs


def retrieve_posting_list(term, dictionary):
    # dictionary[term] : [seek_ptr, bytes_to_read, df]
    # postings file e.g. : [246391, 1, 30, 1587517, 1, 33, 1587784, 1, 34, 1620199, 2, 22551, 23322, 2125001, 2, 20, 119, 2125230, 2, 12, 97]
    
    pf = open(filenames.postings_file, 'rb')

    postings = {}
    # A dictionary structure for the postings.
    # There will be df number of keys, with values as list with len tf, e.g.:
    # {
    #    246391: [30]
    #    1587517: [33]
    #    1587784: [34]
    #    1620199: [22551, 23322]
    #    ...
    # }

    if term in dictionary:
        posting_seek_ptr = dictionary[term][0]
        bytes_to_read = dictionary[term][1]
        
        pf.seek(posting_seek_ptr)
        postings_encoded = pf.read(bytes_to_read)
        postings_decoded = vb.decode(postings_encoded)

        ptr = 0
        while ptr < len(postings_decoded):
            doc_id = postings_decoded[ptr]
            ptr += 1
            tf = postings_decoded[ptr]
            ptr += 1
            postings[doc_id] = postings_decoded[ptr:ptr + tf]
            ptr += tf
    
    pf.close()

    return postings
    # K: doc_id
    # V: [pos_idx]


def write_results(sorted_scores):
    rf = open(filenames.results_file, 'w')
    rf.write(' '.join([str(doc_id) for doc_id, score in sorted_scores]))
    rf.close()


def write_block(block_id, doc_id_map, block_map, lengths_map):
    print('Writing block', block_id)
    term_map = language_operations.get_term_postings(doc_id_map) # The final dictionary containing term - doc_id mappings

    block_dict = os.path.join(TMP_DICT_DIR, str(block_id) + FILE_EXT)
    block_postings = os.path.join(TMP_POST_DIR, str(block_id) + FILE_EXT)

    # term_map:
    # K: term
    # V: Element 0: df
    #    Element 1:
    #        [  Element 0: doc_id
    #           Element 1: (tf, [pos_idx])  ]  # <= CHANGED

    # doc_id_map:
    #     K: doc_id
    #     V: doc_id_tuple:
    #         Element 0: dict -> K: term 
    #                            V: (tf, [pos_idx])  # <= CHANGED
    #         Element 1: doc_length_squared

    posting_seek_ptr = 0 # to be written to dict file
    dict_seek_ptr = 0 # to be written to block mapping

    bdf = open(block_dict, 'w')
    bpf = open(block_postings, 'wb')
    
    for term in term_map:
        df = term_map[term][0]

        postings = term
        for document in term_map[term][1]:
            doc_id = document[0]
            tf = document[1][0]
            position_indices = document[1][1]

            postings = postings + ' ' + str(doc_id) + ' ' + str(tf)

            for index in position_indices:
                postings = postings + (' ' + str(index))

        # Apply VB encoding to postings list, then write to file
        bpf.write(vb.encode([int(num) for num in postings.split()[1:]]))

        # ADD TO BLOCK MAP
        if term in block_map:
            block_map[term].append((block_id, dict_seek_ptr))
        else:
            block_map[term] = [(block_id, dict_seek_ptr)]

        posting_bytes_to_read = bpf.tell() - posting_seek_ptr
        bdf.write(term + ' ' + str(posting_seek_ptr) + ' ' + str(posting_bytes_to_read) + ' ' + str(df) + '\n')
        posting_seek_ptr = bpf.tell()

        dict_seek_ptr = bdf.tell()

    for doc_id in sorted(doc_id_map):
        lengths_map[doc_id] = doc_id_map[doc_id][1]

    bpf.close()
    bdf.close()


def merge_blocks(block_map, lengths_map):
    print('Merging blocks...')
    mdf = open(filenames.dict_file, 'w')
    mpf = open(filenames.postings_file, 'wb')
    mlf = open(filenames.lengths_file, 'w')
    mpf_seek_ptr = 0

    for term in block_map:
        master_term_df = 0
        master_posting = b''

        for block in block_map[term]:
            # e.g. -> block_map[term]: [(1, 0),(2, 400672),(3, 508304),(4, 272944),(5, 533311),(6, 646261),(7, 207529),(8, 79541),...]
            term_block_id = block[0]
            bdf_seek_ptr = int(block[1])

            block_dict = os.path.join(TMP_DICT_DIR, str(block[0]) + FILE_EXT)
            block_postings = os.path.join(TMP_POST_DIR, str(block[0]) + FILE_EXT)
            bdf = open(block_dict, 'r')
            bpf = open(block_postings, 'rb')

            bdf.seek(bdf_seek_ptr) # seek to position of term in block file
            term_dict = bdf.readline().split() # e.g.: anoth 63078 2324 182

            bpf_seek_ptr = int(term_dict[1])
            bpf_bytes_to_read = int(term_dict[2])
            term_df = int(term_dict[3])
            master_term_df += term_df

            bpf.seek(bpf_seek_ptr)
            master_posting = master_posting + bpf.read(bpf_bytes_to_read)
            
            bpf.close()
            bdf.close()
        
        mpf.write(master_posting)

        mpf_bytes_to_read = mpf.tell() - mpf_seek_ptr
        mdf.write(term + ' ' + str(mpf_seek_ptr) + ' ' + str(mpf_bytes_to_read) + ' ' + str(master_term_df) + '\n')
        mpf_seek_ptr = mpf.tell()

    N = len(lengths_map.keys())
    mlf.write(str(N) + '\n')
    for doc_id in lengths_map:
        mlf.write(str(doc_id) + ' ' + str(lengths_map[doc_id]) + '\n')
        
    mdf.close()
    mpf.close()
    mlf.close()


def flush_temp_dirs():
    for f in os.listdir(TMP_DICT_DIR): os.remove(os.path.join(TMP_DICT_DIR, f))
    os.rmdir(TMP_DICT_DIR)
    for f in os.listdir(TMP_POST_DIR): os.remove(os.path.join(TMP_POST_DIR, f))
    os.rmdir(TMP_POST_DIR)
    os.rmdir(TMP_DIR)
