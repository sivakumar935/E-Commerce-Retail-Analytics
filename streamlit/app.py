import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
import queries as q

st.set_page_config(page_title="Cart2Insights Dashboard", page_icon="🛒", layout="wide")

st.title("🛒 Cart2Insights")
st.caption("Interactive Olist E-commerce Business Dashboard")

try:
    conn = get_connection()
except Exception as e:
    st.error("MySQL connection failed.")
    st.code(str(e))
    st.info("Set MYSQL_PASSWORD and MYSQL_DATABASE, or update database.py.")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")
start = st.sidebar.date_input("Start date", pd.Timestamp("2016-09-01").date())
end = st.sidebar.date_input("End date", pd.Timestamp("2018-10-01").date())
if start > end:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

page = st.sidebar.radio("Go to", [
    "Business Overview", "Sales Analysis", "Customer Analysis",
    "Seller & Product Analysis", "Delivery Analysis", "Customer Experience"
])

# ---------- 1 ----------
if page == "Business Overview":
    st.header("1. Business Overview")

    x = q.get_overview(conn, start, end)

    st.metric("Total Revenue", f"R$ {x['total_revenue']:,.2f}")
    st.metric("Total Orders", f"{int(x['total_orders']):,}")
    st.metric("Customers", f"{int(x['total_customers']):,}")
    st.metric("Sellers", f"{int(x['total_sellers']):,}")
    st.metric("Average Order Value", f"R$ {x['average_order_value']:,.2f}")
    st.metric("Average Review Score", f"{x['average_review_score']:.2f}/5")

    monthly = q.get_monthly_revenue(conn, start, end)

    fig = px.line(
        monthly,
        x="month",
        y="revenue",
        markers=True,
        title="Revenue Trend"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------- 2 ----------
elif page == "Sales Analysis":
    st.header("2. Sales Analysis")
    monthly=q.get_monthly_revenue(conn,start,end)
    fig=px.line(monthly,x="month",y="revenue",markers=True,title="Monthly Revenue Trend")
    st.plotly_chart(fig,use_container_width=True)

    c1,c2=st.columns(2)
    cat=q.get_category_revenue(conn,start,end).head(10)
    c1.plotly_chart(px.bar(cat,x="revenue",y="category",orientation="h",title="Top 10 Categories by Revenue"),use_container_width=True)
    loc=q.get_sales_location(conn,start,end)
    c2.plotly_chart(px.bar(loc,x="state",y="revenue",title="Revenue by Customer State"),use_container_width=True)

    products=q.get_top_products(conn,start,end)
    st.plotly_chart(px.bar(products.sort_values("units_sold"),x="units_sold",y="product_id",orientation="h",hover_data=["category","revenue"],title="Top-Selling Products"),use_container_width=True)

# ---------- 3 ----------
elif page == "Customer Analysis":
    st.header("3. Customer Analysis")
    c1,c2=st.columns(2)
    dist=q.get_customer_distribution(conn,start,end)
    c1.plotly_chart(px.bar(dist,x="order_count",y="customers",title="Customer Distribution by Order Count"),use_container_width=True)
    repeat=q.get_repeat_customers(conn,start,end)
    c2.plotly_chart(px.pie(repeat,names="customer_type",values="customers",hole=.45,title="Repeat vs One-time Customers"),use_container_width=True)

    spend=q.get_customer_spending(conn,start,end)
    st.plotly_chart(px.bar(spend.sort_values("spending"),x="spending",y="customer_unique_id",orientation="h",title="Top Customers by Spending"),use_container_width=True)

# ---------- 4 ----------
elif page == "Seller & Product Analysis":
    st.header("4. Seller & Product Analysis")
    c1,c2=st.columns(2)
    sellers=q.get_top_sellers(conn,start,end)
    c1.plotly_chart(px.bar(sellers.sort_values("revenue"),x="revenue",y="seller_id",orientation="h",title="Top Sellers by Revenue"),use_container_width=True)
    ratings=q.get_seller_ratings(conn,start,end)
    c2.plotly_chart(px.bar(ratings.sort_values("avg_rating"),x="avg_rating",y="seller_id",orientation="h",title="Top Seller Ratings (5+ Reviews)"),use_container_width=True)

    perf=q.get_category_performance(conn,start,end).head(15)
    st.plotly_chart(px.bar(perf,x="category",y="revenue",hover_data=["orders","units_sold"],title="Product Category Performance"),use_container_width=True)

# ---------- 5 ----------
elif page == "Delivery Analysis":
    st.header("5. Delivery Analysis")
    x=q.get_delivery_summary(conn,start,end)
    a,b,c=st.columns(3)
    a.metric("Average Delivery Time",f"{x['avg_days']:.1f} days")
    b.metric("On-time Orders",f"{int(x['on_time']):,}")
    c.metric("Delayed Orders", int(x["delayed_orders"]))

    c1,c2=st.columns(2)
    status=q.get_delivery_status(conn,start,end)
    c1.plotly_chart(px.pie(status,names="delivery_status",values="orders",hole=.45,title="On-time vs Delayed Orders"),use_container_width=True)
    loc=q.get_delivery_location(conn,start,end).head(15)
    c2.plotly_chart(px.bar(loc.sort_values("avg_delay_days"),x="avg_delay_days",y="state",orientation="h",title="Delivery Delay by State"),use_container_width=True)

    dr=q.get_delay_review(conn,start,end)
    fig=px.bar(dr,x="review_score",y="reviews",color="delivery_status",barmode="group",title="Delivery Status vs Review Score")
    st.plotly_chart(fig,use_container_width=True)

# ---------- 6 ----------
else:
    st.header("6. Customer Experience")
    c1,c2=st.columns(2)
    reviews=q.get_review_distribution(conn,start,end)
    c1.plotly_chart(px.bar(reviews,x="review_score",y="review_count",title="Review Score Distribution"),use_container_width=True)
    cats=q.get_reviews_category(conn,start,end)
    c2.plotly_chart(px.bar(cats.sort_values("avg_rating"),x="avg_rating",y="category",orientation="h",title="Average Rating by Category"),use_container_width=True)

    st.subheader("Rating vs Delivery Performance")
    dr=q.get_delay_review(conn,start,end)
    pivot=dr.pivot(index="delivery_status",columns="review_score",values="reviews").fillna(0).reset_index()
    long=dr.copy()
    st.plotly_chart(px.bar(long,x="review_score",y="reviews",color="delivery_status",barmode="group",title="Rating vs Delivery Status"),use_container_width=True)

    pay=q.get_payment_type(conn,start,end)
    st.plotly_chart(px.pie(pay,names="payment_type",values="revenue",hole=.45,title="Revenue by Payment Type"),use_container_width=True)

