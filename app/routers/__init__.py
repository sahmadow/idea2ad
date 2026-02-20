from .auth import router as auth_router
from .images import router as images_router
from .campaigns import router as campaigns_router
from .replica import router as replica_router
from .quick import router as quick_router
from .carousel import router as carousel_router
from .v2 import router as v2_router
from .playground import router as playground_router
from .adpack import router as adpack_router
from .competitor import router as competitor_router

__all__ = ["auth_router", "images_router", "campaigns_router", "replica_router", "quick_router", "carousel_router", "v2_router", "playground_router", "adpack_router", "competitor_router"]
