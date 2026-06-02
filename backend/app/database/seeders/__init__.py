from app.database.seeders.stock_detail import StockDetailSeeder
from app.database.seeders.supported_stocks import SupportedStocksSeeder

SEEDERS = [SupportedStocksSeeder(), StockDetailSeeder()]
