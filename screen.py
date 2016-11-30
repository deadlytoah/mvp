INIT_FORM_INDEX = 0

def init_screens(form_types):
    """initialises the screens created using the given form types."""
    global forms
    forms = [form_type() for form_type in form_types]

    global current_form_index
    current_form_index = INIT_FORM_INDEX
    forms[current_form_index].gui.show()

def _switch_to_screen(form_index):
    global current_form_index
    forms[current_form_index].gui.hide()
    current_form_index = form_index
    forms[current_form_index].gui.show()

def toggle_screen():
    """toggle between current and last screen...  But since I know there
are only two screens I'm gonna take a short cut."""
    _switch_to_screen(1 - current_form_index)
