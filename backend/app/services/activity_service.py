"""活动业务：CRUD、状态机、时间自动推进、操作审计。"""

from __future__ import annotations

from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.activity import Activity
from app.models.enums import ActivityStatus
from app.models.log import OperationLog
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.activity import  ActivityCreate, ActivityUpdate, ActivityRuleConfig
from app.services.lottery_cache import LotteryCacheService


class ActivityService:
    """活动管理服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.activities = ActivityRepository(db)
        self.operation_logs = OperationLogRepository(db)

    # ---- 查询 ---- 管理端可查全部活动、获取活动信息，用户可查看草稿和已结束以外的活动，获取活动信息（仅可见草稿和已结束以外的活动）
    async def list_admin(
            self,
            *,
            page: int = 1,
            page_size: int = 20,
            keyword: str | None = None,
            status: ActivityStatus | None = None,
    ) -> tuple[list[Activity], int]:
        items, total = await self.activities.list_activities(
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status.value if status else None,
        )
        return items, total

    async def get_admin(self, activity_id: int) -> tuple[Activity, int]:
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        prize_count = await self.activities.count_prizes(activity_id)
        return activity, prize_count


    async def list_public(self) -> list[Activity]:
        items, _ = await self.activities.list_activities(
            page=1,
            page_size=100,
            exclude_status=[ActivityStatus.DRAFT.value, ActivityStatus.ENDED.value],
        )
        for activity in items:
            await self._refresh_status(activity)
        return items


    async def get_public(self, activity_id: int) -> tuple[Activity, int]:
        activity, prizes_count = await self.get_admin(activity_id)
        if activity.status in (ActivityStatus.DRAFT, ActivityStatus.ENDED):
            raise NotFoundError("活动未发布或已结束")
        return activity, prizes_count

    # ---- 创建、更新、删除 ----
    async def create(self, user:User, data: ActivityCreate, ip: str | None = None) -> Activity:
        activity = Activity(
            name=data.name,
            description=data.description,
            cover_url=data.cover_url,
            start_time=data.start_time,
            end_time=data.end_time,
            daily_draw_limit=data.daily_draw_limit,
            total_draw_limit = data.total_draw_limit,
            rule_config=data.rule_config.model_dump(exclude_none=True) if data.rule_config else None,
            created_by=user.id,
        )
        activity = await self.activities.add(activity)
        await self._log(user, "create", activity.id, {"name": activity.name}, ip)
        await self.db.commit()
        return activity


    async def update(self, user: User, activity_id: int, data: ActivityUpdate, ip: str | None = None ) -> Activity:
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status == ActivityStatus.ENDED:
            raise BadRequestError("活动已结束，禁止修改")

        payload =data.model_dump(exclude_none=True)
        locked_fields = {
            "start_time",
            "daily_draw_limit",
            "total_draw_limit",
        }
        if activity.status in (ActivityStatus.ONGOING, ActivityStatus.ENDED):
            forbidden = locked_fields.intersection(payload)
            if forbidden:
                raise BadRequestError(f"活动进行中，不可修改字段：{','.join(sorted(forbidden))}")

        new_start = payload.get("start_time", activity.start_time)
        new_end = payload.get("end_time", activity.end_time)
        if new_start and new_end and new_end <= new_start:
            raise BadRequestError("结束时间必须晚于开始时间")

        for field, value in payload.items():
            if field == "rule_config":
                if isinstance(value, ActivityRuleConfig):
                    value = value.model_dump(exclude_none=True)
                elif value is None:
                    value = None
            setattr(activity, field, value)

        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "update", activity.id, jsonable_encoder(payload), ip)
        await self.db.commit()
        return activity


    async def delete(self, user: User, activity_id: int, ip: str | None = None) -> None:
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status not in (ActivityStatus.DRAFT, ActivityStatus.PENDING):
            raise BadRequestError(
                f"仅草稿或待开始的活动可删除，当前状态: {activity.status.value}"
            )
        prizes_count = await self.activities.count_prizes(activity.id)
        if prizes_count > 0:
            raise BadRequestError("活动下仍有奖品，请先删除奖品")

        activity.is_deleted = True
        await self.db.flush()
        await self._log(user, "delete", activity.id, None, ip)
        await self.db.commit()

    # ---- 状态变更 ----
    async def publish(self, user:User, activity_id: int, ip: str | None = None) -> Activity:
        """草稿 -> 待开始"""
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status != ActivityStatus.DRAFT:
            raise BadRequestError(f"仅草稿活动可发布，当前状态为：{activity.status.value}")
        if not activity.start_time or not activity.end_time:
            raise BadRequestError("请先配置活动的开始/结束时间")
        if activity.end_time <= datetime.now():
            raise BadRequestError("活动时间已过，无法发布")
        activity.status = ActivityStatus.PENDING
        if activity.start_time <= datetime.now():
            activity.status = ActivityStatus.ONGOING
        activity.published_at = datetime.now()
        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "publish", activity.id, {"status": activity.status.value}, ip)
        await self.db.commit()
        await LotteryCacheService(self.db).warm_activity(activity.id)
        return activity


    async def start(self, user: User, activity_id: int, ip: str | None = None) -> Activity:
        """待开始 -> 进行中"""
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status != ActivityStatus.PENDING:
            raise BadRequestError(f"仅开始的活动可启用，当前状态：{activity.status.value}")
        if activity.end_time and activity.end_time <= datetime.now():
            raise BadRequestError("活动已结束，无法启动")

        activity.status = ActivityStatus.ONGOING
        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "start", activity.id, None, ip)
        await self.db.commit()
        return activity


    async def pause(self, user: User, activity_id: int, ip: str | None = None) -> Activity:
        """进行中 -> 暂停"""
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status != ActivityStatus.ONGOING:
            raise BadRequestError(f"仅进行中的活动可暂停，当前状态: {activity.status.value}")
        activity.status = ActivityStatus.PAUSED
        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "pause", activity.id, None, ip)
        await self.db.commit()
        return activity

    async def resume(self, user: User, activity_id: int, ip: str | None = None) -> Activity:
        """已暂停 -> 进行中"""
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status != ActivityStatus.PAUSED:
            raise BadRequestError(f"仅已暂停的活动可恢复，当前状态:{activity.status.value}")
        if activity.end_time and activity.end_time <= datetime.now():
            raise BadRequestError("活动已到期，无法恢复")
        activity.status = ActivityStatus.ONGOING
        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "resume", activity.id, None, ip)
        await self.db.commit()
        return activity

    async def end(self, user: User, activity_id: int, ip: str | None = None) -> Activity:
        """结束活动： 待开始/进行中/已暂停 -> 已结束"""
        activity = await self.activities.get(activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        await self._refresh_status(activity)
        if activity.status not in(ActivityStatus.PENDING, ActivityStatus.ONGOING, ActivityStatus.PAUSED):
            raise BadRequestError(f"当前活动状态:{activity.status.value}不可结束")
        activity.status = ActivityStatus.ENDED
        if activity.end_time and activity.end_time <= datetime.now():
            activity.end_time = datetime.now()
        await self.db.flush()
        await self.db.refresh(activity)
        await self._log(user, "end", activity.id, None, ip)
        await self.db.commit()
        return activity

    # --- 内部方法 ---
    async def _refresh_status(self, activity: Activity) -> None:
        now = datetime.now()
        if (
            activity.status == ActivityStatus.PENDING
            and activity.start_time
            and activity.start_time <= now
        ):
            activity.status = ActivityStatus.ONGOING


    async def _log(
            self,
            user:User,
            action: str,
            target_id: int | None,
            detail: dict | None = None,
            ip: str | None = None
    ) -> None:
        await self.operation_logs.add(
            OperationLog(
                user_id=user.id,
                module="activity",
                action=action,
                target_type="activity",
                target_id=target_id,
                detail_json=jsonable_encoder(detail) if detail else None,
                ip=ip,
            )
        )





