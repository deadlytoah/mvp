# coding: utf-8
""" Stores and loads the session """

import json

SESSION_FILE = 'session.json'

class InvalidSessionError(Exception):
    """Indicates the session data found in the session file was corrupt or
    invalid

    """
    pass

def init():
    """Creates a new session object with default values"""
    return {
        'name': 'default session',
        'range': {
            'start': {
                'translation': 'esv',
                'book': 'Gen',
                'chapter': 1,
                'verse': 1,
                'sentence': 0,
            },
            'end': {
                'translation': 'esv',
                'book': 'Rev',
                'chapter': 22,
                'verse': 21,
                'sentence': 29,
            },
        },
        'level': 0,
        'strategy': 0,
    }

def store(session):
    """Persists the session on disk"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(session, f, indent=2)

def load():
    """Reads the session from disk"""
    try:
        with open(SESSION_FILE, 'r') as f:
            session = json.load(f)
    except FileNotFoundError:
        return None
    except json.decoder.JSONDecodeError:
        raise InvalidSessionError()

    if _validate(session):
        return session
    else:
        raise InvalidSessionError()

def _validate(session):
    """Validates the session objects.  Checks if all attributes are there."""
    for attr in ['name', 'range', 'level', 'strategy']:
        if not attr in session:
            return False
    for attr in ['start', 'end']:
        if not attr in session['range']:
            return False
    for attr in ['translation', 'book', 'chapter', 'verse', 'sentence']:
        if not attr in session['range']['start']:
            return False
        if not attr in session['range']['end']:
            return False
    return True
