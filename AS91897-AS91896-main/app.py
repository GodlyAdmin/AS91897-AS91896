from flask import Flask, render_template
 
app = Flask(__name__)
 
 
@app.route("/")
def home():
    return render_template("Index.html")
 
 
@app.route("/menu")
def menu():
    return render_template("menu.html")
 
 
@app.route("/orders")
def order_history():
    return render_template("order_history.html")
 
 
@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/login")
def login():
    return render_template("login.html")
 
if __name__ == "__main__":
    app.run(debug=True)
 