#!/usr/bin/env python3
from prompt_toolkit.patch_stdout import patch_stdout
from bettersync import BetteRsync

if __name__ == '__main__':
    bettersync = BetteRsync()
    with patch_stdout():
        bettersync.app.run()
    
    print('GoodBye!')