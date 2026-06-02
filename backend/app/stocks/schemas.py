from pydantic import BaseModel, ConfigDict, Field


class StockSearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str


class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]
