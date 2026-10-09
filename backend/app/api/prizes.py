"""奖品接口：分类管理、奖品管理、MinIO 图片上传、用户端奖品展示。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.minio import upload_image
from app.core.database import get_db
from app.models.enums import PrizeStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageParams, PaginatedResponse, ok
from app.schemas.prize import PrizeCategoryCreate, PrizeCategoryResponse, PrizeCategoryUpdate, PrizeCreate, PrizesResponse, PrizePublishResponse, PrizeStockAdjust, PrizeUpdate
from app.services.prize_service import PrizeService

public_router = APIRouter(prefix="/activities", tags=["活动-奖品"])
admin_router = APIRouter(prefix="/admin/prizes", tags=["管理-奖品"])
category_admin_router = APIRouter(prefix="/admin/prize-categories", tags=["管理-奖品分类"])
files_router = APIRouter(prefix="/admin/files", tags=["文件"])

def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@public_router.get("/{activity_id}/prizes", response_model=ApiResponse[list[PrizePublishResponse]])
async def list_activity_prizes(activity_id: int, db: AsyncSession = Depends(get_db)) -> ApiResponse[list[PrizePublishResponse]]:
    """用户端活动奖品列表"""
    return ok(await PrizeService(db).list_activity_prizes(activity_id))


@admin_router.get("", response_model=ApiResponse[PaginatedResponse[PrizesResponse]])
async def list_prizes(
        params: PageParams = Depends(),
        activity_id: int | None = None,
        category_id: int | None = None,
        keyword: str | None = None,
        status: PrizeStatus | None = None,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[PrizesResponse]]:
    """奖品分页列表（按活动/分类/关键字/状态筛选）"""
    items, total = await PrizeService(db).list_prizes(
        activity_id = activity_id,
        category_id = category_id,
        keyword = keyword,
        status = status,
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

@admin_router.post("", response_model=ApiResponse[PrizesResponse], status_code=201)
async def create_prize(
        data: PrizeCreate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizesResponse]:
    """创建奖品"""
    prize = await PrizeService(db).create_prize(
        current_user, data, ip=_client_ip(request)
    )
    return ok(prize, "奖品已创建")

@admin_router.get("/{prize_id}", response_model=ApiResponse[PrizesResponse])
async def get_prize(
        prize_id: int,
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizesResponse]:
    return ok(await PrizeService(db).get_prizes(prize_id))


@admin_router.put("/{prize_id}", response_model=ApiResponse[PrizesResponse])
async def update_prize(
        prize_id: int,
        data: PrizeUpdate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizesResponse]:
    return ok(await PrizeService(db).update_prize(current_user, prize_id, data, ip=_client_ip(request)), "奖品已更新")


@admin_router.put("/{prize_id}/stock", response_model=ApiResponse[PrizesResponse])
async def adjust_prize(
        prize_id: int,
        data: PrizeStockAdjust,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizesResponse]:
    """库存调整（乐观锁： 携带当前 version, 冲突返回409）"""
    prize = await PrizeService(db).adjust_stock(current_user, prize_id, data, ip=_client_ip(request))
    return ok(prize, "库存已调整")


@admin_router.delete("/{prize_id}", response_model=ApiResponse[None])
async def delete_prize(
        prize_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """删除奖品（软删除，已有中奖/抽奖记录时拒绝）"""
    await PrizeService(db).delete_prize(current_user, prize_id, ip=_client_ip(request))
    return ok(message="奖品已删除")


@category_admin_router.get("", response_model=ApiResponse[list[PrizeCategoryResponse]])
async def list_categories(
        _: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PrizeCategoryResponse]]:
    """奖品分类"""
    return ok(await PrizeService(db).list_categories())


@category_admin_router.post("", response_model=ApiResponse[PrizeCategoryResponse])
async def create_category(
        data: PrizeCategoryCreate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizeCategoryResponse]:
    """创建奖品分类"""
    category = await PrizeService(db).create_category(current_user, data, ip=_client_ip(request))
    return ok(category, "分类已创建")


@category_admin_router.put("/{category_id}", response_model=ApiResponse[PrizeCategoryResponse])
async def update_category(
        category_id: int,
        data: PrizeCategoryUpdate,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[PrizeCategoryResponse]:
    """更新奖品分类"""
    category = await PrizeService(db).update_category(
        current_user, category_id, data, ip=_client_ip(request)
    )
    return ok(category, "分类已更新")


@category_admin_router.delete("/{category_id}", response_model=ApiResponse[None])
async def delete_category(
        category_id: int,
        request: Request,
        current_user: User = Depends(require_roles("admin", "operator")),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """删除奖品分类（被引用时拒绝）"""
    await PrizeService(db).delete_category(current_user, category_id, ip=_client_ip(request))
    return ok(message="分类已删除")

@files_router.post("/images", response_model=ApiResponse[dict], status_code=201)
async def upload_image_file(
        file: UploadFile = File(...),
        _: User = Depends(require_roles("admin", "operator")),
) -> ApiResponse[dict]:
    """上传图片到MinIo，返回公开访问的URL"""
    url = await upload_image(file)
    return ok({"url": url}, "上传成功")