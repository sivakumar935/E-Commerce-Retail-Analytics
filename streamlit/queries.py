import pandas as pd


def read_sql(conn, query, params=None):
    return pd.read_sql(query, conn, params=params)


def filters(alias="o"):
    return f"""WHERE {alias}.order_purchase_timestamp >= %s
      AND {alias}.order_purchase_timestamp < DATE_ADD(%s, INTERVAL 1 DAY)"""


def filter_params(start_date, end_date):
    return [start_date, end_date]


def get_overview(conn, start_date, end_date):
    q = f"""
    SELECT
      (SELECT COALESCE(SUM(p.payment_value),0)
       FROM orders o JOIN order_payments p ON o.order_id=p.order_id
       {filters()}) AS total_revenue,
      (SELECT COUNT(DISTINCT o.order_id) FROM orders o {filters()}) AS total_orders,
      (SELECT COUNT(DISTINCT c.customer_unique_id)
       FROM orders o JOIN customers c ON o.customer_id=c.customer_id {filters()}) AS total_customers,
      (SELECT COUNT(DISTINCT oi.seller_id)
       FROM orders o JOIN order_items oi ON o.order_id=oi.order_id {filters()}) AS total_sellers,
      (SELECT AVG(order_total) FROM (
          SELECT o.order_id, SUM(p.payment_value) order_total
          FROM orders o JOIN order_payments p ON o.order_id=p.order_id
          {filters()} GROUP BY o.order_id
      ) x) AS average_order_value,
      (SELECT AVG(r.review_score)
       FROM orders o JOIN order_reviews r ON o.order_id=r.order_id {filters()}) AS average_review_score
    """
    params = filter_params(start_date,end_date)*6
    return read_sql(conn,q,params).iloc[0].to_dict()


def get_monthly_revenue(conn,start_date,end_date):
    q=f"""SELECT DATE_FORMAT(o.order_purchase_timestamp,'%Y-%m-01') month,
    SUM(p.payment_value) revenue
    FROM orders o JOIN order_payments p ON o.order_id=p.order_id
    {filters()} GROUP BY month ORDER BY month"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_category_revenue(conn,start_date,end_date):
    q=f"""SELECT COALESCE(t.product_category_name_english,'Unknown') category,
    SUM(oi.price+oi.freight_value) revenue
    FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
    JOIN products p ON oi.product_id=p.product_id
    LEFT JOIN product_category_translation t ON p.product_category_name=t.product_category_name
    {filters()} GROUP BY category ORDER BY revenue DESC"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_top_products(conn,start_date,end_date):
    q=f"""SELECT oi.product_id, COALESCE(t.product_category_name_english,'Unknown') category,
    COUNT(*) units_sold, SUM(oi.price) revenue
    FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
    JOIN products p ON oi.product_id=p.product_id
    LEFT JOIN product_category_translation t ON p.product_category_name=t.product_category_name
    {filters()} GROUP BY oi.product_id,category ORDER BY units_sold DESC LIMIT 10"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_sales_location(conn,start_date,end_date):
    q=f"""SELECT c.customer_state state, SUM(p.payment_value) revenue
    FROM orders o JOIN customers c ON o.customer_id=c.customer_id
    JOIN order_payments p ON o.order_id=p.order_id
    {filters()} GROUP BY c.customer_state ORDER BY revenue DESC"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_customer_distribution(conn,start_date,end_date):
    q=f"""SELECT order_count, COUNT(*) customers FROM (
      SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) order_count
      FROM customers c JOIN orders o ON c.customer_id=o.customer_id
      {filters()} GROUP BY c.customer_unique_id
    ) x GROUP BY order_count ORDER BY order_count"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_customer_spending(conn,start_date,end_date):
    q=f"""SELECT c.customer_unique_id, SUM(p.payment_value) spending
    FROM customers c JOIN orders o ON c.customer_id=o.customer_id
    JOIN order_payments p ON o.order_id=p.order_id
    {filters()} GROUP BY c.customer_unique_id ORDER BY spending DESC LIMIT 10"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_repeat_customers(conn,start_date,end_date):
    q=f"""SELECT CASE WHEN order_count>1 THEN 'Repeat Customer' ELSE 'One-time Customer' END customer_type,
    COUNT(*) customers FROM (
      SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) order_count
      FROM customers c JOIN orders o ON c.customer_id=o.customer_id
      {filters()} GROUP BY c.customer_unique_id
    ) x GROUP BY customer_type"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_top_sellers(conn,start_date,end_date):
    q=f"""SELECT oi.seller_id, COUNT(DISTINCT oi.order_id) orders,
    SUM(oi.price) revenue FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
    {filters()} GROUP BY oi.seller_id ORDER BY revenue DESC LIMIT 10"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_seller_ratings(conn,start_date,end_date):
    q=f"""SELECT oi.seller_id, ROUND(AVG(r.review_score),2) avg_rating,
    COUNT(r.review_id) reviews FROM orders o
    JOIN order_items oi ON o.order_id=oi.order_id
    JOIN order_reviews r ON o.order_id=r.order_id
    {filters()} GROUP BY oi.seller_id HAVING COUNT(r.review_id)>=5
    ORDER BY avg_rating DESC LIMIT 10"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_category_performance(conn,start_date,end_date):
    q=f"""WITH category_sales AS (
      SELECT COALESCE(t.product_category_name_english,'Unknown') category,
      COUNT(DISTINCT oi.order_id) orders, COUNT(*) units_sold,
      SUM(oi.price+oi.freight_value) revenue
      FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
      JOIN products p ON oi.product_id=p.product_id
      LEFT JOIN product_category_translation t ON p.product_category_name=t.product_category_name
      {filters()} GROUP BY category)
    SELECT * FROM category_sales WHERE units_sold>0 ORDER BY revenue DESC"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_delivery_summary(conn, start_date, end_date):
    q = """
    WITH d AS (
        SELECT
            DATEDIFF(
                order_delivered_customer_date,
                order_purchase_timestamp
            ) AS delivery_days,

            DATEDIFF(
                order_delivered_customer_date,
                order_estimated_delivery_date
            ) AS delay

        FROM orders o

        WHERE o.order_purchase_timestamp >= %s
          AND o.order_purchase_timestamp < DATE_ADD(%s, INTERVAL 1 DAY)
          AND order_delivered_customer_date IS NOT NULL
    )

    SELECT
        AVG(delivery_days) AS avg_days,

        SUM(
            CASE
                WHEN delay <= 0 THEN 1
                ELSE 0
            END
        ) AS on_time,

        SUM(
            CASE
                WHEN delay > 0 THEN 1
                ELSE 0
            END
        ) AS delayed_orders

    FROM d
    """

    return read_sql(
        conn,
        q,
        filter_params(start_date, end_date)
    ).iloc[0].to_dict()


