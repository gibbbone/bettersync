#!/usr/bin/env python
"""
An example of a BufferControl in a full screen layout that offers auto
completion.

Important is to make sure that there is a `CompletionsMenu` in the layout,
otherwise the completions won't be visible.
"""
from prompt_toolkit.application import Application, get_app, run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts.utils import print_formatted_text
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.completion.fuzzy_completer import FuzzyCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.filters import is_done, renderer_height_is_known, Condition
from prompt_toolkit.layout import (
    Float,
    ConditionalContainer,
    FloatContainer,
    HSplit,
    Window,
    BufferControl,
    FormattedTextControl,
    Layout,
    Dimension,
    CompletionsMenu, 
)
from .db import (
    db_connect, 
    initialize_database,
    create_rsync_record,
    get_source_paths,
    get_target_paths,
)
from .utilities import FormatText, make_text_area
import subprocess

class BetteRsync:
    def __init__(self):
        # styling
        style = Style.from_dict({
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'scrollbar.background': 'bg:#88aaaa',
            'scrollbar.button': 'bg:#222222',
            'input-field':'#004400',
            'buffer': '#ff0066',
        })    

        # create input fields
        self.source_field = make_text_area('[Source folder]: ')
        self.target_field = make_text_area('[Target folder]: ')
        self.dry_field = make_text_area('[{:13}]: '.format("Dry? (y/n)"))

        # get completers
        initialize_database()
        con = db_connect()   
            
        self.source_field.completer = FuzzyCompleter(
            WordCompleter(
                get_source_paths(con), 
                ignore_case=True))
        self.target_field.completer = FuzzyCompleter(
            WordCompleter(
                get_target_paths(con), 
                ignore_case=True))
        self.dry_field.completer = WordCompleter(
            ['Yes','No','True','False', 'yes', 'no'], 
            ignore_case=True)

        # bottom toolbar
        def bottom_toolbar_call():
            s1 = '<b><style bg="ansired">C-H</style></b>: history mode.'
            s2 = '<b><style bg="ansired">C-C/C-Q</style></b>: exit app.'
            s3 = '<b><style bg="ansired">C-O</style></b>: ordered paths.'
            s4 = '<b><style bg="ansired">C-R</style></b>: reverse paths.'
            return HTML(" ".join([s1,s2, s3, s4]))  
                  
        self.bottom_toolbar = ConditionalContainer(
            Window(
                FormattedTextControl(
                    lambda: bottom_toolbar_call,
                    style='class:bottom-toolbar.text'),
                style='class:bottom-toolbar',
                dont_extend_height=True,
                height=Dimension(min=1)),
            filter=(~is_done & renderer_height_is_known & Condition(lambda: bottom_toolbar_call is not None)))             

        # create app body
        self.body = FloatContainer(
            content=HSplit(
                children=[
                    self.source_field,
                    self.target_field,
                    self.dry_field,
                    self.bottom_toolbar], 
                height=8),
            floats=[Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=12, scroll_offset=1))])

        # define internal logic
        def execute_command(buff):
            """Send command to subprocess dealing with dry argument recursively"""
            dry = False if buff.text.lower() in ['n','no','false'] else True                     
            dry_flag = 'DRY' if dry else 'NOT DRY'
            dry_string = 'n' if dry else ''
            command = "rsync -avucP{} {} {}".format(
                dry_string,
                self.source_field.text,
                self.target_field.text)    

            def run_script():                         
                subprocess.call(command, shell=True)  
            def print_info():
                print_formatted_text(HTML('<ansired>{} </ansired>'.format(dry_flag)))
                print_formatted_text(HTML('<ansired>{} </ansired>'.format(
                    'You entered: {}'.format(command))))
                print_formatted_text(HTML('<ansired>{} </ansired>'.format('Running...')))            
            run_in_terminal(print_info) 

            if dry:        
                run_in_terminal(run_script)                        
                return 
            else:
                con = db_connect()
                create_rsync_record(
                    con, 
                    self.source_field.text,
                    self.target_field.text)    
                run_in_terminal(run_script)
                
                app = get_app()
                app.exit()       
                return

        self.dry_field.buffer.accept_handler = execute_command

        # Key bindings
        self.kb = KeyBindings()

        @self.kb.add('c-q')
        @self.kb.add('c-c')
        def _(event):
            " Quit application. "
            event.app.exit()

        #kb.add('enter')(focus_next)
        self.kb.add('tab')(focus_next)
        self.kb.add('s-tab')(focus_previous)

        # The `Application`
        self.app = Application(
            layout=Layout(self.body),
            #style=style,
            key_bindings=self.kb,
            full_screen=False, 
            mouse_support=True)

        
