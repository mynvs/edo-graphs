from itertools import combinations
from os import system
from temp_settings import *

def all_rotations(bin_str):
    return [bin_str[i:] + bin_str[:i] for i in range(len(bin_str))]

def smallest_rotation(bin_str):
    return min(all_rotations(bin_str))

def binaries_with_n_ones(length, num_ones):
    return [''.join('1' if i in comb else '0' for i in range(length)) 
            for comb in combinations(range(length), num_ones)]

def unique_binaries(edo, chord_size):
    binaries = set()
    for binary in binaries_with_n_ones(edo, chord_size):
        binaries.add(smallest_rotation(binary))
    return sorted(binaries, key=lambda x: int(x, 2))

def all_unique_binaries(edo):
    return [unique_binaries(edo, s) for s in range(edo+1)]

CHARACTERS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CHAR_TO_VALUE = {char: index for index, char in enumerate(CHARACTERS)}
def int_to_base62(num):
    if num == 0:
        return CHARACTERS[0]
    result = ''
    while num:
        result = CHARACTERS[num % 62] + result
        num //= 62
    return result

def base62_to_int(b62_str):
    return sum(CHAR_TO_VALUE[char] * (62 ** i) for i, char in enumerate(reversed(b62_str)))

def zeros_between_ones(bin_str):
    zeros = []
    zero_count = 0
    first_one_encountered = False
    for bit in bin_str + bin_str[0]:
        if bit == '0':
            zero_count += 1
        else:
            if first_one_encountered or zero_count > 0:
                zeros.append(int_to_base62(zero_count))
            first_one_encountered = True
            zero_count = 0
    return ''.join(zeros)

def binary_to_symbol(bin_str, edo, simplify_symbol=False):
    rotations = all_rotations(bin_str)
    min_rot = min(rotations, key=lambda x: int(x[::-1], 2))
    rotation_index = rotations.index(min_rot)
    symbol = zeros_between_ones(min_rot)
    if simplify_symbol and rotation_index == 0:
        return symbol
    return f"{symbol}.{int_to_base62(rotation_index)}"

def symbol_to_binary(symbol, edo, simplify_symbol=False):
    if '.' not in symbol and simplify_symbol:
        chord = symbol
        rotation = 0
    else:
        chord, key = symbol.split('.')
        rotation = base62_to_int(key)
    if not chord:
        return '0' * edo

    zeros = [base62_to_int(x) for x in chord]
    bin_list = ['1']
    for zero_count in zeros:
        bin_list.extend(['0'] * zero_count + ['1'])

    bin_list = bin_list[:-1] if len(bin_list) > edo else bin_list
    bin_list.extend(['0'] * (edo - len(bin_list)))

    return ''.join(bin_list[-rotation:] + bin_list[:-rotation])

def interval_neighbors(bin_str, offsets, reduce):
    shifted_numbers = set()
    one_positions = [i for i, digit in enumerate(bin_str) if digit == '1']
    for offset in offsets:
        for p in one_positions:
            shifted = list(bin_str)
            shifted[p] = '0'
            shifted[(p+offset)%len(bin_str)] = '1'
            if shifted.count('1') == bin_str.count('1'):
                if reduce:
                    shifted_numbers.add(smallest_rotation(''.join(shifted)))
                else:
                    shifted_numbers.add(''.join(shifted))
    return shifted_numbers

def generate_rotated_instructions(transformations, edo, simplify_symbol=False, truncate=True):
    labels = set()
    instructions = set()
    for t in transformations:
        for _ in range(edo):
            a = zip(all_rotations(symbol_to_binary(t[0], edo, simplify_symbol)),
                    all_rotations(symbol_to_binary(t[1], edo, simplify_symbol)))
            for e in a:
                t0 = binary_to_symbol(e[0], edo, simplify_symbol)
                t1 = binary_to_symbol(e[1], edo, simplify_symbol)
                if truncate:
                    try:
                        t0 = t0.split('.')[0][:-1] + '.' + t0.split('.')[1]
                    except:
                        t0 = t0[:-1]
                    try:
                        t1 = t1.split('.')[0][:-1] + '.' + t1.split('.')[1]
                    except:
                        t1 = t1[:-1]
                labels.add(t0)
                labels.add(t1)
                instructions.add((t0, t1))
    return labels, instructions

def generate_instructions(transformations, edo, simplify_symbol=False, truncate=True):
    labels = set()
    instructions = set()
    for t in transformations:
        t0 = binary_to_symbol(symbol_to_binary(t[0], edo, simplify_symbol), edo, simplify_symbol)
        t1 = binary_to_symbol(symbol_to_binary(t[1], edo, simplify_symbol), edo, simplify_symbol)
        if truncate:
            try:
                t0 = t0.split('.')[0][:-1] + '.' + t0.split('.')[1]
            except:
                t0 = t0[:-1]
            try:
                t1 = t1.split('.')[0][:-1] + '.' + t1.split('.')[1]
            except:
                t1 = t1[:-1]
        for _ in range(edo):
            labels.add(t0)
            labels.add(t1)
            instructions.add((t0, t1))
    return labels, instructions

