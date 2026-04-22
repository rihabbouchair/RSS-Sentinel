
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import threading
from pipeline import run_pipeline
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routes import users, articles, feeds, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting RSS Sentinel backend...")
    init_db()
    start_scheduler()
    @app.on_event("startup")
    async def startup_event():
        init_db()
        start_scheduler()
        # Run pipeline once immediately on startup
        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()
    yield
    # Shutdown
    print("Shutting down RSS Sentinel backend...")
    stop_scheduler()

app = FastAPI(title="RSS Sentinel", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(feeds.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "RSS Sentinel API", "status": "running"}
