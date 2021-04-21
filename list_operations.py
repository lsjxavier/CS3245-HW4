import math

def create_skip_ptrs(li):
    skip_ptrs = []
    skip_dist = math.floor(math.sqrt(len(li)))
    
    for s in range(0, len(li), skip_dist):
        skip_ptrs.append(s)
    return skip_ptrs


def search(a_val, b_posting, b_ptr, b_skip_ptr, skip_ptrs):
    found = False

    if b_posting[b_ptr] <= a_val:
        # Advance skip_ptr and b_ptr is less than value to find
        while b_skip_ptr < len(skip_ptrs) and b_posting[skip_ptrs[b_skip_ptr]] < a_val:
            b_ptr = skip_ptrs[b_skip_ptr]
            b_skip_ptr += 1
        
        # If value at skip_ptr is the target value, output
        if b_skip_ptr < len(skip_ptrs) and b_posting[skip_ptrs[b_skip_ptr]] == a_val:
            found = True
            b_ptr = skip_ptrs[b_skip_ptr]
        else:
            # Target value may exist between b_ptr and skip_ptr in b.
            # Binary search to check if target value exists in b,
            # then advance b_ptr to the end position of the binary
            # search regardless of search result.

            low = b_ptr
            high = 0
            if b_skip_ptr < len(skip_ptrs):
                high = skip_ptrs[b_skip_ptr]
            else:
                high = len(b_posting) - 1
            
            mid = 0
            while low <= high:
                mid = math.floor((high + low) / 2)

                if b_posting[mid] < a_val:
                    low = mid + 1
                elif b_posting[mid] > a_val:
                    high = mid - 1
                else:
                    found = True
                    break
            b_ptr = mid
    return b_ptr, b_skip_ptr, found

# ====================================================================
# SET OPERATION METHODS

def intersect(x, y):
    if not x or not y: return []
    skip_ptrs = []
    if len(x) < len(y):
        a = x
        b = y
        skip_ptrs = create_skip_ptrs(y)
    else:
        a = y
        b = x
        skip_ptrs = create_skip_ptrs(x)
    
    b_ptr = 0
    b_skip_ptr = 0

    result = []

    for a_val in a:
        b_ptr, b_skip_ptr, found = search(a_val, b, b_ptr, b_skip_ptr, skip_ptrs)
        if found:
            result.append(a_val)

    return result


def union(a, b):
    if not a: return b
    if not b: return a

    result = []
    while a and b:
        if a[0] < b[0]:
            result.append(a.pop(0))
        elif a[0] > b[0]:
            result.append(b.pop(0))
        else:
            result.append(a.pop(0))
            b.pop(0)
    
    if a:
        result += a
    if b:
        result += b

    return result


def subtract(x, y):
    if not x: return []
    if not y: return x

    x_posting_len = x[0]
    y_posting_len = y[0]
    
    a_posting = x[1:x_posting_len + 1]
    b_posting = y[1:y_posting_len + 1]
    skip_ptrs = y[y_posting_len + 1:]

    b_ptr = 0
    b_skip_ptr = 0

    a_ptr = 0
    while a_ptr < len(a_posting):
        b_ptr, b_skip_ptr, found = search(a_posting[a_ptr], b_posting, b_ptr, b_skip_ptr, skip_ptrs)
        if found:
            a_posting.remove(a_posting[a_ptr])
        else:
            a_ptr += 1
    
    result = a_posting
    
    return result
