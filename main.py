from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.lead_created import LEAD_CREATED_ROUTER

app = FastAPI()

app.include_router(LEAD_CREATED_ROUTER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
