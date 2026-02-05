# myapp/models/__init__.py
from .flashcard import Deck, FlashCard
from .payroll import Payroll, PaySchedule, SalaryType
from .user import User

# Import other models as needed

# Optional: define what is exposed by "from models import *"
__all__ = ["User", "Payroll", "PaySchedule", "SalaryType", "FlashCard", "Deck"]
