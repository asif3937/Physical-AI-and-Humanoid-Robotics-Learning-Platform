class InvalidInputError(Exception):
    def __init__(self, message: str):
        self.message = message
        self.error_code = "INVALID_INPUT"
        super().__init__(self.message)


class BookNotFoundError(Exception):
    def __init__(self, book_id: str):
        self.book_id = book_id
        self.message = f"Book with ID {book_id} not found"
        self.error_code = "BOOK_NOT_FOUND"
        super().__init__(self.message)


class ContentNotFoundError(Exception):
    def __init__(self, message: str):
        self.message = message
        self.error_code = "CONTENT_NOT_FOUND"
        super().__init__(self.message)