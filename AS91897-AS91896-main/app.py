import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash
 
app = Flask(__name__)
app.secret_key = 'HunterZolomon'
 
 # Routes

@app.route("/")
def home():
    return render_template("Index.html")

@app.route('/menu')
def menu():
    search_term = request.args.get('q', '')
    pizzas = load_pizzas()
    categories = group_by_category(pizzas, search_term)
    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())

    return render_template('menu.html', categories=categories, cart=cart,
                            subtotal=subtotal, search_term=search_term)

ADMIN_USERNAME = 'Admin'
ADMIN_PASSWORD = 'GloryGodspeed'

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Logged in successfully.')
            return redirect(url_for('home'))

        flash('Incorrect username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Logged out.')
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Please log in to view the admin dashboard.')
        return redirect(url_for('login'))

    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY order_id DESC')
        rows = cursor.fetchall()

    orders = []
    revenue = 0
    for row in rows:
        orders.append({
            'order_id': row[0],
            'invoice_number': row[1],
            'customer_name': row[2],
            'cart_items': json.loads(row[3]),
            'total': row[4],
            'date': row[5]
        })
        revenue += row[4]

    return render_template('admin.html', orders=orders, order_count=len(orders), revenue=revenue)

@app.route('/admin/delete/<int:order_id>', methods=['POST'])
def admin_delete_order(order_id):
    if not session.get('is_admin'):
        flash('Please log in to do that.')
        return redirect(url_for('login'))

    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
        conn.commit()

    flash('Order deleted.')
    return redirect(url_for('admin_dashboard'))

@app.route("/orders")
def order_history():
    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY order_id DESC')
        rows = cursor.fetchall()

    orders = []
    for row in rows:
        orders.append({
            'order_id': row[0],
            'invoice_number': row[1],
            'customer_name': row[2],
            'cart_items': json.loads(row[3]),
            'total': row[4],
            'date': row[5]
        })

    return render_template('order_history.html', orders=orders)

@app.route('/checkout')
def checkout():
    GST_RATE = 15  # percent, prices already include GST
    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    total, discount_applied, code_used = calculate_total(
        subtotal, request.args.get('promo', ''))
    gst_amount = total * GST_RATE / (100 + GST_RATE)

    return render_template('checkout.html', cart=cart, subtotal=subtotal,
                           total=total, discount_applied=discount_applied,
                           code_used=code_used, gst_rate=GST_RATE,
                           gst_amount=gst_amount)

def calculate_total(subtotal, promo_code=''):
    total = round(subtotal * (1), 2)
    discount_applied = False
    code_used = None

    promo_code = promo_code.strip().upper()
    if promo_code in PROMO_CODES:
        total = total * (1 - PROMO_CODES[promo_code])
        discount_applied = True
        code_used = promo_code
    elif promo_code:
        flash('That promo code is not valid.')

    return round(total, 2), discount_applied, code_used

@app.route('/checkout/confirm', methods=['POST'])
def confirm_order():
    customer_name = request.form.get('customer_name')
    cart = session.get('cart')
    customer_email = request.form.get('customer_email')
    delivery_address = request.form.get('delivery_address')

    if not customer_name:
        flash('Please enter your name to confirm the order.')
        return redirect(url_for('checkout'))

    if not cart:
        flash('Your cart is empty. Please add items before confirming the order.')
        return redirect(url_for('menu'))

    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    total, discount_applied, code_used = calculate_total(
        subtotal, request.form.get('promo', ''))

    flash(f"Thank you {customer_name}! Your order has been confirmed. Total: ${total}")

    session.pop('cart', None)
    session.modified = True

    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (invoice_number, customer_name, cart_items, total)
            VALUES (?, ?, ?, ?)
        ''', (invoice_number, customer_name, json.dumps(cart), total))
        conn.commit()

    return render_template('order_confirmed.html', invoice_number=invoice_number,customer_name=customer_name, cart=cart, total=total,delivery_address=delivery_address,
                           customer_email=customer_email,discount_applied=discount_applied, code_used=code_used)

def initialise_database():
    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                customer_name TEXT,
                cart_items TEXT,
                total REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    pizza_id = request.form.get('pizza_id')
    size = request.form.get('size')
    quantity = int(request.form['quantity'])

    pizzas = load_pizzas()

    if pizza_id not in pizzas or size not in SIZE_MULTIPLIER:
        flash('Invalid item selected.')
        return redirect(url_for('menu'))

    if quantity <= 0 or quantity > 10:
        flash('Quantity must be between 1 and 10.')
        return redirect(url_for('menu'))

    pizza = pizzas[pizza_id]
    unit_price = round(pizza['base_price'] * SIZE_MULTIPLIER[size], 2)

    # each pizza is imputed based on both size and pizza id so that the same pizza of different sizes can be added to the cart seperately
    item_key = f"{pizza_id}_{size}"
    cart = session.get('cart', {})

    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        cart[item_key] = {
            'name': pizza['name'],
            'size': size,
            'price': unit_price,
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True

    flash(f"{quantity} {pizza['name']} ({size}) added to cart.")

    return redirect(url_for('menu'))


@app.route('/cart/remove')
def remove_from_cart():
    item_key = request.args.get('item')
    cart = session.get('cart', {})

    if item_key in cart:
        cart[item_key]['quantity'] -= 1
        flash(f"Removed 1 {cart[item_key]['name']} from the cart.")

        # Remove the line entirely once quantity reaches zero
        if cart[item_key]['quantity'] <= 0:
            del cart[item_key]

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('menu'))
# menu data

# Groups the flat pizzas dict into category -> list of pizzas
# Also Filters the pizzas based on the search term if provided
def group_by_category(pizzas, search_term=''):
    search_term = search_term.strip().lower()
    grouped = {}

    for pizza_id, pizza in pizzas.items():
        if search_term:
            haystack = f"{pizza['name']} {pizza['description']} {' '.join(pizza['tags'])}".lower()
            if search_term not in haystack:
                continue

        category = pizza['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append({**pizza, 'id': pizza_id})

    return grouped


def load_pizzas():
    with open('AS91897-AS91896-main/data/pizzas.json') as file:
        return json.load(file)

# The multiplier for the piza size price
SIZE_MULTIPLIER = {'S': 0.8, 'M': 1.0, 'L': 1.2, 'XL': 1.4}

# code -> discount as a decimal fraction
PROMO_CODES = {'WELCOME10': 0.10, 'GLORY20': 0.20}
if __name__ == "__main__":
    initialise_database()
    app.run(debug=True)
 