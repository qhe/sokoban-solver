#!/usr/bin/env python3

# -1: invalid
#  0: wall
#  1: open space
#
# bitfields:
#  0x10: character
#  0x20: destination
#  0x40: box
#  0x80: reachable by character

# directions:
#   1: up
#   2: right
#   3: down
#   4: left

import array
import copy
from enum import Enum

m =   [[0,    0,    0,    0,    0,    0],
       [0,    1,    1,    1, 0x21,    0],
       [0,    1, 0x21,    1, 0x11,    0],
       [0,    1,    0,    1,    0,    0,    0],
       [0,    1,    0,    1, 0x41,    1,    0,    0],
       [0,    1, 0x41, 0x21,    1,    1,    1,    0,    0],
       [0,    0,    0,    0,    1, 0x41,    1,    1,    0,    0],
       [-1,  -1,   -1,    0,    0,    1,    1,    1,    1,    0],
       [-1,  -1,   -1,   -1,    0,    0,    1,    1,    1,    0],
       [-1,  -1,   -1,   -1,   -1,    0,    0,    0,    0,    0]]

m2 =  [[-1,  -1,   -1,    0,    0,    0,    0,    0,    0],
       [0,    0,    0,    0, 0x21,    1,    1, 0x11,    0],
       [0,    1,    1, 0x41, 0x41, 0x41,    1,    1,    0],
       [0, 0x21,    0,    0, 0x21,    0,    0, 0x21,    0],
       [0,    1,    1,    1, 0x41,    1,    1,    1,    0],
       [0,    1,    1, 0x41, 0x21,    0,    1,    0,    0],
       [0,    0,    0,    0,    1,    1,    1,    0],
       [-1,  -1,   -1,    0,    0,    0,    0,    0]]

class Dir(Enum):
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4

