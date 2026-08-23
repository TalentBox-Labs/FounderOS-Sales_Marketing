from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.auth import get_current_user
from revenue_os.database import get_db
from revenue_os.models.task import (
    RelatedEntityType,
    Task,
    TaskPriority,
    TaskStatus,
)
from revenue_os.models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.NONE
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    due_at: Optional[datetime] = None
    position: Optional[int] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_users(cls, task):
        assignee = getattr(task, "assignee", None)
        creator = getattr(task, "creator", None)
        related_type = task.related_entity_type.value if task.related_entity_type else None
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to,
            created_by=task.created_by,
            assignee_name=assignee.full_name if assignee else None,
            creator_name=creator.full_name if creator else None,
            priority=task.priority,
            status=task.status,
            related_entity_type=related_type,
            related_entity_id=task.related_entity_id,
            due_at=task.due_at,
            completed_at=task.completed_at,
            position=task.position,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[str] = Query(None),
    related_type: Optional[str] = Query(None),
    related_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import joinedload

    query = db.query(Task).options(
        joinedload(Task.assignee), joinedload(Task.creator)
    )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == uuid.UUID(assigned_to))
    if related_type:
        query = query.filter(Task.related_entity_type == related_type)
    if related_id:
        query = query.filter(Task.related_entity_id == uuid.UUID(related_id))
    if search:
        pattern = f"%{search}%"
        query = query.filter(Task.title.ilike(pattern))
    query = query.order_by(Task.position, Task.created_at.desc())
    tasks = query.offset(skip).limit(limit).all()
    return [TaskResponse.from_orm_with_users(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import joinedload

    task = (
        db.query(Task)
        .options(joinedload(Task.assignee), joinedload(Task.creator))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.from_orm_with_users(task)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    related_type = None
    if body.related_entity_type:
        try:
            related_type = RelatedEntityType(body.related_entity_type.lower())
        except ValueError:
            pass

    task = Task(
        title=body.title,
        description=body.description,
        assigned_to=uuid.UUID(body.assigned_to) if body.assigned_to else None,
        created_by=current_user.id,
        priority=body.priority,
        related_entity_type=related_type,
        related_entity_id=uuid.UUID(body.related_entity_id) if body.related_entity_id else None,
        due_at=body.due_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm_with_users(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import joinedload

    task = (
        db.query(Task)
        .options(joinedload(Task.assignee), joinedload(Task.creator))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data:
        update_data["status"] = body.status
        if body.status == TaskStatus.DONE:
            update_data["completed_at"] = datetime.utcnow()
        elif body.status != TaskStatus.DONE:
            update_data["completed_at"] = None

    if "assigned_to" in update_data:
        update_data["assigned_to"] = uuid.UUID(body.assigned_to) if body.assigned_to else None

    if "related_entity_type" in update_data:
        if body.related_entity_type:
            try:
                update_data["related_entity_type"] = RelatedEntityType(body.related_entity_type.lower())
            except ValueError:
                del update_data["related_entity_type"]
        else:
            update_data["related_entity_type"] = None

    if "related_entity_id" in update_data:
        update_data["related_entity_id"] = uuid.UUID(body.related_entity_id) if body.related_entity_id else None

    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm_with_users(task)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import joinedload

    task = (
        db.query(Task)
        .options(joinedload(Task.assignee), joinedload(Task.creator))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.DONE
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return TaskResponse.from_orm_with_users(task)
