from fastapi import HTTPException

class AuthError(HTTPException):

    def __init__(self, detail: str, error_code: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail= detail)
        self.error_code = error_code