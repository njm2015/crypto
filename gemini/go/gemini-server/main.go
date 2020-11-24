package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"

	"github.com/gorilla/websocket"
	_ "github.com/lib/pq"
)

const (
	url 		= "wss://api.gemini.com/v1/marketdata/BTCUSD?top_of_book=true"
	pgHost 		= "localhost"
	pgPort		= 5432
	pgDbName	= "crypto"
)

type EventData struct {
	Type 	string 	`json:"type"`
	Side 	string 	`json:"side"`
	Price 	string 	`json:"price"`
	Maker	string 	`json:"makerSide"`
	Remaining string `json:"remaining"`
	Amount	string 	`json:"amount"`
}

type TradeData struct {
	Type 	string 		`json:"type"`
	Id		float64 	`json:"eventId"`
	Ts		float64		`json:"timestampms"`
	Events	[]EventData `json:"events"`
}


func main() {
	
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	// u := url.URL{Scheme: "wss", Host: hostname, Path: path}
	log.Printf("connecting to %s", url)

	c, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s " + 
					"password=%s dbname=%s sslmode=disable",
					pgHost, pgPort, os.Getenv("DBUSER"), os.Getenv("DBPWD"), pgDbName)

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		log.Fatal("sql.Open: ", err)
	}
	defer db.Close()

	done := make(chan struct{})

	go func() {
		defer close(done)
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			var data TradeData
			json.Unmarshal(message, &data)

			for _, v := range data.Events {
				if v.Type == "change" {
					_, err := db.Exec(`INSERT INTO gemini_btc_bid_ask(ts, symbol, type, price, remaining) 
								 VALUES(TO_TIMESTAMP($1::double precision / 1000), 'BTC', $2, $3::decimal, $4::decimal)`, data.Ts, (v.Side == "ask"), v.Price, v.Remaining)
					if err != nil {
						panic(err)
					}
				} else {
					_, err := db.Exec(`INSERT INTO gemini_btc_trade(ts, symbol, type, price, amount) 
								 VALUES(TO_TIMESTAMP($1::double precision / 1000), 'BTC', $2, $3::decimal, $4::decimal)`, data.Ts, (v.Side == "ask"), v.Price, v.Amount)
					if err != nil {
						panic(err)
					}
				}
			}
			
			
		}
	}()

	for {
		select {
		case <- done:
			return
		case <-interrupt:
			log.Println("interrupt")
			err := c.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
			if err != nil {
				log.Println("write close:", err)
				return
			}
		}
	}
}
