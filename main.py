from fastapi import FastAPI

from db import initialize_db
from faq_router import router as faq_router
from config import Config


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Include routes
app.include_router(faq_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
