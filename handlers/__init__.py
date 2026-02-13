"""Bot handlers moduli"""
from .start import start_handler
from .user_search import search_handler
from .admin_add import add_movie_handler
from .admin_delete import delete_movie_handler
from .admin_send import send_message_handler
from .callbacks import callback_handler
from .errors import error_handler
__all__ = [
'start_handler',
'search_handler',
'add_movie_handler',
'delete_movie_handler',
'send_message_handler',
'callback_handler',
'error_handler',
]

