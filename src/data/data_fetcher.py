import asyncio
from typing import List, Dict
from datetime import datetime, timedelta
from polygon import RESTClient
from dataclasses import dataclass
import pandas as pd
import logging

@dataclass
class MarketData:
    timestamp: datetime
    symbol: str
    price: float
    volume: int

class DataFetcher:
    def __init__(self, api_key: str, symbols: List[str], batch_size: int = 5):
        if not api_key:
            raise ValueError("API key is required")
        if not symbols:
            raise ValueError("At least one symbol is required")
        if batch_size < 1:
            raise ValueError("Batch size must be positive")
        
        self.client = RESTClient(api_key)
        self.symbols = symbols
        self.batch_size = batch_size # batch when calling fetch_all
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for latest data point for each stock
        self._cache: Dict[str, MarketData] = {}
        
    async def fetch_minute_stock_data(self, symbol: str, start_time: datetime) -> List[MarketData]:
        """Fetch minute-by-minute data for a single symbol"""
        try:
            bars = self.client.get_aggs(
                symbol,
                1,  # 1 minute multiplier
                "minute",
                start_time,
                start_time + timedelta(minutes=1000)  # Polygon limit
            )
            
            return [
                MarketData(
                    timestamp=datetime.fromtimestamp(bar.timestamp/1000),
                    symbol=symbol,
                    price=bar.close,
                    volume=bar.volume
                )
                for bar in bars
            ]
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return []
    
    async def fetch_stock_batch(self, symbols: List[str], start_time: datetime) -> List[MarketData]:
        """Fetch data for a batch of symbols concurrently"""
        tasks = [
            self.fetch_minute_stock_data(symbol, start_time)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results for item in sublist]
    
    async def fetch_stock_all(self, start_time: datetime) -> pd.DataFrame:
        """Fetch data for all stock symbols in batches. """
        all_data = []
        
        for i in range(0, len(self.symbols), self.batch_size):
            batch_symbols = self.symbols[i:i + self.batch_size]
            batch_data = await self.fetch_stock_batch(batch_symbols, start_time)
            all_data.extend(batch_data)
            
            # Rate limiting - be nice to the API
            await asyncio.sleep(0.2)
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame([
            {
                'timestamp': d.timestamp,
                'symbol': d.symbol,
                'price': d.price,
                'volume': d.volume
            }
            for d in all_data
        ])
        
        return df

    def update_cache(self, data: MarketData):
        """Update the in-memory cache with latest data point"""
        self._cache[data.symbol] = data     