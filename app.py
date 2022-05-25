import os, csv
import talib
import yfinance as yf
import pandas
from flask import Flask, escape, request, render_template
from patterns import candlestick_patterns
import plotly.offline as po
import plotly.graph_objs as go

app = Flask(__name__)
app.debug = True

@app.route('/snapshot')
def snapshot():
    with open('datasets/symbols_nse.csv') as f:
        for line in f:
            symbol = line
            data = yf.download(symbol, start="2022-01-01", end="2022-05-19")
            data.to_csv('datasets/daily/{}.csv'.format(symbol.strip().split('.')[0]))

    return {
        "code": "success"
    }

def get_chart(df,symbol):
    df['Date'] = pandas.to_datetime(df['Date'],errors='coerce',format='%Y-%m-%d')

    df=df.set_index('Date')
    df=df.tail(70)

    trace = go.Candlestick(x=df.index,open=df['Open'],high=df['High'],low=df['Low'],close=df['Close'],
                            name = symbol)
    
    data = [trace]
    
    layout = {'title':''}
    fig = go.Figure()
    fig = dict(data=data)
    
    filename=symbol+'.html'
    po.plot(fig, filename='templates/'+filename,auto_open=False)


@app.route('/')
def index():
    pattern  = request.args.get('pattern', False)
    stocks = {}

    with open('datasets/symbols_nse.csv') as f:
        print(csv.reader(f))
        for row in csv.reader(f):
            
            stocks[row[0].split('.')[0]] = {'company': row[0].split('.')[0]}

    if pattern:
        for filename in os.listdir('datasets/daily'):
            df = pandas.read_csv('datasets/daily/{}'.format(filename))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]
            

            try:
                results = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                #print(results)
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                    get_chart(df,symbol)
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                    get_chart(df,symbol)

                elif last == 0:
                    stocks[symbol][pattern] = None
                    
            except Exception as e:
                print('failed on filename: ', e)

    return render_template('index.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)
