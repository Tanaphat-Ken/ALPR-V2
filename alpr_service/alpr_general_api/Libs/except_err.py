from fastapi import HTTPException


def response_exception(e):
    error_details = e.args[0]
    status_code = error_details.get("status_code")
    message = error_details.get("message")
    raise HTTPException(status_code=status_code, detail=message)
