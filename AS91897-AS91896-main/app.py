import os
import json
from flask import Flask, render_template
 
app = Flask(__name__)
app.secret_key = 'HunterZolomon'
 
 # Routes

@app.route("/")
def home():
    return render_template("Index.html")
 
 
@app.route("/menu")
def menu():
    pizzas = load_pizzas()
    categories = group_by_category(pizzas)
    return render_template('menu.html', categories=categories)
 
 
@app.route("/orders")
def order_history():
    return render_template("order_history.html")
 
 
@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/login")
def login():
    return render_template("login.html")

# menu data

# Groups the flat pizzas dict into category -> list of pizzas
def group_by_category(pizzas):
    grouped = {}
    for pizza_id, pizza in pizzas.items():
        category = pizza['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append({**pizza, 'id': pizza_id})
    return grouped


def load_pizzas():
    with open('AS91897-AS91896-main/data/pizzas.json') as file:
        return json.load(file)
 
if __name__ == "__main__":
    app.run(debug=True)
 