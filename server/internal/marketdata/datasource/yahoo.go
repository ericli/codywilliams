package datasource

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/ericli/lip/internal/marketdata"
)

const (
	yahooFinanceBaseURL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%s"
)

type YahooFinanceDataSource struct {
	client     *http.Client
	dataStream chan marketdata.MarketData
	symbols    []string
}

func NewYahooFinanceDataSource(symbols []string) *YahooFinanceDataSource {
	return &YahooFinanceDataSource{
		client:     &http.Client{Timeout: 10 * time.Second},
		dataStream: make(chan marketdata.MarketData, 100),
		symbols:    symbols,
	}
}

func (yf *YahooFinanceDataSource) Connect() error {
	go yf.fetchDataPeriodically()
	return nil
}

func (yf *YahooFinanceDataSource) Disconnect() error {
	close(yf.dataStream)
	return nil
}

func (yf *YahooFinanceDataSource) Stream() <-chan marketdata.MarketData {
	return yf.dataStream
}

func (yf *YahooFinanceDataSource) fetchDataPeriodically() {
	ticker := time.NewTicker(5 * time.Second)
	for {
		<-ticker.C
		yf.fetchRealtimeData()
	}
}

func (yf *YahooFinanceDataSource) fetchRealtimeData() {
	symbolString := strings.Join(yf.symbols, ",")
	url := fmt.Sprintf(yahooFinanceBaseURL, symbolString)

	resp, err := yf.client.Get(url)
	if err != nil {
		fmt.Printf("Error fetching data: %v\n", err)
		return
	}
	defer resp.Body.Close()

	var result struct {
		QuoteResponse struct {
			Result []struct {
				Symbol string  `json:"symbol"`
				Price  float64 `json:"regularMarketPrice"`
				Volume int64   `json:"regularMarketVolume"`
			} `json:"result"`
		} `json:"quoteResponse"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		fmt.Printf("Error decoding response: %v\n", err)
		return
	}

	for _, quote := range result.QuoteResponse.Result {
		marketData := marketdata.MarketData{
			Symbol: quote.Symbol,
			Price:  quote.Price,
			Volume: quote.Volume,
		}
		yf.dataStream <- marketData
	}
}
