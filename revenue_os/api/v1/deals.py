from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.integrations.n8n import deal_stage_changed_webhook, new_deal_webhook
from revenue_os.models.contact import Company, Contact
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType
from revenue_os.services.deal_service import forecast_pipeline, pipeline_health
from revenue_os.services.export_service import export_deals_csv
from revenue_os.services.search_service import index_deal

router = APIRouter(prefix="/deals", tags=["deals"])


class PipelineCreate(BaseModel):
    name: str
    pipeline_type: PipelineType = PipelineType.SALES
    stages: str = "discovery,qualified,proposal,negotiation,closed_won,closed_lost"


class PipelineResponse(BaseModel):
    id: uuid.UUID
    name: str
    pipeline_type: PipelineType
    stages: Optional[str] = None
    is_default: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.post("/pipelines", response_model=PipelineResponse, status_code=201)
def create_pipeline(body: PipelineCreate, db: Session = Depends(get_db)):
    pipeline = Pipeline(
        name=body.name,
        pipeline_type=body.pipeline_type,
        stages=body.stages,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


@router.get("/pipelines", response_model=list[PipelineResponse])
def list_pipelines(
    pipeline_type: Optional[PipelineType] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Pipeline)
    if pipeline_type:
        query = query.filter(Pipeline.pipeline_type == pipeline_type)
    return query.all()


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


class DealCreate(BaseModel):
    pipeline_id: str
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    name: str
    stage: DealStage = DealStage.DISCOVERY
    probability: int = 10
    value: float = 0.0
    currency: str = "USD"
    description: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    tags: Optional[str] = None


class DealUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[DealStage] = None
    probability: Optional[int] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    tags: Optional[str] = None


class DealResponse(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    name: str
    stage: DealStage
    probability: int
    value: float
    currency: str
    description: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: Optional[str] = None
    client_name: Optional[str] = None
    contact_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MoveStageBody(BaseModel):
    stage: DealStage
    probability: Optional[int] = None


class BoardColumn(BaseModel):
    stage: str
    label: str
    deals: list[DealResponse]


class BoardResponse(BaseModel):
    pipeline_id: uuid.UUID
    pipeline_name: str
    columns: list[BoardColumn]


@router.get("", response_model=list[DealResponse])
def list_deals(
    stage: Optional[DealStage] = Query(None),
    pipeline_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    query = db.query(Deal).options(joinedload(Deal.company), joinedload(Deal.contact))
    if stage:
        query = query.filter(Deal.stage == stage)
    if pipeline_id:
        query = query.filter(Deal.pipeline_id == pipeline_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(Deal.name.ilike(pattern))
    deals = query.offset(skip).limit(limit).all()
    return [_enrich_deal(d) for d in deals]


@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: str, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    deal = db.query(Deal).options(joinedload(Deal.company), joinedload(Deal.contact)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _enrich_deal(deal)


@router.post("", response_model=DealResponse, status_code=201)
def create_deal(body: DealCreate, db: Session = Depends(get_db)):
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == body.pipeline_id
    ).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    deal = Deal(
        pipeline_id=uuid.UUID(body.pipeline_id),
        company_id=(
            uuid.UUID(body.company_id) if body.company_id else None
        ),
        contact_id=(
            uuid.UUID(body.contact_id) if body.contact_id else None
        ),
        name=body.name,
        stage=body.stage,
        probability=body.probability,
        value=body.value,
        currency=body.currency,
        description=body.description,
        expected_close_date=body.expected_close_date,
        tags=body.tags,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)

    index_deal(deal_id=deal.id, name=deal.name, description=deal.description, tags=deal.tags)
    new_deal_webhook(
        deal_id=str(deal.id),
        deal_name=deal.name,
        value=deal.value,
        stage=deal.stage.value,
    )

    return _enrich_deal(deal, db)


@router.put("/{deal_id}", response_model=DealResponse)
def update_deal(
    deal_id: str,
    body: DealUpdate,
    db: Session = Depends(get_db),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = body.model_dump(exclude_unset=True)
    old_stage = deal.stage.value if "stage" in update_data else None

    if "stage" in update_data and update_data["stage"] == DealStage.CLOSED_WON:
        deal.closed_at = datetime.utcnow()

    for key, value in update_data.items():
        if value is not None:
            setattr(deal, key, value)

    db.commit()
    db.refresh(deal)

    index_deal(deal_id=deal.id, name=deal.name, description=deal.description, tags=deal.tags)
    if old_stage and old_stage != deal.stage.value:
        deal_stage_changed_webhook(
            deal_id=str(deal.id),
            deal_name=deal.name,
            previous_stage=old_stage,
            new_stage=deal.stage.value,
        )

    return _enrich_deal(deal)


@router.post("/{deal_id}/move-stage", response_model=DealResponse)
def move_deal_stage(
    deal_id: str,
    body: MoveStageBody,
    db: Session = Depends(get_db),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    old_stage = deal.stage.value
    deal.stage = body.stage
    if body.probability is not None:
        deal.probability = body.probability
    if body.stage == DealStage.CLOSED_WON:
        deal.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(deal)

    deal_stage_changed_webhook(
        deal_id=str(deal.id),
        deal_name=deal.name,
        previous_stage=old_stage,
        new_stage=deal.stage.value,
    )
    return _enrich_deal(deal)


@router.get("/pipelines/{pipeline_id}/board", response_model=BoardResponse)
def get_pipeline_board(
    pipeline_id: str,
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload

    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stage_list = [s.strip() for s in pipeline.stages.split(",")] if pipeline.stages else []
    deals = (
        db.query(Deal)
        .options(joinedload(Deal.company), joinedload(Deal.contact))
        .filter(Deal.pipeline_id == pipeline_id)
        .order_by(Deal.created_at.desc())
        .all()
    )

    deal_map = {d.id: _enrich_deal(d, db) for d in deals}

    columns = []
    for stage in stage_list:
        label = stage.replace("_", " ").title()
        stage_deals = [deal_map[d.id] for d in deals if d.stage.value == stage]
        columns.append(BoardColumn(stage=stage, label=label, deals=stage_deals))

    return BoardResponse(
        pipeline_id=pipeline.id,
        pipeline_name=pipeline.name,
        columns=columns,
    )


def _enrich_deal(deal, db=None):
    company = getattr(deal, "company", None)
    if not company and db and deal.company_id:
        from revenue_os.models.contact import Company
        company = db.query(Company).filter(Company.id == deal.company_id).first()
    contact = getattr(deal, "contact", None)
    if not contact and db and deal.contact_id:
        contact = db.query(Contact).filter(Contact.id == deal.contact_id).first()
    return DealResponse(
        id=deal.id,
        pipeline_id=deal.pipeline_id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
        name=deal.name,
        stage=deal.stage if hasattr(deal.stage, 'value') else deal.stage,
        probability=deal.probability,
        value=deal.value,
        currency=deal.currency,
        description=deal.description,
        expected_close_date=deal.expected_close_date,
        closed_at=deal.closed_at,
        client_name=company.name if company else None,
        contact_name=f"{contact.first_name} {contact.last_name}" if contact else None,
        tags=deal.tags,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


@router.get("/pipelines/{pipeline_id}/forecast")
def get_forecast(pipeline_id: str, db: Session = Depends(get_db)):
    return forecast_pipeline(db, pipeline_id)


@router.get("/pipelines/{pipeline_id}/health")
def get_health(pipeline_id: str, db: Session = Depends(get_db)):
    return pipeline_health(db, pipeline_id)


@router.get("/export/csv")
def export_deals(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    csv_data = export_deals_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=deals.csv"},
    )
