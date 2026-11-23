from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.base import get_db
from backend.app.services.seed_service import reset_and_seed_database

router = APIRouter(prefix="/seed", tags=["Database Seed & Reset"])

@router.post("/reset")
async def reset_seed_data(db: AsyncSession = Depends(get_db)):
    """
    1-Click Reset & Seed:
    Clears test records and loads 3 realistic synthetic patients:
    1. Ramesh Sharma (Normal flow, joint stiffness)
    2. Sunita Deshmukh (Lab mismatch: denies diabetes, HbA1c 7.9%)
    3. Vijay Patil (Emergency Red-Flag halt: chest pain, crisis alert)
    """
    result = await reset_and_seed_database(db)
    return {
        "status": "success",
        "message": "Database reset and seeded with 3 synthetic test patients.",
        "details": result
    }
