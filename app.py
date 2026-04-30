from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os

#initialize app and config database locally into app.db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#creates app.db and connects it to flask app
db = SQLAlchemy()
db.init_app(app)

#user table with primary key of id
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

# category table with primary key of id
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

#transactions table (the main table) with primary key of id and foreign keys of category and user
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    type = db.Column(db.String(10), index=True)
    date = db.Column(db.Date, index=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    category = db.relationship('Category')
    user = db.relationship('User')

# display
@app.route("/")
def transactions():
    #get all rows from transaction
    transactions = Transaction.query.all()
    #renders transactions.html file and passes in the data
    return render_template("transactions.html", transactions=transactions)

# add transaction
@app.route("/transactions/add", methods=["GET", "POST"])
def add_transaction():
    #gets all rows in category
    categories = Category.query.all()
    if request.method == "POST":
        # if form was submitted uses that data to populate a row
        # and insert into transaction table
        t = Transaction(
            amount=float(request.form["amount"]),
            type=request.form["type"],
            date=date.fromisoformat(request.form["date"]),
            category_id=int(request.form["category_id"])
        )
        db.session.add(t)
        db.session.commit()
        return redirect(url_for("transactions"))
    #if get request then renders the form (when add is first clicked from / page)
    return render_template("add_transaction.html", categories=categories)

# edit a transaction based on id from url
@app.route("/transactions/edit/<int:id>", methods=["GET", "POST"])
def edit_transaction(id):
    #get transaction from id in url
    t = Transaction.query.get_or_404(id)
    categories = Category.query.all()
    if request.method == "POST":
        #if form was submitted then edits the tuple in transaction
        t.amount = float(request.form["amount"])
        t.type = request.form["type"]
        t.date = date.fromisoformat(request.form["date"])
        t.category_id = int(request.form["category_id"])
        db.session.commit()
        return redirect(url_for("transactions"))
    #if get request then renders the form (when edit is first clicked from / page)
    return render_template("edit_transaction.html", transaction=t, categories=categories)

# delete a transaction using id
@app.route("/transactions/delete/<int:id>")
def delete_transaction(id):
    #get transaction from id in url
    t = Transaction.query.get_or_404(id)
    #delete that tuple from transaction table
    db.session.delete(t)
    db.session.commit()
    #go back to transaction page
    return redirect(url_for("transactions"))

@app.route("/report", methods=["GET", "POST"])
def report():
    categories = Category.query.all()
    transactions = []
    stats = {}

    if request.method == "POST":
        # if form submitted (so a filter is requested), grab values requested
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        category_id = request.form.get("category_id")
        type_filter = request.form.get("type")

        query = Transaction.query

        #apply filters
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category_id and category_id != "all":
            query = query.filter(Transaction.category_id == int(category_id))
        if type_filter and type_filter != "all":
            query = query.filter(Transaction.type == type_filter)

        transactions = query.all()

        #summary stats
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        net_balance = total_income - total_expense

        stats = {
            "count": len(transactions),
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": net_balance
        }
    #displays form (if form was submitted it reloads page with filtered data
    return render_template("report.html", categories=categories, transactions=transactions, stats=stats)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Category.query.first():
            #populate categories hardcoded
            db.session.add_all([
                Category(name="Food"),
                Category(name="Rent"),
                Category(name="Salary"),
                Category(name="Entertainment")
            ])
            db.session.commit()
            port = int(os.environ.get("PORT", 5000))
            app.run(host="0.0.0.0", port=port)
    app.run(debug=True)