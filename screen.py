from dataentry import DataEntryForm
from flashcard import FlashCardForm
from speedtype import SpeedTypeForm

FORM_TYPES = [FlashCardForm, DataEntryForm, SpeedTypeForm]

FLASH_CARD_INDEX = 0
DATA_ENTRY_INDEX = 1
SPEED_TYPE_INDEX = 2

INIT_FORM_INDEX = SPEED_TYPE_INDEX

def init_screens():
    """initialises the screens created using the given form types."""
    global current_form_index
    current_form_index = INIT_FORM_INDEX

    global form_types
    form_types = FORM_TYPES

    global form
    form = form_types[current_form_index]()
    form.gui.show()

def switch_to(form_index):
    global current_form_index
    current_form_index = form_index

    global form
    form.gui.hide()
    form.gui.close()
    form.gui.destroy(True, True)

    form = form_types[current_form_index]()
    form.gui.show()
