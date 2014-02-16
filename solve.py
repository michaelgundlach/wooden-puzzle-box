"""
Finds the solution to a wooden 3d puzzle.

The puzzle is a 6x5x2 unit wooden box, containing 12 wooden pieces, each made
of 5 units of wood in 2d (e.g. all the 5-block tetris shapes).  The goal is
to fit all 12 pieces into the box in two layers of 6 pieces each.

The program finds a solution for one layer using 6 pieces, then hopes to
find a solution using the remaining 6 pieces, in which case the puzzle is
solved.

The algorithm for finding a solution in one layer is recursive: it takes a
partially-filled in layer, tries every way it can to place a single piece from
the 'unplaced' pile into that layer, and recurses.  It wins when it has used 6
pieces.
"""


class Box(object):
    """Defines the width and height of the box."""
    def __init__(self):
        self.x = 6
        self.y = 5


class Move(object):
    """
    Represents a Piece in a specific position and orientation.
    As in, we can solve the puzzle by making a series of specific
    Moves, one correct Move with each Piece.
    """
    def __init__(self, piece, ascii=None, mask=None):
        """Specify ascii (2d ascii art of the placement) or mask (1d bitmask
        of the piece.)."""
        self.piece = piece
        if ascii is not None:
            self.mask = self._asMask(ascii)
        else:
            self.mask = mask

    def _asMask(self, shape):
        """
        Converts a character-based 2d placement to a 1d bitmask.
        """
        binary = lambda word: ''.join('0' if x == ' ' else '1' for x in word)
        number = ''.join(binary(word) for word in shape.art)
        return int(number, 2)

    def fits(self, move2):
        """Can this move and another move be made legally?"""
        return not (self.mask & move2.mask)

    def combined(self, move2):
        """The result of making two moves -- a larger "move" that is the
        combination of the two."""
        return Move(self.piece, mask=self.mask | move2.mask)

    def __str__(self):
        return str(self.toAsciiShape())

    def toAsciiShape(self, char='.'):
        """Returns the ascii representation of the Move."""
        x, y = self.piece.box.x, self.piece.box.y
        art = []
        rowmask = int('1' * x, 2)
        number = self.mask
        while number:
            string = bin(number & rowmask)[2:] # strip the '0b'
            string = string.replace('1', char).replace('0', ' ')
            leftpad = ' ' * (x-len(string))
            art.insert(0, leftpad + string)
            number >>= x
        while len(art) < y:
            art.insert(0, ' '*x)
        return AsciiShape(art)

    def __repr__(self):
        return str(self)

    # Required so we can live in a set()
    def __hash__(self):
        return self.mask
    def __eq__(self, other):
        return hash(self) == hash(other)


class Piece(object):
    """Represents a wooden piece.  A Piece knows all of the possible ways
    it can be laid in a Box (its 'moves')."""
    def __init__(self, name, box, shape):
        """
        box: Box
        shape: two-dimensional array showing the shape of the Piece, with
               spaces for blanks and any other character for the object.
               e.g. [" | ", "-+-", " | "] for a plus.
        """
        self.name = name
        self.box = box
        self.moves = self._moves(shape)

    def _moves(self, shape):
        """
        Example input for a cross:
        [" | ", "-+-", " | ", " | "]
        Returns, for a 6x5 box:
        [Move([
            '    | ',
            '   -+-',
            '    | ',
            '    | ',
            '      ']),
         # plus every other way that you could put the cross in an empty
         # box, flipping or rotating or sliding it
        ]
        """
        x, y = self.box.x, self.box.y
        return {Move(self, translation)
                for rotation in AsciiShape(shape).rotations()
                for flip in rotation.flips()
                for translation in flip.translations(x, y)}


class AsciiShape(object):
    """
    An ascii art drawing of a shape on a blank background.
    Vocab:
      'art' is the 2d ascii art, composed of a list of 'words', which are
      strings each representing a row of the art.  The art is any characters
      on a background of 'blanks' (space characters).
    """
    def __init__(self, art):
        """art: a list of strings, representing an ascii drawing on a
        background made of spaces.  All strings must be the same length."""
        self.art = art

    def rotations(self):
        """Returns a list of all 4 rotations of the ascii shape."""
        r1 = self.rotated()
        r2 = r1.rotated()
        r3 = r2.rotated()
        return [self, r1, r2, r3]

    def rotated(self):
        """Returns the ascii shape rotated 90 degrees. Really."""
        return AsciiShape(self._flipped(self._pivoted(self.art)))

    def flips(self):
        """Returns a list of the ascii shape, and the shape flipped."""
        return [self, AsciiShape(self._flipped(self.art))]

    def _flipped(self, art):
        """Mirrors the art about the vertical axis."""
        return [''.join(reversed(word)) for word in art]

    def translations(self, x, y):
        """Return all translations of the ascii shape on an x by y grid."""
        def rowSlides(art):
            result = [art]
            while not art[-1].strip(): # blank bottom word
                art = art[-1:] + art[:-1]
                result.append(art)
            return result

        def colSlides(art):
            return [self._pivoted(pivotedArt)
                    for pivotedArt in rowSlides(self._pivoted(art))]

        shapeAtTopLeft = self._extend(self.art, x, y)
        return [AsciiShape(art)
                for row in rowSlides(shapeAtTopLeft)
                for art in colSlides(row)]

    def _pivoted(self, art):
        """Turn rows into cols and vice versa."""
        return [''.join(x) for x in zip(*art)]

    def _extend(self, art, x, y):
        """Pad the right and bottom edges of |art| to a total of x by y."""
        xgrown = [ word + ' '*(x-len(word)) for word in art ]
        yrows = [' '*x] * (y - len(art))
        return xgrown + yrows

    def __str__(self):
        """A pretty ascii printout of the shape."""
        width = len(self.art[0])
        border = "+%s+" % ('-' * width)
        result = ['\n', border]
        result.extend('|%s|' % word for word in self.art)
        result.extend([border, '\n'])
        return '\n'.join(result)

    def __repr__(self):
        return '\n%s\n' % str(self)


