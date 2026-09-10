import streamlit as st
from supabase import create_client
from datetime import date, datetime
from collections import defaultdict

# =========================================================
# BALOCH HONDA MOTORS - COMPLETE BUSINESS MANAGEMENT SYSTEM
# =========================================================
st.set_page_config(
    page_title="BALOCH HONDA MOTORS",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================== STYLE ===========================
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
.hero {
    background: linear-gradient(115deg,#090909 0%,#1c1c1c 55%,#b40000 100%);
    border-radius: 20px; padding: 20px 24px; color: white;
    margin-bottom: 18px; border: 1px solid #333;
}
.hero-title {font-size: 30px; font-weight: 900; letter-spacing: .5px;}
.hero-sub {color: #d1d5db; font-size: 14px; margin-top: 3px;}
.hero-bike {font-size: 72px; text-align: right;}
.side-brand {
    background: linear-gradient(145deg,#080808,#242424);
    border-radius: 18px; padding: 16px 10px; margin-bottom: 16px;
    text-align: center; color: white; border: 1px solid #3b3b3b;
}
.side-bike {font-size: 42px; line-height: 1.05;}
.side-title {font-size: 18px; font-weight: 900;}
.side-sub {font-size: 11px; font-weight: 900; color: #ef4444; letter-spacing: 3px;}
.side-location {font-size: 11px; color: #cbd5e1; margin-top: 6px;}
.kpi {
    border-radius: 16px; padding: 14px 16px; background: white;
    border: 1px solid #e5e7eb; box-shadow: 0 2px 10px rgba(0,0,0,.04);
}
.kpi-label {font-size: 11px; color: #6b7280; font-weight: 800; text-transform: uppercase;}
.kpi-value {font-size: 22px; font-weight: 900; color: #111827; margin-top: 4px;}
.section-title {font-size: 19px; font-weight: 900; margin: 14px 0 8px;}
div[data-testid="stSidebar"] {border-right: 1px solid #e5e7eb;}
div[data-testid="stSidebar"] .stRadio label {font-weight: 700;}
.stTextArea textarea {min-height: 100px !important;}
</style>
""", unsafe_allow_html=True)

# ==================== SUPABASE CONNECTIONS ====================
try:
    supabase_main = create_client(
        st.secrets["SUPABASE_URL"], 
        st.secrets["SUPABASE_KEY"]
    )
    
    supabase_reg = create_client(
        st.secrets["SUPABASE_REG_URL"], 
        st.secrets["SUPABASE_REG_KEY"]
    )
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    supabase_main = None
    supabase_reg = None

# ==================== SESSION STATE =======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "previous_page" not in st.session_state:
    st.session_state.previous_page = None

# ==================== HELPERS =============================
BIKE_PRESETS = ["CD 70", "CG 125", "CB 125F", "CD 70 Dream", "Pridor"]

def money(v):
    try: return f"PKR {float(v or 0):,.0f}"
    except: return "PKR 0"

def n(v):
    try: return float(v or 0)
    except: return 0.0

def q(v):
    try: return int(float(v or 0))
    except: return 0

def rows(table):
    if not supabase_main:
        return []
    try:
        return supabase_main.table(table).select("*").execute().data or []
    except Exception as e:
        st.error(f"Could not read {table}: {e}")
        return []

def purchase_total(x):
    return q(x.get("quantity")) * n(x.get("rate_per_bike"))

def sale_total(x):
    return q(x.get("quantity")) * n(x.get("sale_rate_per_bike"))

def in_range(value, start, end):
    try:
        d = date.fromisoformat(str(value)[:10])
        return start <= d <= end
    except:
        return False

def date_range(label, key):
    v = st.date_input(
        label,
        value=(date.today().replace(day=1), date.today()),
        format="DD-MM-YYYY",
        key=key,
    )
    if isinstance(v, tuple) and len(v) == 2:
        return v[0], v[1]
    if isinstance(v, tuple) and len(v) == 1:
        return v[0], v[0]
    return v, v

def stock_data(purchases, sales):
    bought, sold = defaultdict(int), defaultdict(int)
    for x in purchases:
        bought[str(x.get("model") or "Other")] += q(x.get("quantity"))
    for x in sales:
        sold[str(x.get("model") or "Other")] += q(x.get("quantity"))
    models = sorted(set(bought) | set(sold))
    return [{"Model": m, "Purchased": bought[m], "Sold": sold[m],
             "Current Stock": bought[m] - sold[m]} for m in models]

def get_customer_balance(code):
    bal = 0.0
    for x in sales:
        if str(x.get("customer_code") or "") == code:
            bal += max(sale_total(x) - n(x.get("amount_received")), 0)
    for x in payments:
        if str(x.get("customer_code") or "") == code:
            bal -= n(x.get("amount"))
    for x in cash_trans:
        if str(x.get("customer_code") or "") == code:
            if x.get("transaction_type") == "Cash Udaar":
                bal += n(x.get("amount"))
            else:
                bal -= n(x.get("amount"))
    return bal

def generate_code(prefix, existing_codes):
    i = 1
    while f"{prefix}-{i}" in existing_codes:
        i += 1
    return f"{prefix}-{i}"

# ==================== LOGIN ===============================
if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div class="hero-title">BALOCH HONDA MOTORS</div>
          <div class="hero-sub">Dera Murad Jamali — Business Management System</div>
        </div>
        <div class="hero-bike">🏍️</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("🔐 Login", use_container_width=True):
            if supabase_main:
                try:
                    r = (supabase_main.table("users").select("*")
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

# ==================== DATA LOAD ===========================
purchases = rows("purchases")
sales = rows("sales")
customers = rows("customers")
expenses = rows("expenses")
payments = rows("customer_payments")
cash_trans = rows("customer_cash_transactions")
suppliers = rows("suppliers")
supplier_payments = rows("supplier_payments")
supplier_advances = rows("supplier_advances")

# ==================== SIDEBAR =============================
st.sidebar.markdown("""
<div class="side-brand">
  <div class="side-bike">🏍️</div>
  <div class="side-title">BALOCH HONDA</div>
  <div class="side-sub">MOTORS</div>
  <div class="side-location">Dera Murad Jamali</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("MAIN MENU", [
    "🏠 Dashboard",
    "🛒 Purchases",
    "🏍️ Sales",
    "👥 Customers",
    "💰 Customer Khata",
    "💵 Cash Transaction",
    "💸 Expenses",
    "📦 Stock",
    "📄 Bike Registration",
    "📅 Reports"
])

if page != st.session_state.previous_page:
    st.session_state.previous_page = page

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# ==================== DASHBOARD ===========================
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="hero">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div class="hero-title">BALOCH HONDA MOTORS</div>
          <div class="hero-sub">Professional Motorcycle Dealership Dashboard • Dera Murad Jamali</div>
        </div>
        <div class="hero-bike">🏍️</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    pt = sum(purchase_total(x) for x in purchases)
    stot = sum(sale_total(x) for x in sales)
    exp = sum(n(x.get("amount")) for x in expenses)
    pq = sum(q(x.get("quantity")) for x in purchases)
    sq = sum(q(x.get("quantity")) for x in sales)

    costs = defaultdict(lambda: [0, 0.0])
    for x in purchases:
        m = str(x.get("model") or "Other")
        costs[m][0] += q(x.get("quantity"))
        costs[m][1] += purchase_total(x)
    gross = 0
    for x in sales:
        m = str(x.get("model") or "Other")
        avg = costs[m][1] / costs[m][0] if costs[m][0] else 0
        gross += sale_total(x) - q(x.get("quantity")) * avg

    receivables = 0
    for c in customers:
        code = str(c.get("customer_code") or "")
        receivables += max(get_customer_balance(code), 0)

    cards = [
        ("TOTAL PURCHASE", money(pt)),
        ("TOTAL SALES", money(stot)),
        ("CURRENT STOCK", f"{pq-sq:,} Bikes"),
        ("GROSS PROFIT", money(gross)),
        ("EXPENSES", money(exp)),
        ("RECEIVABLES", money(receivables)),
    ]
    cols = st.columns(6)
    for col, (label, val) in zip(cols, cards):
        col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div>'
                     f'<div class="kpi-value">{val}</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("NET PROFIT / LOSS", money(gross - exp))
    c2.metric("BIKES PURCHASED / SOLD", f"{pq:,} / {sq:,}")

    l, r = st.columns(2)
    with l:
        st.markdown("### 🧾 Recent Sales")
        rs = sorted(sales, key=lambda x: str(x.get("sale_date") or ""), reverse=True)[:10]
        st.dataframe([
            {"Date": x.get("sale_date"), "Customer": x.get("customer_name"),
             "Model": x.get("model"), "Qty": q(x.get("quantity")),
             "Total": sale_total(x), "Received": n(x.get("amount_received")),
             "Balance": max(sale_total(x) - n(x.get("amount_received")), 0)}
            for x in rs
        ], use_container_width=True, hide_index=True)

    with r:
        st.markdown("### 🛒 Recent Purchases")
        rp = sorted(purchases, key=lambda x: str(x.get("purchase_date") or ""), reverse=True)[:10]
        st.dataframe([
            {"Date": x.get("purchase_date"), "Supplier": x.get("supplier_name") or x.get("dealer"),
             "Model": x.get("model"), "Qty": q(x.get("quantity")),
             "Rate": n(x.get("rate_per_bike")), "Total": purchase_total(x)}
            for x in rp
        ], use_container_width=True, hide_index=True)

    st.markdown("### 📦 Model-wise Stock")
    st.dataframe(stock_data(purchases, sales), use_container_width=True, hide_index=True)

# ==================== PURCHASES ===========================
elif page == "🛒 Purchases":
    st.title("🛒 Purchase Entry")

    with st.form("purchase"):
        cols = st.columns(2)
        with cols[0]:
            d = st.date_input("Date", date.today(), format="DD-MM-YYYY")
            supplier_code = st.text_input("Supplier Code", placeholder="SUP-1")
            supplier_name = st.text_input("Supplier Name", placeholder="Type name or code")
            phone = st.text_input("Phone (Optional)")
        with cols[1]:
            model_choice = st.selectbox("Bike Model", BIKE_PRESETS + ["Custom / Other"])
            custom_model = st.text_input("Custom Bike Name", disabled=(model_choice != "Custom / Other"))
            model = custom_model.strip() if model_choice == "Custom / Other" else model_choice
            qty_input = st.number_input("Quantity", min_value=1, step=1, value=1)
            rate = st.number_input("Per Bike Rate (PKR)", min_value=0.0, step=1000.0, value=None, placeholder="Enter rate")
        notes = st.text_area("Notes / Details", placeholder="Enter any details about this purchase...", height=100)

        total = qty_input * (rate or 0)
        st.write(f"**Total Purchase: {money(total)}**")

        if st.form_submit_button("💾 Save Purchase", use_container_width=True):
            if not model:
                st.error("Enter bike/model name.")
            elif not rate or rate <= 0:
                st.error("Enter a valid rate.")
            else:
                try:
                    if supplier_code:
                        existing = supabase_main.table("suppliers").select("*").eq("supplier_code", supplier_code).execute()
                        if not existing.data and supplier_name:
                            supabase_main.table("suppliers").insert({
                                "supplier_code": supplier_code,
                                "name": supplier_name,
                                "phone": phone
                            }).execute()
                            st.info(f"New supplier created: {supplier_code}")
                        elif existing.data and supplier_name:
                            if existing.data[0].get("name") != supplier_name:
                                supabase_main.table("suppliers").update({"name": supplier_name}).eq("supplier_code", supplier_code).execute()

                    supabase_main.table("purchases").insert({
                        "purchase_date": str(d),
                        "supplier_code": supplier_code,
                        "supplier_name": supplier_name,
                        "model": model,
                        "quantity": int(qty_input),
                        "rate_per_bike": float(rate),
                        "total_amount": float(total),
                        "notes": notes
                    }).execute()
                    st.success("Purchase saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Purchase error: {e}")

    st.markdown("### 🔎 Purchase History")
    start, end = date_range("From Date → To Date", "purchase_history_range")
    data = [x for x in purchases if in_range(x.get("purchase_date"), start, end)]

    c = st.columns(3)
    c[0].metric("TOTAL PURCHASE", money(sum(purchase_total(x) for x in data)))
    c[1].metric("BIKES PURCHASED", sum(q(x.get("quantity")) for x in data))
    c[2].metric("ENTRIES", len(data))
    st.dataframe(data, use_container_width=True, hide_index=True)

    if purchases:
        st.markdown("### ✏️ Edit / Delete Purchase")
        ids = [x.get("id") for x in purchases if x.get("id")]
        if ids:
            sid = st.selectbox("Select Purchase ID", ids)
            row = next(x for x in purchases if x.get("id") == sid)
            with st.form("edit_purchase"):
                nd = st.date_input("Date", date.fromisoformat(str(row.get("purchase_date"))[:10]), format="DD-MM-YYYY")
                nsup = st.text_input("Supplier", str(row.get("supplier_name") or row.get("dealer") or ""))
                nmodel = st.text_input("Model", str(row.get("model") or ""))
                nq = st.number_input("Quantity", min_value=1, value=max(q(row.get("quantity")), 1), step=1)
                nr = st.number_input("Rate", min_value=0.0, value=n(row.get("rate_per_bike")), step=1000.0)
                nn = st.text_area("Notes", str(row.get("notes") or ""), height=80)
                u, dlt = st.columns(2)
                update = u.form_submit_button("✅ Update", use_container_width=True)
                delete = dlt.form_submit_button("🗑️ Delete", use_container_width=True)
                if update:
                    try:
                        supabase_main.table("purchases").update({
                            "purchase_date": str(nd), "supplier_name": nsup,
                            "model": nmodel, "quantity": int(nq),
                            "rate_per_bike": float(nr), "notes": nn
                        }).eq("id", sid).execute()
                        st.success("Purchase updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase_main.table("purchases").delete().eq("id", sid).execute()
                        st.success("Purchase deleted."); st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# ==================== SALES ===============================
elif page == "🏍️ Sales":
    st.title("🏍️ Sales Entry")

    customer_names = [c.get("name") for c in customers if c.get("name")]
    customer_codes = {c.get("customer_code"): c.get("name") for c in customers if c.get("customer_code")}
    customer_phones = {c.get("customer_code"): c.get("phone") for c in customers if c.get("customer_code")}

    with st.form("sale"):
        cols = st.columns(2)
        with cols[0]:
            d = st.date_input("Date", date.today(), format="DD-MM-YYYY")
            customer_code = st.text_input("Customer Code", placeholder="CUS-1")
            customer_name = st.text_input("Customer Name", placeholder="Type name or code")
            phone = st.text_input("Phone (Optional)")
        with cols[1]:
            model_choice = st.selectbox("Bike Model", BIKE_PRESETS + ["Custom / Other"])
            custom_model = st.text_input("Custom Bike Name", disabled=(model_choice != "Custom / Other"))
            model = custom_model.strip() if model_choice == "Custom / Other" else model_choice
            qty_input = st.number_input("Quantity", min_value=1, step=1, value=1)
            rate = st.number_input("Per Bike Sale Rate (PKR)", min_value=0.0, step=1000.0, value=None, placeholder="Enter rate")
            received = st.number_input("Amount Received (PKR)", min_value=0.0, step=1000.0, value=None, placeholder="Enter received")
        notes = st.text_area("Notes / Details", placeholder="Enter any details about this sale...", height=100)

        total = qty_input * (rate or 0)
        balance = max(total - (received or 0), 0)

        st.write(f"**Total Sale: {money(total)}**")
        st.write(f"**Balance (Udhaar): {money(balance)}**")

        if st.form_submit_button("💾 Save Sale", use_container_width=True):
            if not model:
                st.error("Enter bike/model name.")
            elif not rate or rate <= 0:
                st.error("Enter a valid rate.")
            else:
                try:
                    if customer_name and customer_code and customer_code not in customer_codes:
                        supabase_main.table("customers").insert({
                            "customer_code": customer_code,
                            "name": customer_name,
                            "phone": phone
                        }).execute()
                        st.info(f"New customer created: {customer_code}")

                    supabase_main.table("sales").insert({
                        "sale_date": str(d),
                        "customer_code": customer_code,
                        "customer_name": customer_name or customer_codes.get(customer_code, ""),
                        "model": model,
                        "quantity": int(qty_input),
                        "sale_rate_per_bike": float(rate),
                        "amount_received": float(received or 0),
                        "notes": notes
                    }).execute()
                    st.success("Sale saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sale error: {e}")

    st.markdown("### 🔎 Sales History")
    start, end = date_range("From Date → To Date", "sales_history_range")
    data = [x for x in sales if in_range(x.get("sale_date"), start, end)]

    c = st.columns(4)
    c[0].metric("TOTAL SALES", money(sum(sale_total(x) for x in data)))
    c[1].metric("BIKES SOLD", sum(q(x.get("quantity")) for x in data))
    c[2].metric("RECEIVED", money(sum(n(x.get("amount_received")) for x in data)))
    c[3].metric("BALANCE", money(sum(max(sale_total(x) - n(x.get("amount_received")), 0) for x in data)))
    st.dataframe(data, use_container_width=True, hide_index=True)
    if sales:
        st.markdown("### ✏️ Edit / Delete Sale")
        ids = [x.get("id") for x in sales if x.get("id")]
        if ids:
            sid = st.selectbox("Select Sale ID", ids)
            row = next(x for x in sales if x.get("id") == sid)
            with st.form("edit_sale"):
                nd = st.date_input("Date", date.fromisoformat(str(row.get("sale_date"))[:10]), format="DD-MM-YYYY")
                nc = st.text_input("Customer Code", str(row.get("customer_code") or ""))
                nn = st.text_input("Customer Name", str(row.get("customer_name") or ""))
                nmodel = st.text_input("Model", str(row.get("model") or ""))
                nq = st.number_input("Quantity", min_value=1, value=max(q(row.get("quantity")), 1), step=1)
                nr = st.number_input("Rate", min_value=0.0, value=n(row.get("sale_rate_per_bike")), step=1000.0)
                nrec = st.number_input("Received", min_value=0.0, value=n(row.get("amount_received")), step=1000.0)
                nnotes = st.text_area("Notes", str(row.get("notes") or ""), height=80)
                u, dlt = st.columns(2)
                update = u.form_submit_button("✅ Update", use_container_width=True)
                delete = dlt.form_submit_button("🗑️ Delete", use_container_width=True)
                if update:
                    try:
                        supabase_main.table("sales").update({
                            "sale_date": str(nd), "customer_code": nc, "customer_name": nn,
                            "model": nmodel, "quantity": int(nq), "sale_rate_per_bike": float(nr),
                            "amount_received": float(nrec), "notes": nnotes
                        }).eq("id", sid).execute()
                        st.success("Sale updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase_main.table("sales").delete().eq("id", sid).execute()
                        st.success("Sale deleted."); st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# ==================== CUSTOMERS ===========================
elif page == "👥 Customers":
    st.title("👥 Customers List")

    st.markdown("### 📋 All Customers")
    table = []
    for c in customers:
        code = str(c.get("customer_code") or "")
        table.append({
            "Customer Code": code,
            "Name": c.get("name"),
            "Phone": c.get("phone"),
            "Outstanding": money(max(get_customer_balance(code), 0))
        })
    st.dataframe(table, use_container_width=True, hide_index=True)

# ==================== CUSTOMER KHATA ======================
elif page == "💰 Customer Khata":
    st.title("💰 Customer Khata / Ledger")

    if customers:
        opts = [f'{c.get("customer_code")} — {c.get("name")}' for c in customers if c.get("customer_code")]
        selected = st.selectbox("Select Customer", opts)

        if selected:
            code = selected.split(" — ")[0]
            customer = next(c for c in customers if c.get("customer_code") == code)

            st.markdown(f"""
            <div style="background:#1a1a1a;padding:15px;border-radius:10px;margin-bottom:15px;color:white;">
                <b>Customer:</b> {customer.get('name')} | <b>Code:</b> {code} | <b>Phone:</b> {customer.get('phone')}
            </div>
            """, unsafe_allow_html=True)

            start, end = date_range("From Date → To Date", f"khata_range_{code}")

            ledger = []
            for x in sales:
                if str(x.get("customer_code") or "") == code and in_range(x.get("sale_date"), start, end):
                    ledger.append({
                        "Date": x.get("sale_date"),
                        "Type": "Bike Sale",
                        "Description": f"{x.get('model')} × {q(x.get('quantity'))}",
                        "Debit (Udhaar)": max(sale_total(x) - n(x.get("amount_received")), 0),
                        "Credit (Payment)": 0
                    })
            for x in payments:
                if str(x.get("customer_code") or "") == code and in_range(x.get("payment_date"), start, end):
                    ledger.append({
                        "Date": x.get("payment_date"),
                        "Type": "Payment",
                        "Description": x.get("notes") or "Payment received",
                        "Debit (Udhaar)": 0,
                        "Credit (Payment)": n(x.get("amount"))
                    })
            for x in cash_trans:
                if str(x.get("customer_code") or "") == code and in_range(x.get("transaction_date"), start, end):
                    ledger.append({
                        "Date": x.get("transaction_date"),
                        "Type": x.get("transaction_type"),
                        "Description": x.get("description") or "Cash transaction",
                        "Debit (Udhaar)": n(x.get("amount")) if x.get("transaction_type") == "Cash Udaar" else 0,
                        "Credit (Payment)": n(x.get("amount")) if x.get("transaction_type") == "Cash Jama" else 0
                    })

            ledger.sort(key=lambda x: str(x["Date"] or ""))

            running = 0
            for x in ledger:
                running += x["Debit (Udhaar)"] - x["Credit (Payment)"]
                x["Balance"] = running

            c = st.columns(3)
            c[0].metric("TOTAL UDHAAR", money(sum(x["Debit (Udhaar)"] for x in ledger)))
            c[1].metric("TOTAL PAYMENTS", money(sum(x["Credit (Payment)"] for x in ledger)))
            c[2].metric("CURRENT BALANCE", money(max(running, 0)))

            st.dataframe(ledger, use_container_width=True, hide_index=True)
    else:
        st.info("No customers found.")

# ==================== CASH TRANSACTION ====================
elif page == "💵 Cash Transaction":
    st.title("💵 Cash Transaction (Customer)")

    if customers:
        opts = [f'{c.get("customer_code")} — {c.get("name")}' for c in customers if c.get("customer_code")]

        with st.form("cash_transaction"):
            selected = st.selectbox("Customer", opts)
            code = selected.split(" — ")[0] if selected else ""
            trans_type = st.selectbox("Transaction Type", ["Cash Udaar", "Cash Jama"])
            d = st.date_input("Date", date.today(), format="DD-MM-YYYY")
            amount = st.number_input("Amount (PKR)", min_value=0.0, step=1000.0, value=None, placeholder="Enter amount")
            description = st.text_area("Description / Details", placeholder="Enter transaction details...", height=100)

            if st.form_submit_button("💾 Save Cash Transaction", use_container_width=True):
                if not amount or amount <= 0:
                    st.error("Enter a valid amount.")
                else:
                    try:
                        supabase_main.table("customer_cash_transactions").insert({
                            "customer_code": code,
                            "transaction_date": str(d),
                            "transaction_type": trans_type,
                            "amount": float(amount),
                            "description": description
                        }).execute()
                        st.success(f"Cash {trans_type} saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transaction error: {e}")

        st.markdown("### 🔎 Cash Transaction History")
        start, end = date_range("From Date → To Date", "cash_trans_range")
        data = [x for x in cash_trans if in_range(x.get("transaction_date"), start, end)]
        st.dataframe(data, use_container_width=True, hide_index=True)

# ==================== EXPENSES ============================
elif page == "💸 Expenses":
    st.title("💸 Expenses")

    with st.form("expense"):
        d = st.date_input("Date", date.today(), format="DD-MM-YYYY")
        category = st.selectbox("Category", ["Rent", "Electricity", "Transport", "Staff", "Maintenance", "Other"])
        description = st.text_area("Description / Details", placeholder="Enter expense details...", height=80)
        amount = st.number_input("Amount (PKR)", min_value=0.0, step=500.0, value=None, placeholder="Enter amount")

        if st.form_submit_button("💾 Save Expense", use_container_width=True):
            if not amount or amount <= 0:
                st.error("Enter a valid amount.")
            else:
                try:
                    supabase_main.table("expenses").insert({
                        "expense_date": str(d),
                        "category": category,
                        "description": description,
                        "amount": float(amount)
                    }).execute()
                    st.success("Expense saved."); st.rerun()
                except Exception as e:
                    st.error(f"Expense error: {e}")

    start, end = date_range("From Date → To Date", "expense_history_range")
    data = [x for x in expenses if in_range(x.get("expense_date"), start, end)]
    st.metric("TOTAL EXPENSES", money(sum(n(x.get("amount")) for x in data)))
    st.dataframe(data, use_container_width=True, hide_index=True)

    if expenses:
        ids = [x.get("id") for x in expenses if x.get("id")]
        if ids:
            st.markdown("### ✏️ Edit / Delete Expense")
            sid = st.selectbox("Select Expense ID", ids)
            row = next(x for x in expenses if x.get("id") == sid)
            with st.form("edit_expense"):
                nd = st.date_input("Date", date.fromisoformat(str(row.get("expense_date"))[:10]), format="DD-MM-YYYY")
                cats = ["Rent", "Electricity", "Transport", "Staff", "Maintenance", "Other"]
                old_cat = str(row.get("category") or "Other")
                nc = st.selectbox("Category", cats, index=cats.index(old_cat) if old_cat in cats else 5)
                ndesc = st.text_area("Description", str(row.get("description") or ""), height=80)
                namt = st.number_input("Amount", min_value=0.0, value=n(row.get("amount")), step=500.0)
                u, dlt = st.columns(2)
                update = u.form_submit_button("✅ Update", use_container_width=True)
                delete = dlt.form_submit_button("🗑️ Delete", use_container_width=True)
                if update:
                    try:
                        supabase_main.table("expenses").update({
                            "expense_date": str(nd), "category": nc,
                            "description": ndesc, "amount": float(namt)
                        }).eq("id", sid).execute()
                        st.success("Expense updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase_main.table("expenses").delete().eq("id", sid).execute()
                        st.success("Expense deleted."); st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# ==================== STOCK ===============================
elif page == "📦 Stock":
    st.title("📦 Current Stock")
    st.dataframe(stock_data(purchases, sales), use_container_width=True, hide_index=True)
# ==================== BIKE REGISTRATION ====================
elif page == "📄 Bike Registration":
    st.title("📄 Bike Registration / Ownership")
    
    if not supabase_reg:
        st.error("Registration database not connected. Please check secrets.")
    else:
        tab1, tab2 = st.tabs(["📝 New Registration", "🔍 Search Registration"])
        
        # ========== TAB 1: NEW REGISTRATION ==========
        with tab1:
            with st.form("bike_registration"):
                st.markdown("### 🔧 Bike Details")
                col1, col2 = st.columns(2)
                with col1:
                    engine_number = st.text_input("Engine Number", placeholder="ENG-001")
                    chassis_number = st.text_input("Chassis Number", placeholder="CH-001")
                with col2:
                    model = st.selectbox("Model", BIKE_PRESETS + ["Custom / Other"])
                    custom_model = st.text_input("Custom Model Name", disabled=(model != "Custom / Other"))
                    final_model = custom_model.strip() if model == "Custom / Other" else model
                
                st.markdown("---")
                st.markdown("### 👤 Owner Details")
                col1, col2 = st.columns(2)
                with col1:
                    owner_name = st.text_input("Owner Name", placeholder="Full name as per NIC")
                    father_name = st.text_input("Father Name", placeholder="Father's full name")
                    owner_nic = st.text_input("NIC", placeholder="12345-6789012-3")
                with col2:
                    owner_phone = st.text_input("Phone", placeholder="0300-1234567")
                    owner_address = st.text_area("Address", placeholder="House #12, Street 5, ...", height=80)
                
                st.markdown("---")
                st.markdown("### 📅 Registration Details")
                col1, col2 = st.columns(2)
                with col1:
                    registration_date = st.date_input("Registration Date", date.today(), format="DD-MM-YYYY")
                    serial_number = st.text_input("Serial Number", placeholder="Optional")
                with col2:
                    purchase_dealer = st.text_input("Purchase Dealer", placeholder="Dealer name")
                
                st.markdown("---")
                st.markdown("### 📎 Upload NIC")
                col1, col2 = st.columns(2)
                with col1:
                    nic_front = st.file_uploader("NIC Front", type=["jpg", "jpeg", "png", "pdf"], key="nic_front")
                with col2:
                    nic_back = st.file_uploader("NIC Back", type=["jpg", "jpeg", "png", "pdf"], key="nic_back")
                
                notes = st.text_area("Notes", placeholder="Any additional notes...", height=80)
                
                if st.form_submit_button("💾 Save Registration", use_container_width=True):
                    if not engine_number:
                        st.error("Engine Number is required.")
                    elif not owner_name:
                        st.error("Owner Name is required.")
                    else:
                        try:
                            existing = supabase_reg.table("bike_registrations").select("*").eq("engine_number", engine_number).execute()
                            if existing.data:
                                st.error(f"Engine number '{engine_number}' already registered!")
                            else:
                                nic_front_url = None
                                nic_back_url = None
                                
                                if nic_front:
                                    file_path = f"nic-front/{engine_number}_front.jpg"
                                    supabase_reg.storage.from_("bike-documents").upload(file_path, nic_front.getvalue(), {"content-type": nic_front.type})
                                    nic_front_url = supabase_reg.storage.from_("bike-documents").get_public_url(file_path)
                                
                                if nic_back:
                                    file_path = f"nic-back/{engine_number}_back.jpg"
                                    supabase_reg.storage.from_("bike-documents").upload(file_path, nic_back.getvalue(), {"content-type": nic_back.type})
                                    nic_back_url = supabase_reg.storage.from_("bike-documents").get_public_url(file_path)
                                
                                supabase_reg.table("bike_registrations").insert({
                                    "engine_number": engine_number,
                                    "chassis_number": chassis_number,
                                    "model": final_model,
                                    "owner_name": owner_name,
                                    "father_name": father_name,
                                    "owner_nic": owner_nic,
                                    "owner_phone": owner_phone,
                                    "owner_address": owner_address,
                                    "registration_date": str(registration_date),
                                    "serial_number": serial_number,
                                    "purchase_dealer": purchase_dealer,
                                    "nic_front_url": nic_front_url,
                                    "nic_back_url": nic_back_url,
                                    "notes": notes
                                }).execute()
                                
                                st.success(f"✅ Registration saved for {owner_name}!")
                                st.balloons()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Registration error: {e}")
        
        # ========== TAB 2: SEARCH REGISTRATION ==========
        with tab2:
            st.markdown("### 🔍 Search Registration")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                search_by = st.selectbox("Search by", ["Engine Number", "Chassis Number", "Owner Name", "Father Name", "NIC"])
            with col2:
                search_query = st.text_input("Search", placeholder=f"Enter {search_by}...")
            
            if st.button("🔍 Search", use_container_width=True):
                if search_query:
                    try:
                        query = supabase_reg.table("bike_registrations").select("*")
                        
                        if search_by == "Engine Number":
                            query = query.eq("engine_number", search_query)
                        elif search_by == "Chassis Number":
                            query = query.eq("chassis_number", search_query)
                        elif search_by == "Owner Name":
                            query = query.ilike("owner_name", f"%{search_query}%")
                        elif search_by == "Father Name":
                            query = query.ilike("father_name", f"%{search_query}%")
                        elif search_by == "NIC":
                            query = query.ilike("owner_nic", f"%{search_query}%")
                        
                        results = query.execute().data
                        
                        if results:
                            st.success(f"Found {len(results)} record(s)")
                            
                            for record in results:
                                with st.expander(f"🔧 {record.get('engine_number')} — {record.get('owner_name')}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"""
                                        **Engine Number:** {record.get('engine_number')}  
                                        **Chassis Number:** {record.get('chassis_number')}  
                                        **Model:** {record.get('model')}  
                                        **Registration Date:** {record.get('registration_date')}  
                                        **Serial Number:** {record.get('serial_number')}
                                        """)
                                    with col2:
                                        st.markdown(f"""
                                        **Owner Name:** {record.get('owner_name')}  
                                        **Father Name:** {record.get('father_name') or 'N/A'}  
                                        **NIC:** {record.get('owner_nic')}  
                                        **Phone:** {record.get('owner_phone')}  
                                        **Address:** {record.get('owner_address')}  
                                        **Purchase Dealer:** {record.get('purchase_dealer')}
                                        """)
                                    
                                    st.markdown("#### 🪪 NIC Images")
                                    nic_col1, nic_col2 = st.columns(2)
                                    with nic_col1:
                                        if record.get('nic_front_url'):
                                            st.image(record.get('nic_front_url'), caption="NIC Front", use_container_width=True)
                                        else:
                                            st.info("No NIC Front uploaded")
                                    
                                    with nic_col2:
                                        if record.get('nic_back_url'):
                                            st.image(record.get('nic_back_url'), caption="NIC Back", use_container_width=True)
                                        else:
                                            st.info("No NIC Back uploaded")
                                    
                                    if record.get('notes'):
                                        st.markdown(f"**Notes:** {record.get('notes')}")

                                    # ========== EDIT & DELETE BUTTONS ==========
                                    st.markdown("---")
                                    col_edit, col_delete = st.columns(2)
                                    
                                    with col_edit:
                                        if st.button(f"✏️ Edit", key=f"edit_{record.get('id')}"):
                                            st.session_state.edit_record = record
                                            st.rerun()
                                    
                                    with col_delete:
                                        if st.button(f"🗑️ Delete", key=f"delete_{record.get('id')}"):
                                            try:
                                                supabase_reg.table("bike_registrations").delete().eq("id", record.get('id')).execute()
                                                st.success(f"Record {record.get('engine_number')} deleted successfully!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Delete error: {e}")
                        
                        # ========== EDIT FORM ==========
                        if "edit_record" in st.session_state and st.session_state.edit_record:
                            record = st.session_state.edit_record
                            st.markdown("---")
                            st.markdown("### ✏️ Edit Registration")
                            
                            with st.form("edit_registration_form"):
                                st.markdown("#### 🔧 Bike Details")
                                col1, col2 = st.columns(2)
                                with col1:
                                    engine_number = st.text_input("Engine Number", value=record.get('engine_number'), disabled=True)
                                    chassis_number = st.text_input("Chassis Number", value=record.get('chassis_number') or "")
                                with col2:
                                    model = st.text_input("Model", value=record.get('model') or "")
                                
                                st.markdown("#### 👤 Owner Details")
                                col1, col2 = st.columns(2)
                                with col1:
                                    owner_name = st.text_input("Owner Name", value=record.get('owner_name') or "")
                                    father_name = st.text_input("Father Name", value=record.get('father_name') or "")
                                    owner_nic = st.text_input("NIC", value=record.get('owner_nic') or "")
                                with col2:
                                    owner_phone = st.text_input("Phone", value=record.get('owner_phone') or "")
                                    owner_address = st.text_area("Address", value=record.get('owner_address') or "", height=80)
                                
                                st.markdown("#### 📅 Registration Details")
                                col1, col2 = st.columns(2)
                                with col1:
                                    registration_date = st.date_input("Registration Date", value=date.fromisoformat(record.get('registration_date')) if record.get('registration_date') else date.today())
                                    serial_number = st.text_input("Serial Number", value=record.get('serial_number') or "")
                                with col2:
                                    purchase_dealer = st.text_input("Purchase Dealer", value=record.get('purchase_dealer') or "")
                                
                                st.markdown("#### 📎 Upload NIC (Optional)")
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_nic_front = st.file_uploader(
                                        "New NIC Front (optional)", 
                                        type=["jpg", "jpeg", "png", "pdf"], 
                                        key=f"edit_nic_front_{record.get('id')}"
                                    )
                                    if record.get('nic_front_url'):
                                        st.image(record.get('nic_front_url'), caption="Current NIC Front", width=150)
                                with col2:
                                    new_nic_back = st.file_uploader(
                                        "New NIC Back (optional)", 
                                        type=["jpg", "jpeg", "png", "pdf"], 
                                        key=f"edit_nic_back_{record.get('id')}"
                                    )
                                    if record.get('nic_back_url'):
                                        st.image(record.get('nic_back_url'), caption="Current NIC Back", width=150)
                                
                                notes = st.text_area("Notes", value=record.get('notes') or "", height=80)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Update Registration", use_container_width=True):
                                        try:
                                            update_data = {
                                                "chassis_number": chassis_number,
                                                "model": model,
                                                "owner_name": owner_name,
                                                "father_name": father_name,
                                                "owner_nic": owner_nic,
                                                "owner_phone": owner_phone,
                                                "owner_address": owner_address,
                                                "registration_date": str(registration_date),
                                                "serial_number": serial_number,
                                                "purchase_dealer": purchase_dealer,
                                                "notes": notes
                                            }
                                            
                                            if new_nic_front:
                                                file_path = f"nic-front/{record.get('engine_number')}_front.jpg"
                                                supabase_reg.storage.from_("bike-documents").upload(file_path, new_nic_front.getvalue(), {"content-type": new_nic_front.type})
                                                update_data["nic_front_url"] = supabase_reg.storage.from_("bike-documents").get_public_url(file_path)
                                            
                                            if new_nic_back:
                                                file_path = f"nic-back/{record.get('engine_number')}_back.jpg"
                                                supabase_reg.storage.from_("bike-documents").upload(file_path, new_nic_back.getvalue(), {"content-type": new_nic_back.type})
                                                update_data["nic_back_url"] = supabase_reg.storage.from_("bike-documents").get_public_url(file_path)
                                            
                                            supabase_reg.table("bike_registrations").update(update_data).eq("id", record.get('id')).execute()
                                            st.success("✅ Record updated successfully!")
                                            st.session_state.edit_record = None
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Update error: {e}")
                                
                                with col2:
                                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                                        st.session_state.edit_record = None
                                        st.rerun()
                        else:
                            st.warning("No records found.")
                    except Exception as e:
                        st.error(f"Search error: {e}")
                else:
                    st.warning("Please enter a search query.")
