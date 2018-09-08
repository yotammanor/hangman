#!/usr/local/bin/python3


# A simple implementation of Hangman.
# On game, see: https://en.wikipedia.org/wiki/Hangman_(game)
# Created by Yotam Manor.
# Words extracted from: https://www.hangmanwords.com/words, 2018/06/06

import curses
import random
import string
from abc import (
    ABCMeta,
    abstractmethod,
)

DEFAULT_MAX_TRIES = 10


def main():
    board = initialize_board()
    play_game(board)


def initialize_board():
    try:
        board = BoardGame(TerminalPainterBoardGameView)
    except curses.error:
        print('Failed to load Advanced display, using fallback '
              'simplified display')
        # I started with the simple console view, and then added the prettier
        # one above. The following will load as a backup if it the former fails
        # on initialization. Feel free to make it fail to see the older
        # functionality.
        #
        # Either way, the goal was to practice the Open/Closed Principle, so
        # that's why there are two views for the same game.
        board = BoardGame(SimpleConsoleBoardGameView)
    return board


def play_game(board):
    try:
        board.play_game()
    except AttributeError as e:
        # This will make sure that curses library cleans up if it failed
        # badly mid-game. This may happen if your console gets shrunk
        # mid-game.
        #
        # This is not the cleanest of solutions, but a compromise under a
        # tight schedule.
        #
        TerminalPainterBoardGameView.cleanup_screen_display()
        print(e)


class BoardGame(object):
    REQUEST_USER_INPUT_MSG = 'Please Guess a character: '
    EMPTY_INPUT_MSG = 'You must insert a character to continue!'
    MULTI_CHAR_INPUT_MSG = 'Please insert one character only!'
    ALREADY_GUESSED_MSG = '{character} was already guessed!'
    INVALID_INPUT_MSG = '{character} is an invalid option!'

    def __init__(self, view_class):
        self.view = view_class(self)
        self.word = Word(word=WordPool().randomize_word(),
                         view_class=self.view.word_view_class)
        self.man = Man(view_class=self.view.man_view_class)
        self.character_pool = CharacterPool(
            view_class=self.view.character_pool_view_class)

    def play_game(self):
        while not (self.is_game_lost or self.is_game_won):
            self.play_round()
        self.end_the_game()

    @property
    def is_game_won(self):
        return self.word.is_guessed

    @property
    def is_game_lost(self):
        return self.man.is_hanged

    def end_the_game(self):
        if self.is_game_lost:
            self.word.reveal()
        self.display_end_of_game()

    def play_round(self):
        self.display_board_game()
        guess = self.get_valid_guess()
        is_guessed_correctly = self.word.guess_character(guess)
        if not is_guessed_correctly:
            self.man.bring_closer_to_hanging()
        self.character_pool.use_character(guess)

    def get_valid_guess(self):
        is_valid_guess = False
        while not is_valid_guess:
            round_guess = self.get_user_input()
            is_valid_guess = self.validate_input(round_guess)
        return round_guess

    def get_user_input(self):
        raw_input = self.get_raw_input(self.REQUEST_USER_INPUT_MSG)
        return self.character_pool.normalize_character(raw_input)

    def get_raw_input(self, msg):
        return self.view.get_raw_input(msg)

    def display_board_game(self):
        return self.view.display_board_game()

    def display_end_of_game(self):
        return self.view.display_end_of_game()

    def display_message(self, msg):
        return self.view.display_message(msg)

    def validate_input(self, round_guess):
        valid_guess = False
        if self._valid_guess(round_guess):
            valid_guess = True
        elif self._empty_input(round_guess):
            self.display_message(self.EMPTY_INPUT_MSG)
        elif self._multi_character_input(round_guess):
            self.display_message(self.MULTI_CHAR_INPUT_MSG)
        elif self._character_already_guessed(round_guess):
            self.display_message(self.ALREADY_GUESSED_MSG.format(
                character=round_guess))
        else:
            self.display_message(self.INVALID_INPUT_MSG.format(
                character=round_guess))
        return valid_guess

    def _valid_guess(self, round_guess):
        return round_guess in self.character_pool.unused_characters

    def _character_already_guessed(self, round_guess):
        return round_guess in self.character_pool.used_characters

    @staticmethod
    def _multi_character_input(round_guess):
        return len(round_guess) > 1

    @staticmethod
    def _empty_input(round_guess):
        return not round_guess


