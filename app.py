import streamlit as st
from supabase import create_client
from datetime import date
from collections import defaultdict

# =========================================================
# BALOCH HONDA MOTORS - BUSINESS MANAGEMENT SYSTEM
# =========================================================
st.set_page_config(
    page_title="BALOCH HONDA MOTORS",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- STYLE -------------------------
st.markdown("""
<style>
.block-container{padding-top:1rem;padding-bottom:2rem}
.hero{background:linear-gradient(115deg,#090909 0%,#1c1c1c 55%,#b40000 100%);
border-radius:20px;padding:20px 24px;color:white;margin-bottom:18px;border:1px solid #333}
.hero-title{font-size:30px;font-weight:900;letter-spacing:.5px}
.hero-sub{color:#d1d5db;font-size:14px;margin-top:3px}
.hero-bike{font-size:72px;text-align:right}
.side-brand{background:linear-gradient(145deg,#080808,#242424);border-radius:18px;
padding:16px 10px;margin-bottom:16px;text-align:center;color:white;border:1px solid #3b3b3b}
.side-bike{font-size:42px;line-height:1.05}.side-title{font-size:18px;font-weight:900}
.side-sub{font-size:11px;font-weight:900;color:#ef4444;letter-spacing:3px}
.side-location{font-size:11px;color:#cbd5e1;margin-top:6px}
.kpi{border-radius:16px;padding:14px 16px;background:white;border:1px solid #e5e7eb;
box-shadow:0 2px 10px rgba(0,0,0,.04)}
.kpi-label{font-size:11px;color:#6b7280;font-weight:800;text-transform:uppercase}
.kpi-value{font-size:22px;font-weight:900;color:#111827;margin-top:4px}
.section-title{font-size:19px;font-weight:900;margin:14px 0 8px}
div[data-testid="stSidebar"]{border-right:1px solid #e5e7eb}
div[data-testid="stSidebar"] .stRadio label{font-weight:700}
</style>
""", unsafe_allow_html=True)

# ---------------------- SUPABASE ------------------------
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    supabase = None

# ----------------------- HELPERS ------------------------
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
    for x in purchases: bought[str(x.get("model") or "Other")] += q(x.get("quantity"))
    for x in sales: sold[str(x.get("model") or "Other")] += q(x.get("quantity"))
    models = sorted(set(bought) | set(sold))
    return [{"Model":m,"Purchased":bought[m],"Sold":sold[m],
             "Current Stock":bought[m]-sold[m]} for m in models]

# ------------------------- LOGIN ------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div><div class="hero-title">BALOCH HONDA MOTORS</div>
        <div class="hero-sub">Dera Murad Jamali — Business Management System</div></div>
        <div class="hero-bike">🏍️</div>
      </div>
    </div>""", unsafe_allow_html=True)

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("🔐 Login", use_container_width=True):
            if supabase:
                try:
                    r=(supabase.table("users").select("*")
                       .eq("username",username)
                       .eq("password_hash",password)
                       .limit(1).execute())
                    if r.data:
                        st.session_state.logged_in=True
                        st.session_state.user=r.data[0]
                        st.rerun()
                    else: st.error("Invalid username or password.")
                except Exception as e: st.error(f"Login error: {e}")
            else: st.error("Supabase connection is not configured.")
    st.caption("Initial test login: admin / demo123")
    st.stop()

# ------------------------ SIDEBAR -----------------------
st.sidebar.markdown("""
<div class="side-brand">
<div class="side-bike">🏍️</div>
<div class="side-title">BALOCH HONDA</div>
<div class="side-sub">MOTORS</div>
<div class="side-location">Dera Murad Jamali</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("MAIN MENU",[
    "🏠 Dashboard","🛒 Purchases","🏍️ Sales","👤 Customers / Khata",
    "💵 Customer Payments","💸 Expenses","📦 Stock","📅 Daily Report","📊 Monthly Report"
])
if st.sidebar.button("🚪 Logout",use_container_width=True):
    st.session_state.logged_in=False
    st.rerun()

purchases=rows("purchases")
sales=rows("sales")
customers=rows("customers")
expenses=rows("expenses")
payments=rows("customer_payments")

# ======================= DASHBOARD ======================
if page=="🏠 Dashboard":
    st.markdown("""
    <div class="hero"><div style="display:flex;align-items:center;justify-content:space-between">
    <div><div class="hero-title">BALOCH HONDA MOTORS</div>
    <div class="hero-sub">Professional Motorcycle Dealership Dashboard • Dera Murad Jamali</div></div>
    <div class="hero-bike">🏍️</div></div></div>""",unsafe_allow_html=True)

    pt=sum(purchase_total(x) for x in purchases)
    stot=sum(sale_total(x) for x in sales)
    exp=sum(n(x.get("amount")) for x in expenses)
    pq=sum(q(x.get("quantity")) for x in purchases)
    sq=sum(q(x.get("quantity")) for x in sales)

    costs=defaultdict(lambda:[0,0.0])
    for x in purchases:
        m=str(x.get("model") or "Other")
        costs[m][0]+=q(x.get("quantity")); costs[m][1]+=purchase_total(x)
    gross=0
    for x in sales:
        m=str(x.get("model") or "Other")
        avg=costs[m][1]/costs[m][0] if costs[m][0] else 0
        gross += sale_total(x)-q(x.get("quantity"))*avg

    receivables=0
    for c in customers:
        code=str(c.get("customer_code") or "")
        bal=0
        for x in sales:
            if str(x.get("customer_code") or "")==code:
                bal += max(sale_total(x)-n(x.get("amount_received")),0)
        for x in payments:
            if str(x.get("customer_code") or "")==code:
                bal -= n(x.get("amount"))
        receivables += max(bal,0)

    cards=[("TOTAL PURCHASE",money(pt)),("TOTAL SALES",money(stot)),
           ("CURRENT STOCK",f"{pq-sq:,} Bikes"),("GROSS PROFIT",money(gross)),
           ("EXPENSES",money(exp)),("RECEIVABLES",money(receivables))]
    cc=st.columns(6)
    for col,(label,val) in zip(cc,cards):
        col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div>'
                     f'<div class="kpi-value">{val}</div></div>',unsafe_allow_html=True)

    a,b=st.columns(2)
    a.metric("NET PROFIT / LOSS",money(gross-exp))
    b.metric("BIKES PURCHASED / SOLD",f"{pq:,} / {sq:,}")

    l,r=st.columns(2)
    with l:
        st.markdown("### 🧾 Recent Sales")
        rs=sorted(sales,key=lambda x:str(x.get("sale_date") or ""),reverse=True)[:10]
        st.dataframe([{"Date":x.get("sale_date"),"Customer":x.get("customer_name"),
                       "Model":x.get("model"),"Qty":q(x.get("quantity")),
                       "Total":sale_total(x),"Received":n(x.get("amount_received")),
                       "Balance":max(sale_total(x)-n(x.get("amount_received")),0)} for x in rs],
                     use_container_width=True,hide_index=True)
    with r:
        st.markdown("### 🛒 Recent Purchases")
        rp=sorted(purchases,key=lambda x:str(x.get("purchase_date") or ""),reverse=True)[:10]
        st.dataframe([{"Date":x.get("purchase_date"),"Dealer":x.get("dealer"),
                       "Model":x.get("model"),"Qty":q(x.get("quantity")),
                       "Rate":n(x.get("rate_per_bike")),"Total":purchase_total(x)} for x in rp],
                     use_container_width=True,hide_index=True)

    st.markdown("### 📦 Model-wise Stock")
    st.dataframe(stock_data(purchases,sales),use_container_width=True,hide_index=True)

