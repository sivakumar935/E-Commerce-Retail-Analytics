# Cart2Insights — Decoding E-Commerce Performance

> An end-to-end e-commerce analytics solution built with **Python, Pandas, SQL, MySQL, Statistics, and Streamlit** to transform multi-table transactional data into validated business insights and actionable recommendations.


---

## Overview

Cart2Insights analyzes a relational e-commerce dataset covering **orders, customers, products, sellers, payments, reviews, delivery, categories, and geography**.

The project follows an end-to-end analytics workflow:

```text
Raw CSV Data
     ↓
Data Understanding
     ↓
Data Quality Analysis
     ↓
Data Cleaning & Validation
     ↓
MySQL Database Analysis
     ↓
Feature Engineering
     ↓
EDA + Statistical Analysis
     ↓
Interactive Streamlit Dashboard
     ↓
Business Insights & Recommendations
```

The goal is not simply to create charts. The project is designed to answer business questions, validate analytical assumptions, prevent relational-data errors, and translate findings into decisions.

---

## Business Objectives

The analysis focuses on six major business areas:

1. **Business Performance** — revenue, orders, customers, sellers, AOV, and satisfaction.
2. **Sales Analysis** — revenue trends, category performance, products, and geography.
3. **Customer Analysis** — customer frequency, spending, repeat behavior, and high-value customers.
4. **Seller & Product Performance** — seller revenue, order volume, ratings, and product performance.
5. **Delivery & Operations** — delivery duration, delays, geographic variation, and customer impact.
6. **Customer Experience** — review distribution, category satisfaction, and delivery-related satisfaction.

---
## Dataset Structure

The project contains **9 related tables**:

| Table | Grain | Key / Relationship |
|---|---|---|
| `customers` | One row per customer record | `customer_id` |
| `orders` | One row per order | `order_id` |
| `order_items` | One row per order item | `(order_id, order_item_id)` |
| `order_payments` | One row per payment record | `(order_id, payment_sequential)` |
| `order_reviews` | One row per review record | `(review_id, order_id)` |
| `products` | One row per product | `product_id` |
| `sellers` | One row per seller | `seller_id` |
| `geolocation` | Multiple rows per ZIP prefix | No source-aligned unique ZIP key |
| `product_category_name_translation` | One row per translated category | `product_category_name` |

## Data Quality & Cleaning

The project uses a **find → understand → decide → transform → validate** approach rather than automatically dropping or correcting unusual records.

### Key data-quality findings

- `customers`: no missing values or exact duplicates; `customer_id` unique.
- `orders`: lifecycle missingness was contextual; **166 carrier-before-purchase** and **23 delivery-before-carrier** anomalies were retained because they could not be reliably reconstructed.
- `order_items`: no missing values or exact duplicates; **383 zero-freight records** were retained as potentially legitimate.
- `order_payments`: retained **2 zero-installment records** and **9 zero-payment records** because intended values could not be reconstructed reliably.
- `order_reviews`: `review_id` is not unique; `(review_id, order_id)` is unique. Review text is optional and missing text was preserved.
- `products`: **610 products** have missing category/descriptive attributes; missing values were retained because reliable reconstruction was not possible.
- `sellers`: **19 seller records** were corrected after ambiguous ZIP/state mappings were validated against geolocation evidence.
- `geolocation`: **261,831 exact duplicate rows** were removed, reducing the table from **1,000,163 to 738,332 rows**. Repeated ZIP prefixes were preserved because they are structural to the source grain.

### Final cleaned-data validation

After cleaning, the tested relational links showed no invalid references for the enforced relationships, and primary/composite-key checks passed.

---

## SQL Database

The project uses **MySQL 8.0.46** as the analytical database.


### Database loading design

```text
cleaned CSVs
     ↓
load the data 
     ↓
cart2insights
```

### Loaded row counts

| Table | Rows |
|---|---:|
| `customers` | 99,441 |
| `product_category_translation` | 71 |
| `orders` | 99,441 |
| `products` | 32,951 |
| `sellers` | 3,095 |
| `order_items` | 112,650 |
| `order_payments` | 103,886 |
| `order_reviews` | 99,224 |
| `geolocation` | 738,332 |

