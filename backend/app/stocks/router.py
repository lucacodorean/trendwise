from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.stocks.repository import StockSearchRepository, get_stock_search_repository
from app.stocks.schemas import StockSearchResponse, StockSearchResult


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=StockSearchResponse, operation_id="searchStocks")
def search_stocks(
    repository: Annotated[StockSearchRepository, Depends(get_stock_search_repository)],
    q: Annotated[str, Query()] = "",
) -> StockSearchResponse:
    rows = repository.examples() if q.strip() == "" else repository.search(q)
    return StockSearchResponse(
        results=[
            StockSearchResult(
                ticker=row["ticker"],
                company_name=row["company_name"],
                exchange=row["exchange"],
            )
            for row in rows
        ]
    )
