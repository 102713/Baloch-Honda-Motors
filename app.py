import streamlit as st
from supabase import create_client
from datetime import date
from collections import defaultdict

st.set_page_config(
    page_title="BALOCH HONDA MOTORS",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme / UI
# -----------------------------
st.markdown("""
<style>
:root {
    --red: #d71920;
    --dark: #111827;
    --muted: #6b7280;
}
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
.hero {
    background: linear-gradient(115deg,#080808 0%,#1c1c1c 55%,#b00000 100%);
    border-radius: 18px;
    padding: 18px 24px;
    color: white;
    margin-bottom: 18px;
    border: 1px solid #333;
}
.hero-title {font-size: 30px; font-weight: 800; letter-spacing: .5px;}
.hero-sub {color:#d1d5db; font-size:14px; margin-top:2px;}
.bike {font-size:72px; line-height:1; text-align:right;}
.kpi {
    border-radius: 16px; padding: 14px 16px; background: white;
    border:1px solid #e5e7eb; box-shadow:0 2px 10px rgba(0,0,0,.04);
}
.kpi-label {font-size:12px; color:#6b7280; font-weight:700; text-transform:uppercase;}
.kpi-value {font-size:23px; font-weight:800; color:#111827; margin-top:4px;}
.section-title {font-size:19px; font-weight:800; margin: 12px 0 8px;}
.badge {display:inline-block; padding:4px 9px; border-radius:999px; background:#fee2e2; color:#991b1b; font-weight:700; font-size:12px;}
[data-testid="stSidebar"] {border-right:1px solid #e5e7eb;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Supabase
# -----------------------------
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    supabase = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# Helpers
# -----------------------------
BIKE_PRESETS = ["CD 70", "CG 125", "CB 125F", "CD 70 Dream", "Pridor"]

def money(v):
    try:
        return f"PKR {float(v or 0):,.0f}"
    except Exception:
        return "PKR 0"

def num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0

def qty(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0

def fetch_rows(table):
    if not supabase:
        return []
    try:
        r = supabase.table(table).select("*").execute()
        return r.data or []
    except Exception as e:
        st.error(f"Could not read {table}: {e}")
        return []

def safe_refresh():
    st.rerun()

def purchase_total(r):
    return qty(r.get("quantity")) * num(r.get("rate_per_bike"))

def sale_total(r):
    return qty(r.get("quantity")) * num(r.get("sale_rate_per_bike"))

def payment_total(r):
    return num(r.get("amount"))

def get_models(purchases, sales):
    models = []
    for r in purchases + sales:
        m = str(r.get("model") or "").strip()
        if m and m not in models:
            models.append(m)
    return models

def stock_rows(purchases, sales):
    bought = defaultdict(int)
    sold = defaultdict(int)
    for r in purchases:
        bought[str(r.get("model") or "Other")] += qty(r.get("quantity"))
    for r in sales:
        sold[str(r.get("model") or "Other")] += qty(r.get("quantity"))
    models = sorted(set(bought) | set(sold))
    return [{"Model": m, "Purchased": bought[m], "Sold": sold[m], "Current Stock": bought[m] - sold[m]}
            for m in models]

def refresh_after_change():
    st.session_state.pop("customers_cache", None)
    st.rerun()

# -----------------------------
# Login
# -----------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div class="hero-title">BALOCH HONDA MOTORS</div>
          <div class="hero-sub">Dera Murad Jamali — Business Management System</div>
        </div>
        <div class="bike">🏍️</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            if supabase:
                try:
                    r = (supabase.table("users").select("*")
                         .eq("username", username)
                         .eq("password_hash", password)
                         .limit(1).execute())
                    if r.data:
                        st.session_state.logged_in = True
                        st.session_state.user = r.data[0]
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Login error: {e}")
            else:
                st.error("Supabase connection is not configured.")
    st.caption("Initial test login: admin / demo123")
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## 🏍️ BALOCH HONDA MOTORS")
st.sidebar.caption("Dera Murad Jamali")
page = st.sidebar.radio(
    "MENU",
    ["Dashboard", "Purchases", "Sales", "Customers / Khata",
     "Customer Payments", "Expenses", "Stock", "Daily Report", "Monthly Report"]
)
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# -----------------------------
# Load core data
# -----------------------------
purchases = fetch_rows("purchases")
sales = fetch_rows("sales")
customers = fetch_rows("customers")
expenses = fetch_rows("expenses")
payments = fetch_rows("customer_payments")

# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    st.markdown("""
    <div class="hero">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div class="hero-title">BALOCH HONDA MOTORS</div>
          <div class="hero-sub">Professional Motorcycle Dealership Dashboard • Dera Murad Jamali</div>
        </div>
        <div class="bike">🏍️</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    purchase_total_all = sum(purchase_total(x) for x in purchases)
    sales_total_all = sum(sale_total(x) for x in sales)
    expenses_total = sum(num(x.get("amount")) for x in expenses)
    purchased_qty = sum(qty(x.get("quantity")) for x in purchases)
    sold_qty = sum(qty(x.get("quantity")) for x in sales)
    current_stock = purchased_qty - sold_qty

    # Average-cost gross profit approximation by model
    costs = defaultdict(lambda: [0, 0.0])
    for x in purchases:
        m = str(x.get("model") or "Other")
        costs[m][0] += qty(x.get("quantity"))
        costs[m][1] += purchase_total(x)
    gross = 0.0
    for x in sales:
        m = str(x.get("model") or "Other")
        q = qty(x.get("quantity"))
        avg = costs[m][1] / costs[m][0] if costs[m][0] else 0
        gross += sale_total(x) - q * avg
    net = gross - expenses_total

    # Receivables from sales balances minus payments
    customer_balance = defaultdict(float)
    for x in sales:
        code = str(x.get("customer_code") or "").strip()
        if code:
            customer_balance[code] += max(sale_total(x) - num(x.get("amount_received")), 0)
    for x in payments:
        code = str(x.get("customer_code") or "").strip()
        if code:
            customer_balance[code] -= num(x.get("amount"))

    receivables = sum(max(v, 0) for v in customer_balance.values())

    cards = [
        ("TOTAL PURCHASE", money(purchase_total_all)),
        ("TOTAL SALES", money(sales_total_all)),
        ("CURRENT STOCK", f"{current_stock:,} Bikes"),
        ("GROSS PROFIT", money(gross)),
        ("EXPENSES", money(expenses_total)),
        ("RECEIVABLES", money(receivables)),
    ]
    cols = st.columns(6)
    for col, (label, value) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">📊 Business Overview</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Net Profit / Loss", money(net))
    with c2:
        st.metric("Bikes Purchased / Sold", f"{purchased_qty:,} / {sold_qty:,}")

    # Recent sales + purchases
    left, right = st.columns(2)
    with left:
        st.markdown("### 🧾 Recent Sales")
        recent_sales = sorted(sales, key=lambda x: str(x.get("sale_date") or ""), reverse=True)[:10]
        st.dataframe(
            [{"Date": x.get("sale_date"), "Customer": x.get("customer_name"),
              "Model": x.get("model"), "Qty": qty(x.get("quantity")),
              "Total": sale_total(x), "Received": num(x.get("amount_received")),
              "Balance": max(sale_total(x)-num(x.get("amount_received")),0)}
             for x in recent_sales],
            use_container_width=True, hide_index=True
        )
    with right:
        st.markdown("### 🛒 Recent Purchases")
        recent_purchases = sorted(purchases, key=lambda x: str(x.get("purchase_date") or ""), reverse=True)[:10]
        st.dataframe(
            [{"Date": x.get("purchase_date"), "Dealer": x.get("dealer"),
              "Model": x.get("model"), "Qty": qty(x.get("quantity")),
              "Rate": num(x.get("rate_per_bike")), "Total": purchase_total(x)}
             for x in recent_purchases],
            use_container_width=True, hide_index=True
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📦 Model-wise Stock")
        st.dataframe(stock_rows(purchases, sales), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### ⚠️ Outstanding Customers")
        name_by_code = {str(c.get("customer_code") or ""): c.get("name") for c in customers}
        outstanding = []
        for code, bal in customer_balance.items():
            bal = max(bal, 0)
            if bal > 0:
                outstanding.append({"Customer": name_by_code.get(code, code), "Customer ID": code, "Balance": bal})
        st.dataframe(sorted(outstanding, key=lambda x: x["Balance"], reverse=True),
                     use_container_width=True, hide_index=True)

# -----------------------------
# Purchases
# -----------------------------
elif page == "Purchases":
    st.title("🛒 Purchase Entry")
    custom_options = BIKE_PRESETS + ["Custom / Other"]
    with st.form("purchase"):
        d = st.date_input("Date", value=date.today())
        dealer = st.text_input("Dealer / Supplier")
        model_choice = st.selectbox("Bike Model", custom_options)
        custom_model = st.text_input("Custom Bike Name", disabled=(model_choice != "Custom / Other"))
        model = custom_model.strip() if model_choice == "Custom / Other" else model_choice
        q = st.number_input("Quantity", min_value=1, step=1)
        rate = st.number_input("Per Bike Purchase Rate (PKR)", min_value=0.0, step=1000.0)
        notes = st.text_input("Notes")
        st.write(f"**Total Purchase: {money(q * rate)}**")
        if st.form_submit_button("Save Purchase", use_container_width=True):
            if not model:
                st.error("Enter a bike/model name.")
            else:
                try:
                    supabase.table("purchases").insert({
                        "purchase_date": str(d), "dealer": dealer, "model": model,
                        "quantity": int(q), "rate_per_bike": float(rate), "notes": notes
                    }).execute()
                    st.success("Purchase saved.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Purchase error: {e}")

    st.markdown("### Existing Purchases")
    st.dataframe(purchases, use_container_width=True, hide_index=True)

    st.markdown("### ✏️ Edit / Delete Purchase")
    if purchases:
        ids = [x.get("id") for x in purchases if x.get("id") is not None]
        if ids:
            selected_id = st.selectbox("Select Purchase ID", ids)
            row = next(x for x in purchases if x.get("id") == selected_id)
            with st.form("edit_purchase"):
                nd = st.date_input("Date", value=date.fromisoformat(str(row.get("purchase_date"))[:10]) if row.get("purchase_date") else date.today())
                ndealer = st.text_input("Dealer / Supplier", value=str(row.get("dealer") or ""))
                nmodel = st.text_input("Bike Model", value=str(row.get("model") or ""))
                nq = st.number_input("Quantity", min_value=1, value=max(qty(row.get("quantity")),1), step=1)
                nr = st.number_input("Rate", min_value=0.0, value=num(row.get("rate_per_bike")), step=1000.0)
                nn = st.text_input("Notes", value=str(row.get("notes") or ""))
                a,b = st.columns(2)
                update = a.form_submit_button("Update Purchase", use_container_width=True)
                delete = b.form_submit_button("Delete Purchase", use_container_width=True)
                if update:
                    try:
                        supabase.table("purchases").update({
                            "purchase_date": str(nd), "dealer": ndealer, "model": nmodel,
                            "quantity": int(nq), "rate_per_bike": float(nr), "notes": nn
                        }).eq("id", selected_id).execute()
                        st.success("Purchase updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("purchases").delete().eq("id", selected_id).execute()
                        st.success("Purchase deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# -----------------------------
# Sales
# -----------------------------
elif page == "Sales":
    st.title("🏍️ Sales Entry")
    names = ["Walk-in"] + [f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
    custom_options = BIKE_PRESETS + ["Custom / Other"]
    with st.form("sale"):
        d = st.date_input("Date", value=date.today())
        customer_display = st.selectbox("Customer", names)
        if customer_display == "Walk-in":
            customer_name = "Walk-in"
            customer_code = ""
        else:
            customer_code = customer_display.split(" — ", 1)[0]
            selected_customer = next((x for x in customers if str(x.get("customer_code")) == customer_code), {})
            customer_name = selected_customer.get("name", customer_display)
        model_choice = st.selectbox("Bike Model", custom_options)
        custom_model = st.text_input("Custom Bike Name", disabled=(model_choice != "Custom / Other"))
        model = custom_model.strip() if model_choice == "Custom / Other" else model_choice
        q = st.number_input("Quantity", min_value=1, step=1)
        rate = st.number_input("Per Bike Sale Rate (PKR)", min_value=0.0, step=1000.0)
        received = st.number_input("Amount Received (PKR)", min_value=0.0, step=1000.0)
        notes = st.text_input("Notes")
        total = q * rate
        st.write(f"**Total Sale: {money(total)}**")
        st.write(f"**Balance: {money(max(total-received,0))}**")
        if st.form_submit_button("Save Sale", use_container_width=True):
            if not model:
                st.error("Enter a bike/model name.")
            else:
                try:
                    supabase.table("sales").insert({
                        "sale_date": str(d), "customer_name": customer_name,
                        "customer_code": customer_code, "model": model,
                        "quantity": int(q), "sale_rate_per_bike": float(rate),
                        "amount_received": float(received), "notes": notes
                    }).execute()
                    st.success("Sale saved.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sale error: {e}")

    st.markdown("### Existing Sales")
    st.dataframe(sales, use_container_width=True, hide_index=True)

    st.markdown("### ✏️ Edit / Delete Sale")
    if sales:
        ids = [x.get("id") for x in sales if x.get("id") is not None]
        if ids:
            selected_id = st.selectbox("Select Sale ID", ids)
            row = next(x for x in sales if x.get("id") == selected_id)
            with st.form("edit_sale"):
                nd = st.date_input("Date", value=date.fromisoformat(str(row.get("sale_date"))[:10]) if row.get("sale_date") else date.today())
                ncode = st.text_input("Customer ID", value=str(row.get("customer_code") or ""))
                nname = st.text_input("Customer Name", value=str(row.get("customer_name") or ""))
                nmodel = st.text_input("Bike Model", value=str(row.get("model") or ""))
                nq = st.number_input("Quantity", min_value=1, value=max(qty(row.get("quantity")),1), step=1)
                nr = st.number_input("Sale Rate", min_value=0.0, value=num(row.get("sale_rate_per_bike")), step=1000.0)
                nreceived = st.number_input("Received", min_value=0.0, value=num(row.get("amount_received")), step=1000.0)
                nn = st.text_input("Notes", value=str(row.get("notes") or ""))
                a,b = st.columns(2)
                update = a.form_submit_button("Update Sale", use_container_width=True)
                delete = b.form_submit_button("Delete Sale", use_container_width=True)
                if update:
                    try:
                        supabase.table("sales").update({
                            "sale_date": str(nd), "customer_code": ncode, "customer_name": nname,
                            "model": nmodel, "quantity": int(nq), "sale_rate_per_bike": float(nr),
                            "amount_received": float(nreceived), "notes": nn
                        }).eq("id", selected_id).execute()
                        st.success("Sale updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("sales").delete().eq("id", selected_id).execute()
                        st.success("Sale deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# -----------------------------
# Customers / Khata
# -----------------------------
elif page == "Customers / Khata":
    st.title("👤 Customers & Khata")
    with st.form("customer"):
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone")
        address = st.text_input("Address")
        if st.form_submit_button("Add Customer", use_container_width=True):
            if not name.strip():
                st.error("Customer name is required.")
            else:
                try:
                    # Create a human-friendly unique ID.
                    existing_codes = {str(x.get("customer_code") or "") for x in customers}
                    n = 1
                    while f"CUS-{n:04d}" in existing_codes:
                        n += 1
                    code = f"CUS-{n:04d}"
                    supabase.table("customers").insert({
                        "customer_code": code, "name": name.strip(),
                        "phone": phone, "address": address
                    }).execute()
                    st.success(f"Customer added: {code}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Customer error: {e}")

    st.markdown("### Customer List")
    table = []
    for c in customers:
        code = str(c.get("customer_code") or "")
        bal = 0.0
        for x in sales:
            if str(x.get("customer_code") or "") == code:
                bal += max(sale_total(x)-num(x.get("amount_received")),0)
        for x in payments:
            if str(x.get("customer_code") or "") == code:
                bal -= num(x.get("amount"))
        table.append({"Customer ID": code, "Name": c.get("name"), "Phone": c.get("phone"),
                      "Address": c.get("address"), "Outstanding": max(bal,0)})
    st.dataframe(table, use_container_width=True, hide_index=True)

    if customers:
        options = [f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
        selected = st.selectbox("Open Customer Khata", options)
        code = selected.split(" — ",1)[0]
        c = next(x for x in customers if str(x.get("customer_code")) == code)
        st.markdown(f"### 📒 {c.get('name')} — {code}")

        ledger = []
        balance = 0.0
        for x in sales:
            if str(x.get("customer_code") or "") == code:
                debit = max(sale_total(x)-num(x.get("amount_received")),0)
                balance += debit
                ledger.append({"Date": x.get("sale_date"), "Type": "Sale",
                               "Description": f'{x.get("model")} x{qty(x.get("quantity"))}',
                               "Debit": debit, "Credit": 0, "Balance": balance})
        for x in payments:
            if str(x.get("customer_code") or "") == code:
                credit = num(x.get("amount"))
                balance -= credit
                ledger.append({"Date": x.get("payment_date"), "Type": "Payment",
                               "Description": x.get("notes") or "Payment received",
                               "Debit": 0, "Credit": credit, "Balance": balance})
        ledger.sort(key=lambda x: str(x["Date"] or ""))
        running = 0.0
        for x in ledger:
            running += x["Debit"] - x["Credit"]
            x["Balance"] = running
        st.metric("Current Outstanding", money(max(running,0)))
        st.dataframe(ledger, use_container_width=True, hide_index=True)

        st.markdown("### ✏️ Edit / Delete Customer")
        with st.form("edit_customer"):
            nn = st.text_input("Name", value=str(c.get("name") or ""))
            np = st.text_input("Phone", value=str(c.get("phone") or ""))
            na = st.text_input("Address", value=str(c.get("address") or ""))
            a,b = st.columns(2)
            update = a.form_submit_button("Update Customer", use_container_width=True)
            delete = b.form_submit_button("Delete Customer", use_container_width=True)
            if update:
                try:
                    supabase.table("customers").update({"name": nn, "phone": np, "address": na}).eq("customer_code", code).execute()
                    st.success("Customer updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update error: {e}")
            if delete:
                try:
                    supabase.table("customers").delete().eq("customer_code", code).execute()
                    st.success("Customer deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete error: {e}")

# -----------------------------
# Customer Payments
# -----------------------------
elif page == "Customer Payments":
    st.title("💵 Customer Payment / Khata Jama")
    if not customers:
        st.info("Add a customer first.")
    else:
        options = [f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
        with st.form("payment"):
            selected = st.selectbox("Customer", options)
            code = selected.split(" — ",1)[0]
            pd = st.date_input("Payment Date", value=date.today())
            amount = st.number_input("Payment Amount (PKR)", min_value=0.0, step=1000.0)
            notes = st.text_input("Notes")
            if st.form_submit_button("Save Payment", use_container_width=True):
                if amount <= 0:
                    st.error("Enter a payment amount.")
                else:
                    try:
                        supabase.table("customer_payments").insert({
                            "customer_code": code, "payment_date": str(pd),
                            "amount": float(amount), "notes": notes
                        }).execute()
                        st.success("Payment added to customer Khata.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Payment error: {e}")

    st.markdown("### Payment History")
    st.dataframe(payments, use_container_width=True, hide_index=True)

# -----------------------------
# Expenses
# -----------------------------
elif page == "Expenses":
    st.title("💸 Expenses")
    with st.form("expense"):
        d = st.date_input("Date", value=date.today())
        category = st.selectbox("Category", ["Rent", "Electricity", "Transport", "Staff", "Other"])
        desc = st.text_input("Description")
        amount = st.number_input("Amount (PKR)", min_value=0.0, step=500.0)
        if st.form_submit_button("Save Expense", use_container_width=True):
            try:
                supabase.table("expenses").insert({
                    "expense_date": str(d), "category": category,
                    "description": desc, "amount": float(amount)
                }).execute()
                st.success("Expense saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Expense error: {e}")

    st.dataframe(expenses, use_container_width=True, hide_index=True)

    if expenses:
        ids = [x.get("id") for x in expenses if x.get("id") is not None]
        if ids:
            st.markdown("### ✏️ Edit / Delete Expense")
            selected_id = st.selectbox("Select Expense ID", ids)
            row = next(x for x in expenses if x.get("id") == selected_id)
            with st.form("edit_expense"):
                nd = st.date_input("Date", value=date.fromisoformat(str(row.get("expense_date"))[:10]) if row.get("expense_date") else date.today())
                nc = st.selectbox("Category", ["Rent", "Electricity", "Transport", "Staff", "Other"],
                                  index=["Rent", "Electricity", "Transport", "Staff", "Other"].index(str(row.get("category"))) if str(row.get("category")) in ["Rent", "Electricity", "Transport", "Staff", "Other"] else 4)
                ndesc = st.text_input("Description", value=str(row.get("description") or ""))
                namt = st.number_input("Amount", min_value=0.0, value=num(row.get("amount")), step=500.0)
                a,b = st.columns(2)
                update = a.form_submit_button("Update Expense", use_container_width=True)
                delete = b.form_submit_button("Delete Expense", use_container_width=True)
                if update:
                    try:
                        supabase.table("expenses").update({
                            "expense_date": str(nd), "category": nc,
                            "description": ndesc, "amount": float(namt)
                        }).eq("id", selected_id).execute()
                        st.success("Expense updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("expenses").delete().eq("id", selected_id).execute()
                        st.success("Expense deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# -----------------------------
# Stock
# -----------------------------
elif page == "Stock":
    st.title("📦 Current Stock")
    st.dataframe(stock_rows(purchases, sales), use_container_width=True, hide_index=True)

# -----------------------------
# Daily Report
# -----------------------------
elif page == "Daily Report":
    st.title("📅 Date-wise Business Report")
    selected_date = st.date_input("Select Date", value=date.today())
    key = selected_date.isoformat()

    dp = [x for x in purchases if str(x.get("purchase_date",""))[:10] == key]
    ds = [x for x in sales if str(x.get("sale_date",""))[:10] == key]
    de = [x for x in expenses if str(x.get("expense_date",""))[:10] == key]
    dpay = [x for x in payments if str(x.get("payment_date",""))[:10] == key]

    c = st.columns(5)
    c[0].metric("Purchases", money(sum(purchase_total(x) for x in dp)))
    c[1].metric("Sales", money(sum(sale_total(x) for x in ds)))
    c[2].metric("Expenses", money(sum(num(x.get("amount")) for x in de)))
    c[3].metric("Customer Payments", money(sum(num(x.get("amount")) for x in dpay)))
    c[4].metric("Bikes Sold", sum(qty(x.get("quantity")) for x in ds))

    st.markdown("### 🛒 Purchases")
    st.dataframe(dp, use_container_width=True, hide_index=True)
    st.markdown("### 🧾 Sales")
    st.dataframe(ds, use_container_width=True, hide_index=True)
    st.markdown("### 💸 Expenses")
    st.dataframe(de, use_container_width=True, hide_index=True)
    st.markdown("### 💵 Customer Payments")
    st.dataframe(dpay, use_container_width=True, hide_index=True)

# -----------------------------
# Monthly Report
# -----------------------------
else:
    st.title("📊 Monthly Report")
    selected = st.date_input("Select any date in the month", value=date.today())
    key = selected.strftime("%Y-%m")
    mp = [x for x in purchases if str(x.get("purchase_date","")).startswith(key)]
    ms = [x for x in sales if str(x.get("sale_date","")).startswith(key)]
    me = [x for x in expenses if str(x.get("expense_date","")).startswith(key)]
    mpay = [x for x in payments if str(x.get("payment_date","")).startswith(key)]

    c = st.columns(6)
    vals = [
        money(sum(purchase_total(x) for x in mp)),
        money(sum(sale_total(x) for x in ms)),
        sum(qty(x.get("quantity")) for x in mp),
        sum(qty(x.get("quantity")) for x in ms),
        money(sum(num(x.get("amount")) for x in me)),
        money(sum(num(x.get("amount")) for x in mpay)),
    ]
    for col, label, val in zip(c,
        ["Purchases", "Sales", "Bikes Purchased", "Bikes Sold", "Expenses", "Customer Payments"], vals):
        col.metric(label, val)

    st.markdown("### Purchases")
    st.dataframe(mp, use_container_width=True, hide_index=True)
    st.markdown("### Sales")
    st.dataframe(ms, use_container_width=True, hide_index=True)
    st.markdown("### Expenses")
    st.dataframe(me, use_container_width=True, hide_index=True)
