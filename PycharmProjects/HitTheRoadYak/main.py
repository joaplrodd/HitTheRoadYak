from flask import Flask, jsonify, request, render_template
import pandas as pd
from tools import read_xml, create_order_df,\
    milk_per_elapsed_day, skin_per_elapsed_day, stock, process_order, check_request


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


## Stock
@app.route("/yak-shop/stock/", methods=["GET"])
def get_stock():
    if request.args.get('day'):
        milk, skin = stock(df_yaks, int(request.args.get('day')))
        sMilk = str(milk) + " liters of milk"
        sSkin = str(skin) + " skin of wool"

        return jsonify(milk=sMilk, skin=sSkin)
    return render_template("stock.html", title="stock")


@app.route("/yak-shop/stock/<int:day>", methods=["GET"])
def api_stock(day):
    # Generated goods
    milk, skin = stock(df_yaks, day)

    #Already sold goods
    soldMilk = df_order[df_order['day'] <= day]['milk'].sum()
    soldSkin = df_order[df_order['day'] <= day]['skin'].sum()

    # Print
    sMilk = str(milk - soldMilk) + " liters of milk"
    sSkin = str(skin - soldSkin) + " skin of wool"

    return jsonify(milk=sMilk, skin=sSkin)


## Herd
@app.route("/yak-shop/herd/", methods=["GET"])
def herd():
    if request.args.get('day'):
        stock(df_yaks, int(request.args.get('day')))
        df_print = pd.DataFrame()
        df_print['name'] = df_yaks['name'].astype(str)
        df_print['age'] = df_yaks['age_elapsed'].astype(str)
        df_print['age-last-shaved'] = df_yaks['last_shaved'].astype(str)

        return jsonify(herd=df_print.to_dict('records'))
    return render_template("herd.html", title="herd")


@app.route("/yak-shop/herd/<int:day>", methods=["GET"])
def api_herd(day):
    stock(df_yaks, day)
    df_print = pd.DataFrame()
    df_print['name'] = df_yaks['name'].astype(str)
    df_print['age'] = df_yaks['age_elapsed'].astype(str)
    df_print['age-last-shaved'] = df_yaks['last_shaved'].astype(str)

    return jsonify(herd=df_print.to_dict('records'))


# ## Skins
# @app.route("/yak-shop/skin/<int:day>", methods=["GET"])
# def get_skin(day):
#     return jsonify({"skins": str(skin_per_elapsed_day(df_yaks, day))})
#
#
# ## Milk
# @app.route("/yak-shop/milk/<int:day>", methods=["GET"])
# def get_milk(day):
#     return jsonify({"milk": str(milk_per_elapsed_day(df_yaks, day))})


## Order
@app.route("/yak-shop/order/", methods=["GET", "POST"])
def post_order():
    if request.method == "GET":
        return render_template("order.html", title="order")
    else:
        day = request.form['day']
        milk = request.form['milk']
        skin = request.form['skin']
        # orders DataFrame
        global df_order

        # Bad request
        if not check_request([milk, skin, day]):
            return 400

        soldMilk, soldSkin, wholeOrder, df_order = process_order(df_yaks, int(day), df_order, [milk, skin])

        return jsonify({"milk": soldMilk, "skin": soldSkin}, wholeOrder)


@app.route("/yak-shop/order/<int:day>", methods=["GET", "POST"])
def api_order(day):
    global df_order
    orderRequest = request.get_json()

    # Bad request
    if not check_request(orderRequest):
        return 400
    ordered = [orderRequest['order']['milk'], orderRequest['order']['skins']]

    soldMilk, soldSkin, wholeOrder, df_order = process_order(df_yaks, day, df_order, ordered)

    return jsonify({"milk": soldMilk, "skin": soldSkin}, wholeOrder)


if __name__ == '__main__':
    df_yaks = read_xml(file='data.xml', tag='labyak')
    df_order = create_order_df()

    app.run(debug=True)
