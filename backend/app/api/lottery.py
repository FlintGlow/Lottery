"""抽奖接口： 抽奖入口与记录查询"""

from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

from app.schemas.common import ApiResponse, ok, PaginatedResponse, PageParams
from app.schemas.lottery import DrawResultOut, LotteryRecordResponse

from app.services.lottery_service import LotteryService

router = APIRouter(prefix="/lottery", tags=["抽奖"])

def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None

@router.post("/{activity_id}/draw", response_model=ApiResponse[DrawResultOut])
async def draw(
        activity_id: int,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[DrawResultOut]:
    """发起抽奖： Redis预扣库存 + MQ异步落库， 返回 order_no供轮询"""

    result = await LotteryService(db).draw(current_user, activity_id, ip=_client_ip(request))
    return ok(result, "抽奖请求已受理")

@router.get("/records", response_model=ApiResponse[PaginatedResponse[LotteryRecordResponse]])
async def my_records(
        params: PageParams = Depends(),
        activity_id: int | None = None,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[LotteryRecordResponse]]:
    """我的抽奖记录"""
    items, total = await LotteryService(db).list_my_records(
        current_user,
        activity_id = activity_id,
        page = params.page,
        page_size = params.page_size,
    )
    return ok(
        PaginatedResponse(
            items = items,
            total = total,
            page = params.page,
            page_size = params.page_size,
        )
    )


@router.get("/records/{order_id}", response_model=ApiResponse[LotteryRecordResponse])
async def my_record(
        order_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[LotteryRecordResponse]:
    """按order_no查询单次抽奖结果"""
    return ok(await LotteryService(db).get_my_record(current_user, order_id))