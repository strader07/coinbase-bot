
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from django import template
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

import cbpro
from app.config import *
from app.models import *

import json
import websocket
import requests
from threading import Thread
import time
import math
import talib
import pandas as pd
import numpy as np


@login_required(login_url="/login/")
def index(request):
    accounts = Account.objects.all()
    settings = Setting.objects.all()
    balances = Balance.objects.all()
    portfolios = Portfolio.objects.all()
    context = {}
    context["portfolios"] = portfolios
    if accounts.count() > 0:
        data = [
            {
                'portfolio': account.portfolio.id,
                'currency': account.currency,
                'balance': account.balance,
                'hold': account.hold,
                'available': account.available,
                'last_balance': account.last_balance,
                'percent_chng': account.percent_chng,
                'can_trade': account.can_trade
            } for account in accounts
        ]
    else:
        data=[]

    context['data'] = json.dumps(data)
    for portfolio in portfolios:
        if portfolio.acc_type == "LIVE":
            sub_data = [item for item in data if item["portfolio"]==portfolio.id]
            context['currencies'] = [sub_data[i*3:(i+1)*3] for i in range(len(sub_data)//3)]
            break

    if balances.count() > 0:
        balance = balances[0]
        context['balance'] = {
            "balance_usd": balance.balance_usd,
            "balance_btc": balance.balance_btc,
            "balance3": balance.balance3,
            "currency3": balance.currency3
        }
    else:
        context['balance'] = {}

    if settings.count() > 0:
        setting = settings[0]
        context['setting'] = {
            'trade_status': setting.trade_status,
            'potential_trade': setting.potential_trade,
            'trade_btc': setting.trade_btc,
            'trade_usd': setting.trade_usd
        }
    context['segment'] = 'index'
    html_template = loader.get_template( 'index.html' )
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    try:
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:

        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def update_tradecurrency(request):
    if request.method == "POST":
        try:
            setting = Setting.objects.all()[0]
        except:
            setting = None
            pass

        accounts = Account.objects.all()
        for account in accounts:
            can_trade = request.POST.get(account.currency)
            can_trade = True if can_trade == "on" else False
            if account.can_trade == can_trade:
                continue
            account.can_trade = can_trade
            account.save()

        messages.info(request, "Your settings successfully saved!")
        return redirect("/")
    else:
        return redirect("/")


def check_trade_status():
    try:
        setting = Setting.objects.all()[0]
        if setting.trade_status:
            return True
    except:
        return False

    return False


def update_account(request):
    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        api_key = portfolio.api_key
        api_secret = portfolio.api_secret
        passphrase = portfolio.passphrase
        if str(portfolio.acc_type).upper() == "LIVE":
            auth_client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase)
        else:
            api_url = SANDBOX_API_URL
            auth_client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase, api_url=api_url)

        accounts = auth_client.get_accounts()
        print(accounts)
        old_accounts = Account.objects.filter(portfolio=portfolio.id)
        if old_accounts.count() > 0:
            for acc in old_accounts:
                new_acc = [item for item in accounts if item["currency"]==acc.currency][0]
                if acc.balance != new_acc["balance"] or acc.hold != new_acc["hold"] or acc.available != new_acc["available"]:
                    acc.balance = new_acc["balance"]
                    acc.hold = new_acc["hold"]
                    acc.available = new_acc["available"]
                    acc.save()

    messages.info(request, "Accounts successfully updated!")

        # bal_accounts = [acc for acc in accounts if float(acc["available"]) > 0]
        # try:
        #     balance = Balance.objects.all()[0]
        # except:
        #     return redirect("/")
        
        # try:
        #     balance_usd, balance_btc, balance3 = get_total_balance(bal_accounts, balance.currency3)
        # except:
        #     return redirect("/")

        # balance.balance_usd = balance_usd
        # balance.balance_btc = balance_btc
        # balance.balance3 = balance3
        # balance.save()

    return redirect("/")