def get_delivery_status(conn,start_date,end_date):
    q=f"""SELECT CASE WHEN o.order_delivered_customer_date IS NULL THEN 'Not Delivered'
      WHEN o.order_delivered_customer_date<=o.order_estimated_delivery_date THEN 'On Time'
      ELSE 'Delayed' END delivery_status, COUNT(*) orders
      FROM orders o {filters()} GROUP BY delivery_status"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_delivery_location(conn,start_date,end_date):
    q=f"""SELECT c.customer_state state,
      AVG(DATEDIFF(o.order_delivered_customer_date,o.order_purchase_timestamp)) avg_delivery_days,
      AVG(DATEDIFF(o.order_delivered_customer_date,o.order_estimated_delivery_date)) avg_delay_days
      FROM orders o JOIN customers c ON o.customer_id=c.customer_id
      {filters()} AND o.order_delivered_customer_date IS NOT NULL
      GROUP BY c.customer_state ORDER BY avg_delay_days DESC"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_delay_review(conn,start_date,end_date):
    q=f"""SELECT CASE WHEN o.order_delivered_customer_date<=o.order_estimated_delivery_date
      THEN 'On Time' ELSE 'Delayed' END delivery_status,
      r.review_score, COUNT(*) reviews
      FROM orders o JOIN order_reviews r ON o.order_id=r.order_id
      {filters()} AND o.order_delivered_customer_date IS NOT NULL
      GROUP BY delivery_status,r.review_score ORDER BY delivery_status,r.review_score"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_review_distribution(conn,start_date,end_date):
    q=f"""SELECT r.review_score, COUNT(*) review_count
      FROM orders o JOIN order_reviews r ON o.order_id=r.order_id
      {filters()} GROUP BY r.review_score ORDER BY r.review_score"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_reviews_category(conn,start_date,end_date):
    q=f"""SELECT COALESCE(t.product_category_name_english,'Unknown') category,
      COUNT(r.review_id) reviews, AVG(r.review_score) avg_rating
      FROM orders o JOIN order_reviews r ON o.order_id=r.order_id
      JOIN order_items oi ON o.order_id=oi.order_id
      JOIN products p ON oi.product_id=p.product_id
      LEFT JOIN product_category_translation t ON p.product_category_name=t.product_category_name
      {filters()} GROUP BY category ORDER BY avg_rating DESC LIMIT 15"""
    return read_sql(conn,q,filter_params(start_date,end_date))


def get_payment_type(conn,start_date,end_date):
    q=f"""SELECT p.payment_type, SUM(p.payment_value) revenue
      FROM orders o JOIN order_payments p ON o.order_id=p.order_id
      {filters()} GROUP BY p.payment_type ORDER BY revenue DESC"""
    return read_sql(conn,q,filter_params(start_date,end_date))
