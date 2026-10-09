"""中奖记录业务：我的中奖、运营列表、状态机流转（含审计）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RedemptionStatus
from app.models.user import User
from app.core.exceptions import NotFoundError

from app.repositories.activity_repository import ActivityRepository
from app.repositories.lottery_repository import LotteryRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.user_repository import UserRepository
from app.repositories.win_record_repository import WinRecordRepository

from app.schemas.winnings import WinRecordResponse
from app.core.exceptions import BadRequestError
from app.models import OperationLog, WinRecord
from app.schemas.winnings import WinRecordStatusUpdate

#领奖状态机合法流转
_ALLOWED_TRANSITIONS: dict[RedemptionStatus, set[RedemptionStatus]] = {
    RedemptionStatus.PENDING: {RedemptionStatus.SUBMITTED, RedemptionStatus.CANCELLED},
    RedemptionStatus.SUBMITTED: {RedemptionStatus.PROCESSING, RedemptionStatus.CANCELLED},
    RedemptionStatus.PROCESSING: {RedemptionStatus.COMPLETED, RedemptionStatus.CANCELLED},
    RedemptionStatus.COMPLETED: set(),
    RedemptionStatus.CANCELLED: set(),
}


class WinningsService:
    """中奖记录服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.winnings = WinRecordRepository(db)
        self.records = LotteryRepository(db)
        self.activities = ActivityRepository(db)
        self.users = UserRepository(db)
        self.operation_logs = OperationLogRepository(db)


    async def list_my(
            self,
            user: User,
            *,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[WinRecordResponse], int]:
        items, total = await self.winnings.list_by_user(
            user_id = user.id,
            page = page,
            page_size = page_size,
        )
        return [await self._to_out(win) for win in items], total

    async def get_my(self, user:User, win_id: int) -> WinRecordResponse:
        win = await self.winnings.get(win_id)
        if win is None or win.user_id != user.id:
            raise NotFoundError("中奖记录不存在")
        return await self._to_out(win)

    async def list_for_operations(
            self,
            *,
            activity_id: int | None = None,
            status: str | None = None,
            keyword: str | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[WinRecordResponse], int]:
        items, total = await self.winnings.list_for_operations(
            activity_id = activity_id,
            status = status,
            keyword = keyword,
            page = page,
            page_size = page_size,
        )
        return [await self._to_out(win) for win in items], total

    async def update_status(
            self,
            operator: User,
            win_id: int,
            data: WinRecordStatusUpdate,
    ) -> WinRecordResponse:
        win = await self.winnings.get(win_id)
        if win is None:
            raise NotFoundError("中奖记录不存在")

        allowed = _ALLOWED_TRANSITIONS.get(win.redemption_status, set())
        if data.status not in allowed:
            raise BadRequestError(f"状态不允许从 {win.redemption_status.value} 变更为 {data.status.value}")
        old_status = win.redemption_status.value
        win.redemption_status = data.status
        win.processed_by = operator.id
        win.processed_at = datetime.now()
        if data.remark is not None:
            win.process_remark = data.remark
        await self.db.flush()
        await self.db.refresh(win)
        await self.operation_logs.add(
            OperationLog(
                user_id = operator.id,
                module = "winnings",
                action = f"update_status:{data.status.value}",
                target_type = "win_record",
                target_id = win.id,
                detail_json = {"from": old_status, "to": data.status.value},
            )
        )
        await self.db.commit()
        return await self._to_out(win)

    async def _to_out(self, win: WinRecord) -> WinRecordResponse:
        record = await self.records.get(win.draw_record_id)
        activity = await self.activities.get(win.activity_id)
        user = await self.users.get(win.user_id)
        return WinRecordResponse(
            id = win.id,
            order_no = record.order_no if record else "",
            activity_id = win.activity_id,
            activity_name = activity.name if activity else None,
            username = user.username if user else None,
            prize_id = win.prize_id,
            prize_name = win.prize_name,
            prize_image = win.prize_image,
            prize_type = win.prize_type,
            redemption_status = win.redemption_status,
            redemption_code = win.redemption_code,
            expire_at = win.expire_at,
            recipient_name = win.recipient_name,
            recipient_phone = win.recipient_phone,
            recipient_address = win.recipient_address,
            redemption_at = win.redemption_at,
            processed_by = win.processed_by,
            processed_at = win.processed_at,
            process_remark= win.process_remark,
            created_at = win.created_at,
        )

