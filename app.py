import streamlit as st
from supabase import create_client

st.set_page_config(page_title="BALOCH HONDA MOTORS", page_icon="🏍️", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    supabase = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("BALOCH HONDA MOTORS")
    st.caption("Dera Murad Jamali — Business Management System")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            if supabase:
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
            else:
                st.error("Supabase connection is not configured.")
    st.caption("Initial test login: admin / demo123")
    st.stop()

st.sidebar.title("BALOCH HONDA MOTORS")
st.sidebar.caption("Dera Murad Jamali")
page = st.sidebar.radio("Menu", ["Dashboard","Purchases","Sales","Customers","Expenses","Stock","Monthly Report"])
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

def rows(table):
    return supabase.table(table).select("*").execute().data or []

def s(rows_, key):
    return sum(float(x.get(key) or 0) for x in rows_)

if page == "Dashboard":
    st.title("Dashboard")
    p, sales, e = rows("purchases"), rows("sales"), rows("expenses")
    purchase_total, sales_total, expenses_total = s(p,"total_amount"), s(sales,"total_sale"), s(e,"amount")
    purchased = sum(int(x.get("quantity") or 0) for x in p)
    sold = sum(int(x.get("quantity") or 0) for x in sales)
    stock = purchased - sold
    overdue = sum(max(float(x.get("balance") or 0),0) for x in sales)
    costs = {}
    for x in p:
        costs.setdefault(x["model"], [0,0])
        costs[x["model"]][0] += int(x["quantity"])
        costs[x["model"]][1] += int(x["quantity"]) * float(x["rate_per_bike"])
    gross = 0
    for x in sales:
        q = int(x["quantity"])
        c = costs.get(x["model"], [0,0])
        avg = c[1]/c[0] if c[0] else 0
        gross += float(x["total_sale"]) - q*avg
    net = gross-expenses_total
    a=st.columns(6)
    for c,label,val in zip(a,["TOTAL PURCHASE","TOTAL SALES","CURRENT STOCK","GROSS PROFIT","EXPENSES","NET PROFIT / LOSS"],
                           [f"PKR {purchase_total:,.0f}",f"PKR {sales_total:,.0f}",f"{stock:,} Bikes",
                            f"PKR {gross:,.0f}",f"PKR {expenses_total:,.0f}",f"PKR {net:,.0f}"]):
        c.metric(label,val)
    st.subheader("Recent Sales")
    st.dataframe(sales[-10:][::-1], use_container_width=True, hide_index=True)

elif page == "Purchases":
    st.title("Purchase Entry")
    with st.form("purchase"):
        date=st.date_input("Date"); dealer=st.text_input("Dealer / Supplier")
        model=st.selectbox("Bike Model",["CD 70","CG 125","CB 125F","CD 70 Dream","Pridor","Other"])
        q=st.number_input("Quantity",1,step=1); rate=st.number_input("Per Bike Purchase Rate (PKR)",0.0,step=1000.0)
        st.write(f"**Total Purchase: PKR {q*rate:,.0f}**")
        notes=st.text_input("Notes")
        if st.form_submit_button("Save Purchase",use_container_width=True):
            supabase.table("purchases").insert({"purchase_date":str(date),"dealer":dealer,"model":model,
                "quantity":int(q),"rate_per_bike":float(rate),"notes":notes}).execute()
            st.success("Purchase saved."); st.rerun()
    st.dataframe(rows("purchases"),use_container_width=True,hide_index=True)

elif page == "Sales":
    st.title("Sales Entry")
    customers=rows("customers"); names=["Walk-in"]+[x["name"] for x in customers]
    with st.form("sale"):
        date=st.date_input("Date"); customer=st.selectbox("Customer",names)
        model=st.selectbox("Bike Model",["CD 70","CG 125","CB 125F","CD 70 Dream","Pridor","Other"])
        q=st.number_input("Quantity",1,step=1); rate=st.number_input("Per Bike Sale Rate (PKR)",0.0,step=1000.0)
        received=st.number_input("Amount Received (PKR)",0.0,step=1000.0)
        st.write(f"**Total Sale: PKR {q*rate:,.0f}**")
        st.write(f"**Balance: PKR {max(q*rate-received,0):,.0f}**")
        notes=st.text_input("Notes")
        if st.form_submit_button("Save Sale",use_container_width=True):
            supabase.table("sales").insert({"sale_date":str(date),"customer_name":customer,"model":model,
                "quantity":int(q),"sale_rate_per_bike":float(rate),"amount_received":float(received),"notes":notes}).execute()
            st.success("Sale saved."); st.rerun()
    st.dataframe(rows("sales"),use_container_width=True,hide_index=True)

elif page == "Customers":
    st.title("Customers / Udhaar")
    with st.form("customer"):
        name=st.text_input("Customer Name"); phone=st.text_input("Phone"); address=st.text_input("Address")
        if st.form_submit_button("Add Customer",use_container_width=True) and name:
            supabase.table("customers").insert({"name":name,"phone":phone,"address":address}).execute()
            st.success("Customer added."); st.rerun()
    st.dataframe(rows("customers"),use_container_width=True,hide_index=True)

elif page == "Expenses":
    st.title("Expenses")
    with st.form("expense"):
        date=st.date_input("Date"); category=st.selectbox("Category",["Rent","Electricity","Transport","Staff","Other"])
        desc=st.text_input("Description"); amount=st.number_input("Amount (PKR)",0.0,step=500.0)
        if st.form_submit_button("Save Expense",use_container_width=True):
            supabase.table("expenses").insert({"expense_date":str(date),"category":category,"description":desc,"amount":float(amount)}).execute()
            st.success("Expense saved."); st.rerun()
    st.dataframe(rows("expenses"),use_container_width=True,hide_index=True)

elif page == "Stock":
    st.title("Current Stock")
    st.dataframe(supabase.table("stock_summary").select("*").execute().data or [],use_container_width=True,hide_index=True)

else:
    st.title("Monthly Report")
    month=st.date_input("Select any date in the month")
    key=month.strftime("%Y-%m")
    p=[x for x in rows("purchases") if str(x.get("purchase_date","")).startswith(key)]
    sales=[x for x in rows("sales") if str(x.get("sale_date","")).startswith(key)]
    e=[x for x in rows("expenses") if str(x.get("expense_date","")).startswith(key)]
    c=st.columns(5)
    for col,label,val in zip(c,["Purchases","Sales","Bikes Purchased","Bikes Sold","Expenses"],
                             [f"PKR {s(p,'total_amount'):,.0f}",f"PKR {s(sales,'total_sale'):,.0f}",
                              sum(int(x.get('quantity') or 0) for x in p),sum(int(x.get('quantity') or 0) for x in sales),
                              f"PKR {s(e,'amount'):,.0f}"]):
        col.metric(label,val)
