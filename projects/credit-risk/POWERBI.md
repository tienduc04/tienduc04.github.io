# Building the Power BI dashboard

## Quick route: open the ready-made project (about 5 minutes)
`powerbi/credit_risk_dashboard.pbip` is a Power BI Project that already contains the data model, the 9 DAX measures below, the navy and copper theme, and the 3 pages described in sections 3–5.

1. Double-click `powerbi/credit_risk_dashboard.pbip`. It opens in Power BI Desktop.
2. Click **Refresh now** in the yellow bar. This loads the 30,000 rows from `clients_clean.csv`.
3. Look through the 3 pages and move or resize anything you like.
4. **File → Save as** → choose *Power BI file (.pbix)* → `powerbi/credit_risk_dashboard.pbix`, so there is one file to upload to GitHub.
5. Take the screenshots and the PDF as described in section 6.

The project reads the CSV from the folder it was created in. If you move the project, run `python powerbi/make_pbip.py` again. Alternatively, in Power BI go to **Transform data → Edit parameters** and change `DataFolder`.

The sections below explain how to build the same report by hand, for example if you want to practise.

## Building it by hand (about 45 minutes)

Everything the dashboard needs is in `powerbi/clients_clean.csv`. That is the cleaned table produced by the SQL in `sql/02_clean.sql`, one row per client. Power BI Desktop is already installed on your PC.

## 1. Load the data
1. Open Power BI Desktop and choose **Blank report**.
2. **Home → Get data → Text/CSV** → `projects/credit-risk/powerbi/clients_clean.csv` → **Load**.
3. **View → Themes → Browse for themes** → `powerbi/theme.json`. This applies the navy and copper colours.
4. In **Table view**, check the data types:
   - `utilisation` and `payment_ratio` should be *Decimal number*.
   - `default_next_month` and `watch_list` should be *Whole number*.
   - All `*_band` columns should be *Text*. They sort correctly because each starts with a number ("1 <30%", "2 30-70%" …).

## 2. Create the measures
**Home → New measure**, then paste each line one at a time:

```DAX
Clients = COUNTROWS ( clients_clean )
Defaults = SUM ( clients_clean[default_next_month] )
Default Rate = DIVIDE ( [Defaults], [Clients] )
Portfolio Default Rate = CALCULATE ( [Default Rate], ALL ( clients_clean ) )
Lift vs Portfolio = DIVIDE ( [Default Rate], [Portfolio Default Rate] )
Balance of Defaulters (NT$ m) =
    DIVIDE ( SUMX ( FILTER ( clients_clean, clients_clean[default_next_month] = 1 ),
                    MAX ( clients_clean[balance_latest], 0 ) ), 1000000 )
Watch-list Share = DIVIDE ( CALCULATE ( [Clients], clients_clean[watch_list] = 1 ), [Clients] )
Watch-list Recall = DIVIDE ( CALCULATE ( [Defaults], clients_clean[watch_list] = 1 ), [Defaults] )
Watch-list Precision = CALCULATE ( [Default Rate], clients_clean[watch_list] = 1 )
```

Set the format of **Default Rate**, **Portfolio Default Rate**, **Watch-list Share**, **Recall** and **Precision** to *Percentage* with 1 decimal (Measure tools → Format). Set **Lift vs Portfolio** to *Decimal*, 1 decimal.

## 3. Page 1: "Portfolio overview"
| Visual | Fields |
|---|---|
| 4 **Cards** across the top | Clients · Default Rate · Balance of Defaulters (NT$ m) · Watch-list Recall |
| **Clustered column chart** | X: `status_band`; Y: Default Rate; tooltip: Clients |
| **Line chart** | X: `months_late_6m`; Y: Default Rate |
| **Slicers** (right side) | `limit_band`, `age_band`, `education` |

Title: *"About 1 in 5 clients defaults; clients late this month default at 2.3× the portfolio rate"*.

## 4. Page 2: "Risk drivers"
| Visual | Fields |
|---|---|
| **Matrix** (the heatmap) | Rows: `status_band`; Columns: `utilisation_band`; Values: Default Rate. Then Format → Cell elements → **Background colour** on, using the theme's min/max colours. |
| **Bar chart** | Y: `limit_band`; X: Default Rate |
| **Bar chart** | Y: `payment_band`; X: Default Rate |

Title: *"Repeated lateness and small limits carry most of the risk"*.

## 5. Page 3: "Early-warning watch list"
| Visual | Fields |
|---|---|
| 3 **Cards** | Watch-list Share · Watch-list Precision · Watch-list Recall |
| **Clustered column chart** | X: `watch_list` (rename the axis values to "Not flagged" / "Flagged"); Y: Default Rate |
| **Text box** | The rule: *flag any account that is one or more months late this month*, plus the 3 recommendations from the README |

## 6. Save and share
1. **File → Save as** → `projects/credit-risk/powerbi/credit_risk_dashboard.pbix`.
2. Take a screenshot of each page (Windows: `Win + Shift + S`). Save them as `powerbi/page1.png`, `page2.png` and `page3.png`, at least 1600 px wide.
3. Optional: **File → Export → Export to PDF** → `powerbi/credit_risk_dashboard.pdf`.

Publishing to the Power BI web service needs a work or school account, so a personal Gmail cannot use it. Instead, upload the `.pbix`, the PDF and the screenshots to GitHub with the rest of the project. Then put the link in the portfolio site (`content/site.json` → the credit risk card → `links`).

Once you have the screenshots, tell Claude. It can add them to the site and the README.
