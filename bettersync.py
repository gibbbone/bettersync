from __future__ import unicode_literals
import subprocess
import csv
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer
from prompt_toolkit.styles import Style
from prompt_toolkit import print_formatted_text, HTML, ANSI
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory #Suggestion, ThreadedAutoSuggest 
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from db import (
    DEFAULT_PATH,
    DEFAULT_START_FILE,
    db_connect,
    reset_dataset,
    create_tables,
    create_path,
    create_command,
    get_path_id,
    create_rsync_record,
    get_source_paths,
    get_target_paths,
)
from prompt_elements import radiolist_dialog

def bottom_toolbar():
    s1 = '<b><style bg="ansired">Ctrl-H</style></b>: history mode.'
    s2 = '<b><style bg="ansired">Ctrl-C</style></b>: reset application.'
    return HTML(" ".join([s1,s2]))

def details_toolbar(source_fold='', target_fold=''):
    s1 = '<b><style bg="ansired">Source</style></b>: {}'.format(source_fold)
    s2 = '<b><style bg="ansired">Target</style></b>: {}'.format(target_fold)
    return HTML("\n".join([s1,s2]))

def initialize_database():
    # create database if it does not exist
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    if len(cur.fetchall()) == 0:
        print("(Initial config): Database is empty. Initializing..")
        create_tables(con)
        if os.path.exists(DEFAULT_START_FILE):
            print(
                "(Initial config): Database populated from file:\n{}".format(DEFAULT_START_FILE))                
            with open(DEFAULT_START_FILE, 'r') as path_file:
                my_paths = [tuple(row) for row in csv.reader(path_file, skipinitialspace=True)]        
            con = db_connect()
            for p1,p2 in my_paths:
                create_rsync_record(con, p1, p2)        
        else:
            print("(Initial config): Starting file not found. Database intialized with empty tables.")  
        return
    else:
        return  

def get_command(dry, source, target):
    """Obtain command string and print informative lines"""
    dry_flag = 'DRY' if dry else 'NOT DRY'
    dry_string = 'n' if dry else ''
    text = "rsync -avucP{} {} {}".format(dry_string, source,target)    
    print_formatted_text(FormattedText(
        [('#ff0066', dry_flag)]))
    print_formatted_text(FormattedText(
        [('#ff0066', 'You entered:{}'.format(text))]))
    print_formatted_text(FormattedText(
        [('#ff0066','Running...')]))       
    return text

def execute_command(dry, source, target, session):
    """Send command to subprocess dealing with dry argument recursively"""
    text = get_command(dry, source, target)
    if dry:
        subprocess.call(text, shell=True)    
        go_on = session.prompt(
            '[{:13}]: '.format("Execute? (y/n)"), 
            completer=WordCompleter(
                ['Yes','No','True','False', 'yes', 'no'], 
                ignore_case=True), 
            auto_suggest=AutoSuggestFromHistory())      
        go_on = True if go_on.lower() in ['y','yes','true'] else False    
        if go_on:            
            execute_command(False, source, target, session)
        else:
            return
    else:
        con = db_connect()
        create_rsync_record(con, source, target)          
        subprocess.call(text, shell=True)    

# bindings = KeyBindings()
# @bindings.add('c-z')
# def _(event):
#     """ Restart the session pressing Ctrl-Z"""
#     event.app.reset()    
#     return 

def main():
    # initialize database if necessary
    initialize_database()    
    # connect to database
    con = db_connect()
    # get completers
    source_completer = FuzzyCompleter(
        WordCompleter(
            get_source_paths(con), 
            ignore_case=True))
    target_completer = FuzzyCompleter(
        WordCompleter(
            get_target_paths(con), 
            ignore_case=True))
    # get history
    history = InMemoryHistory()
    for s in ['Yes','yes','No','no', 'True', 'False']:
        history.append_string(s)
    # define dropdown style
    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })    
    # define session
    session = PromptSession(
        lexer=PygmentsLexer(BashLexer),         
        style=style, 
        bottom_toolbar=bottom_toolbar) 
        #key_bindings=bindings)

    # start session
    while True:
        try:
            source = session.prompt(
                '[Source folder]: ', 
                completer=source_completer)    
            target = session.prompt(
                '[Target folder]: ', 
                completer=target_completer)            
            dry = session.prompt(
                '[{:13}]: '.format("Dry? (y/n)"), 
                completer=WordCompleter(
                    ['Yes','No','True','False', 'yes', 'no'], 
                    ignore_case=True), 
                auto_suggest=AutoSuggestFromHistory())      
            dry = False if dry.lower() in ['n','no','false'] else True               
        except KeyboardInterrupt:
            continue
        except EOFError:
            break # Control-D pressed.
        else:
            execute_command(dry, source, target, session)
            break
    print('GoodBye!')



if __name__ == '__main__':
    main()