@csrf_exempt
def update_balance(request):
    if request.method == "POST":
        currency3 = request.POST.get("currency3")
        print(currency3)
        if not currency3:
            messages.error(request, "Invalid currency requested!")
            return redirect("/")

        accounts = auth_client.get_accounts()

        old_accounts = Account.objects.all()
        if old_accounts.count() > 0:
            for acc in old_accounts:
                new_acc = [item for item in accounts if item["currency"]==acc.currency][0]
                acc.id = new_acc["currency"]
                acc.currency = new_acc["currency"]
                acc.balance = new_acc["balance"]
                acc.hold = new_acc["hold"]
                acc.available = new_acc["available"]
                acc.save()

        bal_accounts = [acc for acc in accounts if float(acc["available"]) > 0]
        balances = Balance.objects.all()
        if balances.count() > 0:
            balance = balances[0]
        else:
            balance = Balance(
                balance_usd="0",
                balance_btc="0",
                balance3="0",
                currency3=currency3
                )

        balance.currency3 = currency3
        try:
            balance_usd, balance_btc, balance3 = get_total_balance(bal_accounts, currency3)
        except Exception as e:
            messages.error(request, "Invalid currency!")
            return redirect("/")

        balance.balance_usd = balance_usd
        balance.balance_btc = balance_btc
        balance.balance3 = balance3

        balance.save()

    messages.info(request, "Successfully updated the total balance.")
    return redirect("/")

@csrf_exempt
def run_trade(request):
    if not check_trade_status():
        return HttpResponse("Trade is off, make sure your turn on before applying any orders!")

    if request.method == "POST":
        res = json.loads(request.body)
        pairs = res["pair"]
        side = res["side"]

        try:
            pair1 = pairs.split("/")[0]
            pair2 = pairs.split(":")[1]
        except Exception as e:
            print(e)
            return HttpResponse("Unsupported pair!")

        if side == "DOWN":
            buypair = pair1
            sellpair = pair2
        else:
            buypair = pair2
            sellpair = pair1

        quote_currency_buy = ""
        quote_currency_sell = ""
        for qp in QUOTE_PAIRS:
            if qp == buypair[-len(qp):]:
                buy_currency = qp
                buypair = buypair.replace(qp, "-"+qp)
            if qp == sellpair[-len(qp):]:
                sell_currency = qp
                sellpair = sellpair.replace(qp, "-"+qp)
                sell_currency = sellpair.split("-")[0]

        if not buy_currency or not sell_currency:
            return HttpResponse("Unsuppoted pairs!")

        print(buy_currency, sell_currency)
        print(buypair, sellpair)

        accounts = auth_client.get_accounts()
        update_account_stats(accounts, sellpair, "SELL")

        sell_balance = float([account["available"] for account in accounts if account["currency"]==sell_currency][0])
        sell_size = get_trade_size(sellpair, sell_balance, "SELL")

        sellpairbook = auth_client.get_product_order_book(sellpair, level=2)
        is_liquid = check_liquidity(sellpair, sellpairbook, sell_size, "SELL")
        if not is_liquid:
            return HttpResponse(f"{sellpair} market is not liquid!")

        sellorder = auth_client.place_order(sellpair, "sell", "market", size=sell_size)
        print(sellorder)

        accounts = auth_client.get_accounts()
        buy_balance = float([account["available"] for account in accounts if account["currency"]==buy_currency][0])
        buy_size = get_trade_size(buypair, buy_balance, "BUY")

        buypairbook = auth_client.get_product_order_book(buypair, level=2)
        is_liquid = check_liquidity(buypair, buypairbook, buy_size, "BUY")
        if not is_liquid:
            return HttpResponse(f"{buypair} market is not liquid!")

        buyorder = auth_client.place_order(buypair, "buy", "market", funds=buy_size)
        print(buyorder)

        accounts = auth_client.get_accounts()
        update_accounts(accounts)
        update_account_stats(accounts, buypair, "BUY")

        return HttpResponse("Trade Executed!")
    else:
        print("OK")
        return HttpResponse("Invalid Request Method!")


@login_required(login_url="/login/")
def get_portfolio(request):
    context = {}
    portfolios = Portfolio.objects.all()
    context["portfolios"] = portfolios
    context['segment'] = 'portfolio'
    return render(request, "portfolio.html", context)


def validate_api(acc_type, passphrase, api_key, api_secret):
    if acc_type == "LIVE":
        api_url = "https://api.pro.coinbase.com"
    else:
        api_url = "https://api-public.sandbox.pro.coinbase.com"

    print(api_url)
    print(passphrase)
    print(api_key)
    print(api_secret)

    try:
        client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase, api_url=api_url)
        accounts = client.get_accounts()
        if type(accounts) is list and len(accounts) > 1:
            return True
        else:
            return False
    except Exception as e:
        return False


