from fastapi import HTTPException, status


class UserNotFoundException(HTTPException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class EmailAlreadyExistsException(HTTPException):
    def __init__(self, detail: str = "Email already exists"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FlashcardNotFoundException(HTTPException):
    def __init__(self, detail: str = "Flashcard not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidPayScheduleException(HTTPException):
    def __init__(
        self,
        detail: str = "Invalid pay schedule cannot be processed. Must be weekly, biweekly, or monthly",
    ):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