BOX = Box()
PIECES = [
        # The first 6 pieces and last 6 pieces each form a layer in
        # a 6x5 box.  But we shuffle in solve() just to prove to ourselves
        # that this works correctly.
        Piece("plus", BOX, [' | ', '-|-', ' | ']),
        Piece("L", BOX, ['|  ', '|  ', '+--']),
        Piece("u", BOX, ['---', '| |']),
        Piece("q", BOX, ['++', '++', ' |']),
        Piece("f", BOX, [' | ', '-+-', '  |']),
        Piece("z", BOX, ['--+ ', '  +-']),
        Piece("p", BOX, ['-+--', ' |  ']),
        Piece("t", BOX, ['-+-', ' | ', ' | ']),
        Piece("w", BOX, ['-+ ', ' ++', '  |']),
        Piece("2", BOX, ['+  ', '+-+', '  |']),
        Piece("r", BOX, ['+---', '|   ']),
        Piece("i", BOX, ['-----']),
        ]


def solve():
    """Solves the puzzle.

    Alg:
    Call the 1st piece in PIECES the Gold piece.
    Find a solution using Gold and 5 other pieces.
    When you find it, check for a solution using the remaining 6 pieces.
    If so, we win. if not, try another 5-piece-and-Gold combo.

    This approach, as apposed to trying every 12-choose-6 combo and then
    checking the other 6 pieces, prevents us from doing double work.  E.g.
    if we checked piece 1-6 and found no solution, we would stupidly try
    7-12 later anyway.  (An alternate approach: when we find no solution to
    1-6, mark 7-12 as toast as well, and always check the toast tables before
    starting a given combo.)
    """
    # Don't let us cheat with an optimal ordering
    import random
    random.shuffle(PIECES)

    # A pseudo-Move that is an empty board of the right dimensions.
    initialBoard = Move(PIECES[0], mask=0)

    gold = PIECES[0] # see comments above for name explanation
    from itertools import combinations
    ways_to_join_gold = combinations(PIECES[1:], 5)
    for option in ways_to_join_gold:
        option = list(option) + [gold]
        debug_names = ', '.join(p.name for p in option)
        soln = solveRecursive(initialBoard, [], 6, option)
        if soln is not None:
            print "Solved board 1: %s..." % debug_names,
            soln2 = solveRecursive(initialBoard, [], 6,
                    [p for p in PIECES if p not in option])
            if soln2 is not None:
                print "and solved board 2."
                print
                print "Board 1:"
                print soln
                print "Board 2:"
                print soln2
                print
                print
                print
            else:
                print "but no solution otherwise."
        else:
            print "No solution for: %s" % debug_names

    #solveWithFixedPieces(box, PIECES[:6]) # random 6 pieces... good luck!


def solveRecursive(board, moves, n, unused_pieces):
    """
    Given a |board| layout and a set of |moves| that have been made,
    find a way to place |n| Pieces from |unused_pieces| on the board.
    Returns None if there is no solution.
    Returns an array of the subsequent Moves needed to place |n|
    Pieces on the board.
    """
    if n <= 0:
        return [] # base case: the board is solved; no further moves required.
    for i, piece in enumerate(unused_pieces):
        for move in piece.moves:
            if move.fits(board):
                soln = solveRecursive(
                        board.combined(move),
                        moves + [move],
                        n-1,
                        # Try the pieces we haven't already exhausted or used
                        # ourselves -- no need to try a piece's moves twice.
                        unused_pieces[i+1:])
                if soln is not None:
                    return [move] + soln
    return None


def solveWithFixedPieces(box, pieces):
    """Find a solution given a specific set of Pieces."""
    # NB: After writing the recursive solution above, I stopped maintaining
    # this function, so it may not work.
    options = [
            # The root option is a blank board.
            [ (Move(pieces[0], mask=0), []) ]
            ]
    for piece in pieces:
        print "Adding piece %s" % piece.name
        thisPiecesOptions = []
        for move in piece.moves:
            for stage, trail in options[-1]:
                # this is breadth-first search
                if move.fits(stage):
                    newOption = (move.combined(stage), trail + [move])
                    thisPiecesOptions.append(newOption)
        options.append(thisPiecesOptions)
    print "%d winners!" % len(options[-1])
    stage, trail = options[-1][0]
    print stage
    print trail


def main():
    solve()


def test():
    b = Box()
    x = Piece('cross', b, [' | ', '---', ' | '])
    for move in x.moves:
        print move


if __name__ == '__main__':
    main()
