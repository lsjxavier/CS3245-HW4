This is the README file for A0185203M's submission
Email: e0318494@u.nus.edu

== Python Version ==

I'm using Python Version 3.9 for this assignment. (Also tested for version 3.6.8)



== General Notes about this assignment ==

INDEXING:

Framework:
    1. Open CSV file, store the iterator into memory.
    2. Split the iterator into blocks
    3. For each block:
        - Split block into x slices, where x is the number of worker processes
        - Each worker condenses the documents within their own slice
        - Once all workers are done, they consolidate their condensed document
          mappings and pass to the writers to create:
            - Postings file with Variable-byte (VB) encoding
            - Dictionary file with pointers on where to read from the postings
            - Lengths file containing the collection size and document lengths
    4. When all blocks are written, merge all the blocks by terms

The details:
-   The same process as HW3 is used, where each document is condensed into a dict
    structure with terms, their frequencies (tf) as well as an array of their
    positions. This is used as the base to derived the 3 structures needed:
      - Posting file: doc_id, term_frequency, [positional indices]
      - Dictionary file: term, posting seek pointer, no. of bytes to read,
        document_frequency
      - Lengths file: doc_id, document_length (and collection size included
        in the header)

-   Due to the large collection size of over 17,000 documents, SPIMI is also
    introduced during indexing in the same style as HW2, where a term - block_id
    mapping is maintained while writing the blocks, then terms are merged across
    blocks that the term appears in. Multiprocessing was also implemented within
    each block during document processing, which decreased indexing time, but at
    the cost of slightly higher memory consumption. Smaller block sizes were
    therefore used (maximum 256 documents per block).

-   Variable-byte encoding was chosen to compress the postings list as it is
    not as expensive to decode as gamma encoding, although the resultant
    file size would be slightly larger. In addition, it was performed during
    writing of individual blocks rather than at the merging stage, so that the
    merging stage is just a simple appending of byte strings, and is less
    memory exhaustive than reading in the uncompressed postings for each term
    into memory.


SEARCHING:

Framework:
    1. First parse the query as a boolean query. Free search queries will be
    separated by the 'OR' operator, except when they are a part of a phrase,
    which they will then be separated by the 'AND' operator instead.
    2. Perform boolean retrieval with index elimination (removing low idf).
    3. With our boolean retrieval result, calculate VSM scores for all
    documents in the result (parallelization involved).

The details:
-   Due to the multiple formats and factors to consider for the query, a
    generalized workflow was designed to streamline the search process:
    - Treat query input as a boolean query, and add OR operators in between
      two terms if no operator exists, unless if it is part of a phrase,
      then add AND operators.

    - Thesaurus-based query expansion would be executed here, however as it
      greatly increased the resultant pool of documents to compute, the code
      for this process has been commented out.

    - Perform boolean search on our boolean query to obtain a list of documents
      that satisfies our query. In addition, perform index elimination tecniques
      to reduce the number of potential documents returned that are non-relevant.

    - Produce a free search version of our query input, then use the VSM method
      with lnc.ltc weighting scheme to compute the VSM score for our query
      against the documents returned by our boolean search as well as the given
      relevant documents.

-   Evaluation of the vector scores remains the same as that in HW3, where we
    calculate the square of the scores using the modified formula to avoid
    computing square roots. To recap, the original formula for computing the
    document vector score,

                                 Σ(qi * di)
                           ----------------------,
                            √q_length * √d_length

    where q_length and d_length = Σ(q_wt ^ 2) and Σ(d_wt ^ 2) respectively,
    was rewritten as 
                                 Σ(qi * di)
                          ( ------------------- ) ^ 2 * q_length * d_length,
                             q_length * d_length

    which evaluates to the square of the score as computed by the original
    formula. There were two motivations behind this: to avoid the expensive
    computation of square roots during indexing and searching, as well as easier
    score computation on a per term basis (qi * di).

-   Due to the potentially large number of results that may be returned, multiprocessing
    techniques were used to parallelize the computation of the scores. The list is
    split into 4 parts for 4 workers, where each worker calculates and returns the
    scores.



== Files included with this submission ==

index.py ---------------------- Entry point for indexing process.
                                Extraction of content in CSV dataset is also
                                done here.

search.py --------------------- Entry point for search process.

boolean_retrival.py ----------- Main helper for boolean retrival:
                                  - Index elimination methods
                                  - Shunting-yard algorithm
                                  - Reverse Polish notation evaluation

vsm.py ------------------------ Main helper for VSM scoring:
                                  - Conversion to tf-idf
                                  - Creation of query vector
                                  - Computing the score per term

list_operations.py ------------ Secondary helper for list traversal:
                                  - Creation of skip pointers
                                  - List intersect, union and subtraction

language_operations.py -------- Secondary helper for language processing:
                                  - Processing content for each document
                                  - Assembling term posting list for a block
                                    of documents
                                  - Query parsing to both boolean query and
                                    free search versions
                                  - Thesaurus-based query expansion
                                    (commented out)

file_operations.py ------------ Secondary helper for disk operations:
                                  - Writing a block of dictionary and postings
                                    list to disk
                                  - Merging of term posting list across blocks
                                  - Retrieval of dictionary, postings list and
                                    document lengths

config.py --------------------- Stores global configurable values

filenames.py ------------------ Stores file path of all relevant files.

vbcode.py --------------------- External library for variable-byte encoding
                                (see references).

dictionary.txt ---------------- Dictionary file containing pointers to read
                                from postings list.

postings.txt ------------------ The VB-encoded postings list. In binary format.

lengths.txt ------------------- File containing document lengths for each document.


== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] I, A0185203M, certify that I have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I
expressly vow that I have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I, A0185203M, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

I suggest that I should be graded as follows:

<Please fill in>



== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>

1: External library for VB encoding/decoding from https://github.com/utahta/pyvbcode
   distributed under the MIT license, which in turn is an implementaion of the
   algorithm presented in the IR textbook by Manning, Raghavan and Schütze (2008).

2: As with HW2, the Shunting-yard algorithm to transform infix notation to Reverse
   Polish notation, and the evaluation algorithm of Reverse Polish notation were
   inspired from the following websites:
       https://en.wikipedia.org/wiki/Shunting-yard_algorithm
       https://stevenpcurtis.medium.com/evaluate-reverse-polish-notation-using-a-stack-7c618c9f80c0

3: Topics on Python multiprocessing were consulted from the following websites:
   https://www.geeksforgeeks.org/multiprocessing-python-set-2/
   https://pymotw.com/2/multiprocessing/basics.html
   https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes

4: Misc pythonic tricks adapted as part of cleaning up messy code structures from
   previous assignments:
   
   a. Splitting list into a specific number of parts:
   https://stackoverflow.com/questions/752308/split-list-into-smaller-lists-split-in-half

   b. Slicing an iterator:
   https://stackoverflow.com/questions/1915170/split-a-generator-iterable-every-n-items-in-python-splitevery

   c. Using regex to remove special characters
   https://stackoverflow.com/questions/6323296/python-remove-anything-that-is-not-a-letter-or-number
