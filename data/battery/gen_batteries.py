import os
from itertools import combinations

# remove previous combinations of batteries
if os.path.exists('comb'):
    os.system('rm -r comb')

# create new batteries
os.makedirs('comb')

# create batteries
batteries = [fname for fname in os.listdir(os.getcwd()) if fname.endswith('.yaml')]

MAX_BATTERIES = 3

# create combinations of at most MAX_BATTERIES batteries
ctr = 0

for i in range(1, MAX_BATTERIES + 1):
    comb = list(combinations(batteries, i))

    if not comb:
        continue

    # concatenate two files with a line between them
    for c in comb:
        with open(f'comb/bat{ctr}.yaml', 'w') as out:
            for bat in c:
                text = open(bat).read()
                out.write(text)
                out.write('\n')

        ctr += 1

