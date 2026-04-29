# Nexus AI
### Omnichannel Customer Intelligence Platform

Nexus AI is a customer analytics agent that connects your web, in-store, and app data into a single customer view. It scores every customer on recency, frequency, and spend, then segments them into lifecycle tiers and generates AI-powered action playbooks for each group. Upload your CSVs, run the analysis, download your results.

---

## Table of Contents

1. [What is Nexus AI](#1-what-is-nexus-ai)
2. [The Problem it Solves](#2-the-problem-it-solves)
3. [How it Works](#3-how-it-works)
4. [The Analytics it Does](#4-the-analytics-it-does)
5. [Input Files](#5-input-files)
6. [Output Files](#6-output-files)
7. [How Companies Can Use It](#7-how-companies-can-use-it)
8. [Project Structure](#8-project-structure)
9. [Setup and Installation](#9-setup-and-installation)
10. [Running the App](#10-running-the-app)
11. [API Cost](#11-api-cost)

---

## 1. What is Nexus AI

Nexus AI is an omnichannel customer analytics agent built for retail, D2C, and multi-channel brands. It takes raw CSV exports from your sales channels, unifies them into a single customer database, computes RFM and lifetime value scores for every customer, assigns each customer to a lifecycle segment, and generates AI-powered strategic playbooks for each segment using the Claude API.

It replaces days of manual data work with a two-minute automated pipeline. A marketing manager, CRM analyst, or growth lead can use it without any technical background. You do not need a data team, a BI tool, or a database to use Nexus AI. You just need your CSV exports and a browser.

The agent is built with Python, Streamlit, pandas, and the Anthropic Claude API. Every calculation is deterministic and transparent. The AI layer handles the strategic language, not the math.

---

## 2. The Problem it Solves

Most brands that sell across multiple channels have the same core problem. Their customer data is fragmented across systems that were never designed to talk to each other.

Web orders live in Shopify, WooCommerce, or a custom checkout. In-store transactions live in a POS system like Square, Lightspeed, or Revel. App activity lives in Firebase, Amplitude, or Mixpanel. Each system uses a different customer ID format. None of them share data with the others.

The result is that when a marketing team wants to understand their customers, they are working with an incomplete picture. A customer who bought online four times, visited a store twice, and browsed the app twenty times looks like four completely different people depending on which system you look at. Their true lifetime value is invisible. Their real purchase frequency is unknown. And any segmentation built on a single channel is wrong by definition.

The manual workaround is for a data analyst to export three spreadsheets, spend hours trying to match customers across systems using email or phone as a bridge, build RFM scores by hand in Excel, write segment strategies from scratch, and then repeat the entire process every month when the data changes. This approach is slow, error-prone, and does not scale.

Nexus AI automates this entire workflow. It resolves customer identities across all three channels automatically, builds the unified customer profile, runs all the scoring math, and uses AI to produce the strategic layer on top of the data.

---

## 3. How it Works

The pipeline runs in seven sequential steps every time you click Run analysis.

### Step 1: File Upload and Channel Detection

You upload one, two, or all three CSV files through a single multi-file uploader. The app reads each file and examines the column names to determine what type of data it contains. A file with an `order_total` column is classified as a web orders export. A file with a `loyalty_id` or `store_location` column is classified as an in-store transactions export. A file with an `event_type` or `app_user_id` column is classified as an app events export. No manual labelling is required from the user. The detection is automatic.

The app then validates each file, checks for missing required columns, and surfaces any data quality warnings before the pipeline runs.

### Step 2: Identity Resolution

Each file uses a different primary key. Web orders use `customer_id`. In-store transactions use `loyalty_id`. App events use `app_user_id`. These IDs are completely different across systems.

The identity resolution engine reads all three files and normalizes every ID into a common format by pairing each raw ID with the customer email address that appeared next to it in that file. It then builds a lookup table where every raw ID maps to a unified `customer_id` which is the email address. From this point forward the pipeline works exclusively off email as the single customer identifier.

This means a customer who appears as `CID-1212` in your web store, as `LYL-9834` in your POS system, and as `APP-7721` in your mobile app is correctly identified as the same person and merged into a single profile.

### Step 3: Customer 360 Aggregation

The aggregation engine groups all transactions and events by unified `customer_id` and computes a complete profile for each customer. This includes total orders, total spend, average order value, channels used, last purchase date across all channels, number of app sessions, favourite store location, and favourite product category.

The result is one row per customer with their full cross-channel history. This is the Customer 360 profile.

### Step 4: RFM Scoring

The RFM engine computes three raw values for each customer and ranks them against the full customer base using quintile scoring.

Recency is the number of days since their last purchase. Lower days means higher score because a customer who bought yesterday is more valuable than one who bought a year ago. The scoring is inverted so recent buyers receive a score of 5 and long-inactive buyers receive a score of 1.

Frequency is the total number of orders the customer has placed across all channels. Higher frequency earns a higher score.

Monetary is the total spend across all channels. Higher spend earns a higher score.

Each dimension is scored from 1 to 5 using pandas `qcut`, which splits the customer base into five equal groups based on the actual data distribution. The scores are therefore relative to your own customer base, not to an external benchmark.

The three scores are combined into an RFM composite ranging from 3 to 15. A customer with a composite of 15 is the best possible customer on all three dimensions. A customer with a composite of 3 is the weakest.

The RFM score string is formatted as `R5_F5_M5` to avoid Excel auto-formatting issues that occur when dashes are used as separators.

### Step 5: Lifecycle Segment Assignment

Based on their RFM scores, every customer is classified into one of six lifecycle tiers using a priority-ordered set of rules.

| Segment | What it means |
|---|---|
| Champions | Bought recently, buy often, spend a lot. Your best customers. |
| Loyal | Buy regularly and spend well but slightly less active than Champions. |
| Promising | Bought recently but only one or two orders. High potential, not yet proven. |
| At-Risk | Used to buy frequently and spend well but have gone quiet recently. |
| Lapsed | Bought multiple times historically but have not been seen in a very long time. |
| New | Placed just one order recently and are in the early relationship phase. |
| Other | Customers who do not clearly fit any of the tiers above. |

Rules are evaluated in priority order and the first match wins. A customer only lands in one segment.

### Step 6: LTV Scoring

Two lifetime value numbers are computed for every customer.

Historical LTV is the direct sum of all recorded spend across all uploaded channels. This is a factual number with no assumptions.

Projected LTV is a forward-looking estimate of what the customer is likely to spend in the future. The formula is:

```
Projected LTV = AOV x purchase_frequency_per_year x lifespan_years
```

Where AOV is their average order value, purchase frequency per year is their total orders divided by two (because the dataset covers approximately two years), and lifespan years is the expected number of additional years a customer in their segment will remain active.

The lifespan assumption varies by segment and reflects typical retention patterns:

| Segment | Default lifespan |
|---|---|
| Champions | 4.0 years |
| Loyal | 3.0 years |
| New | 2.5 years |
| Promising | 2.0 years |
| At-Risk | 1.5 years |
| Other | 1.0 years |
| Lapsed | 0.5 years |

These defaults can be changed by the user in the Advanced settings panel before running the analysis without touching any code.

Every customer also receives an LTV score percentile from 0 to 100 showing where they rank within the full customer base. A percentile of 90 means that customer is in the top 10 percent of projected lifetime value across all your customers.

### Step 7: AI Playbook Generation

For each segment that exists in the data, one call is made to the Claude API. The prompt sent to Claude includes the segment name, customer count, percentage of the total base, average RFM composite score, average recency in days, average order frequency, average order value, average historical LTV, average projected LTV, revenue contribution percentage, and channel mix breakdown.

Claude returns a structured JSON object with seven fields covering the complete strategic playbook for that segment. The response is parsed, validated, and stored. Em dashes are stripped from all Claude output automatically to ensure clean formatting in the exported files.

The playbooks are grounded in the real numbers from your actual data. Champions with an average projected LTV of nine thousand dollars get a very different playbook than Lapsed customers with an average projected LTV of eighty-four dollars.

---

## 4. The Analytics it Does

### RFM Analysis

RFM is the most widely used customer segmentation methodology in retail analytics globally. It scores customers on three behavioural dimensions that together predict future purchasing behaviour better than any single metric.

The quintile approach means scores are always relative to your own customer base. If you have a very active customer base, the bar for a Frequency score of 5 is higher than it would be for a less engaged base. The analysis adapts to your data.

In a typical healthy brand, Champions represent around 10 to 20 percent of customers but drive 50 to 70 percent of revenue. This Pareto distribution is a normal and expected finding. Nexus makes it visible and actionable.

### Lifecycle Segmentation

The six-tier lifecycle model reflects the natural stages of a customer relationship with a brand. Understanding which stage each customer is in tells you what they need from you next.

A Champion needs to feel recognised and rewarded. A Promising customer needs to be converted from a one-time buyer into a repeat buyer. An At-Risk customer needs to be reached before they leave. A Lapsed customer needs a compelling reason to come back. A New customer needs an onboarding experience that builds habit.

Without segmentation every customer gets the same email at the same time. With segmentation each group gets communication that is relevant to where they actually are.

### LTV Scoring

Projected LTV is the most important number in customer analytics because it tells you how much a customer is worth in the future, not just what they have already spent. This changes how you make investment decisions.

If you know a Champion has a projected LTV of ten thousand dollars, spending fifty dollars to retain them is an obvious decision. If you know a Lapsed customer has a projected LTV of sixty dollars, a thirty percent discount offer to win them back destroys margin rather than recovering it.

The LTV percentile score allows you to rank and prioritise individual customers within any segment. It is especially useful when combined with the customer table filter to identify the highest-value customers within a segment like At-Risk where urgent action is needed.

### AI Playbooks

The playbook generation layer translates data into strategy. Each playbook answers seven specific questions about a segment.

The headline gives the single most important strategic priority for that segment in one sentence. The email strategy specifies the cadence, tone, and content type that works for that segment's behaviour pattern. The offer type recommends what kind of incentive to use and explains why it fits this segment specifically. The channel priority identifies which channel to focus budget and effort on based on the segment's actual channel mix. The re-engagement trigger defines the specific behavioural or time-based signal that should initiate outreach. The success metric identifies the one KPI that tells you whether your strategy is working. The risk section quantifies what happens to revenue if this segment is ignored.

---

## 5. Input Files

Nexus accepts up to three CSV files uploaded simultaneously. The channel type of each file is auto-detected from column names. Files do not need to be pre-formatted or relabelled before uploading.

### Web Orders CSV

Auto-detected by the presence of the `order_total` column.

| Column | Required | Description |
|---|---|---|
| order_id | Yes | Unique order identifier |
| customer_id | Yes | Customer identifier in your web system |
| customer_email | Yes | Customer email address, used for identity resolution |
| order_date | Yes | Date of the order |
| order_total | Yes | Order value in dollars |
| product_category | No | Category of the product purchased |
| items_count | No | Number of items in the order |
| promo_applied | No | Whether a promotion was used |
| channel | No | Channel label, defaults to web |

### In-Store Transactions CSV

Auto-detected by the presence of `loyalty_id` or `store_location`.

| Column | Required | Description |
|---|---|---|
| txn_id | Yes | Unique transaction identifier |
| loyalty_id | Yes | Customer loyalty or POS identifier |
| customer_email | Yes | Customer email address, used for identity resolution |
| txn_date | Yes | Date of the transaction |
| amount | Yes | Transaction value in dollars |
| store_location | No | Store identifier or location name |
| product_category | No | Category of the product purchased |
| payment_method | No | Payment method used |
| channel | No | Channel label, defaults to instore |

### App Events CSV

Auto-detected by the presence of `event_type` or `app_user_id`.

| Column | Required | Description |
|---|---|---|
| session_id | Yes | Unique session identifier |
| app_user_id | Yes | Customer identifier in your mobile system |
| customer_email | Yes | Customer email address, used for identity resolution |
| event_date | Yes | Date of the event |
| event_type | Yes | Type of event such as purchase, view_product, add_to_cart, wishlist_add |
| product_sku | No | Product identifier |
| product_category | No | Category of the product viewed or purchased |
| app_version | No | Version of the app the customer was using |
| channel | No | Channel label, defaults to app |

The `customer_email` column must be present in at least one file for cross-channel identity resolution to work. If only one file is uploaded the app runs normally on that channel alone.

---

## 6. Output Files

### customer_360_scores.csv

One row per unique customer. This is the primary analytical output containing every computed field across all channels.

| Column | Description |
|---|---|
| customer_id | Unified customer identifier (email address) |
| email | Customer email |
| total_orders | Total order count across all channels |
| total_spend | Total spend across web and in-store in dollars |
| aov | Average order value in dollars |
| channels_used | Pipe-separated list such as web or web or instore or app |
| channel_count | Number of channels the customer appears in |
| web_orders | Order count from web channel |
| store_orders | Order count from in-store channel |
| app_sessions | Event count from app channel |
| last_purchase_date | Date of most recent purchase across all channels |
| recency_days | Days since last purchase as of the analysis date |
| frequency | Total orders used for the F score calculation |
| monetary | Total spend used for the M score calculation |
| R | Recency quintile score from 1 to 5 |
| F | Frequency quintile score from 1 to 5 |
| M | Monetary quintile score from 1 to 5 |
| RFM_score | Score string formatted as R5_F4_M3 |
| RFM_composite | Sum of R, F, and M scores ranging from 3 to 15 |
| segment | Lifecycle tier name |
| historical_ltv | Sum of all past spend in dollars |
| projected_ltv | Forward LTV estimate in dollars |
| ltv_score_percentile | Rank within full customer base from 0 to 100 |

### playbooks_report.csv

One row per segment. This is the strategic activation output generated by Claude.

| Column | Description |
|---|---|
| segment | Segment name |
| customer_count | Number of customers in this segment |
| pct_customers | Percentage of the total customer base |
| avg_rfm_composite | Mean RFM composite score for this segment |
| avg_historical_ltv | Mean historical LTV in dollars |
| avg_projected_ltv | Mean projected LTV in dollars |
| total_revenue | Total revenue attributed to this segment |
| headline | One-sentence strategic priority |
| email_strategy | Email and CRM approach with cadence, tone, and content type |
| offer_type | Recommended incentive or offer with rationale |
| channel_priority | Which channel to focus on and how to activate it |
| reengagement_trigger | Behavioral or time-based trigger to act on |
| success_metric | The one KPI to track for this segment |
| risk | Revenue consequence of ignoring this segment |

---

## 7. How Companies Can Use It

### Monthly CRM refresh

Run Nexus at the start of every month with fresh exports from your sales systems. The segment assignments will shift as customers move through their lifecycle. Champions who stop buying will drift into At-Risk. New customers who buy again will graduate into Promising or Loyal. The monthly run gives your CRM team an updated picture of where every customer stands and a fresh set of playbooks to act on.

### Campaign planning

Before planning a campaign, run Nexus to understand how large each segment is and what each segment is worth. This tells you where to invest your campaign budget. A ten percent improvement in Champions retention is worth far more than a ten percent improvement in Lapsed reactivation if Champions drive sixty percent of revenue and Lapsed drive three percent.

### Win-back campaigns

Export the Lapsed segment from `customer_360_scores.csv` and use the Lapsed playbook from `playbooks_report.csv` to design a win-back sequence. The playbook specifies what offer to make, when to trigger it, which channel to use, and what metric to track.

### VIP program design

Export the Champions segment and sort by `projected_ltv` descending. The customers at the top of that list are your highest-value customers. The Champions playbook tells you exactly how to treat them to maintain their loyalty and protect that projected revenue.

### At-Risk intervention

The At-Risk segment contains customers who used to be good customers but are showing early signs of churn. These are the highest-priority customers for intervention because they have proven purchase behaviour and are still recoverable. Sort the At-Risk segment by `historical_ltv` descending to find the highest-value customers who are at risk and reach them first.

### Cross-channel activation

The `channels_used` column in the output identifies which customers are single-channel versus multi-channel. Research consistently shows that multi-channel customers have higher LTV and lower churn rates. Brands can use this data to design campaigns that convert single-channel customers into multi-channel ones, for example driving web-only customers to download the app or visit a store.

---

## 8. Project Structure

```
Nexus AI/
├── app.py                      Main Streamlit application and UI
├── requirements.txt            Python dependencies
├── engine/
│   ├── __init__.py
│   ├── ingest.py               Channel detection, identity resolution, Customer 360 aggregation
│   └── scoring.py              RFM scoring, lifecycle segments, LTV calculation
└── ai/
    ├── __init__.py
    └── playbooks.py            Claude API integration and playbook generation
```

### What each file does

**app.py** contains the entire Streamlit user interface including the upload zone, configure panel, pipeline orchestration, progress tracking, results dashboard, and download buttons. This is the only file the user interacts with directly.

**engine/ingest.py** handles everything related to reading and unifying the input data. It detects which channel each file belongs to, validates the column structure, resolves customer identities across different ID formats, and aggregates all transactions into a single Customer 360 profile per customer.

**engine/scoring.py** contains all the analytical math. It computes raw RFM values, applies quintile ranking, runs the lifecycle tier assignment rules, calculates historical and projected LTV, and builds the final consolidated dataframe. The `SEGMENT_LTV_LIFESPAN` dictionary at the top of this file controls the lifespan assumptions used in the projected LTV formula.

**ai/playbooks.py** manages the Claude API integration. It builds a structured prompt for each segment using the real metrics from the scoring output, calls the API, parses the JSON response, strips any em dashes from the output, and returns a clean dataframe of playbooks ready for display and export.

---

## 9. Setup and Installation

### What you need before starting

- Python 3.10 or higher installed on your machine
- An Anthropic API key from console.anthropic.com (only needed for playbook generation)
- Your CSV exports from your sales systems, or the test files included in the project

### Windows CMD: First time setup

```cmd
cd "C:\MSBA\Projects\Nexus AI"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
mkdir engine
mkdir ai
move ingest.py engine\
move scoring.py engine\
move playbooks.py ai\
type nul > engine\__init__.py
type nul > ai\__init__.py
```

### Windows CMD: Run the app

```cmd
cd "C:\MSBA\Projects\Nexus AI"
venv\Scripts\activate
set ANTHROPIC_API_KEY=sk-ant-your-key-here
python -m streamlit run app.py
```

### Mac or Linux: First time setup

```bash
cd ~/Desktop/nexus
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Mac or Linux: Run the app

```bash
cd ~/Desktop/nexus
source venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-your-key-here
python -m streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`. To stop the app press `Ctrl + C` in the terminal.

The `ANTHROPIC_API_KEY` is only required if you want playbook generation. The app runs fully without it and skips the Claude API step.

---

## 10. Running the App

Once the app is open in your browser, follow these steps.

**Upload your files.** In section 01, click Upload and select one, two, or all three CSV files at once. The app detects each file type automatically and shows a status row for each file confirming the channel name, row count, and unique customer count detected.

**Configure the analysis.** In section 02, optionally enter your brand name. Choose an analysis window. Toggle AI playbook generation on or off. If you want to adjust the lifespan assumptions used in the projected LTV formula, open the Advanced panel and change any of the seven segment values.

**Run the analysis.** Click the Run analysis button. A progress bar steps through each pipeline stage: identity resolution, Customer 360 aggregation, RFM scoring, segment assignment, LTV scoring, consolidated output build, and Claude API playbook generation.

**Review the results.** When the pipeline completes, the results section renders below with five summary metric cards and four tabs.

The Segments tab shows the segment distribution donut chart, a detailed segment table with customer count, average projected LTV, revenue share, and average RFM for each tier, an RFM scatter plot of recency versus spend, and a projected LTV bar chart by segment.

The Customer table tab shows the full scored customer database. You can search by email or customer ID, filter by segment, and sort by RFM composite, projected LTV, total spend, or recency.

The Playbooks tab shows the Claude-generated action playbook for every segment, each containing the strategic headline, email strategy, offer type, channel priority, re-engagement trigger, success metric, and risk section.

The Download tab provides buttons to download both output CSV files.

---

## 11. API Cost

The Claude API is called once per segment during each run. With six segments the total usage per complete run is approximately 1,677 input tokens and 1,500 output tokens.

| Usage | Estimated cost |
|---|---|
| 1 run | ~$0.03 |
| 10 runs per day | ~$0.28 per day |
| 100 runs per day | ~$2.75 per day |
| 1,000 runs per month | ~$27.50 per month |

Pricing is based on claude-sonnet-4 at $3 per million input tokens and $15 per million output tokens. Switching to claude-haiku-4-5 reduces the cost to approximately $0.003 per run at the cost of slightly less detailed playbook output.

---

## Built With

- Python 3.11
- Streamlit
- pandas and numpy
- Plotly
- Anthropic Claude API
- Faker (test data generation)

---

*Nexus AI | Omnichannel Customer Intelligence*
