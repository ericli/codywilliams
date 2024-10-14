package datasource

import "github.com/ericli/lip/internal/marketdata"

type DataSource interface {
    Connect() error
    Disconnect() error
    Stream() <-chan marketdata.MarketData
}