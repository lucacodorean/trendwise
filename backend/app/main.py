from fastapi import FastAPI

from app.stocks.router import router as stocks_router

app = FastAPI(title="Trendwise API")
app.include_router(stocks_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
