from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.stocks.router import router as stocks_router

app = FastAPI(title="Trendwise API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+):8081$",
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stocks_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
