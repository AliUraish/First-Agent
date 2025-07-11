from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, flags, email_sorting
from app.database import init_db

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(auth.router)
app.include_router(flags.router)
app.include_router(email_sorting.router)

@app.get("/")
def read_root():
    return {"message": "Email Flag Agent API"} 