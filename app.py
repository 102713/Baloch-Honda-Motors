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
/* Main Theme */
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
/* Big Text Area */
.stTextArea textarea {min-height: 100px !important;}
/* Price Input - No default 0.00 */
input[type="number"] {color: #111827 !important;}
</style>
""", unsafe_allow_html=True)

# ==================== SUPABASE ============================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    supabase = None

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
    if not supabase: return []
    try:
        return supabase.table(table).select("*").execute().data or []
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
    # Sales udhaar
    for x in sales:
        if str(x.get("customer_code") or "") == code:
            bal += max(sale_total(x) - n(x.get("amount_received")), 0)
    # Payments
    for x in payments:
        if str(x.get("customer_code") or "") == code:
            bal -= n(x.get("amount"))
    # Cash transactions
    for x in cash_trans:
        if str(x.get("customer_code") or "") == code:
            if x.get("transaction_type") == "Cash Udaar":
                bal += n(x.get("amount"))
            else:  # Cash Jama
                bal -= n(x.get("amount"))
    return bal

def get_supplier_balance(code):
    bal = 0.0
    # Purchases
    for x in purchases:
        if str(x.get("supplier_code") or "") == code:
            bal += n(x.get("total_amount") or purchase_total(x))
    # Payments
    for x in supplier_payments:
        if str(x.get("supplier_code") or "") == code:
            bal -= n(x.get("amount"))
    # Advances
    for x in supplier_advances:
        if str(x.get("supplier_code") or "") == code:
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
    "📅 Reports"
])

# Auto-collapse sidebar
if page != st.session_state.previous_page:
    st.session_state.previous_page = page
    # Sidebar collapse via JavaScript
    st.markdown("""
    <script>
    // Auto collapse sidebar on page change
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.width = '0px';
        sidebar.style.minWidth = '0px';
        sidebar.style.maxWidth = '0px';
    }
    </script>
    """, unsafe_allow_html=True)

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

    # Gross Profit
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

    # Receivables
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

    # Supplier codes
    supplier_codes = [s.get("supplier_code") for s in suppliers if s.get("supplier_code")]

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
                    # Auto-create supplier if new
                    if supplier_name and supplier_code not in supplier_codes:
                        supabase.table("suppliers").insert({
                            "supplier_code": supplier_code,
                            "name": supplier_name,
                            "phone": phone
                        }).execute()
                        st.info(f"New supplier created: {supplier_code}")

                    supabase.table("purchases").insert({
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

    # Edit/Delete
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
                        supabase.table("purchases").update({
                            "purchase_date": str(nd), "supplier_name": nsup,
                            "model": nmodel, "quantity": int(nq),
                            "rate_per_bike": float(nr), "notes": nn
                        }).eq("id", sid).execute()
                        st.success("Purchase updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("purchases").delete().eq("id", sid).execute()
                        st.success("Purchase deleted."); st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# ==================== SALES ===============================
elif page == "🏍️ Sales":
    st.title("🏍️ Sales Entry")

    # Customer auto-suggest
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
                    # Auto-create customer if new
                    if customer_name and customer_code not in customer_codes:
                        # Generate new code if not provided
                        if not customer_code:
                            existing = {c.get("customer_code") for c in customers}
                            customer_code = generate_code("CUS", existing)
                        supabase.table("customers").insert({
                            "customer_code": customer_code,
                            "name": customer_name,
                            "phone": phone
                        }).execute()
                        st.info(f"New customer created: {customer_code}")

                    supabase.table("sales").insert({
                        "sale_date": str(d),
                        "customer_code": customer_code,
                        "customer_name": customer_name or customer_codes.get(customer_code, ""),
                        "model": model,
                        "quantity": int(qty_input),
                        "sale_rate_per_bike": float(rate),
                        "amount_received": float(received or 0),
                        "balance": float(balance),
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

    # Edit/Delete
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
                        supabase.table("sales").update({
                            "sale_date": str(nd), "customer_code": nc, "customer_name": nn,
                            "model": nmodel, "quantity": int(nq), "sale_rate_per_bike": float(nr),
                            "amount_received": float(nrec), "notes": nnotes
                        }).eq("id", sid).execute()
                        st.success("Sale updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("sales").delete().eq("id", sid).execute()
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

            # Build ledger
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

            # Running balance
            running = 0
            for x in ledger:
                running += x["Debit (Udhaar)"] - x["Credit (Payment)"]
                x["Balance"] = running

            c = st.columns(3)
            c[0].metric("TOTAL UDHAAR", money(sum(x["Debit (Udhaar)"] for x in ledger)))
            c[1].metric("TOTAL PAYMENTS", money(sum(x["Credit (Payment)"] for x in ledger)))
            c[2].metric("CURRENT BALANCE", money(max(running, 0)))

            st.dataframe(ledger, use_container_width=True, hide_index=True)

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
                        supabase.table("customer_cash_transactions").insert({
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
                    supabase.table("expenses").insert({
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

    # Edit/Delete
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
                        supabase.table("expenses").update({
                            "expense_date": str(nd), "category": nc,
                            "description": ndesc, "amount": float(namt)
                        }).eq("id", sid).execute()
                        st.success("Expense updated."); st.rerun()
                    except Exception as e:
                        st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("expenses").delete().eq("id", sid).execute()
                        st.success("Expense deleted."); st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")

# ==================== STOCK ===============================
elif page == "📦 Stock":
    st.title("📦 Current Stock")
    st.dataframe(stock_data(purchases, sales), use_container_width=True, hide_index=True)

# ==================== REPORTS =============================
else:  # Reports
    st.title("📅 Date Range Report")

    start, end = date_range("Report From Date → To Date", "report_range")

    dp = [x for x in purchases if in_range(x.get("purchase_date"), start, end)]
    ds = [x for x in sales if in_range(x.get("sale_date"), start, end)]
    de = [x for x in expenses if in_range(x.get("expense_date"), start, end)]
    dpay = [x for x in payments if in_range(x.get("payment_date"), start, end)]
    dcash = [x for x in cash_trans if in_range(x.get("transaction_date"), start, end)]

    c = st.columns(5)
    c[0].metric("PURCHASES", money(sum(purchase_total(x) for x in dp)))
    c[1].metric("SALES", money(sum(sale_total(x) for x in ds)))
    c[2].metric("EXPENSES", money(sum(n(x.get("amount")) for x in de)))
    c[3].metric("PAYMENTS", money(sum(n(x.get("amount")) for x in dpay)))
    c[4].metric("CASH TRANS", money(sum(n(x.get("amount")) for x in dcash)))

    st.markdown("### 🛒 Purchases")
    st.dataframe(dp, use_container_width=True, hide_index=True)
    st.markdown("### 🧾 Sales")
    st.dataframe(ds, use_container_width=True, hide_index=True)
    st.markdown("### 💸 Expenses")
    st.dataframe(de, use_container_width=True, hide_index=True)
    st.markdown("### 💵 Customer Payments")
    st.dataframe(dpay, use_container_width=True, hide_index=True)
    st.markdown("### 💵 Cash Transactions")
    st.dataframe(dcash, use_container_width=True, hide_index=True)
