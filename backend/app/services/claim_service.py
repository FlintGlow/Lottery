"""领奖业务： 按奖品类型进行校验领奖信息并提交"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.enums import RedemptionStatus, PrizeType
from app.models.user import User
from app.models.lottery import WinRecord
from app.repositories.win_record_repository import WinRecordRepository
from app.schemas.winnings import RedemptionSubmitRequest


class ClaimService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.winnings = WinRecordRepository(db)

    async def submit(self, user:User, win_id: int, data: RedemptionSubmitRequest) -> WinRecord:
        win = await self.winnings.get(win_id)
        if win is None or win.user_id != user.id:
            raise NotFoundError("中奖记录不存在")
        if win.redemption_status != RedemptionStatus.PENDING:
            raise BadRequestError("领奖信息已提交或该记录不可重复提交")

        if win.prize_type == PrizeType.PHYSICAL:
            if not data.recipient_name or not data.recipient_phone or not data.recipient_address:
                raise BadRequestError("实物奖品需填写收件人、手机号和收货地址")
            win.recipient_name = data.recipient_name
            win.recipient_phone = data.recipient_phone
            win.recipient_address = data.recipient_address
        else:
            if not data.recipient_phone:
                raise BadRequestError("虚拟奖品需填写领奖手机号")
            win.recipient_phone = data.recipient_phone
            win.recipient_name = None
            win.recipient_address = None

        win.redemption_status = RedemptionStatus.SUBMITTED
        win.redemption_at = datetime.now()
        await self.db.flush()
        await self.db.commit()
        return win