@login_required(login_url="/login/")
def new_portfolio(request):
    if request.method == "POST":
        name = request.POST.get("name")
        acc_type = request.POST.get("acc_type")
        passphrase = request.POST.get("passphrase")
        api_key = request.POST.get("api_key")
        api_secret = request.POST.get("api_secret")

        if not validate_api(acc_type, passphrase, api_key, api_secret):
            messages.error(request, "API auth failed, credentials not valid!")
            return redirect("/portfolio/")

        portfolio = Portfolio(
            name=name,
            acc_type=acc_type,
            passphrase=passphrase,
            api_key=api_key,
            api_secret=api_secret
        )
        portfolio.save()
        messages.info(request, "New portfolio successfully created!")

        return redirect("/portfolio/")
    else:
        context = {}
        context['segment'] = 'portfolio'
        return render(request, "new-portfolio.html", context)


@login_required(login_url="/login/")
def edit_portfolio(request, pk=0):
    try:
        portfolio = Portfolio.objects.get(id=pk)
        if request.method == "GET":
            context = {}
            context['segment'] = 'portfolio'
            context['portfolio'] = portfolio
            context['pk'] = pk
            return render(request, "edit-portfolio.html", context)
        else:
            name = request.POST.get("name")
            acc_type = request.POST.get("acc_type")
            passphrase = request.POST.get("passphrase")
            api_key = request.POST.get("api_key")
            api_secret = request.POST.get("api_secret")

            if not validate_api(acc_type, passphrase, api_key, api_secret):
                messages.error(request, "API auth failed, credentials not valid!")
                return redirect("/portfolio/")

            portfolio.name = name
            portfolio.acc_type = acc_type
            portfolio.passphrase = passphrase
            portfolio.api_key = api_key
            portfolio.api_secret = api_secret
            portfolio.save()

            messages.info(request, "The portfolio successfully updated!")
            return redirect("/portfolio/")
    except Exception as e:
        messages.error(request, e)
        return redirect("/portfolio/")


@login_required(login_url="/login/")
def del_portfolio(request, pk=0):
    try:
        portfolio = Portfolio.objects.get(id=pk)
        portfolio.delete()

        messages.info(request, "The portfolio successfully deleted!")
        return redirect("/portfolio/")
    except Exception as e:
        messages.error(request, e)
        return redirect("/portfolio/")


@login_required(login_url="/login/")
def delete_portfolios(request):
    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        portfolio.delete()
    return redirect("/portfolio/")


@login_required(login_url="/login/")
def get_bots(request):
    context = {}
    bots = BotConfiguration.objects.all()
    context["bots"] = bots
    context["segment"] = 'bot'
    return render(request, "bots.html", context)


@login_required(login_url="/login/")
def new_bot(request):
    if request.method == "POST":
        name = request.POST.get("name")
        portfolio_id = int(request.POST.get("portfolio"))
        portfolio = Portfolio.objects.get(id=portfolio_id)
        symbol = request.POST.get("symbol")
        timeframe = request.POST.get("timeframe")
        price_var = float(request.POST.get("price_var"))
        is_active = request.POST.get("is_active")
        if is_active == "on":
            is_active = True
        else:
            is_active = False

        bot = BotConfiguration(
            name=name,
            portfolio=portfolio,
            is_active=is_active,
            symbol=symbol,
            timeframe=timeframe,
            price_var=price_var
        )
        bot.save()
        messages.info(request, "New bot successfully created!")

        return redirect("/bot/")
    else:
        portfolios = Portfolio.objects.all()
        context = {}
        context['portfolios'] = portfolios
        context["segment"] = 'bot'
        return render(request, "new-bot.html", context)


