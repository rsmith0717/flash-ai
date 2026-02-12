# myapp/models/__init__.py
from .flashcard import Deck, FlashCard
from .user import User

# Import other models as needed

# Optional: define what is exposed by "from models import *"
__all__ = ["User", "FlashCard", "Deck"]
