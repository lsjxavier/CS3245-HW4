import file_operations
import list_operations
import vsm

bool_functions = {
    '(': (99, 'right', 'left_paran'),
    ')': (99, 'right', 'right_paran'),
    'AND': (2, 'left', 'operator'),
    'OR': (1, 'left', 'operator')
}

def is_operator(string):
    return string in bool_functions and bool_functions[string][2] == 'operator'

def is_function(string):
    return string in bool_functions and bool_functions[string][2] == 'function'

def is_left_paranthesis(string):
    return string in bool_functions and bool_functions[string][2] == 'left_paran'

def is_right_paranthesis(string):
    return string in bool_functions and bool_functions[string][2] == 'right_paran'

def is_left_associative(string):
    return string in bool_functions and bool_functions[string][1] == 'left'

def is_right_associative(string):
    return string in bool_functions and bool_functions[string][1] == 'right'

def is_term(string):
    return not (is_operator(string) or is_function(string) or is_left_paranthesis(string) or is_right_paranthesis(string))

# ========================================================================
# INDEX ELIMINATION METHODS

def remove_low_idf(token, dictionary, N):
    # If a term has low_idf, remove from query.

    # What if original query is boolean query?

    pl = {}
    if token in dictionary:
        # term_idf = vsm.compute_idf(N, dictionary[token][2])
        # if term_idf > 0.4: # Accept term if its df is at most 2/5th of collection size
        #     pl = file_operations.retrieve_posting_list(token, dictionary)
        
        term_df = dictionary[token][2]
        if (term_df / N < 0.4):
            pl = file_operations.retrieve_posting_list(token, dictionary)

    return pl


def index_elimination(token, dictionary, N):
    pl = remove_low_idf(token, dictionary, N)
    return list(pl.keys())

# ========================================================================
# SHUNTING YARD ALGORITHM AND EVALUATION

def create_rpn(tokens):
    rpn = []
    op_stack = []
    for token in tokens:
        if isinstance(token, list):
            rpn.append(token)

        elif is_function(token):
            op_stack.append(token)

        elif is_left_paranthesis(token):
            op_stack.append(token)

        elif is_right_paranthesis(token):
            while op_stack and not is_left_paranthesis(op_stack[-1]):
                rpn.append(op_stack.pop())
            if op_stack and is_left_paranthesis(op_stack[-1]):
                op_stack.pop()
            if op_stack and is_function(op_stack[-1]):
                rpn.append(op_stack.pop())

        elif is_operator(token):
            while (
                op_stack
                and (
                    bool_functions[op_stack[-1]][0] > bool_functions[token][0]
                    or (bool_functions[op_stack[-1]][0] == bool_functions[token][0] and is_left_associative(token)))
                and not is_left_paranthesis(op_stack[-1])
            ):
                rpn.append(op_stack.pop())
            
            op_stack.append(token)
        else:
            rpn.append(token)

    while op_stack:
        rpn.append(op_stack.pop())

    return rpn


def eval_rpn(rpn, dictionary, N):
    eval_stack = []
    while rpn:
        token = rpn.pop(0)

        if isinstance(token, list):
            if isinstance(token[0], int): eval_stack.append(token)
            else:
                # The current token is a phrase.
                # Create a new RPN and evaluate the phrase,
                # then check the positional indices.

                phrase_postings = {}
                # K: term
                # V: { K: doc_id
                #      V: [positions] }
                offset = 0 # To offset positions

                # For each term, align positional indices to the first term such that the intersection
                # of all indices later on tells us if the phrase appears at least once in the document.
                for term in token:
                    if is_term(term):
                        term_posting = file_operations.retrieve_posting_list(term, dictionary)
                        
                        # Align the positonal indices
                        phrase_postings[term] = {doc_id: [pos - offset for pos in indices] for doc_id, indices in term_posting.items()}
                        offset += 1
                phrase_rpn = create_rpn(token)

                for term in phrase_rpn:
                    # We've already gotten the posting list of each term earlier above,
                    # So substitute term with posting list of the term
                    if is_term(term): term = list(phrase_postings[term].keys()) 
                
                # Returns a list of documents containing all terms in the phrase,
                # without considering position first.
                # phrase_result = eval_rpn(phrase_rpn, dictionary, postings_file, N)
                phrase_result = eval_rpn(phrase_rpn, dictionary, N)

                result = []

                # Now intersect the positional indices retrieved earlier on in relation to each document
                # in the returned list.
                # If the list produced from the intersection has at least one element, then the
                # document contains the phrase.
                for doc_id in phrase_result:
                    position_intersect = None

                    for term in phrase_postings:
                        if term not in phrase_postings or doc_id not in phrase_postings[term]: continue

                        if position_intersect == None:
                            position_intersect = phrase_postings[term][doc_id]
                        else:
                            position_intersect = list_operations.intersect(position_intersect, phrase_postings[term][doc_id])
                    if position_intersect: result.append(doc_id)
                
                # ADD TO DICTIONARY?
                # ADD TO POSTINGS?
                    
                eval_stack.append(result)

        elif token == 'AND':
            right_term = eval_stack.pop()
            left_term = eval_stack.pop()

            left = []
            right = []
            if isinstance(left_term, str):
                left = index_elimination(left_term, dictionary, N)
            else:
                left = left_term
            
            if isinstance(right_term, str):
                right = index_elimination(right_term, dictionary, N)
            else:
                right = right_term

            eval_stack.append(list_operations.intersect(left, right))

        elif token == 'OR':
            right_term = eval_stack.pop()
            left_term = eval_stack.pop()

            left = []
            right = []
            if isinstance(left_term, str):
                left = index_elimination(left_term, dictionary, N)
            else:
                left = left_term
            
            if isinstance(right_term, str):
                right = index_elimination(right_term, dictionary, N)
            else:
                right = right_term

            eval_stack.append(list_operations.union(left, right))
            
        else:
            pl = index_elimination(token, dictionary, N)
            eval_stack.append(pl)

    output = eval_stack.pop()
    return output