@login_required(login_url="/login/")
def edit_bot(request, pk=0):
    try:
        bot = BotConfiguration.objects.get(id=pk)
        if request.method == "GET":
            portfolios = Portfolio.objects.all()
            context = {}
            context["segment"] = 'bot'
            context["bot"] = bot
            context["portfolios"] = portfolios
            context["pk"] = pk
            return render(request, "edit-bot.html", {"bot": bot, "pk":pk, "portfolios":portfolios})
        else:
            name = request.POST.get("name")
            portfolio_id = int(request.POST.get("portfolio"))
            portfolio = Portfolio.objects.get(id=portfolio_id)
            symbol = request.POST.get("symbol")
            timeframe = request.POST.get("timeframe")
            price_var = float(request.POST.get("price_var"))
            is_active = request.POST.get("is_active")
            if is_active == "on":
                is_active = True
            else:
                is_active = False

            bot.name = name
            bot.portfolio = portfolio
            bot.is_active = is_active
            bot.symbol = symbol
            bot.timeframe = timeframe
            bot.price_var = price_var
            bot.save()

            messages.info(request, "The bot successfully updated!")
            return redirect("/bot/")
    except Exception as e:
        messages.error(request, e)
        return redirect("/bot/")


@login_required(login_url="/login/")
def del_bot(request, pk=0):
    try:
        bot = BotConfiguration.objects.get(id=pk)
        bot.delete()

        messages.info(request, "The bot successfully deleted!")
        return redirect("/bot/")
    except Exception as e:
        messages.error(request, e)
        return redirect("/bot/")


@login_required(login_url="/login/")
def delete_bots(request):
    bots = BotConfiguration.objects.all()
    for bot in bots:
        bot.delete()
    return redirect("/bot/")


def update_account_stats(accs, pair, side, portfolio):
    currency = pair.split("-")[0]
    accounts = Account.objects.filter(portfolio=portfolio.id)
    account = accounts[0]
    for acc in accounts:
        if currency == acc.currency:
            account = acc
            break
    acc = [x for x in accs if x["currency"]==currency][0]

    if side == "SELL":
        account.last_balance = account.balance
        account.save()
        return 0
    else:
        account.balance = acc["balance"]
        perc_chng = (float(account.balance) - float(account.last_balance))*100/float(account.last_balance)
        account.percent_chng = str(round(perc_chng, 4))
        account.save()


