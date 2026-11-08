from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    try:
        database_connected = check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    if not database_connected:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return {"status": "healthy"}
