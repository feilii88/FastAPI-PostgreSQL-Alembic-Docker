from fastapi import Depends, FastAPI

from app.router import user_router

# Create the FastAPI app
app = FastAPI()

# Index route
@app.get("/")
async def index():
    return {"message": "Master Server API"}

app.include_router(user_router, prefix="/api")