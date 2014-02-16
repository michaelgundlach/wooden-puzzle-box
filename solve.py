class Box(object):
    def __init__(self):
        self.x = 6
        self.y = 5
        self._bits = self.x * self.y

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

    def overlaps(self, move2):
        return self.mask & move2.mask

    def combined(self, move2):
        return Move(self.piece, mask=self.mask | move2.mask)

    def __str__(self):
        return str(self.toAsciiShape(char='.'))

    def toAsciiShape(self, char='.'):
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

    def __hash__(self):
        return self.mask
    def __eq__(self, other):
        return hash(self) == hash(other)

class Piece(object):
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
        [Move(mask=0b 000010 000111 000010 000010 000000),
         # plus every other way that you could put the cross in the
         # box, flipping or rotating or translating it
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
        width = len(self.art[0])
        border = "+%s+" % ('-' * width)
        result = ['\n', border]
        result.extend('|%s|' % word for word in self.art)
        result.extend([border, '\n'])
        return '\n'.join(result)

    def __repr__(self):
        return '\n%s\n' % str(self)

def solve():
    box = Box()
    pieces = [
            Piece("plus", box, [' | ', '-|-', ' | ']),
            Piece("u", box, ['---', '| |']),
            Piece("q", box, ['++', '++', ' |']),
            Piece("r", box, [' | ', '-+-', '  |']),
            Piece("L", box, ['|  ', '|  ', '+--']),
            Piece("z", box, ['--- ', '  |-']),
            ]
    solveWithFixedPieces(box, pieces)

def solveWithFixedPieces(box, pieces):
    """Find a solution given a specific set of Pieces."""
    # Options starts with every way the first piece can go in.
    options = [
        [ (m, [m]) for m in pieces[0].moves ]
    ]
    print options[0][0][0]
    for piece in pieces[1:]:
        print "Adding piece %s" % piece.name
        thisPiecesOptions = []
        for move in piece.moves:
            for stage, trail in options[-1]:
                # TODO: depth-first rather than breadth-first search!
                if not move.overlaps(stage):
                    newOption = (move.combined(stage), trail + [move])
                    thisPiecesOptions.append(newOption)
        options.append(thisPiecesOptions)
        if len(options) == len(pieces):
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