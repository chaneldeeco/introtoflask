from flask import Flask,redirect
from flask import render_template
from flask import request
from flask import session
import database as db
import authentication
import logging
import ordermanagement as om

app = Flask(__name__)

# Set the secret key to some random bytes.
# Keep this really secret!
app.secret_key = b's@g@d@c0ff33!'

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)

navbar = """
         <a href='/'>Home</a> | <a href='/products'>Products</a> |
         <a href='/branches'>Branches</a> | <a href='/aboutus'>About Us</a>

         """

@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('products.html', page="Products", product_list=product_list)
    
@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    return render_template('productdetails.html', code=code,product=product)

@app.route('/branches')
def branches():
    branches = db.get_branches()
    return render_template('branches.html', page="Branches", branches=branches)

@app.route('/branchdetails')
def branchdetails():
    code = request.args.get('code', '')
    branch = db.get_branch(int(code))
    return render_template('branchdetails.html', code=code,branch=branch)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', page="About Us")

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    is_successful_login, user = authentication.login(username, password)
    app.logger.info('%s', is_successful_login)
    if(is_successful_login):
        session["user"] = user
        return redirect('/')
    else:
        return render_template('login.html', invalid=True)

@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')

@app.route('/addtocart')
def addtocart():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    item=dict()
    # A click to add a product translates to a 
    # quantity of 1 for now

    item["qty"] = 1
    item["name"] = product["name"]
    item["subtotal"] = product["price"]*item["qty"]
    item["code"] = code

    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart
    return redirect('/cart')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/updatecart', methods=['POST'])
def updatecart():
    code = request.form.getlist("code")
    qty = request.form.getlist("qty")

    for code, qty in zip(code, qty):
        if (qty != ''):
            product = db.get_product(int(code))
            item=dict()

            item["qty"] = int(qty)
            item["name"] = product["name"]
            item["subtotal"] = product["price"]*item["qty"]
            item["code"] = code
        
            cart = session["cart"]
            cart[code] = item
            session["cart"]=cart
    return redirect('/cart')

@app.route('/removefromcart')
def removefromcart():
    code = request.args.get('code', '')

    cart = session["cart"]
    cart.pop(code)
    session["cart"] = cart
    return redirect('/cart')

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')

@app.route('/orderhistory')
def orderhistory():
    if (session.get("user") is not None):
        orders = db.get_orderhistory(session["user"]["username"])

        return render_template('orderhistory.html', orders=orders)
    else:
        return redirect('/login')

@app.route('/updatepassword')
def updatepassword():
    if (session.get("user") is not None):
        return render_template('updatepassword.html')
    else:
        return redirect('/login')

@app.route('/updatedpassword', methods=['POST'])
def updatedpassword():
    response = True
    current_password = request.form.get('currentpassword')
    new_password1 = request.form.get('newpassword1')
    new_password2 = request.form.get('newpassword2')

    user = db.get_user(session["user"]["username"])
    if (current_password != user["password"]):
        response = False
    
    if (new_password1 != new_password2):
        response = False
    
    if (response):
        db.updated_password(user["username"], new_password1)

    return render_template('updatepassword.html', response=response)

