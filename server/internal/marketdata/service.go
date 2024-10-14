package main

import (
	"sync"
)

type MarketDataService struct {
	sources        map[string]DataSource
	dataChannel    chan MarketData
	subscribers    map[string][]chan MarketData
	subscribersMux sync.RWMutex
}

type DataSource interface {
	Connect() error
	Disconnect() error
	Stream() <-chan MarketData
}

type MarketData struct {
	Symbol string
	Price  float64
	Volume int64
	// Add other relevant fields
}

func NewMarketDataService() *MarketDataService {
	return &MarketDataService{
		sources:     make(map[string]DataSource),
		dataChannel: make(chan MarketData, 1000),
		subscribers: make(map[string][]chan MarketData),
	}
}

func (mds *MarketDataService) AddSource(name string, source DataSource) {
	mds.sources[name] = source
}

func (mds *MarketDataService) Start() error {
	for _, source := range mds.sources {
		if err := source.Connect(); err != nil {
			return err
		}
		go mds.consumeSource(source)
	}
	go mds.distributeData()
	return nil
}

func (mds *MarketDataService) consumeSource(source DataSource) {
	for data := range source.Stream() {
		mds.dataChannel <- data
	}
}

func (mds *MarketDataService) distributeData() {
	for data := range mds.dataChannel {
		mds.subscribersMux.RLock()
		for _, subs := range mds.subscribers[data.Symbol] {
			select {
			case subs <- data:
			default:
				// Skip if subscriber's channel is full
			}
		}
		mds.subscribersMux.RUnlock()
	}
}

func (mds *MarketDataService) Subscribe(symbol string) <-chan MarketData {
	ch := make(chan MarketData, 100)
	mds.subscribersMux.Lock()
	mds.subscribers[symbol] = append(mds.subscribers[symbol], ch)
	mds.subscribersMux.Unlock()
	return ch
}

// Implement Unsubscribe, WebSocket handlers, and HTTP API handlers here

func main() {
	mds := NewMarketDataService()
	// Add data sources, start the service, and set up API servers here
}