# ======================= PURCHASES ======================
elif page=="🛒 Purchases":
    st.title("🛒 Purchase Entry")
    with st.form("purchase"):
        d=st.date_input("Date",date.today(),format="DD-MM-YYYY")
        dealer=st.text_input("Dealer / Supplier")
        choice=st.selectbox("Bike Model",BIKE_PRESETS+["Custom / Other"])
        custom=st.text_input("Custom Bike Name",disabled=choice!="Custom / Other")
        model=custom.strip() if choice=="Custom / Other" else choice
        quantity=st.number_input("Quantity",min_value=1,step=1)
        rate=st.number_input("Per Bike Purchase Rate (PKR)",min_value=0.0,step=1000.0)
        notes=st.text_input("Notes")
        st.write(f"**Total Purchase: {money(quantity*rate)}**")
        if st.form_submit_button("💾 Save Purchase",use_container_width=True):
            if not model: st.error("Enter bike/model name.")
            else:
                try:
                    supabase.table("purchases").insert({
                        "purchase_date":str(d),"dealer":dealer,"model":model,
                        "quantity":int(quantity),"rate_per_bike":float(rate),"notes":notes
                    }).execute()
                    st.success("Purchase saved."); st.rerun()
                except Exception as e: st.error(f"Purchase error: {e}")

    st.markdown("### 🔎 Purchase History")
    start,end=date_range("From Date → To Date","purchase_history_range")
    data=[x for x in purchases if in_range(x.get("purchase_date"),start,end)]
    c=st.columns(3)
    c[0].metric("TOTAL PURCHASE",money(sum(purchase_total(x) for x in data)))
    c[1].metric("BIKES PURCHASED",sum(q(x.get("quantity")) for x in data))
    c[2].metric("ENTRIES",len(data))
    st.dataframe(data,use_container_width=True,hide_index=True)

    if purchases:
        st.markdown("### ✏️ Edit / Delete Purchase")
        ids=[x.get("id") for x in purchases if x.get("id") is not None]
        if ids:
            sid=st.selectbox("Select Purchase ID",ids)
            row=next(x for x in purchases if x.get("id")==sid)
            with st.form("edit_purchase"):
                nd=st.date_input("Date",date.fromisoformat(str(row.get("purchase_date"))[:10]),format="DD-MM-YYYY")
                ndealer=st.text_input("Dealer",str(row.get("dealer") or ""))
                nmodel=st.text_input("Model",str(row.get("model") or ""))
                nq=st.number_input("Quantity",min_value=1,value=max(q(row.get("quantity")),1),step=1)
                nr=st.number_input("Rate",min_value=0.0,value=n(row.get("rate_per_bike")),step=1000.0)
                nn=st.text_input("Notes",str(row.get("notes") or ""))
                u,dlt=st.columns(2)
                update=u.form_submit_button("Update Purchase",use_container_width=True)
                delete=dlt.form_submit_button("Delete Purchase",use_container_width=True)
                if update:
                    try:
                        supabase.table("purchases").update({
                            "purchase_date":str(nd),"dealer":ndealer,"model":nmodel,
                            "quantity":int(nq),"rate_per_bike":float(nr),"notes":nn}).eq("id",sid).execute()
                        st.success("Purchase updated.");st.rerun()
                    except Exception as e:st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("purchases").delete().eq("id",sid).execute()
                        st.success("Purchase deleted.");st.rerun()
                    except Exception as e:st.error(f"Delete error: {e}")

