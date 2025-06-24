from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database

router = APIRouter(prefix="/state_vectors", tags=["state_vectors"])

@router.post("/",response_model=schemas.StateVector)
def create_state_vector(
    sv: schemas.StateVector, 
    db: Session = Depends(database.get_db)
):
    db_sv = models.StateVector(**sv.dict())
    db.add(db_sv)
    db.commit()
    db.refresh(db_sv)
    return db_sv

@router.get("/",response_model=List[schemas.StateVector])
def read_state_vector(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    return db.query(models.StateVector).offset(skip).limit(limit).all()

