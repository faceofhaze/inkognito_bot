# Ініціалізація handlers
from .start import register_start_handlers
from .search import register_search_handlers
from .chat import register_chat_handlers
from .profile import register_profile_handlers
from .donate import register_donate_handlers, set_bot

__all__ = [
    'register_start_handlers',
    'register_search_handlers', 
    'register_chat_handlers',
    'register_profile_handlers',
    'register_donate_handlers',
    'set_bot'
]