class Man(object):
    def __init__(self, view_class, tries=DEFAULT_MAX_TRIES):
        self.view = view_class(self)
        self.tries = tries

    def __repr__(self):
        return self.view.__repr__()

    @property
    def is_hanged(self):
        return not self.tries

    def bring_closer_to_hanging(self):
        self.tries -= 1


class Word(object):
    def __init__(self, word, view_class):
        self.view = view_class(self)
        self._plain_word = word.upper()
        self._characters_in_word = set(self._plain_word)
        self._guessed_characters = set()

    def __repr__(self):
        return self.view.__repr__()

    @property
    def current_guessed_state(self):
        return [c if c in self._guessed_characters else '_'
                for c in self._plain_word]

    @property
    def is_guessed(self):
        return self._guessed_characters == self._characters_in_word

    def reveal(self):
        self._guessed_characters = self._characters_in_word

    def guess_character(self, char):
        if self._is_character_in_word(char):
            self._guessed_characters.add(char)
            return True
        return False

    def _is_character_in_word(self, char):
        return char in self._characters_in_word


class CharacterPool(object):
    def __init__(self, view_class):
        self.view = view_class(self)
        self.unused_characters = set(string.ascii_uppercase)
        self.used_characters = set()

    def __repr__(self):
        return self.view.__repr__()

    def use_character(self, char):
        self.used_characters.add(char)
        self.unused_characters.remove(char)

    @staticmethod
    def normalize_character(char):
        return str(char).strip().upper()


class WordPool(object):
    POOL_OF_WORDS = [
        # Source: https://www.hangmanwords.com/words, extracted 2018/06/06
        'abruptly', 'absurd', 'abyss', 'affix', 'askew', 'avenue', 'awkward',
        'axiom', 'azure', 'bagpipes', 'bandwagon', 'banjo', 'bayou',
        'beekeeper', 'bikini', 'blitz', 'blizzard', 'boggle', 'bookworm',
        'boxcar', 'boxful', 'buckaroo', 'buffalo', 'buffoon', 'buxom',
        'buzzard', 'buzzing', 'buzzwords', 'caliph', 'cobweb', 'cockiness',
        'croquet', 'crypt', 'curacao', 'cycle', 'daiquiri', 'dirndl',
        'disavow', 'dizzying', 'duplex', 'dwarves', 'embezzle', 'equip',
        'espionage', 'euouae', 'exodus', 'faking', 'fishhook', 'fixable',
        'fjord', 'flapjack', 'flopping', 'fluffiness', 'flyby', 'foxglove',
        'frazzled', 'frizzled', 'fuchsia', 'funny', 'gabby', 'galaxy',
        'galvanize', 'gazebo', 'giaour', 'gizmo', 'glowworm', 'glyph',
        'gnarly', 'gnostic', 'gossip', 'grogginess', 'haiku', 'haphazard',
        'hyphen', 'iatrogenic', 'icebox', 'injury', 'ivory', 'ivy', 'jackpot',
        'jaundice', 'jawbreaker', 'jaywalk', 'jazziest', 'jazzy', 'jelly',
        'jigsaw', 'jinx', 'jiujitsu', 'jockey', 'jogging', 'joking', 'jovial',
        'joyful', 'juicy', 'jukebox', 'jumbo', 'kayak', 'kazoo', 'keyhole',
        'khaki', 'kilobyte', 'kiosk', 'kitsch', 'kiwifruit', 'klutz',
        'knapsack', 'larynx', 'lengths', 'lucky', 'luxury', 'lymph', 'marquis',
        'matrix', 'megahertz', 'microwave', 'mnemonic', 'mystify', 'naphtha',
        'nightclub', 'nowadays', 'numbskull', 'nymph', 'onyx', 'ovary',
        'oxidize', 'oxygen', 'pajama', 'peekaboo', 'phlegm', 'pixel', 'pizazz',
        'pneumonia', 'polka', 'pshaw', 'psyche', 'puppy', 'puzzling', 'quartz',
        'queue', 'quips', 'quixotic', 'quiz', 'quizzes', 'quorum',
        'razzmatazz', 'rhubarb', 'rhythm', 'rickshaw', 'schnapps', 'scratch',
        'shiv', 'snazzy', 'sphinx', 'spritz', 'squawk', 'staff', 'strength',
        'strengths', 'stretch', 'stronghold', 'stymied', 'subway', 'swivel',
        'syndrome', 'thriftless', 'thumbscrew', 'topaz', 'transcript',
        'transgress', 'transplant', 'triphthong', 'twelfth', 'twelfths',
        'unknown', 'unworthy', 'unzip', 'uptown', 'vaporize', 'vixen', 'vodka',
        'voodoo', 'vortex', 'voyeurism', 'walkway', 'waltz', 'wave', 'wavy',
        'waxy', 'wellspring', 'wheezy', 'whiskey', 'whizzing', 'whomever',
        'wimpy', 'witchcraft', 'wizard', 'woozy', 'wristwatch', 'wyvern',
        'xylophone', 'yachtsman', 'yippee', 'yoked', 'youthful', 'yummy',
        'zephyr', 'zigzag', 'zigzagging', 'zilch', 'zipper', 'zodiac',
        'zombie'
    ]

    def randomize_word(self):
        return random.choice(self.POOL_OF_WORDS)


