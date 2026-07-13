from fastapi.responses import JSONResponse
from datetime import datetime

def success_response(data=None, message="success", status_code=200):
    return JSONResponse(
        content={
            "code": 0,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        },
        status_code=status_code
    )

def error_response(message="error", status_code=500, errors=None):
    return JSONResponse(
        content={
            "code": status_code,
            "message": message,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        },
        status_code=status_code
    )