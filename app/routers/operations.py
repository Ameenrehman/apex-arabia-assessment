"""Operations task management router (CRUD endpoints)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OperationTask
from app.schemas import (
    OperationTaskCreate,
    OperationTaskResponse,
    OperationTaskUpdate,
)

router = APIRouter(prefix="/api/v1/operations", tags=["Operations Tasks"])


@router.post(
    "",
    response_model=OperationTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Operation Task",
    description="Registers a new operational task in the system.",
)
def create_operation_task(
    payload: OperationTaskCreate,
    db: Session = Depends(get_db),
) -> OperationTask:
    task = OperationTask(
        title=payload.title,
        service_name=payload.service_name,
        environment=payload.environment,
        status=payload.status,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "",
    response_model=List[OperationTaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List Operation Tasks",
    description="Retrieves a list of operational tasks, with optional filtering by status.",
)
def list_operation_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by task status"),
    environment_filter: Optional[str] = Query(None, alias="environment", description="Filter by environment"),
    limit: int = Query(50, ge=1, le=100, description="Max number of items to return"),
    db: Session = Depends(get_db),
) -> List[OperationTask]:
    query = db.query(OperationTask)
    if status_filter:
        query = query.filter(OperationTask.status == status_filter)
    if environment_filter:
        query = query.filter(OperationTask.environment == environment_filter)
    return query.order_by(OperationTask.created_at.desc()).limit(limit).all()


@router.get(
    "/{task_id}",
    response_model=OperationTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Operation Task by ID",
    description="Retrieves the details of a specific operational task.",
)
def get_operation_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> OperationTask:
    task = db.query(OperationTask).filter(OperationTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation task with ID {task_id} not found",
        )
    return task


@router.patch(
    "/{task_id}",
    response_model=OperationTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Operation Task",
    description="Updates the status or attributes of an operational task.",
)
def update_operation_task(
    task_id: int,
    payload: OperationTaskUpdate,
    db: Session = Depends(get_db),
) -> OperationTask:
    task = db.query(OperationTask).filter(OperationTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation task with ID {task_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Operation Task",
    description="Removes an operational task from the system.",
)
def delete_operation_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> None:
    task = db.query(OperationTask).filter(OperationTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation task with ID {task_id} not found",
        )
    db.delete(task)
    db.commit()
