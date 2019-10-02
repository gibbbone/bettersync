#!/usr/bin/env python
"""
An example of a BufferControl in a full screen layout that offers auto
completion.

Important is to make sure that there is a `CompletionsMenu` in the layout,
otherwise the completions won't be visible.
"""
from prompt_toolkit.application import Application, get_app, run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts.utils import print_formatted_text
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.filters import is_done, renderer_height_is_known, Condition
from prompt_toolkit.patch_stdout import patch_stdout
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
from prompt_toolkit.formatted_text import (
    FormattedText, 
    to_formatted_text, 
    fragment_list_to_text, 
    HTML, 
    ANSI
)
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
import subprocess
from time import sleep

class FormatText(Processor):
    def apply_transformation(self, transformation_input):        
        fragments = to_formatted_text(HTML(fragment_list_to_text(transformation_input.fragments)))
        return Transformation(fragments)

# styling
style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
    'input-field':'#004400',
    'buffer': '#ff0066',
})    
# get completers
con = db_connect()
source_completer = FuzzyCompleter(
    WordCompleter(
        get_source_paths(con), 
        ignore_case=True))
target_completer = FuzzyCompleter(
    WordCompleter(
        get_target_paths(con), 
        ignore_case=True))



# create input fields
source_field = TextArea(
    height=1, 
    prompt='[Source folder]: ', 
    style='class:input-field', 
    multiline=False, 
    wrap_lines=True, 
    focus_on_click=True,
    completer=source_completer, 
    complete_while_typing=True)

target_field = TextArea(
    height=1, 
    prompt='[Target folder]: ', 
    style='class:input-field', 
    multiline=False, 
    wrap_lines=True,
    focus_on_click=True, 
    completer=target_completer, 
    complete_while_typing=True)

def bottom_toolbar_call():
    s1 = '<b><style bg="ansired">Ctrl-H</style></b>: history mode.'
    s2 = '<b><style bg="ansired">Ctrl-C/Z</style></b>: reset application.'
    return HTML(" ".join([s1,s2]))

bottom_toolbar = ConditionalContainer(
    Window(FormattedTextControl(
                lambda: bottom_toolbar_call,
                style='class:bottom-toolbar.text'),
            style='class:bottom-toolbar',
            dont_extend_height=True,
            height=Dimension(min=1)),
    filter=~is_done & renderer_height_is_known &
            Condition(lambda: bottom_toolbar_call is not None))


dry_field = TextArea(
    height=1, 
    prompt='[{:13}]: '.format("Dry? (y/n)"), 
    style='class:input-field',     
    multiline=False, 
    wrap_lines=True,
    focus_on_click=True,     
    completer=WordCompleter(
        ['Yes','No','True','False', 'yes', 'no'], 
        ignore_case=True), 
    complete_while_typing=True)

def get_command(dry, source, target):
    """Obtain command string and print informative lines"""
    dry_flag = 'DRY' if dry else 'NOT DRY'
    dry_string = 'n' if dry else ''
    text = "rsync -avucP{} {} {}".format(dry_string, source,target)    
    return text, dry_flag

def execute_command(buff):
    """Send command to subprocess dealing with dry argument recursively"""
    dry = False if buff.text.lower() in ['n','no','false'] else True               
    source = source_field.text
    target = target_field.text        
    text, flag = get_command(dry, source, target)    

    def run_script():                         
        subprocess.call(text, shell=True)  
    def print_info():
        print_formatted_text(HTML('<ansired>{} </ansired>'.format(flag)))
        print_formatted_text(HTML('<ansired>{} </ansired>'.format(
            'You entered: {}'.format(text))))
        print_formatted_text(HTML('<ansired>{} </ansired>'.format('Running...')))            
    run_in_terminal(print_info) 

    if dry:        
        run_in_terminal(run_script)                        
        return 
    else:
        con = db_connect()
        create_rsync_record(con, source, target)          
        run_in_terminal(run_script)
        
        app = get_app()
        app.exit()       
        return

dry_field.buffer.accept_handler = execute_command

body = FloatContainer(
    content=HSplit([
        source_field,
        target_field,
        dry_field,
        #buff_window,
        #Window(FormattedTextControl('Press "q" to quit.'), height=1, style='reverse'), 
        bottom_toolbar], 
    height=8),
    floats=[
        Float(xcursor=True,
              ycursor=True,
              content=CompletionsMenu(max_height=12, scroll_offset=1))
    ]
)

# Key bindings
kb = KeyBindings()

@kb.add('q')
@kb.add('c-c')
def _(event):
    " Quit application. "
    event.app.exit()

#kb.add('enter')(focus_next)
kb.add('tab')(focus_next)
kb.add('s-tab')(focus_previous)

# The `Application`
application = Application(
    layout=Layout(body),
    #style=style,
    key_bindings=kb,
    full_screen=False, 
    mouse_support=True)


if __name__ == '__main__':
    with patch_stdout():
        application.run()
    
    print('GoodBye!')