class skb_map(object):
    def __init__(self, mapl):
        '''init from an 2d array (trailing -1 for each row may be omitted)'''
        self.height = len(mapl)
        self.width = 0
        for i in mapl:
            if len(i) > self.width:
                self.width = len(i)
        flatten = []
        for i in mapl:
            l = len(i)
            flatten.extend(i)
            flatten.extend([-1] * (self.width - l))
        self.array = array.array('i', flatten)

        self.validate()
        self.resolve_reachable()

    def element(self, x, y):
        '''return the element at a coordinate'''
        return self.array[x + y * self.width]

    def update_element(self, x, y, value):
        '''update the element at a coordinate'''
        self.array[x + y * self.width] = value

    def is_reachable(self, x, y):
        '''whether the coordinate is reachable from the current character position'''
        return self.reachable[x + y * self.width] & 0x80 == 0x80

    def is_blocked(self, x, y):
        '''whether the coordinate is blocked (cannot move in, by wall or box)'''
        return self.element(x, y) == 0 or (self.element(x, y) & 0x40) == 0x40

    def is_wall(self, x, y):
        '''whether the coordinate is wall'''
        return self.element(x, y) == 0

    def is_dead_corner(self, x, y):
        '''whether the coordinate is a dead corner (i.e. if moved to here, cannot get out)'''
        if self.element(x, y) & 0x20 != 0:   # a destination is not a dead corner
            return False

        if (self.is_wall(x+1, y) and self.is_wall(x, y+1)) or \
            (self.is_wall(x+1, y) and self.is_wall(x, y-1)) or \
            (self.is_wall(x-1, y) and self.is_wall(x, y+1)) or \
            (self.is_wall(x-1, y) and self.is_wall(x, y-1)):
            return True
        return False

    def compare(self, another_map):
        '''if 2 maps are equivalent (same box positions and equivalent character position'''
        return self.reachable == another_map.reachable

    def completed(self):
        '''it's fully solved'''
        return self.unsolved == 0

    def print(self, reachable=False):
        for y in range(self.height):
            for x in range(self.width):
                if not reachable:
                    e = self.element(x, y)
                else:
                    e = self.reachable[x + y * self.width]

                if e == -1:
                    p = '     '
                elif e < 0x10:
                    p = '{:5d}'.format(e)
                else:
                    p = '{:5x}'.format(e)

                print(p, end='')
            print('\n')
        print('box: {}, unsolved: {}, character: ({}, {})'.format(self.box, self.unsolved, self.character[0], self.character[1]))

    def validate(self, no_update=False):
        '''check if the map is valid'''
        total_box = 0
        total_dest = 0
        total_unsolved = 0
        total_character = 0
        character = None

        for y in range(self.height):
            for x in range(self.width):
                e = self.element(x, y)
                if e == 0 or e == -1:    # walls and invalid space are not interested
                    continue

                if (e & 1) == 0 or (e & ~0x71) != 0:   # any special flags on non open space, or any unexpected flags (undefined or reachable)
                    print('invalid element at {}, {}'.format(x, y))
                    exit(-1)

                if x == 0 or x == self.width-1 or y == 0 or y == self.height-1:
                    print('open space on the border at {}, {}'.format(x, y))
                    exit(-1)

                if (e & 0x1) == 1 and (self.element(x-1, y) == -1 or self.element(x+1, y) == -1 or self.element(x, y-1) == -1 or self.element(x, y+1) == -1):
                    print('open space adjacent to invalid at {}, {}'.format(x, y))
                    exit(-1)

                if (e & 0x10) != 0:
                    total_character += 1
                    character = (x, y)

                if (e & 0x20) != 0:
                    total_dest += 1

                if (e & 0x40) != 0:
                    total_box += 1
                    if (e & 0x20) == 0:
                        total_unsolved += 1
                    if self.is_dead_corner(x, y):
                        print('unmovable box at {}, {}'.format(x, y))
                        exit(-1)

                if (e & 0x10) != 0 and (e & 0x40) != 0:
                    print('character standing on the box at {}, {}'.format(x, y))
                    exit(-1)

        if total_character != 1:
            print('number of characters incorrect {}'.format(total_character))
            exit(-1)

        if total_box == 0:
            print('no boxes')
            exit(-1)

        if total_box != total_dest:
            print('boxes and destinations don''t match')
            exit(-1)

        if no_update:
            if self.box != total_box or self.dest != total_dest or self.unsolved != total_unsolved:
                print('inconsistent box/dest/unsolved count')
                exit(-1)
            if self.character != character:
                print('inconsistent character data')
                exit(-1)
        else:
            self.box = total_box
            self.dest = total_dest
            self.unsolved = total_unsolved
            self.character = character

    def resolve_reachable(self):
        '''find all reachable spots'''
        self.reachable = copy.copy(self.array)

        # starting from character point, clear the character flag for easy comparison of equivalence
        x, y = self.character
        self.reachable[x + y * self.width] &= ~0x10
        todo = set([(x, y)])

        def check_xy(x, y):
            t = self.reachable[x + y * self.width]
            if t != 0 and (t & 0x40) == 0 and (t & 0x80) == 0:   # not wall, not box, not already counted as reachable
                todo.add((x, y))
        while (todo):
            x, y = todo.pop()
            self.reachable[x + y * self.width] |= 0x80
            check_xy(x+1, y)
            check_xy(x-1, y)
            check_xy(x, y+1)
            check_xy(x, y-1)

    def find_all_possible_moves(self):
        '''find all possible moves, return a list of (x, y, direction)'''
        moves = []
        for y in range(self.height):
            for x in range(self.width):
                if self.element(x, y) == -1 or (self.element(x, y) & 0x40) == 0:  # not a box
                    continue
                if self.is_reachable(x, y+1) and not self.is_blocked(x, y-1) and not self.is_dead_corner(x, y-1):
                    moves.append((x, y, Dir.UP))
                if self.is_reachable(x-1, y) and not self.is_blocked(x+1, y) and not self.is_dead_corner(x+1, y):
                    moves.append((x, y, Dir.RIGHT))
                if self.is_reachable(x, y-1) and not self.is_blocked(x, y+1) and not self.is_dead_corner(x, y+1):
                    moves.append((x, y, Dir.DOWN))
                if self.is_reachable(x+1, y) and not self.is_blocked(x-1, y) and not self.is_dead_corner(x-1, y):
                    moves.append((x, y, Dir.LEFT))
        return moves

    def create_new_map_by_move(self, x, y, direction):
        '''retrun a new map after move'''

        # 0. minimal sanity check only
        new_map = copy.deepcopy(self)
        if (new_map.element(x, y) & 0x40) == 0:
            print('bad move attemp ({}, {}), {}, no box'.format(x, y, direction))
            exit(-1)

        # 1. erase character
        cx, cy = new_map.character
        new_map.update_element(cx, cy, new_map.element(cx, cy) & ~0x10)

        # 2. clear the box from current location, if we are moving away from a destination, update unsolved count
        new_map.update_element(x, y, new_map.element(x, y) & ~0x40)
        if (new_map.element(x, y) & 0x20) != 0:
            new_map.unsolved += 1

        # 3. update the box to the new location (update unsolved accordingly)
        nx = x
        ny = y
        if direction == Dir.UP:
            ny = y - 1
        elif direction == Dir.RIGHT:
            nx = x + 1
        elif direction == Dir.DOWN:
            ny = y + 1
        elif direction == Dir.LEFT:
            nx = x - 1
        else:
            print('bad move direction ({}, {}), {}'.format(x, y, direction))
            exit(-1)

        new_map.update_element(nx, ny, new_map.element(nx, ny) | 0x40)
        if (new_map.element(nx, ny) & 0x20) != 0:
            new_map.unsolved -= 1

        # 4. set new character position and resolve reachable
        new_map.character = (x, y)
        new_map.update_element(x, y, new_map.element(x, y) | 0x10)
        new_map.resolve_reachable()

        # it should be a valid map now, check to make sure, not necessary
        new_map.validate(True)

        return new_map

# each level:  [skbmap, all_moves, current move]
def find_skb_map_solutions(skbmap):
    history = []
    seen = [skbmap]
    moves = 0
    solutions = 0

    if skbmap.completed():
        print('already resolved')
        return

    history.append([skbmap, skbmap.find_all_possible_moves(), -1])

    while (history):
        h = history[-1]

        h[2] += 1     # ready to try next move
        if h[2] >= len(h[1]):   # we are done with all the moves in current layer
            history.pop()
            continue

        moves += 1

        x, y, dir = h[1][h[2]]
        nm = h[0].create_new_map_by_move(x, y, dir)
        if nm.completed():
            print('solution (move count {}):'.format(len(history)))
            for t in history:
                print('\t', t[1][t[2]])
            solutions += 1

        # we still want to add the solution map into seen as well (they may also differ due to character possibly at different position)
        rep = False
        for s in seen:
            if nm.compare(s):   # we already seen this frame, this is not a valid path
                rep = True
                break
        if rep:
            continue

        seen.append(nm)

        if nm.completed():
            continue

        # a new valid non-solution frame
        history.append([nm, nm.find_all_possible_moves(), -1])

    print('moves evaluated: {}, solutions found: {}, frames seen: {}'.format(moves, solutions, len(seen)))



skbmap = skb_map(m)
skbmap.print()
#skbmap.print(reachable=True)
#print(skbmap.find_all_possible_moves())

find_skb_map_solutions(skbmap)
