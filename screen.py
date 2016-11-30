INIT_FORM_INDEX = 0

def init_screens(all_form_types):
    """initialises the screens created using the given form types."""
    global current_form_index
    current_form_index = INIT_FORM_INDEX

    global form_types
    form_types = all_form_types

    global form
    form = form_types[current_form_index]()
    form.gui.show()

def _switch_to_screen(form_index):
    global current_form_index
    current_form_index = form_index

    global form
    form.gui.hide()
    form.gui.close()
    form.gui.deleteLater()
    form.close()
    form.deleteLater()

    form = form_types[current_form_index]()
    form.gui.show()

def toggle_screen():
    """toggle between current and last screen...  But since I know there
are only two screens I'm gonna take a short cut."""
    _switch_to_screen(1 - current_form_index)
