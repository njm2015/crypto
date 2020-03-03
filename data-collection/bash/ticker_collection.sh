#!/bin/bash

SYMBOLS=$(sed '$!s/$/,/' symbols.txt | tr -d '\n')
echo $SYMBOLS

OUTPUT=$(curl "https://api.nomics.com/v1/currencies/ticker?key=040639f478bc2578a18b992f06b6e3da&ids=$SYMBOLS&interval=1h" \
| jq '.[] | [.symbol, .price, ."1h".volume]')

FORMATTED_OUTPUT=$(echo $OUTPUT | \
perl -p -e 's/\] \[/\), \(/g' | \
perl -p -e 's/\]/\)/g' | \
perl -p -e 's/\[/\(/g' | \
perl -p -e 's/\"(?=\d)//g' | \
perl -p -e 's/(?<=\d)\"//g' | \
perl -p -e s/\"/\'/g)

echo $FORMATTED_OUTPUT

INSERTSTR="sudo mysql nomics -e \"insert into 10sec (symbol, price, volume) values$FORMATTED_OUTPUT\""
echo $INSERTSTR
eval $INSERTSTR