def get_trade_size(pair, balance, side):
    if side == "SELL":
        sell_bal = balance*0.995
        sell_pair = pair

        sellOrderMin = CB_MARKETS[CB_MARKETS["MARKET"]==sell_pair].iloc[0]["BASE ORDER MIN"]
        sellOrderMax = CB_MARKETS[CB_MARKETS["MARKET"]==sell_pair].iloc[0]["BASE ORDER MAX"]
        sellTick = CB_MARKETS[CB_MARKETS["MARKET"]==sell_pair].iloc[0]["BASE TICK SIZE"]

        buySize = 0
        sellSize = 0
        if sell_bal > sellOrderMax:
            sellSize = sellOrderMax
        if sell_bal >= sellOrderMin and sell_bal <= sellOrderMax:
            sellSize = rm_trail(int(sell_bal // sellTick) / round(1/sellTick))
        return float(sellSize)

    else:
        buy_bal = balance*0.995
        buy_pair = pair

        buyOrderMin = CB_MARKETS[CB_MARKETS["MARKET"]==buy_pair].iloc[0]["QUOTE ORDER MIN"]
        buyOrderMax = CB_MARKETS[CB_MARKETS["MARKET"]==buy_pair].iloc[0]["QUOTE ORDER MAX"]
        buyTick = CB_MARKETS[CB_MARKETS["MARKET"]==buy_pair].iloc[0]["QUOTE TICK SIZE"]

        buySize = 0
        if buy_bal > buyOrderMax:
            buySize = buyOrderMax
        if buy_bal >= buyOrderMin and buy_bal <= buyOrderMax:
            buySize = rm_trail(int(buy_bal // buyTick) / round(1/buyTick))
        return buySize


def rm_trail(x):
    return ('%f' % x).rstrip('0').rstrip('.')


def check_liquidity(pair, book, balance, side):
    spread = float(book["asks"][0][0]) - float(book["bids"][0][0])
    print(f"spread: {spread}")
    # if spread > 0.05 or spread > 0.05:
    #     return False

    if side == "BUY":
        depth = sum([float(ask[1])*float(ask[2]) for ask in book["asks"]])
        print(f"Buy depth: {depth}")
        if depth < float(balance):
            return False
    else:
        depth = sum([float(bid[1])*float(bid[2])/float(bid[0]) for bid in book["bids"]])
        print(f"Sell depth: {depth}")
        if depth < float(balance):
            return False

    return True


def initialize_accounts():
    old_accounts = Account.objects.all()
    if old_accounts.count() > 0:
        for acc in old_accounts:
            acc.delete()

    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        api_key = portfolio.api_key
        passphrase = portfolio.passphrase
        api_secret = portfolio.api_secret
        if portfolio.acc_type != "LIVE":
            api_url = "https://api-public.sandbox.pro.coinbase.com"
            client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase, api_url=api_url)
        else:
            client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase)

        accounts = client.get_accounts()

        for account in accounts:
            new_acc = Account(
                id=account["currency"]+"_"+str(portfolio.id),
                portfolio=portfolio,
                currency=account["currency"],
                balance=account["balance"],
                hold=account["hold"],
                available=account["available"],
                last_balance=account["balance"],
                percent_chng = "0.00",
                can_trade=float(account["balance"])>0
            )
            new_acc.save()


def get_total_balance(accs, currency):
    usd_bal = 0
    for acc in accs:
        if acc["currency"] == "USD":
            usd_bal += float(acc["available"])
            continue
        prod = acc["currency"]+"-USD"
        try:
            prod_price = auth_client.get_product_ticker(prod)["price"]
            usd_amount = float(prod_price)*float(acc["available"])
            usd_bal += usd_amount
        except:
            continue

    usd_bal = round(usd_bal, 2)

    btc_price = auth_client.get_product_ticker("BTC-USD")["price"]
    btc_bal = round(usd_bal / float(btc_price), 8)

    prod = currency + "-USD"
    price = auth_client.get_product_ticker(prod)["price"]
    bal3 = usd_bal / float(price)
    tick = CB_MARKETS[CB_MARKETS["MARKET"]==prod].iloc[0]["BASE TICK SIZE"]
    bal3 = round(bal3, round(math.log10(round(1/tick))))
    return str(usd_bal), str(btc_bal), str(bal3)


def update_accounts(accounts, portfolio):
    old_accounts = Account.objects.filter(portfolio=portfolio.id)
    if old_accounts.count() > 0:
        for acc in old_accounts:
            new_acc = [item for item in accounts if item["currency"]==acc.currency][0]
            if acc.balance != new_acc["balance"] or acc.hold != new_acc["hold"] or acc.available != new_acc["available"]:
                acc.balance = new_acc["balance"]
                acc.hold = new_acc["hold"]
                acc.available = new_acc["available"]
                acc.save()


def enter_trades(bot, action):
    pair1 = bot.symbol.split(",")[0].strip()
    pair2 = bot.symbol.split(",")[1].strip()

    if action == "BUY":
        buypair = pair1
        sellpair = pair2
    else:
        buypair = pair2
        sellpair = pair1

    buy_currency = buypair.split("-")[1]
    sell_currency = sellpair.split("-")[0]

    print(buy_currency, sell_currency)
    print(buypair, sellpair)

    api_key = bot.portfolio.api_key
    api_secret = bot.portfolio.api_secret
    passphrase = bot.portfolio.passphrase
    if str(bot.portfolio.acc_type).upper() == "LIVE":
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase)
    else:
        api_url = SANDBOX_API_URL
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase, api_url=api_url)

    accounts = auth_client.get_accounts()
    update_account_stats(accounts, sellpair, "SELL", bot.portfolio)

    sell_balance = float([account["available"] for account in accounts if account["currency"]==sell_currency][0])
    sell_size = get_trade_size(sellpair, sell_balance, "SELL")

    sellpairbook = auth_client.get_product_order_book(sellpair, level=2)
    is_liquid = check_liquidity(sellpair, sellpairbook, sell_size, "SELL")
    if not is_liquid:
        print(f"{sellpair} market is not liquid!")
        return False

    sellorder = auth_client.place_order(sellpair, "sell", "market", size=sell_size)
    print(sellorder)

    accounts = auth_client.get_accounts()
    buy_balance = float([account["available"] for account in accounts if account["currency"]==buy_currency][0])
    buy_size = get_trade_size(buypair, buy_balance, "BUY")

    buypairbook = auth_client.get_product_order_book(buypair, level=2)
    is_liquid = check_liquidity(buypair, buypairbook, buy_size, "BUY")
    if not is_liquid:
        print(f"{buypair} market is not liquid!")
        return False

    buyorder = auth_client.place_order(buypair, "buy", "market", funds=buy_size)
    print(buyorder)

    accounts = auth_client.get_accounts()
    update_accounts(accounts, bot.portfolio)
    update_account_stats(accounts, sellpair, "SELL", bot.portfolio)

    return True


