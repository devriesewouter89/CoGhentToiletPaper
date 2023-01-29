import random
from enum import Enum
from time import sleep


class PLACEMENT(Enum):
    NOT_FAR = 0
    CORRECT = 1
    TOO_FAR = 2


def sheet_placement():
    # TODO PLACEHOLDER FUNCTION
    sleep(1)
    result = PLACEMENT(random.randint(0, 1)) # let's skip TOO_FAR for the test, it's confusing
    return result
