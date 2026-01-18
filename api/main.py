"""FastAPI application entry point."""

# Set matplotlib to non-interactive backend (fixes X server error in deployment)
import matplotlib
matplotlib.use('Agg')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_TITLE, API_DESCRIPTION, API_VERSION, CORS_ORIGINS
from api.dependencies import load_model_on_startup
from api.routes import health, predictions, data

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
@app.on_event("startup")
async def startup_event():
    """Load model when API starts."""
    load_model_on_startup()

# Include routers
app.include_router(health.router)
app.include_router(predictions.router)
app.include_router(data.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
