"""奖品业务：分类 CRUD、奖品 CRUD、库存调整、审计。"""

from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError, BadRequestError

from app.repositories.activity_repository import ActivityRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.prize_repository import PrizeRepository, PrizeCategoryRepository

from app.models.prize import Prize, PrizeCategory
from app.models.user import User
from app.models.enums import PrizeStatus, ActivityStatus

from app.schemas.prize import PrizeCategoryCreate, PrizeCategoryUpdate, PrizesResponse, PrizeCreate, PrizeUpdate, PrizeStockAdjust

from app.services.lottery_cache import LotteryCacheService

from app.services.activity_service import ActivityService
from app.models import OperationLog


class PrizeService:
    """奖品与分类管理服务"""

    def __init__(self, db:AsyncSession) -> None:
        self.db = db
        self.prizes = PrizeRepository(db)
        self.categories = PrizeCategoryRepository(db)
        self.activities = ActivityRepository(db)
        self.operation_logs = OperationLogRepository(db)

    # ---- 分类 ----

    async def list_categories(self) -> list[PrizeCategory]:
        return await self.categories.list_categories()

    async def create_category(
            self,
            user: User,
            data: PrizeCategoryCreate,
            ip: str |None = None
    ) -> None:
        if await self.categories.get_by_name(data.name):
            raise ConflictError("分类名称已存在")
        category = PrizeCategory(
            name = data.name,
            description = data.description,
            sort_order = data.sort_order,
        )
        category = await self.categories.add(category)
        await self._log(user, "create", "prize_category", category.id, {"name":category.name}, ip)
        await self.db.commit()
        return category

    async def update_category(
            self,
            user: User,
            category_id: int,
            data: PrizeCategoryUpdate,
            ip: str |None = None
    ) -> PrizeCategory:
        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("分类不存在")
        if data.name is not None and data.name != category.name:
            existing = await self.categories.get_by_name(data.name)
            if existing is not None and existing.id != category.id:
                raise ConflictError("分类名称已存在")
            category.name = data.name
        if data.description is not None:
            category.description = data.description
        if data.sort_order is not None:
            category.sort_order = data.sort_order
        if data.status is not None:
            category.status = data.status
        await self.db.flush()
        await self.db.refresh(category)
        await self._log(user, "update", "prize_category", category.id, jsonable_encoder(data.model_dump(exclude_unset=True)), ip)
        await self.db.commit()
        return category

    async def delete_category(self, user:User, category_id: int, ip: str | None = None) -> None:
        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("分类不存在")
        if await self.categories.count_prizes(category.id) > 0:
            raise BadRequestError("分类下仍有奖品, 无法删除")
        category.is_deleted = True
        await self.db.flush()
        await self._log(user, "delete", "prize_category", category.id, None, ip)
        await self.db.commit()


    # ---- 奖品 ----
    async def list_prizes(
            self,
            *,
            activity_id: int | None = None,
            category_id: int | None = None,
            keyword: str | None = None,
            status: PrizeStatus | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[PrizesResponse], int]:
        items, total = await self.prizes.list_prizes(
            activity_id = activity_id,
            category_id = category_id,
            keyword = keyword,
            status = status,
            page = page,
            page_size = page_size,
        )
        category_map = await self._category_map(
            {item.category_id for item in items if item.category_id is not None},
        )
        outs = []
        for item in items:
            out = PrizesResponse.model_validate(item)
            out.category_name = category_map.get(item.category_id) if item.category_id is not None else None
            outs.append(out)
        return outs, total

    async def get_prizes(self, prize_id: int) -> PrizesResponse:
        prize = await self.prizes.get(prize_id)
        if prize is None:
            raise NotFoundError("奖品不存在")
        return await self._to_out(prize)

    async def create_prize(self, user: User, data: PrizeCreate, ip: str | None = None) -> PrizesResponse:
        activity = await self.activities.get(data.activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        if activity.status == ActivityStatus.ENDED:
            raise BadRequestError("活动已结束，无法添加奖品")
        if data.category_id is not None:
            await self._ensure_category(data.category_id)

        prize = Prize(
            activity_id = data.activity_id,
            category_id = data.category_id,
            prize_type = data.prize_type,
            name = data.name,
            description = data.description,
            img_url = data.img_url,
            prize_level = data.prize_level,
            total_stock = data.total_stock,
            remain_stock = data.total_stock,
            weight = data.weight,
            sort_order = data.sort_order,
        )
        prize = await self.prizes.add(prize)
        await self._log(user, "create", "prize", prize.id, {"name": prize.name, "activity_id": prize.activity_id}, ip,)
        await self.db.commit()
        await LotteryCacheService(self.db).invalidate_activity(prize.activity_id)
        return await self._to_out(prize)

    async def update_prize(
            self,
            user: User,
            prize_id: int,
            data: PrizeUpdate,
            ip: str | None = None
    ) -> PrizesResponse:
        prize = await self.prizes.get(prize_id)
        if prize is None:
            raise NotFoundError("奖品不存在")
        activity = await self.activities.get(prize.activity_id)
        if activity is not None and activity.status == ActivityStatus.ENDED:
            raise BadRequestError("活动已结束，无法修改奖品")
        if data.category_id is not None:
            await  self._ensure_category(data.category_id)

        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(prize, field, value)
        await self.db.flush()
        await self.db.refresh(prize)
        await self._log(user, "update", "prize", prize.id, jsonable_encoder(payload), ip)
        await self.db.commit()
        await LotteryCacheService(self.db).invalidate_activity(prize.activity_id)
        return await self._to_out(prize)

    async def adjust_stock(self, user: User, prize_id: int, data: PrizeStockAdjust, ip: str | None = None) -> PrizesResponse:
        prize = await self.prizes.get(prize_id)
        if prize is None:
            raise NotFoundError("奖品不存在")
        if prize.remain_stock + data.delta < 0:
            raise BadRequestError("活动已结束,无法添加奖品")
        if prize.total_stock + data.delta < 0:
            raise BadRequestError("总库存不能为负")

        updated = await self.prizes.adjust_stock(prize_id, data.delta, data.version)
        if not updated:
            raise ConflictError("库存已被其他操作修改， 请刷新后重试")
        await self.db.refresh(prize)
        await self._log(user, "adjust_stock", "prize", prize.id, {"delta": data.delta}, ip)
        await self.db.commit()
        cache = LotteryCacheService(self.db)
        await cache.set_stock(prize_id, prize.remain_stock)
        await cache.invalidate_activity(prize.activity_id)
        return await self._to_out(prize)

    async def delete_prize(self, user: User, prize_id: int, ip: str | None = None) -> None:
        prize = await self.prizes.get(prize_id)
        if prize is None:
            raise NotFoundError("奖品不存在")
        if await self.prizes.count_references(prize_id) > 0:
            raise BadRequestError("奖品已有抽奖/中奖记录，无法删除")
        prize.is_deleted = True
        await self.db.flush()
        await self._log(user, "delete", "prize", prize.id, None, ip)
        await self.db.commit()
        cache = LotteryCacheService(self.db)
        await cache.remove_stock(prize_id)
        await cache.invalidate_activity(prize.activity_id)


    # ---- 用户端 ----

    async def list_activity_prizes(self, activity_id: int) -> list[Prize]:
        """用户端奖品列表： 仅展示已发布活动中启用奖品"""
        await ActivityService(self.db).get_public(activity_id)
        items, _ = await self.prizes.list_prizes(
            activity_id = activity_id,
            status = PrizeStatus.ENABLED,
            page = 1,
            page_size = 100,
        )
        return items

    # ---- 内部方法 ----

    async def _ensure_category(self, category_id: int) -> None:
        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("奖品分类不存在")

    async def _category_map(self, category_ids: set[int]) -> dict[int, str]:
        if not category_ids:
            return {}
        stmt = select(PrizeCategory).where(PrizeCategory.id.in_(category_ids))
        rows = (await self.db.execute(stmt)).scalars().all()
        return {category.id: category.name for category in rows}

    async def _to_out(self, prize: Prize) -> PrizesResponse:
        out = PrizesResponse.model_validate(prize)
        out.category_name = None
        if prize.category_id is not None:
            category = await self.categories.get(prize.category_id)
            out.category_name = category.name if category is not None else None
        return out

    async def _log(self, user: User, action: str, target_type: str, target_id: int | None = None, detail: dict | None = None, ip: str | None = None) -> None:
        await self.operation_logs.add(
            OperationLog(
                user_id = user.id,
                module = "prize",
                action = action,
                target_type = target_type,
                target_id = target_id,
                detail_json= jsonable_encoder(detail) if detail else None,
                ip = ip,
            )
        )