All recorded row-count validations passed, and the tested enforced foreign-key relationships returned **0 invalid references**.

---

## Feature Engineering

The project implements the **9 officially required analytical features**.

| Feature | Definition / Grain |
|---|---|
| `total_order_value` | `price + freight_value`, aggregated to order grain |
| `delivery_days` | customer delivery timestamp − purchase timestamp |
| `delivery_delay` | actual delivery timestamp − estimated delivery timestamp |
| `customer_order_count` | distinct orders per `customer_unique_id` |
| `customer_total_spending` | sum of order values per customer identity |
| `customer_average_order_value` | customer spending ÷ customer order count |
| `seller_revenue` | sum of `order_items.price` per seller |
| `seller_order_count` | distinct orders per seller |
| `repeat_customer` | customer order count > 1 |

### Feature datasets

```text
 data/features/
 ├── order_features.csv
 ├── customer_features.csv
 └── seller_features.csv
```

### Validated feature results

- **99,441** order records represented.
- **96,096** analytical customer identities.
- **93,099** one-time customers.
- **2,997** repeat customers.
- Maximum observed orders for a customer identity: **17**.
- Customer total spending reconciles to **R$15,843,553.24**.
- Seller revenue reconciles exactly to **R$13,591,643.70** in item-level product sales.

---

## Exploratory Data Analysis

EDA was designed around business questions rather than chart-first exploration.

### Analytical framework

Every major analysis follows:

> **Business Question → Analytical Question → Required Data → Grain → Transformation → Analysis → Visualization → Observation → Interpretation → Business Impact → Recommendation**

### EDA coverage

The analysis covers:

- Univariate analysis
- Bivariate analysis
- Multivariate analysis
- Trend analysis
- Distribution analysis
- Correlation analysis

### Major findings

#### Sales

- Revenue and order volume increased strongly from 2017 into 2018.
- Revenue growth appears primarily **volume-driven**, while AOV remained comparatively stable.
- **Health & Beauty** was the highest-revenue category in the category analysis.
- Sales are geographically concentrated, with **São Paulo (SP)** as the dominant state by revenue.
- September and October 2018 are partial periods and were excluded from mature-period trend interpretation.

#### Customers

- One-time customers dominate the customer base.
- Repeat customers are a much smaller segment.
- Customer spending is strongly right-skewed.
- Repeat customers have higher typical cumulative spending.
- Customer order count and total spending show a **weak positive linear correlation (r = 0.122)**.

#### Sellers

- Seller revenue is unevenly distributed.
- A small high-value seller group exists alongside a long tail of smaller sellers.
- Seller order volume is positively associated with seller revenue.

#### Delivery

- Delivery duration is right-skewed.
- Most orders with known delivery outcomes are on time.
- Delivery performance varies across states.
- Delayed orders receive substantially lower review scores than on-time orders.

#### Customer Experience

- Review scores are concentrated toward **5 stars**.
- A meaningful low-rating segment remains.
- Delivery reliability shows a stronger visible relationship with satisfaction than absolute delivery duration alone.

#### Payments

- **Credit card** is the dominant payment method.
- Payment-method/order-status patterns indicate an association, but sparse cells limit the reliability of the standard chi-square approximation.

---

## Statistical Analysis

Three statistical tests were required by the project brief and were completed with hypotheses, test selection, assumptions, results, decisions, and business interpretation.

### 1. Independent Two-Sample T-Test

**Business question:** Do delayed orders receive lower review scores than on-time orders?

| Metric | On Time | Delayed |
|---|---:|---:|
| Sample size | 88,168 | 7,662 |
| Mean review score | 4.294 | 2.567 |

- Mean difference: **1.727 points**
- Welch t-statistic: **89.5508**
- Decision: **Reject H0**
- Interpretation: delayed orders are associated with substantially lower review scores.

**Limitation:** this is observational evidence and does not establish causation.

### 2. One-Way ANOVA

**Business question:** Does order value differ across product categories?

- F-statistic: **206.9425**
- Decision: **Reject H0**
- Interpretation: there is statistically significant evidence that mean order value differs across categories.

A Tukey post-hoc analysis was not added because it was not required by the brief and the project prioritized the core deliverables within the submission deadline.

