##############################################################################
# game.py - Responsible for generating moves to give to client.py            #
# Moves via stdout in the form of "# # # #" (block index, # rotations, x, y) #
# Important function is find_move, which should contain the main AI          #
##############################################################################

import sys
import json
import copy

# Simple point class that supports equality, addition, and rotations
class Point:
    x = 0
    y = 0

    # Can be instantiated as either Point(x, y) or Point({'x': x, 'y': y})
    def __init__(self, x=0, y=0):
        if isinstance(x, dict):
            self.x = x['x']
            self.y = x['y']
        else:
            self.x = x
            self.y = y

    def __add__(self, point):
        return Point(self.x + point.x, self.y + point.y)

    def __eq__(self, point):
        return self.x == point.x and self.y == point.y

    def __repr__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    # rotates 90deg counterclockwise
    def rotate(self, num_rotations):
        if num_rotations == 1: return Point(-self.y, self.x)
        if num_rotations == 2: return Point(-self.x, -self.y)
        if num_rotations == 3: return Point(self.y, -self.x)
        return self

    def distance(self, point):
        return abs(point.x - self.x) + abs(point.y - self.y)

class Game:
    blocks = []
    grid = []
    bonus_squares = []
    my_number = -1
    dimension = -1 # Board is assumed to be square
    turn = -1

    def __init__(self, args):
        self.interpret_data(args)
        self.turnCount = -1
        self.lastCorner = Point(0,0)

    # find_move is your place to start. When it's your turn,
    # find_move will be called and you must return where to go.
    # You must return a tuple (block index, # rotations, x, y)
    def find_move(self):
        self.turnCount += 1 # Our current turn count, starting from 0th
        openingMovesList = [0, 1, 2] # Indexes of pieces for intial moves
        numOfOpeningTurns = len(openingMovesList)
        moves = []
        N = self.dimension

        if self.turnCount < numOfOpeningTurns:
            block = self.blocks[self.turnCount]
            index = self.turnCount
            for i in range(self.lastCorner.x*N + self.lastCorner.y, N * N):
                    x = i / N
                    y = i % N

                    for rotations in range(0, 4):
                        new_block = self.rotate_block(block, rotations)
                        if self.can_place(new_block, Point(x, y), True):
                            cornerOff = self.block_corner(new_block, (1,1))
                            self.lastCorner = self.lastCorner + cornerOff
                            return (index, rotations, x, y)
        else:
            for index, block in enumerate(self.blocks):
                for i in range(0, N * N):
                    x = i / N
                    y = i % N

                    for rotations in range(0, 4):
                        new_block = self.rotate_block(block, rotations)
                        if (self.can_place(new_block, Point(x, y), True)):
                            move = index, rotations, x, y
                            moves.append(move)

            if len(moves) == 0:
                return (0, 0, 0, 0)
            else:
                return self.best_move(moves)

    # Checks if a block can be placed at the given point
    # modified: going to use this to check "value" of a move as well
    def can_place(self, block, point, me):
        onAbsCorner = False
        onRelCorner = False
        N = self.dimension - 1
        if me:
            nums = [self.my_number]
        else:
            nums = [0,1,2,3]
            nums.remove(self.my_number)

        corners = [Point(0, 0), Point(N, 0), Point(N, N), Point(0, N)]
        corner = corners[self.my_number]

        for offset in block:
            p = point + offset
            x = p.x
            y = p.y
            if (x > N or x < 0 or y > N or y < 0 or self.grid[x][y] != -1 or
                (x > 0 and self.grid[x - 1][y] in nums) or
                (y > 0 and self.grid[x][y - 1] in nums) or
                (x < N and self.grid[x + 1][y] in nums) or
                (y < N and self.grid[x][y + 1] in nums)
            ): return False

            onAbsCorner = onAbsCorner or (p == corner)
            onRelCorner = onRelCorner or (
                (x > 0 and y > 0 and self.grid[x - 1][y - 1] in nums) or
                (x > 0 and y < N and self.grid[x - 1][y + 1] in nums) or
                (x < N and y > 0 and self.grid[x + 1][y - 1] in nums) or
                (x < N and y < N and self.grid[x + 1][y + 1] in nums)
            )

        if self.grid[corner.x][corner.y] < 0 and not onAbsCorner: return False
        if not onAbsCorner and not onRelCorner: return False

        return True

    def best_move(self, moves):
        max_score = -100000000
        max_move = None
        for move in moves:
            score = self.move_score(move)
            if max_score < score:
                max_score = score
                max_move = move
        return max_move

    def pieceArea(self,piece):
        #should return area of a piece
        return len(piece)

    def remainingPiecesArea(self,piece_index):
        #returns total area of a list of pieces
        area = 0
        for i in xrange(len(self.blocks)):
            if i == piece_index: continue
            piece = self.blocks[i]
            area += self.pieceArea(piece)
        return area

    def move_score(self,move):
        # move = index, rotations, x, y
        old_grid = copy.deepcopy(self.grid)
        self.make_move(move)
        areaWeight = -1
        score = areaWeight*self.remainingPiecesArea(move[0])
        blockCornerWeight = 1
        block_corner_score = self.block_corner_score(move)
        score += blockCornerWeight*block_corner_score
        debug("YOUR CORNER SCORE")
        debug(block_corner_score)
        createCornerWeight = 1
        create_corner_score = self.create_corner_score(move)
        score += createCornerWeight*create_corner_score
        debug("MY CORNER SCORE")
        debug(create_corner_score)
        dogeCoinWeight = 1
        score += dogeCoinWeight*self.dogecoin_score(move)
        self.grid = old_grid
        return score

    def block_corner_score(self,move):
        score = self.count_corners(False)
        return score

    def create_corner_score(self,move):
        score = self.count_corners(True)
        return score

    def dogecoin_score(self,move):
        return 0

    def count_corners(self, me):
        N = self.dimension
        block = [Point(0,0)]
        result = 0
        for i in range(0, N * N):
            x = i / N
            y = i % N
            if (self.can_place(block, Point(x, y), me)):
                result += 1
        return result

    def make_move(self,move):
        # move = index, rotations, x, y
        point = Point(move[2], move[3])
        rotated_block = self.rotate_block(self.blocks[move[0]], move[1])
        for offset in rotated_block:
            p = point + offset
            x = p.x
            y = p.y
            self.grid[x][y] = self.my_number
        return

    def undo_move(self,move):
        return

    # rotates block 90deg counterclockwise
    def rotate_block(self, block, num_rotations):
        return [offset.rotate(num_rotations) for offset in block]

    # returns block corner in direction
    def block_corner(self, block, dir):
        maxPiece = Point(0, 0)
        maxScore = 0
        for piece in block:
            score = dir[0]*piece.x + dir[1]*piece.y
            if score > maxScore:
                maxPiece = piece
                maxScore = score
        return maxPiece + Point(1,1)

    # updates local variables with state from the server
    def interpret_data(self, args):
        if 'error' in args:
            debug('Error: ' + args['error'])
            return

        if 'number' in args:
            self.my_number = args['number']

        if 'board' in args:
            self.dimension = args['board']['dimension']
            self.turn = args['turn']
            self.grid = args['board']['grid']
            self.blocks = args['blocks'][self.my_number]
            self.bonus_squares = args['board']['bonus_squares']

            for index, block in enumerate(self.blocks):
                self.blocks[index] = [Point(offset) for offset in block]

        if (('move' in args) and (args['move'] == 1)):
            send_command(" ".join(str(x) for x in self.find_move()))

    def is_my_turn(self):
        return self.turn == self.my_number

def get_state():
    return json.loads(raw_input())

def send_command(message):
    print message
    sys.stdout.flush()

def debug(message):
    send_command('DEBUG ' + str(message))

def main():
    setup = get_state()
    game = Game(setup)

    while True:
        state = get_state()
        game.interpret_data(state)

if __name__ == "__main__":
    main()
