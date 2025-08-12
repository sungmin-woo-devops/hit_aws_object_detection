from .auth import router as auth_router
from .data import router as data_router

routers = [auth_router, data_router]