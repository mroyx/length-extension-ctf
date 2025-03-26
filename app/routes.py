from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import hashlib
from secrets import token_hex


app = Flask(__name__)

# MYSQL CONFIG
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'flaskuser'
app.config['MYSQL_PASSWORD'] = 'flaskpassword'
app.config['MYSQL_DB'] = 'ctf'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.secret_key = 'supersecret'

def get_authenticated_user():
    if 'user' not in session:
        return None, redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT balance FROM users WHERE username = %s", (session['user'],))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        return {
            "username": session['user'],
            "balance": user_data.get('balance', 0)
        }, None
    else:
        return None, redirect(url_for('login'))

def generate_md5_hash(raw_data):
    hash_input = (app.secret_key  + raw_data).encode() # Generates an MD5 hash with a secret key.
    hash_input = hash_input.replace(b"%80", b"\x80") # Handles encoding issues with the padding byte
    print(f"Hash Input: {hash_input}")
    return hashlib.md5(hash_input).hexdigest()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            return redirect(url_for('dashboard'))

        flash("Invalid credentials, try again.", "info")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return jsonify(success=True, redirect_url=url_for('dashboard'))

    if request.method == 'POST':
        if 'username' not in request.form or 'password' not in request.form or 'confirmPassword' not in request.form:
            return jsonify(success=False, error="Missing form data.")

        username = request.form['username']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        if password != confirmPassword:
            flash("The passwords do not match!", "info")
            return redirect(url_for('register'))

        if len(username.strip()) <= 1:
            flash("Username must be longer than 1 character.", "info")
            return redirect(url_for('register'))

        if not username.isalnum():
            flash("Username can only contain letters and numbers.", "info")
            return redirect(url_for('register'))
    
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                        (username, hashed_password))
            mysql.connection.commit()
            return redirect(url_for('login'))
        except Exception as e:
            print("Error:", e)
            flash("Username already exists. Try again.", "info")
            return redirect(url_for('register'))
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    user, redirect_response = get_authenticated_user()
    if redirect_response:
        return redirect_response

    return render_template("dashboard.html", balance=user['balance'], username=user['username'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/members')
def membership():
    user, redirect_response = get_authenticated_user()
    if redirect_response:
        return redirect_response

    cur = mysql.connection.cursor()
    cur.execute("SELECT role FROM users WHERE username = %s", (user['username'],))
    role_data = cur.fetchone()
    cur.close()

    is_member = role_data and role_data['role'] == 'member'

    return render_template(
        'members.html',
        balance=user['balance'],
        username=user['username'],
        is_member=is_member
    )

@app.route('/store')
def store():
    user, redirect_response = get_authenticated_user()
    if redirect_response:
        return redirect_response
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, description, price, image_url FROM store_items")
    store_items = cur.fetchall()  
    cur.close()

    return render_template('store.html', store_items=store_items, balance=user['balance'], username=user['username'])

@app.route('/cart', methods=['GET', 'POST'])
def view_cart():
    user, redirect_response = get_authenticated_user()
    if redirect_response:
        return redirect_response

    if request.method == 'POST':
        item_id = request.form.get('item_id')
        if item_id and 'cart' in session:
            session['cart'] = [item for item in session['cart'] if str(item['id']) != item_id]
            session.modified = True 
            flash("Item removed from cart!", "info")
        return redirect(url_for('view_cart')) 

    cart = session.get('cart', [])
    return render_template('cart.html', cart=cart, balance=user['balance'], username=user['username'])

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        return jsonify({"message": "Please log in first!"}), 403 

    data = request.get_json()
    item_id = data.get('id')

    if not item_id:
        return jsonify({"message": "Invalid request!"}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT name, price FROM store_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    cur.close()

    if not item:
        return jsonify({"message": "Item not found!"}), 404

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        "id": item_id,
        "name": item['name'],
        "price": float(item['price'])
    })

    session.modified = True

    return jsonify({"message": "Your cart has been updated!"})

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user' not in session:
        flash("You must be logged in to complete a purchase.", "danger")
        return redirect(url_for('login'))

    cart = session.get('cart', [])
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('view_cart'))

    total_price = sum(item['price'] for item in cart)
    tx_id = token_hex(16)

    # Construct payment string for signing
    payment_info = f"transaction_id={tx_id}&amount={total_price:.2f}"
    sign = generate_md5_hash(payment_info)

    # Render HTML to auto-submit the form
    return render_template_string(f"""
        <html>
        <body onload="document.getElementById('autoSubmitForm').submit();">
            <form id="autoSubmitForm" action="/process_payment" method="POST">
                <input type="hidden" name="transaction_id" value="{tx_id}">
                <input type="hidden" name="amount" value="{total_price:.2f}">
                <input type="hidden" name="sign" value="{sign}">
            </form>
        </body>
        </html>
    """)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    transaction_id = request.form.get("transaction_id")
    amount = request.form.get("amount")
    received_sign = request.form.get("sign")

    if not transaction_id or not amount or not received_sign:
        return jsonify(success=False, error="Missing parameters."), 400

    raw_body = f"transaction_id={transaction_id}&amount={amount}"
    expected_sign = generate_md5_hash(raw_body)
    print(f"Expected Sign: {expected_sign}")
    print(f"Received Sign: {received_sign}")

    if received_sign != expected_sign:
        return jsonify(success=False, error="Invalid signature - possible tampering detected!"), 403

    cur = mysql.connection.cursor()
    cur.execute("SELECT balance FROM users WHERE username = %s", (session['user'],))
    user_data = cur.fetchone()

    if not user_data:
        cur.close()
        return jsonify(success=False, error="User not found."), 400

    user_balance = float(user_data['balance'])
    total_cost = float(amount)

    if user_balance < total_cost:
        cur.close()
        return jsonify(success=False, error=f"Insufficient funds! You need ${total_cost - user_balance:.2f} more."), 403

    new_balance = user_balance - total_cost
    cur.execute("UPDATE users SET balance = %s WHERE username = %s", (new_balance, session['user']))
    mysql.connection.commit()

    cart = session.get('cart', [])
    membership_item_name = "Totally Secure + Membership"
    for item in cart:
        if item["name"] == membership_item_name:
            cur.execute("UPDATE users SET role = 'member' WHERE username = %s", (session['user'],))
            break

    mysql.connection.commit()
    cur.close()

    session.pop('cart', None)
    session.modified = True

    return jsonify(success=True, message=f"Payment Verified: Transaction {transaction_id} for ${amount}"), 200
    
if __name__ == '__main__':
    app.run(debug=True)