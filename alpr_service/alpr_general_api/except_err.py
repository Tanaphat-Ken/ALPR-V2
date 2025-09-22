from fastapi import HTTPException


def response_exception(error):
    if isinstance(error, dict):
        status_code = error.get("status_code", 500)
        message = error.get("message", "An error occurred")
    elif isinstance(error, Exception):
        status_code = 500
        message = str(error)
    else:
        status_code = 500
        message = "Unexpected error occurred"

    raise HTTPException(status_code=status_code, detail=message)
