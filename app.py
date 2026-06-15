from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import json
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "grocery_secret_2024"

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_data():
    if not os.path.exists(DATA_FILE):
        sample = {
            "next_id": 7,
            "products": [
                {"id": 1, "name": "Basmati Rice", "category": "Grains", "quantity": 50, "unit": "kg", "price": 85.00, "expiry": "2025-12-31", "supplier": "FreshFarm Co.", "min_stock": 10},
                {"id": 2, "name": "Toor Dal", "category": "Pulses", "quantity": 30, "unit": "kg", "price": 120.00, "expiry": "2025-10-15", "supplier": "Organic Farms", "min_stock": 5},
                {"id": 3, "name": "Sunflower Oil", "category": "Oils", "quantity": 20, "unit": "litre", "price": 150.00, "expiry": "2025-08-20", "supplier": "GoldSun Ltd.", "min_stock": 5},
                {"id": 4, "name": "Tomatoes", "category": "Vegetables", "quantity": 15, "unit": "kg", "price": 40.00, "expiry": "2024-07-10", "supplier": "Local Market", "min_stock": 10},
                {"id": 5, "name": "Milk", "category": "Dairy", "quantity": 8, "unit": "litre", "price": 55.00, "expiry": "2024-07-05", "supplier": "Amul", "min_stock": 20},
                {"id": 6, "name": "Wheat Flour", "category": "Grains", "quantity": 40, "unit": "kg", "price": 45.00, "expiry": "2025-06-30", "supplier": "Ashirvaad", "min_stock": 15},
            ]
        }
        save_data(sample)

CATEGORIES = ["Grains", "Pulses", "Vegetables", "Fruits", "Dairy", "Oils", "Spices", "Beverages", "Snacks", "Other"]
UNITS = ["kg", "g", "litre", "ml", "piece", "dozen", "box", "pack"]

@app.route("/")
def index():
    data = load_data()
    products = data["products"]
    today = date.today().isoformat()

    low_stock = [p for p in products if p["quantity"] <= p["min_stock"]]
    expired = [p for p in products if p["expiry"] < today]
    expiring_soon = [p for p in products if today <= p["expiry"] <= (date.today().replace(day=date.today().day)).isoformat()]

    total_value = sum(p["quantity"] * p["price"] for p in products)
    category_counts = {}
    for p in products:
        category_counts[p["category"]] = category_counts.get(p["category"], 0) + 1

    return render_template("index.html",
        products=products,
        low_stock=low_stock,
        expired=expired,
        total_value=total_value,
        category_counts=category_counts,
        total_products=len(products),
        categories=CATEGORIES,
        today=today
    )

@app.route("/products")
def products():
    data = load_data()
    products = data["products"]
    search = request.args.get("search", "").lower()
    category = request.args.get("category", "")
    today = date.today().isoformat()

    if search:
        products = [p for p in products if search in p["name"].lower() or search in p["supplier"].lower()]
    if category:
        products = [p for p in products if p["category"] == category]

    for p in products:
        if p["expiry"] < today:
            p["status"] = "expired"
        elif p["quantity"] <= p["min_stock"]:
            p["status"] = "low"
        else:
            p["status"] = "ok"

    return render_template("products.html",
        products=products,
        categories=CATEGORIES,
        units=UNITS,
        selected_category=category,
        search=search,
        today=today
    )

@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        data = load_data()
        product = {
            "id": data["next_id"],
            "name": request.form["name"],
            "category": request.form["category"],
            "quantity": float(request.form["quantity"]),
            "unit": request.form["unit"],
            "price": float(request.form["price"]),
            "expiry": request.form["expiry"],
            "supplier": request.form["supplier"],
            "min_stock": float(request.form["min_stock"])
        }
        data["products"].append(product)
        data["next_id"] += 1
        save_data(data)
        flash(f"✅ '{product['name']}' added successfully!", "success")
        return redirect(url_for("products"))
    return render_template("add_product.html", categories=CATEGORIES, units=UNITS)

@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    data = load_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        product["name"] = request.form["name"]
        product["category"] = request.form["category"]
        product["quantity"] = float(request.form["quantity"])
        product["unit"] = request.form["unit"]
        product["price"] = float(request.form["price"])
        product["expiry"] = request.form["expiry"]
        product["supplier"] = request.form["supplier"]
        product["min_stock"] = float(request.form["min_stock"])
        save_data(data)
        flash(f"✅ '{product['name']}' updated successfully!", "success")
        return redirect(url_for("products"))

    return render_template("edit_product.html", product=product, categories=CATEGORIES, units=UNITS)

@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    data = load_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if product:
        data["products"] = [p for p in data["products"] if p["id"] != product_id]
        save_data(data)
        flash(f"🗑️ '{product['name']}' deleted.", "info")
    return redirect(url_for("products"))

@app.route("/restock/<int:product_id>", methods=["POST"])
def restock(product_id):
    data = load_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if product:
        qty = float(request.form.get("qty", 0))
        product["quantity"] += qty
        save_data(data)
        flash(f"✅ Restocked '{product['name']}' by {qty} {product['unit']}.", "success")
    return redirect(url_for("products"))

@app.route("/reports")
def reports():
    data = load_data()
    products = data["products"]
    today = date.today().isoformat()

    category_data = {}
    for p in products:
        cat = p["category"]
        if cat not in category_data:
            category_data[cat] = {"count": 0, "value": 0}
        category_data[cat]["count"] += 1
        category_data[cat]["value"] += p["quantity"] * p["price"]

    low_stock = [p for p in products if p["quantity"] <= p["min_stock"]]
    expired = [p for p in products if p["expiry"] < today]
    total_value = sum(p["quantity"] * p["price"] for p in products)

    return render_template("reports.html",
        products=products,
        category_data=category_data,
        low_stock=low_stock,
        expired=expired,
        total_value=total_value,
        today=today
    )

@app.route("/api/chart-data")
def chart_data():
    data = load_data()
    products = data["products"]
    category_counts = {}
    category_values = {}
    for p in products:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        category_values[cat] = round(category_values.get(cat, 0) + p["quantity"] * p["price"], 2)

    return jsonify({
        "labels": list(category_counts.keys()),
        "counts": list(category_counts.values()),
        "values": list(category_values.values())
    })

if __name__ == "__main__":
    init_data()
    app.run(debug=True)
