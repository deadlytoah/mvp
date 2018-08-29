import config

class Caret:
    """Models and controls the caret in speedtype widget.

    This model assumes the speedtype widget does not scroll
    horizontally.

    """

    def __init__(self, height, viewport_height, viewport_margin):
        """Initializes the caret."""
        self.charpos = 0

        # Set caret to the first letter of the first sentence.  This
        # is line followed by column.
        self.pos = (0, 0)

        self.visible = True
        self.height = height
        self.width = 1
        self.colour = config.COLOURS['caret']
        self.viewport_height = viewport_height
        self.viewport_margin = viewport_margin
        self.buflen = None

        # marks the caret position in the buffer that triggers the
        # session to end.
        self.eobuf = None

        # The y coordinate of the speedtype widget with respect to the
        # origin of the viewport.
        self.ydelta = 0

    def is_visible(self):
        """Indicates whether the caret is visible."""
        return self.visible and self.charpos < self.eobuf

    def viewport_visible(self):
        """Is the caret wholy visible in the viewport?"""
        y = self.pos[1]
        ybeg = y + self.ydelta
        yend = ybeg + self.height
        return ybeg >= 0 and yend <= self.viewport_height

    def ideal_ydelta(self):
        """Gets the ideal ydelta value to show the caret.

        Ideally this will position the caret at the 1/4 of the
        viewport height from the top.  This will show a bit of the
        previous text and a lot of the upcoming text.

        What is returned is an ideal value, and may not be valid.

        """
        quarter = self.viewport_height / 4
        y = self.pos[1]
        return y - quarter

    def render(self):
        """Provides data for painting the caret."""
        if self.is_visible():
            (x, y) = self.pos
            return {
                'colour': self.colour,
                'pos': (x, y),
                'height': self.height,
                'width': self.width,
            }
        else:
            return None

    def forward(self):
        """Moves caret forward by one letter.

        If the caret is at the end of the text, returns False.
        Otherwise, advances the caret and returns True.

        """
        caret = self.charpos + 1
        if caret >= self.buflen:
            # do not move caret behind buffer
            return False
        else:
            self.charpos = caret

            # is the session ending?
            if self.charpos >= self.eobuf:
                return False
            else:
                return True

    def backward(self):
        """Moves caret backward by one letter.

        If the caret is at the beginning of the text, returns False.
        Otherwise, moves the caret backward and returns True.

        """
        if self.charpos > 0:
            self.charpos = self.charpos - 1
            return True
        else:
            return False

    def persist(self):
        """Returns information needed for persisting the caret."""
        return {
            'charpos': self.charpos,
            'pos': self.pos,
            'visible': self.visible,
            'width': self.width,
            'eobuf': self.eobuf,
            'buflen': self.buflen,
        }

    def restore(self, session):
        """Restores the caret from the previous session."""
        self.charpos = session['charpos']
        self.pos = session['pos']
        self.visible = session['visible']
        self.width = session['width']
        self.eobuf = session['eobuf']
        self.buflen = session['buflen']
