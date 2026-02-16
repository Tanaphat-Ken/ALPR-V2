from fastapi import HTTPException


def response_exception(e):
    if hasattr(e, 'args') and len(e.args) > 0 and isinstance(e.args[0], dict):
        error_details = e.args[0]
        status_code = error_details.get("status_code", 500)
        message = error_details.get("message", str(e))
    else:
        status_code = 500
        message = str(e)
        
    raise HTTPException(status_code=status_code, detail=message)