# Views

class WordView(object):
    def __init__(self, word):
        self.word = word

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ' '.join(self.word.current_guessed_state)


class CharacterPoolView(object):
    def __init__(self, character_pool):
        self.character_pool = character_pool

    def __repr__(self):
        if not self.character_pool.used_characters:
            return ''
        return (
            f'Used: {" ".join(sorted(self.character_pool.used_characters))}')


class BaseManView(object):
    __metaclass__ = ABCMeta

    def __init__(self, man):
        self.man = man

    @abstractmethod
    def __repr__(self):
        pass


class NaiveManView(BaseManView):
    def __repr__(self):
        return f'Tries Left: {self.man.tries}'


class ASCIIArtManView(BaseManView):

    def __repr__(self):
        return self.ART_DICT.get(self.man.tries, '')

    ART_DICT = {
        0: '''
     -------     
    |       |     
    |       @
    |      /|\\
    |       |  
    |      / \\
    | 
[——-----]
''',
        1: '''
     -------     
    |       |     
    |       @
    |      /|\\
    |       |  
    |      / 
    | 
[——-----]
''',
        2: '''
     -------     
    |       |     
    |       @
    |      /|\\
    |       |  
    |        
    | 
[——-----]
''',
        3: '''
     -------     
    |       |     
    |       @
    |      /|
    |       |  
    |        
    | 
[——-----]
''',
        4: '''
     -------     
    |       |     
    |       @
    |       |
    |       |  
    |        
    | 
[——-----]
''',
        5: '''
     -------     
    |       |     
    |       @
    |
    |         
    |        
    | 
[——-----]
''',
        6: '''
     -------     
    |       |     
    |
    |
    |         
    |        
    | 
[——-----]
''',
        7: '''
     -------     
    |            
    |
    |
    |         
    |        
    | 
[——-----]
''',
        8: '''  

    |           
    |         
    |
    |
    |        
    | 
[——-----]
''',
        9: '''




    |   
    |    
    |            
[——-----]''',
        10: '''







[——-----]
''',
    }


