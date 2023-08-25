"""
GENERALIZED KEYBOARDS

- Map a scale onto Erv Wilson's generalized keyboard layouts
- Retune synths with MTS-ESP to play the laid-out scale on a midi controller

See Wilson's Gral spectrum at https://www.anaphoria.com/gralspectrum.pdf
and Gral keyboard guide at https://www.anaphoria.com/gralkeyboard.pdf.
Also see chapter 3 of 'Microtonality and the Tuning Systems of Erv Wilson'
by T. Narushima.
"""
from fractions import Fraction
from itertools import chain, product, zip_longest

import matplotlib.pyplot as plt
import networkx as nx

import mtsespy as mts

mts.register_master()


def mediant(x, y):
    (a, b), (c, d) = x, y
    return (a + c, b + d)


def next_level(s):
    new = [mediant(x, y) for x, y in zip(s, s[1:])]
    return list(chain.from_iterable(zip_longest(s, new)))[:-1]


def stern_brocot(n):
    s = [(0, 1), (1, 1), (1, 0)]
    all_levels = [s]
    while len(all_levels) < n:
        all_levels.append(s := next_level(s))
    return all_levels


def gral(n):
    return {
        mediant((a, b), (c, d)): ((b, d), (a, c))
        for s in stern_brocot(n)
        for (a, b), (c, d) in zip(s, s[1:])
    }


GRAL = gral(12)


def find_steps(coords, degrees):
    ((a, b), (c, d)) = coords
    i, j = degrees
    assert a * d - b * c == 1
    return (d * i - b * j, -c * i + a * j)


def draw(scale, steps, min_coord=0, max_coord=7):
    x, y = steps
    G = nx.Graph(directed=True)

    scale_length = len(scale)

    for coords in product(range(min_coord, max_coord + 1), repeat=2):
        i, j = coords
        index = i * x + j * y
        degree = index % scale_length
        G.add_node(coords, pos=(i, j), index=index, degree=degree, freq=scale[degree])

    for n in G.nodes():
        p, q = n
        for m in G.nodes():
            r, s = m
            if (p == r and q + 1 == s) or (p + 1 == r and q == s):
                G.add_edge(n, m)

    positions = {n: d["pos"] for n, d in G.nodes(data=True)}
    labels = {n: d["freq"] for n, d in G.nodes(data=True)}
    nx.draw(
        G,
        pos=positions,
        labels=labels,
        with_labels=True,
        node_color="white",
        node_size=1000,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=6,
    )
    plt.gca().set_aspect("equal")
    plt.savefig("out.png")


def tune(scale, steps, base_freq=261.625565):
    # Midi note map for Launchpad X custom mode 4
    midi_note_map = {(i, j): 10 * j + i + 11 for i, j in product(range(8), repeat=2)}
    x, y = steps
    for (i, j), n in midi_note_map.items():
        octave, degree = divmod(i * x + j * y, len(scale))
        mts.set_note_tuning(2**octave * scale[degree] * base_freq, n)


JUST_7 = "1/1 9/8 5/4 4/3 3/2 5/3 15/8"
JUST_12 = "1/1 16/15 9/8 6/5 5/4 4/3 7/5 3/2 8/5 5/3 9/5 15/8"
JUST_19 = """
    1/1 25/24 16/15 9/8 7/6 6/5 5/4 9/7 4/3 7/5 10/7
    3/2 14/9 8/5 5/3 12/7 9/5 15/8 48/25
"""
JUST_31 = """
    1/1 45/44 25/24 16/15 12/11 9/8 8/7 7/6 6/5 11/9 5/4 9/7 13/10
    4/3 11/8 7/5 10/7 16/11 3/2 20/13 14/9 8/5 18/11 5/3 12/7
    7/4 9/5 11/6 15/8 48/25 88/45
"""

if __name__ == "__main__":
    scale_str = JUST_19

    scale = [Fraction(x) for x in scale_str.split()]

    steps = find_steps(coords=GRAL[3, 5], degrees=(len(scale), 11))

    print(steps)
    draw(scale, steps)
    tune(scale, steps)
