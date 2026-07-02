from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import routes
from app.core.settings import settings
from app.dbs.postgres.context import DbContext

db = DbContext()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init(generate_schemas=False)
    try:
        yield
    finally:
        await db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://192.168.10.192:3000",
        "http://192.168.10.192:3001",
        "https://app.komite.cl",
        "https://admin.komite.cl",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("backoffice.html", {"request": request})


@app.get("/backoffice", response_class=HTMLResponse, include_in_schema=False)
async def backoffice_page(request: Request):
    return templates.TemplateResponse("backoffice.html", {"request": request})


@app.get("/backoffice/", include_in_schema=False)
async def backoffice_redirect():
    return RedirectResponse(url="/backoffice", status_code=302)


for router in routes.all_routers:
    app.include_router(router)


@app.get("/health")
async def health_check():
    return await db.check_connection()
