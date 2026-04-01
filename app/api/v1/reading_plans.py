from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.dependencies import get_current_user
from app.core.database import get_session
from app.models import ReadingPlan, User
from app.schemas import ReadingPlanResponse, ReadingPlanUpsert

router = APIRouter(prefix="/reading-plans", tags=["reading-plans"])


@router.put("/me", response_model=ReadingPlanResponse)
def upsert_plan(
    payload: ReadingPlanUpsert,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ReadingPlanResponse:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    plan = session.exec(select(ReadingPlan).where(
        ReadingPlan.user_id == current_user.id)).first()

    if not plan:
        plan = ReadingPlan(
            user_id=current_user.id,
            goal_type=payload.goal_type,
            pages_per_day_goal=payload.pages_per_day_goal,
            chapters_per_day_goal=payload.chapters_per_day_goal,
        )
        session.add(plan)
    else:
        plan.goal_type = payload.goal_type
        plan.pages_per_day_goal = payload.pages_per_day_goal
        plan.chapters_per_day_goal = payload.chapters_per_day_goal
        plan.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(plan)
    return ReadingPlanResponse(**plan.model_dump())


@router.get("/me", response_model=ReadingPlanResponse | None)
def get_plan(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan = session.exec(select(ReadingPlan).where(
        ReadingPlan.user_id == current_user.id)).first()
    if not plan:
        return None
    return ReadingPlanResponse(**plan.model_dump())