def get_data(symbol, interval, api_key):
    pair1 = symbol.split(",")[0].strip().replace("-", "/")
    pair2 = symbol.split(",")[1].strip().replace("-", "/")
    url1_quote = f"https://api.twelvedata.com/price?symbol={pair1}&apikey={api_key}"
    url2_quote = f"https://api.twelvedata.com/price?symbol={pair2}&apikey={api_key}"
    url1 = f"https://api.twelvedata.com/time_series?symbol={pair1}&interval={interval}&apikey={api_key}&outputsize=100"
    url2 = f"https://api.twelvedata.com/time_series?symbol={pair2}&interval={interval}&apikey={api_key}&outputsize=100"

    df1 = pd.DataFrame(requests.get(url1).json()["values"])
    df1["close"] = df1["close"].astype(float)
    df1 = df1.sort_values(["datetime"]).reset_index(drop=True)
    df2 = pd.DataFrame(requests.get(url2).json()["values"])
    df1 = df1.sort_values(["datetime"]).reset_index(drop=True)
    df2["close"] = df2["close"].astype(float)

    price1 = requests.get(url1_quote).json()["price"]
    price2 = requests.get(url2_quote).json()["price"]
    price = float(price1)/float(price2)

    data = [i/j for i, j in zip(df1.close.tolist(), df2.close.tolist())]
    return np.array(data), price


def cross_over(series1, series2):
    if len(series1) < 2 or len(series2) < 2:
        return False
    return series1[-1] > series2[-1] and series1[-2] < series2[-2]


def cross_under(series1, series2):
    if len(series1) < 2 or len(series2) < 2:
        return False
    return series1[-1] < series2[-1] and series1[-2] > series2[-2]


def run_swap_bots():
    while True:
        bots = BotConfiguration.objects.filter(is_active=True)
        for i, bot in enumerate(bots):
            api_key = API_KEYS_12[i%len(API_KEYS_12)]
            data, price = get_data(bot.symbol, bot.timeframe, api_key)
            rsi = talib.RSI(data, RSI_PERIOD)

            ma = talib.SMA(rsi, timeperiod=BAND_LENGTH)
            offs = talib.STDDEV(rsi, BAND_LENGTH) * 1.6185
            up  = ma + offs
            dn = ma - offs

            if MA_LENGTH < 2:
                fastMA = rsi
            else:
                fastMA = talib(rsi, timeperiod=MA_LENGTH)

            print("\nUpper signal: ", up[-1], up[-2])
            print("Lower signal: ", dn[-1], dn[-2])
            print("MA signal: ", fastMA[-1], fastMA[-2])
            print("Price: ", price, "\n")

            if cross_over(fastMA, up):
                if bot.last_action != "SELL":
                    if bot.last_price == "-1":
                        traded = enter_trade(bot, "SELL")
                        if traded:
                            bot.last_action = "SELL"
                            bot.last_price = price
                            continue
                    else:
                        p_var = (price - bot.last_price) / bot.last_price * 100
                        if abs(p_var) > bot.price_var:
                            traded = enter_trade(bot, "SELL")
                            if traded:
                                bot.last_action = "SELL"
                                bot.last_price = price
                                continue
            if cross_under(fastMA, dn):
                if bot.last_action != "BUY":
                    if bot.last_price == "-1":
                        traded = enter_trade(bot, "BUY")
                        if traded:
                            bot.last_action = "BUY"
                            bot.last_price = price
                            continue
                    else:
                        p_var = (price - bot.last_price) / bot.last_price * 100
                        if abs(p_var) > bot.price_var:
                            traded = enter_trade(bot, "BUY")
                            if traded:
                                bot.last_action = "BUY"
                                bot.last_price = price
                                continue

        # break
        time.sleep(50)


initialize_accounts()
# th = Thread(target=update_accounts_thread, name="UPDATE_ACC_THREAD")
# th.start()
th = Thread(target=run_swap_bots, name="RUN_SWAP_BOTS")
th.start()
# run_swap_bots()
