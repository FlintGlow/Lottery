"""活动统计接口（运营端，admin/operator）"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.statistics import ActivityStaticsResponse
from app.schemas.common import ApiResponse, ok
from app.services.statistics_service import StatisticsService

admin_router = APIRouter(prefix="/admin/statustics", tags=["运营-统计"])


@admin_router.get("/activities/{activity_id}", response_model=ApiResponse[ActivityStaticsResponse])
async def get_activity_statistics(
        activity_id: int,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityStaticsResponse]:
    """活动统计： 参与人数/抽奖次数/中奖率/奖品统计/领奖状态"""

    return ok(await StatisticsService(db).activity_statistics(activity_id))