def generate_transformations(edo, chord_size, intervals, do_all_keys,
                             inclusions, exclusions, include_and, exclude_and, simplify_symbol=False, truncate=True):
    
    if type(inclusions) == str:
        inclusions = list(inclusions)
    if type(exclusions) == str:
        exclusions = list(exclusions)
    if type(intervals) == int:
        intervals = [intervals]

    binaries = unique_binaries(edo, chord_size)

    transformations = set()
    for b in binaries:
        if do_all_keys:
            neighbors = interval_neighbors(b, intervals, False)
        else:
            neighbors = interval_neighbors(b, intervals, True)
        for n in neighbors:
            transformations.add((binary_to_symbol(b[::-1], edo, simplify_symbol),
                                 binary_to_symbol(n[::-1], edo, simplify_symbol)))
    transformations = list(transformations)
    transformations_filtered = []
    for t in transformations:
        try:
            t0 = t[0].split('.')[0]
            t1 = t[1].split('.')[0]
        except:
             t0 = t[0]
             t1 = t[1]
        cond_0i = any(e in t0 for e in inclusions) if inclusions else True
        cond_1i = any(e in t1 for e in inclusions) if inclusions else True
        cond_0e = not any(e in t0 for e in exclusions) if exclusions else True
        cond_1e = not any(e in t1 for e in exclusions) if exclusions else True

        if include_and:
            if exclude_and:
                cond = (cond_0i and cond_1i) and (cond_0e and cond_1e)
            else:
                cond = (cond_0i and cond_1i) and (cond_0e or cond_1e)
        else:
            if exclude_and:
                cond = (cond_0i or cond_1i) and (cond_0e and cond_1e)
            else:
                cond = (cond_0i or cond_1i) and (cond_0e or cond_1e)

        if cond:
            transformations_filtered.append(t)
    if do_all_keys:
        return generate_rotated_instructions(transformations_filtered, edo, simplify_symbol, truncate)
    else:
        return generate_instructions(transformations_filtered, edo, simplify_symbol, truncate)

def write_net_file(filename, labels, arcs, EDO):
    labels = list(labels)
    arcs = [(labels.index(i[0])+1, labels.index(i[1])+1) for i in arcs]
    with open(filename, 'w') as file:
        file.write(f'%{EDO}\n')
        file.write(f'*Vertices {len(labels)}\n')
        for i, e in enumerate(labels):
            file.write(f'{i+1} "{e}" 0.0 0.0 0.0\n')
        file.write(f'*Arcs \n')
        for i in arcs:
            file.write(f'{i[0]} {i[1]} 1.0\n')


# EDO = 12
# TRUNCATE_SYMBOLS = True
# SIMPLIFY_SYMBOLS = True

# CHORD_SIZE = 2
# INTERVALS = [7]

# DO_ALL_KEYS = True

# # INCLUSIONS = ['011', '032', '111', '022', '030', '013', '103', '031', '301', '130', '221']
# INCLUSIONS = False
# # EXCLUSIONS = ['32', '23']
# EXCLUSIONS = False

# INCLUDE_AND = True
# EXCLUDE_AND = False


# generates all chord transformations given an interval step, either in all keys or not, then filters them.
labels, arcs = generate_transformations(EDO, CHORD_SIZE, INTERVALS, DO_ALL_KEYS,
                                        INCLUSIONS, EXCLUSIONS, INCLUDE_AND, EXCLUDE_AND,
                                        SIMPLIFY_SYMBOLS, TRUNCATE_SYMBOLS)





# chord A  ->  chord B
# TRANSFORMATIONS =(\
#     ('32', '34'), # Relative
#     ('24', '23'), # Leading tone
#     ('32', '23'), # Parallel
# )
# # takes the given chord transformations and transposes them to all keys.
# labels, arcs = generate_rotated_instructions(TRANSFORMATIONS, EDO, SIMPLIFY_SYMBOLS, TRUNCATE_SYMBOLS)



write_net_file('src/graph.net', labels, arcs, EDO)
system('cd src && display_net.py')


# for l in all_unique_binaries(EDO):
#     for b in l:
#         b = b[::-1]
#         b_symbol = binary_to_symbol(b, EDO, SIMPLIFY_SYMBOLS)
#         if TRUNCATE_SYMBOLS:
#             try:
#                 b_symbol = b_symbol.split('.')[0][:-1] + '.' + b_symbol.split('.')[1]
#             except:
#                 b_symbol = b_symbol[:-1]
#         print(b, '\t', b_symbol)
#     print()


'''
TODO:

0. different interval steps per note
    - this is actually more natural in a system where all binaries are treated as unique shapes

1. ability to have edges across different chord sizes, such as when an interval neighbor
   overlaps with an existing note and the chord size gets reduced by 1.
3. filter based on scales
5. highlight all chords that include a specific note

6. allow flipping as a transformation
7. allow inverting 1's and 0's as a transformation
8. allow adding and removing notes as a transformation

9. ability to treat all binaries as unique shapes, without regard for the minimum rotation

10. ability to highlight specific chord shapes
    - list of chord shapes in the graph along with their other notation forms, ie. indexed and binary

10. ability to highlight chords that contain specific notes

11. ability to "invert" a graph you're looking at.
    - this would be like doing the operation (entire set) NOT (graph in question)
        - boolean logic on graphs

- ability to remove reflections of chords

- change other functions so all_unique_binaries() is simpler

- list of interval combinations that take you from chord A to chord B

9. third program.
    - catalog of all graphs
    - interface for selecting:
        sets of transformations
        sets of chord shapes
        sets of scales

    - sort by binary order or by numerical order of symbols

    - display how subgraphs are embeded in larger graphs


'''