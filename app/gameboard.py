from app.piece import Piece, LightPiece, DarkPiece
from app.result import Result
COLOR_LIGHT = 'light'
COLOR_DARK = 'dark'

class Gameboard:
    @classmethod
    def build(self, size=9):
        """Builds custom size board."""

        board = self.__generate_board(size)
        return Gameboard(board)

    @classmethod
    def __generate_board(self, size):
        """Generates inital state of the board with pieces."""
        board=[]
        for i in range(9):
             board.append([None]*size)
        return board

    def __init__(self, board, last_move=None):
        self.board = self.__ensure_valid_board(board)
        self.size = len(board)
        self.last_move = last_move

    def move(self, current_position, destination):
        """Moves piece from current position to destination on the board."""

        cur_x = current_position['x']
        cur_y = current_position['y']
        dst_x = destination['x']
        dst_y = destination['y']
        if self.last_move == self.board[cur_y][cur_x].color:
            return Result(False, 'It is not your turn!')
        dst_is_legal_move = self.__is_legal_move(current_position, destination)

        if dst_is_legal_move and type(self.board[dst_y][dst_x]) not in (LightPiece, DarkPiece):
            dst_is_last_row_of_board = dst_y in (0, self.size-1)
            if dst_is_last_row_of_board:
                self.board[cur_y][cur_x].become_king()

            self.last_move = self.board[cur_y][cur_x].color
            self.board[cur_y][cur_x], self.board[dst_y][dst_x] = self.board[dst_y][dst_x], self.board[cur_y][cur_x]

            return Result(True)
        else:
            return Result(False, 'This move is not possible!')

    def __ensure_valid_board(self, board):
        """Ensures that board is a square and pieces are set on the black squares."""

        return board

    def __is_legal_square(self, x, y):
        """Checks if given square is black."""

        return (y % 2 == 0 and x % 2 == 1) or (y % 2 == 1 and x % 2 == 0)

    def __is_legal_move(self, current_position, destination):
        """Checks if given move is possible and then performs it."""

        cur_x = current_position['x']
        cur_y = current_position['y']
        dst_x = destination['x']
        dst_y = destination['y']

        if self.__is_move_within_bounds_of_board(dst_x, dst_y):
            dst_is_white_square = (dst_y % 2 == 0 and dst_x % 2 == 0) or (dst_y % 2 == 1 and dst_x % 2 == 1)
            if dst_is_white_square:
                return False

            piece = self.board[cur_y][cur_x]
            jumping_on_diagonals = abs(dst_x - cur_x) == abs(dst_y - cur_y)

            if dst_x == cur_x-2:
                if piece.color == COLOR_LIGHT and dst_y == cur_y - 2 and type(self.board[cur_y-1][cur_x-1]) is DarkPiece:
                    self.board[cur_y-1][cur_x-1] = None
                    return True
                if piece.color == COLOR_DARK and dst_y == cur_y + 2 and type(self.board[cur_y+1][cur_x-1]) is LightPiece:
                    self.board[cur_y+1][cur_x-1] = None
                    return True
            elif dst_x == cur_x+2:
                if piece.color == COLOR_LIGHT and dst_y == cur_y - 2 and type(self.board[cur_y-1][cur_x+1]) is DarkPiece:
                    self.board[cur_y-1][cur_x+1] = None
                    return True
                if piece.color == COLOR_DARK and dst_y == cur_y + 2 and type(self.board[cur_y+1][cur_x+1]) is LightPiece:
                    self.board[cur_y+1][cur_x+1] = None
                    return True
            elif dst_x in (cur_x-1, cur_x+1):
                if piece.color == COLOR_LIGHT and dst_y == cur_y - 1:
                    return True
                if piece.color == COLOR_DARK and dst_y == cur_y + 1:
                    return True

        return False

    def __is_move_within_bounds_of_board(self, dst_x, dst_y):
        """Checks if given move is within bounds of the board."""

        if dst_x in range(self.size) and dst_y in range(self.size):
            return True
        else:
            return False