class BaseBoardGameView(object):
    word_view_class = WordView
    character_pool_view_class = CharacterPoolView
    YOU_WON_MSG = 'You Won!'
    YOU_LOST_MSG = 'You lost :('
    REVEALED_WORD_MSG = 'Word was: {word}'

    __metaclass__ = ABCMeta

    def __init__(self, board_game):
        self.board_game = board_game

    @abstractmethod
    def display_board_game(self):
        pass

    @abstractmethod
    def display_end_of_game(self):
        pass

    @abstractmethod
    def display_message(self, msg):
        pass

    @abstractmethod
    def get_raw_input(self, msg):
        pass


class SimpleConsoleBoardGameView(BaseBoardGameView):
    character_pool_view_class = CharacterPoolView

    def display_board_game(self):
        print(self.board_game.word)
        print(self.board_game.man)
        print(self.board_game.character_pool)

    def display_end_of_game(self):
        if self.board_game.is_game_won:
            print(f'{self.board_game.word}')
            print(self.YOU_WON_MSG)
        if self.board_game.is_game_lost:
            print(self.YOU_LOST_MSG)
            print(self.REVEALED_WORD_MSG.format(
                word=self.board_game.word.__repr__()))

    def display_message(self, msg):
        print(msg)

    def get_raw_input(self, msg):
        raw_input = input(msg)
        return raw_input


class TerminalPainterBoardGameView(BaseBoardGameView):
    man_view_class = ASCIIArtManView

    EXIT_MSG = 'Press any key to exit.'
    SCREEN_TOO_SMALL_MSG = ('Bad terminal height, please resize it '
                            'to be at least '
                            '{min_size} lines.')

    TITLE_LINE = 0
    SUBTITLE_LINE = TITLE_LINE + 2
    WORD_LINE = 1
    CHARACTER_POOL_LINE = 3
    INPUT_LINE = 5
    MESSAGE_LINE = 6
    DRAWING_LINE = 7

    def __init__(self, board_game):
        super().__init__(board_game)
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

    def __del__(self):
        try:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
        except curses.error:
            pass
        self.cleanup_screen_display()

    def display_board_game(self):
        self._validate_display()
        self.stdscr.clear()
        self.stdscr.addstr(self.WORD_LINE, 0,
                           self.board_game.word.__repr__())
        self.stdscr.addstr(self.DRAWING_LINE, 0,
                           self.board_game.man.__repr__())
        self.stdscr.addstr(self.CHARACTER_POOL_LINE, 0,
                           self.board_game.character_pool.__repr__())
        self.stdscr.refresh()

    def display_end_of_game(self):
        if self.board_game.is_game_won:
            self.stdscr.clear()
            self.stdscr.addstr(self.TITLE_LINE, 0, self.YOU_WON_MSG)
            self.stdscr.addstr(self.WORD_LINE, 0,
                               self.board_game.word.__repr__())
        if self.board_game.is_game_lost:
            self.stdscr.clear()
            self.stdscr.addstr(self.TITLE_LINE, 0, self.YOU_LOST_MSG)
            self.stdscr.addstr(self.SUBTITLE_LINE, 0,
                               self.REVEALED_WORD_MSG.format(
                                   word=self.board_game.word.__repr__()))
            self.stdscr.addstr(self.DRAWING_LINE, 0,
                               self.board_game.man.__repr__())
        self.stdscr.addstr(self.MESSAGE_LINE, 0, self.EXIT_MSG)
        self.stdscr.getkey()

    def display_message(self, msg):
        self.stdscr.addstr(self.MESSAGE_LINE, 0, msg)

    def get_raw_input(self, msg):
        self.stdscr.addstr(self.INPUT_LINE, 0, msg)
        raw_input = self.stdscr.getkey()
        return raw_input

    def _validate_display(self):
        if curses.LINES < self._min_screen_size:
            raise AttributeError(
                self.SCREEN_TOO_SMALL_MSG.format(
                    min_size=self._min_screen_size))

    @classmethod
    def cleanup_screen_display(cls):
        curses.endwin()

    @property
    def _min_screen_size(self):
        drawing_height = len(self.board_game.man.__repr__().splitlines())
        return self.DRAWING_LINE + drawing_height


if __name__ == '__main__':
    main()
