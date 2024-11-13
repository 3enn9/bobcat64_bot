from aiogram import Router

from .group import router as group_router
from .users import router as users_router


router = Router(name=__name__)
router.include_routers(group_router, users_router)

__all__ = ('router',)