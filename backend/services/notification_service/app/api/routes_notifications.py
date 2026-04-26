from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, get_current_user, require_permission

from ..models import Preference

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    factory = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class PreferenceResponse(BaseModel):
    email_enabled: bool
    push_enabled: bool
    failure_alerts: bool
    weekly_report: bool


class PreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    failure_alerts: bool | None = None
    weekly_report: bool | None = None
    fcm_token: str | None = None


class TestRequest(BaseModel):
    recipient: EmailStr
    subject: str = "SmartBarrel — Test"
    body: str = "Ceci est un test."


@router.get("/preferences", response_model=PreferenceResponse)
async def get_preferences(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PreferenceResponse:
    pref = await session.get(Preference, UUID(user.id))
    if pref is None:
        pref = Preference(user_id=UUID(user.id))
        session.add(pref)
        await session.flush()
    return PreferenceResponse(
        email_enabled=pref.email_enabled,
        push_enabled=pref.push_enabled,
        failure_alerts=pref.failure_alerts,
        weekly_report=pref.weekly_report,
    )


@router.patch("/preferences", response_model=PreferenceResponse)
async def update_preferences(
    body: PreferenceUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PreferenceResponse:
    pref = await session.get(Preference, UUID(user.id))
    if pref is None:
        pref = Preference(user_id=UUID(user.id))
        session.add(pref)
    for field in ("email_enabled", "push_enabled", "failure_alerts",
                  "weekly_report", "fcm_token"):
        val = getattr(body, field)
        if val is not None:
            setattr(pref, field, val)
    await session.flush()
    return PreferenceResponse(
        email_enabled=pref.email_enabled,
        push_enabled=pref.push_enabled,
        failure_alerts=pref.failure_alerts,
        weekly_report=pref.weekly_report,
    )


@router.post("/test", status_code=202)
async def send_test(
    body: TestRequest,
    _: Annotated[CurrentUser, Depends(require_permission("users:write"))],
    request: Request,
) -> dict:
    from ..core.settings import get_settings
    from ..services.email_sender import send_email
    settings = get_settings()
    try:
        await send_email(
            settings, to=body.recipient, subject=body.subject, body_html=body.body,
        )
    except Exception as e:
        raise HTTPException(500, f"Send failed: {e}") from e
    return {"status": "sent", "to": body.recipient}
