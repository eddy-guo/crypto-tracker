from flask import Flask, request, render_template, redirect, url_for
import requests, redis, ast, jinja_partials, os

etherscan_key = os.getenv('ETHERSCAN_KEY')
moralis_key = os.getenv('MORALIS_KEY')

app = Flask(__name__, static_folder="styles")

r = redis.Redis(
  host= 'global-oriented-frog-31783.upstash.io',
  port= '31783',
  password= 'ce7afed7b4db4ce0a271bccf9b1480b1')

jinja_partials.register_extensions(app)

@app.route('/', methods=['GET','POST'])
def home():
    return render_template('home.html')

@app.route('/coin', methods=['GET', 'POST'])
def coin():
    return render_template('coin.html')

@app.route('/coin/info', methods=['GET','POST'])

def coin_info():
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    if "coin" not in data:
        print("coin does not exist")
        return redirect("/coin")
    requested_coin = data["coin"]
    if len(requested_coin) == 0:
        print("no coin inputted")
        return redirect("/coin")
    cached_coin = r.get(requested_coin)

    if cached_coin:
        print("CACHED") # terminal notification
        dict_coin = ast.literal_eval(cached_coin.decode())
        return render_template('coincache.html', dict_coin=dict_coin)
    else:
        print("NOT CACHED") # terminal notification
        data = requests.get(f'https://api.coingecko.com/api/v3/coins/{requested_coin}')
        coin_json = data.json()
        if "error" in coin_json:
            return redirect("/coin")
        else: # if requested_coin == coin_json["id"]:
            coin_info = {
                "name": coin_json["name"],
                "priceusd": str(coin_json["market_data"]["current_price"]["usd"]),
                "symbol": coin_json["symbol"],
                "image": coin_json["image"]["large"],
                "launch_date": coin_json["genesis_date"],
                "description": coin_json["description"]["en"],
                "homepage_link": coin_json["links"]["homepage"][0],
                "market_cap_rank": coin_json["market_cap_rank"]
            }
            r.set(requested_coin, str(coin_info), ex=30)
            return render_template('coininfo.html', coin_info=coin_info)

@app.route('/exchange', methods=['GET','POST'])
def exchange():
    return render_template('exchange.html')

@app.route('/exchange/info', methods=['GET','POST'])
def exchange_info():
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    if "exchange" not in data:
        print("exchange does not exist")
        return redirect("/exchange")
    requested_exchange = data["exchange"]
    if len(requested_exchange) == 0:
        print("no exchange inputted")
        return redirect("/exchange")
    # cached_exchange = r.get(requested_exchange); no cache, updating exchange information is unnecessary

    print("NOT CACHED")
    data = requests.get(f'https://api.coingecko.com/api/v3/exchanges/{requested_exchange}')
    exchange_json = data.json()
    if "error" in exchange_json:
        return redirect("/exchange")
    else:
        exchange_info = {
            "name": exchange_json["name"],
            "year_established": exchange_json["year_established"],
            "country": exchange_json["country"],
            "description": exchange_json["description"],
            "url": exchange_json["url"],
            # check if exchange has status update, bigger picture available
            "image": exchange_json["status_updates"][0]["project"]["image"]["large"] if exchange_json["status_updates"] else exchange_json["image"]
        }
        return render_template('exchangeinfo.html', exchange_info=exchange_info)

@app.route('/address', methods=['GET', 'POST'])
def address():
    return render_template('address.html')


@app.route('/address/info', methods=['GET', 'POST'])
def address_info():
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.form.to_dict()

    if "address" not in data:
        print("address does not exist")
        return redirect("/address")
    requested_address = data["address"]
    if len(requested_address) == 0:
        print("no address inputted")
        return redirect("/address")
    cached_address = r.get(requested_address)

    if cached_address:
        print("CACHED") # terminal notification
        dict_address = ast.literal_eval(cached_address.decode())
        return render_template('addresscache.html', dict_address=dict_address)
    else:
        print("NOT CACHED")
        headers = {
        'accept': 'application/json',
        'X-API-Key': moralis_key,
        }
        data = requests.get(f'https://api.etherscan.io/api?module=account&action=balance&address={requested_address}&tag=latest&apikey={etherscan_key}')
        data2 = requests.get(f'https://deep-index.moralis.io/api/v2/{requested_address}/nft?chain=eth&format=decimal', headers=headers)   
        if str(data2) == "<Response [404]>":
            return redirect("/address")
        address_json = data.json()
        nft_json = data2.json()
        if "0" in address_json["status"]:
            return redirect("/address")
        else:                
            address_info = {
                "address": requested_address,
                "price": int(address_json["result"]) / 10**18,
                "count": nft_json["total"],
                "list": nft_json["result"]
            }
        r.set(requested_address, str(address_info), ex=30)
        return render_template("addressinfo.html",address_info=address_info)

if __name__ == '__main__':
      app.run(debug=True)
