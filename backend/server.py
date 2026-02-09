from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="GrantFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register all routers
from routes.auth import router as auth_router, set_db as auth_set_db
from routes.organizations import router as org_router, set_db as org_set_db
from routes.projects import router as project_router, set_db as project_set_db
from routes.documents import router as doc_router, set_db as doc_set_db
from routes.compliance import router as compliance_router, set_db as compliance_set_db
from routes.marketplace import router as marketplace_router, set_db as marketplace_set_db
from routes.admin import router as admin_router, set_db as admin_set_db
from routes.funding import router as funding_router, set_db as funding_set_db
from routes.agents import router as agents_router, set_db as agents_set_db
from routes.integrations import router as integrations_router, set_db as integrations_set_db
from middleware.auth_middleware import set_rbac_db

# Set DB references
set_rbac_db(db)
auth_set_db(db)
org_set_db(db)
project_set_db(db)
doc_set_db(db)
compliance_set_db(db)
marketplace_set_db(db)
admin_set_db(db)
funding_set_db(db)
agents_set_db(db)
integrations_set_db(db)

# Include routers
app.include_router(auth_router)
app.include_router(org_router)
app.include_router(project_router)
app.include_router(doc_router)
app.include_router(compliance_router)
app.include_router(marketplace_router)
app.include_router(admin_router)
app.include_router(funding_router)
app.include_router(agents_router)
app.include_router(integrations_router)

@app.get("/api")
async def root():
    return {"message": "GrantFlow API v1.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