# ========================= SALES ========================
elif page=="🏍️ Sales":
    st.title("🏍️ Sales Entry")
    customer_options=["Walk-in"]+[f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
    with st.form("sale"):
        d=st.date_input("Date",date.today(),format="DD-MM-YYYY")
        selected=st.selectbox("Customer",customer_options)
        if selected=="Walk-in": code=""; cname="Walk-in"
        else:
            code=selected.split(" — ",1)[0]
            obj=next(x for x in customers if str(x.get("customer_code"))==code)
            cname=obj.get("name")
        choice=st.selectbox("Bike Model",BIKE_PRESETS+["Custom / Other"])
        custom=st.text_input("Custom Bike Name",disabled=choice!="Custom / Other")
        model=custom.strip() if choice=="Custom / Other" else choice
        quantity=st.number_input("Quantity",min_value=1,step=1)
        rate=st.number_input("Per Bike Sale Rate (PKR)",min_value=0.0,step=1000.0)
        received=st.number_input("Amount Received (PKR)",min_value=0.0,step=1000.0)
        notes=st.text_input("Notes")
        total=quantity*rate
        st.write(f"**Total Sale: {money(total)}**")
        st.write(f"**Balance: {money(max(total-received,0))}**")
        if st.form_submit_button("💾 Save Sale",use_container_width=True):
            if not model:st.error("Enter bike/model name.")
            else:
                try:
                    supabase.table("sales").insert({
                        "sale_date":str(d),"customer_name":cname,"customer_code":code,
                        "model":model,"quantity":int(quantity),"sale_rate_per_bike":float(rate),
                        "amount_received":float(received),"notes":notes}).execute()
                    st.success("Sale saved.");st.rerun()
                except Exception as e:st.error(f"Sale error: {e}")

    st.markdown("### 🔎 Sales History")
    start,end=date_range("From Date → To Date","sales_history_range")
    data=[x for x in sales if in_range(x.get("sale_date"),start,end)]
    c=st.columns(4)
    c[0].metric("TOTAL SALES",money(sum(sale_total(x) for x in data)))
    c[1].metric("BIKES SOLD",sum(q(x.get("quantity")) for x in data))
    c[2].metric("RECEIVED",money(sum(n(x.get("amount_received")) for x in data)))
    c[3].metric("BALANCE",money(sum(max(sale_total(x)-n(x.get("amount_received")),0) for x in data)))
    st.dataframe(data,use_container_width=True,hide_index=True)

    if sales:
        st.markdown("### ✏️ Edit / Delete Sale")
        ids=[x.get("id") for x in sales if x.get("id") is not None]
        if ids:
            sid=st.selectbox("Select Sale ID",ids)
            row=next(x for x in sales if x.get("id")==sid)
            with st.form("edit_sale"):
                nd=st.date_input("Date",date.fromisoformat(str(row.get("sale_date"))[:10]),format="DD-MM-YYYY")
                nc=st.text_input("Customer ID",str(row.get("customer_code") or ""))
                nname=st.text_input("Customer Name",str(row.get("customer_name") or ""))
                nm=st.text_input("Model",str(row.get("model") or ""))
                nq=st.number_input("Quantity",min_value=1,value=max(q(row.get("quantity")),1),step=1)
                nr=st.number_input("Sale Rate",min_value=0.0,value=n(row.get("sale_rate_per_bike")),step=1000.0)
                nrec=st.number_input("Received",min_value=0.0,value=n(row.get("amount_received")),step=1000.0)
                nn=st.text_input("Notes",str(row.get("notes") or ""))
                u,dlt=st.columns(2)
                update=u.form_submit_button("Update Sale",use_container_width=True)
                delete=dlt.form_submit_button("Delete Sale",use_container_width=True)
                if update:
                    try:
                        supabase.table("sales").update({
                            "sale_date":str(nd),"customer_code":nc,"customer_name":nname,
                            "model":nm,"quantity":int(nq),"sale_rate_per_bike":float(nr),
                            "amount_received":float(nrec),"notes":nn}).eq("id",sid).execute()
                        st.success("Sale updated.");st.rerun()
                    except Exception as e:st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("sales").delete().eq("id",sid).execute()
                        st.success("Sale deleted.");st.rerun()
                    except Exception as e:st.error(f"Delete error: {e}")

# ===================== CUSTOMERS / KHATA =================
elif page=="👤 Customers / Khata":
    st.title("👤 Customers & Khata")
    with st.form("customer"):
        name=st.text_input("Customer Name")
        phone=st.text_input("Phone")
        address=st.text_input("Address")
        if st.form_submit_button("➕ Add Customer",use_container_width=True):
            if not name.strip(): st.error("Customer name is required.")
            else:
                try:
                    codes={str(x.get("customer_code") or "") for x in customers}
                    i=1
                    while f"CUS-{i:04d}" in codes:i+=1
                    supabase.table("customers").insert({
                        "customer_code":f"CUS-{i:04d}","name":name.strip(),
                        "phone":phone,"address":address}).execute()
                    st.success(f"Customer added: CUS-{i:04d}");st.rerun()
                except Exception as e:st.error(f"Customer error: {e}")

    summary=[]
    for c in customers:
        code=str(c.get("customer_code") or "")
        bal=0
        for x in sales:
            if str(x.get("customer_code") or "")==code:
                bal+=max(sale_total(x)-n(x.get("amount_received")),0)
        for x in payments:
            if str(x.get("customer_code") or "")==code:bal-=n(x.get("amount"))
        summary.append({"Customer ID":code,"Name":c.get("name"),"Phone":c.get("phone"),
                        "Address":c.get("address"),"Outstanding":max(bal,0)})
    st.dataframe(summary,use_container_width=True,hide_index=True)

    if customers:
        opts=[f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
        selected=st.selectbox("📒 Open Customer Khata",opts)
        code=selected.split(" — ",1)[0]
        customer=next(x for x in customers if str(x.get("customer_code"))==code)

        st.markdown(f"### 📒 {customer.get('name')} — {code}")
        start,end=date_range("Khata From Date → To Date",f"khata_range_{code}")

        ledger=[]
        for x in sales:
            if str(x.get("customer_code") or "")==code and in_range(x.get("sale_date"),start,end):
                ledger.append({"Date":x.get("sale_date"),"Type":"Sale",
                               "Description":f'{x.get("model")} × {q(x.get("quantity"))}',
                               "Debit":max(sale_total(x)-n(x.get("amount_received")),0),
                               "Credit":0})
        for x in payments:
            if str(x.get("customer_code") or "")==code and in_range(x.get("payment_date"),start,end):
                ledger.append({"Date":x.get("payment_date"),"Type":"Payment",
                               "Description":x.get("notes") or "Payment received",
                               "Debit":0,"Credit":n(x.get("amount"))})
        ledger.sort(key=lambda x:str(x["Date"] or ""))
        running=0
        for x in ledger:
            running+=x["Debit"]-x["Credit"];x["Balance"]=running

        c=st.columns(3)
        c[0].metric("PERIOD DEBIT",money(sum(x["Debit"] for x in ledger)))
        c[1].metric("PERIOD CREDIT",money(sum(x["Credit"] for x in ledger)))
        c[2].metric("PERIOD BALANCE",money(max(running,0)))
        st.dataframe(ledger,use_container_width=True,hide_index=True)

        st.markdown("### ✏️ Edit / Delete Customer")
        with st.form("edit_customer"):
            nn=st.text_input("Name",str(customer.get("name") or ""))
            np=st.text_input("Phone",str(customer.get("phone") or ""))
            na=st.text_input("Address",str(customer.get("address") or ""))
            u,dlt=st.columns(2)
            update=u.form_submit_button("Update Customer",use_container_width=True)
            delete=dlt.form_submit_button("Delete Customer",use_container_width=True)
            if update:
                try:
                    supabase.table("customers").update({"name":nn,"phone":np,"address":na}).eq("customer_code",code).execute()
                    st.success("Customer updated.");st.rerun()
                except Exception as e:st.error(f"Update error: {e}")
            if delete:
                try:
                    supabase.table("customers").delete().eq("customer_code",code).execute()
                    st.success("Customer deleted.");st.rerun()
                except Exception as e:st.error(f"Delete error: {e}")

# ===================== CUSTOMER PAYMENTS ==================
elif page=="💵 Customer Payments":
    st.title("💵 Customer Payment / Khata Jama")
    if customers:
        opts=[f'{x.get("customer_code","")} — {x.get("name","")}' for x in customers]
        with st.form("payment"):
            selected=st.selectbox("Customer",opts)
            code=selected.split(" — ",1)[0]
            d=st.date_input("Payment Date",date.today(),format="DD-MM-YYYY")
            amount=st.number_input("Payment Amount (PKR)",min_value=0.0,step=1000.0)
            notes=st.text_input("Notes")
            if st.form_submit_button("💾 Save Payment",use_container_width=True):
                if amount<=0:st.error("Enter payment amount.")
                else:
                    try:
                        supabase.table("customer_payments").insert({
                            "customer_code":code,"payment_date":str(d),
                            "amount":float(amount),"notes":notes}).execute()
                        st.success("Payment added to customer Khata.");st.rerun()
                    except Exception as e:st.error(f"Payment error: {e}")
    else: st.info("Add a customer first.")

    st.markdown("### 🔎 Payment History")
    start,end=date_range("Payment From Date → To Date","payment_history_range")
    data=[x for x in payments if in_range(x.get("payment_date"),start,end)]
    st.dataframe(data,use_container_width=True,hide_index=True)

# ========================= EXPENSES ======================
elif page=="💸 Expenses":
    st.title("💸 Expenses")
    with st.form("expense"):
        d=st.date_input("Date",date.today(),format="DD-MM-YYYY")
        category=st.selectbox("Category",["Rent","Electricity","Transport","Staff","Other"])
        desc=st.text_input("Description")
        amount=st.number_input("Amount (PKR)",min_value=0.0,step=500.0)
        if st.form_submit_button("💾 Save Expense",use_container_width=True):
            try:
                supabase.table("expenses").insert({
                    "expense_date":str(d),"category":category,
                    "description":desc,"amount":float(amount)}).execute()
                st.success("Expense saved.");st.rerun()
            except Exception as e:st.error(f"Expense error: {e}")

    start,end=date_range("Expense From Date → To Date","expense_history_range")
    data=[x for x in expenses if in_range(x.get("expense_date"),start,end)]
    st.metric("PERIOD EXPENSES",money(sum(n(x.get("amount")) for x in data)))
    st.dataframe(data,use_container_width=True,hide_index=True)

    if expenses:
        ids=[x.get("id") for x in expenses if x.get("id") is not None]
        if ids:
            st.markdown("### ✏️ Edit / Delete Expense")
            sid=st.selectbox("Select Expense ID",ids)
            row=next(x for x in expenses if x.get("id")==sid)
            with st.form("edit_expense"):
                nd=st.date_input("Date",date.fromisoformat(str(row.get("expense_date"))[:10]),format="DD-MM-YYYY")
                cats=["Rent","Electricity","Transport","Staff","Other"]
                old=str(row.get("category") or "Other")
                nc=st.selectbox("Category",cats,index=cats.index(old) if old in cats else 4)
                desc=st.text_input("Description",str(row.get("description") or ""))
                amt=st.number_input("Amount",min_value=0.0,value=n(row.get("amount")),step=500.0)
                u,dlt=st.columns(2)
                update=u.form_submit_button("Update Expense",use_container_width=True)
                delete=dlt.form_submit_button("Delete Expense",use_container_width=True)
                if update:
                    try:
                        supabase.table("expenses").update({
                            "expense_date":str(nd),"category":nc,"description":desc,
                            "amount":float(amt)}).eq("id",sid).execute()
                        st.success("Expense updated.");st.rerun()
                    except Exception as e:st.error(f"Update error: {e}")
                if delete:
                    try:
                        supabase.table("expenses").delete().eq("id",sid).execute()
                        st.success("Expense deleted.");st.rerun()
                    except Exception as e:st.error(f"Delete error: {e}")

# ============================ STOCK ======================
elif page=="📦 Stock":
    st.title("📦 Current Stock")
    st.dataframe(stock_data(purchases,sales),use_container_width=True,hide_index=True)

# ====================== DAILY REPORT ====================
elif page=="📅 Daily Report":
    st.title("📅 Date Range Report")
    start,end=date_range("Report From Date → To Date","daily_report_range")
    dp=[x for x in purchases if in_range(x.get("purchase_date"),start,end)]
    ds=[x for x in sales if in_range(x.get("sale_date"),start,end)]
    de=[x for x in expenses if in_range(x.get("expense_date"),start,end)]
    dpay=[x for x in payments if in_range(x.get("payment_date"),start,end)]
    c=st.columns(5)
    c[0].metric("PURCHASES",money(sum(purchase_total(x) for x in dp)))
    c[1].metric("SALES",money(sum(sale_total(x) for x in ds)))
    c[2].metric("EXPENSES",money(sum(n(x.get("amount")) for x in de)))
    c[3].metric("CUSTOMER PAYMENTS",money(sum(n(x.get("amount")) for x in dpay)))
    c[4].metric("BIKES SOLD",sum(q(x.get("quantity")) for x in ds))
    st.markdown("### 🛒 Purchases");st.dataframe(dp,use_container_width=True,hide_index=True)
    st.markdown("### 🧾 Sales");st.dataframe(ds,use_container_width=True,hide_index=True)
    st.markdown("### 💸 Expenses");st.dataframe(de,use_container_width=True,hide_index=True)
    st.markdown("### 💵 Customer Payments");st.dataframe(dpay,use_container_width=True,hide_index=True)

# ===================== MONTHLY REPORT ===================
else:
    st.title("📊 Monthly Report")
    selected=st.date_input("Select any date in month",date.today(),format="DD-MM-YYYY")
    key=selected.strftime("%Y-%m")
    mp=[x for x in purchases if str(x.get("purchase_date","")).startswith(key)]
    ms=[x for x in sales if str(x.get("sale_date","")).startswith(key)]
    me=[x for x in expenses if str(x.get("expense_date","")).startswith(key)]
    pay=[x for x in payments if str(x.get("payment_date","")).startswith(key)]
    c=st.columns(6)
    vals=[money(sum(purchase_total(x) for x in mp)),money(sum(sale_total(x) for x in ms)),
          sum(q(x.get("quantity")) for x in mp),sum(q(x.get("quantity")) for x in ms),
          money(sum(n(x.get("amount")) for x in me)),money(sum(n(x.get("amount")) for x in pay))]
    for col,label,val in zip(c,["Purchases","Sales","Bikes Purchased","Bikes Sold","Expenses","Customer Payments"],vals):
        col.metric(label,val)
    st.markdown("### Purchases");st.dataframe(mp,use_container_width=True,hide_index=True)
    st.markdown("### Sales");st.dataframe(ms,use_container_width=True,hide_index=True)
    st.markdown("### Expenses");st.dataframe(me,use_container_width=True,hide_index=True)
    st.markdown("### Customer Payments");st.dataframe(pay,use_container_width=True,hide_index=True)
