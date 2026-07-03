import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.database.connection import init_db
from app.routes import complaints, analytics, websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes tables on backend startup."""
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down application...")

# Initialize app
app = FastAPI(
    title="Bank Complaint Intelligence System API",
    description="Local AI-powered banking complaints processing and analytics system",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local cross-origin connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(complaints.router)
app.include_router(analytics.router)
app.include_router(websockets.router)

# Mount static folder for assets (shared CSS, JS files, images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Convenient routing for frontend apps
@app.get("/")
async def root():
    """Redirect root to the complaint submission web page."""
    return RedirectResponse(url="/submit")

@app.get("/submit")
async def serve_submit():
    """Serves the Complaint Submission web portal."""
    return FileResponse("app/static/submit/index.html")

@app.get("/dashboard")
async def serve_dashboard():
    """Serves the Analytics Dashboard web portal."""
    return FileResponse("app/static/dashboard/index.html")
