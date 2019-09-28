from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import RadioList, Label
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import HSplit

class RadioListFast(RadioList):
    """
    List of radio buttons. Only one can be checked at the same time.

    :param values: List of (value, label) tuples.
    """
    def __init__(self, values):
        # Initialize
        super().__init__(values)             
        
        # Remove the 'enter' key binding behaviour
        kb = self.control.key_bindings
        kb.remove('enter')
        kb.remove(' ')
        
        # Remove faulty Keys.Any behaviour
        kb.remove(Keys.Any)

        # Rewrite the 'enter' key binding behaviour
        @kb.add('enter')
        @kb.add(' ')
        def _(event):
            self.current_value = self.values[self._selected_index][0]
            # New
            event.app.exit(result=self.current_value) 
        

def radiolist_dialog(title='', values=None, style=None, async_=False):
    # Add exit key binding.
    bindings = KeyBindings()
    @bindings.add('c-d')
    def exit_(event):
        """
        Pressing Ctrl-d will exit the user interface.
        """
        event.app.exit()    
    
    radio_list = RadioListFast(values)        
    application = Application(
        layout=Layout(HSplit([ Label(title), radio_list])),
        key_bindings=merge_key_bindings(
            [load_key_bindings(), bindings]),
        mouse_support=True,
        style=style,        
        full_screen=False)

    if async_:
        return application.run_async()
    else:
        return application.run()         