**Limitation:** category/order-value distributions are right-skewed, and an order containing multiple categories can contribute multiple order-category observations.

### 3. Chi-Square Test of Independence

**Business question:** Is primary payment method associated with order status?

- Chi-square statistic: **677.0831**
- Degrees of freedom: **28**
- Decision: **Reject H0**
- Report p-value as **p < 0.05** rather than literal p = 0.
- Interpretation: the first/official run indicates a statistically significant association between primary payment method and order status.

**Important limitation:** the minimum expected cell frequency was approximately **0.00006**, indicating severe sparsity. The standard chi-square approximation should therefore be interpreted cautiously. The result must not be presented as evidence that payment method causes cancellations or other outcomes.

---

## Streamlit Dashboard

The dashboard is connected directly to MySQL through SQLAlchemy.

### Dashboard sections

```text
Cart2Insights
│
├── Business Overview
│   ├── Total Revenue
│   ├── Total Orders
│   ├── Average Order Value
│   ├── Customers
│   ├── Sellers
│   ├── Average Review Score
│   ├── Revenue Trend
│   └── Revenue by Category
│
├── Sales
│   ├── Monthly Revenue
│   ├── Revenue by Category
│   ├── Sales by State
│   └── Top Products
│
├── Customers
│   ├── Customer Order Distribution
│   ├── One-time vs Repeat
│   ├── Customer Spending
│   └── Top Customers
│
├── Sellers & Products
│   ├── Top Sellers
│   ├── Seller Revenue vs Order Volume
│   └── Seller Ratings
│
├── Delivery
│   ├── Delivery KPIs
│   ├── On-time vs Delayed
│   ├── Delivery by State
│   └── Delivery Status vs Review Score
│
└── Customer Experience
    ├── Review Distribution
    ├── Reviews by Category
    ├── Delivery Status vs Satisfaction
    └── Delivery Duration vs Review Score
```

---

## Project Structure

```text
Cart2Insights/
│
├── data/
│   ├── raw/                         # local raw datasets
│   ├── cleaned/                     # cleaned CSVs
│   └── features/                    # derived analytical datasets
│
├── notebooks/
│   ├── 1.data_understanding.ipynb
│   ├── 2.data_quality_analysis.ipynb
│   ├── 3.data_cleaning.ipynb
│   ├── 4.sql_analysis.ipynb
│   ├── 5.feature_engineering.ipynb
│   ├── 6.eda.ipynb
│   └── 7.statistical_analysis.ipynb
│
├── streamlit/
│   ├── app.py                        # dashboard application
│   ├── queries.py                    # SQL query layer
│   ├── database.py                   # database connection
│   └── requirements.txt
│
├── README.md
```

---

## SQL Analysis Coverage

The project intentionally demonstrates the SQL concepts required by the brief:

- `SELECT`
- `WHERE`
- `ORDER BY`
- `GROUP BY`
- `HAVING`
- `JOIN`
- Subqueries
- CTEs
- Window functions
- Aggregations

---

## Key Business Insights

### 1. Growth is largely volume-driven

Revenue and order volume increased strongly through the main 2017–2018 period, while AOV stayed comparatively stable.

**Business implication:** continued growth depends heavily on sustaining order volume while protecting order economics.

### 2. Customer retention is a major opportunity

The customer base is dominated by one-time buyers, while repeat customers are a small segment with higher typical cumulative spending.

**Business implication:** post-purchase engagement, loyalty, and targeted retention strategies could create incremental customer lifetime value.

### 3. Sales are concentrated

Health & Beauty is the top revenue category, and São Paulo is the leading state by revenue.

**Business implication:** high-performing categories and geographies are important growth anchors, while under-penetrated areas can be assessed for expansion opportunities.

### 4. Delivery reliability matters to satisfaction

Delayed orders have a substantially lower average review score than on-time orders, with a mean difference of **1.727 review points** in the required t-test.

**Business implication:** delivery reliability should be treated as both an operational metric and a customer-experience metric.

### 5. Seller performance is uneven

A small group of sellers generates a disproportionate share of seller revenue while a long tail contributes at lower volumes.

**Business implication:** seller-management efforts can prioritize high-value partners while identifying scalable smaller sellers.

---