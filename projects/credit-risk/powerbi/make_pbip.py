"""Writes the Power BI Project (credit_risk_dashboard.pbip) next to this script.

Run:  python make_pbip.py   then open credit_risk_dashboard.pbip in Power BI Desktop and click Refresh.
The data path is set to this folder, so re-run the script if you move the project.
"""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "credit_risk_dashboard"
T = "clients_clean"
NAVY, INK, COPPER = "#1D2B45", "#1D2733", "#C47A3A"

# ---------- semantic model ----------
COLUMNS = {  # name: (dataType, summarizeBy)
    "id": ("int64", "none"), "limit_bal": ("double", "sum"), "age": ("int64", "none"),
    "education": ("string", "none"), "status_latest": ("int64", "none"),
    "max_delay_6m": ("int64", "none"), "months_late_6m": ("int64", "none"),
    "balance_latest": ("double", "sum"), "utilisation": ("double", "none"),
    "payment_ratio": ("double", "none"), "default_next_month": ("int64", "none"),
    "status_band": ("string", "none"), "utilisation_band": ("string", "none"),
    "limit_band": ("string", "none"), "age_band": ("string", "none"),
    "payment_band": ("string", "none"), "watch_list": ("int64", "none"),
}
RENAMES = {"education": "Education", "months_late_6m": "Months late (last 6)"}
# Readable label column for each band column; the band column ("1 <30%") stays hidden and sets the sort order.
LABELS = {"status_band": "Repayment status", "utilisation_band": "Credit utilisation",
          "limit_band": "Credit limit (NT$)", "age_band": "Age band", "payment_band": "Share of bill paid"}
M_TYPE = {"int64": "Int64.Type", "double": "type number", "string": "type text"}
PCT, INT = "0.0%", "#,0"
MEASURES = [
    ("Clients", f"COUNTROWS ( {T} )", INT),
    ("Defaults", f"SUM ( {T}[default_next_month] )", INT),
    ("Default Rate", "DIVIDE ( [Defaults], [Clients] )", PCT),
    ("Portfolio Default Rate", f"CALCULATE ( [Default Rate], ALL ( {T} ) )", PCT),
    ("Lift vs Portfolio", "DIVIDE ( [Default Rate], [Portfolio Default Rate] )", "0.0"),
    ("Balance of Defaulters (NT$ m)",
     f"DIVIDE ( SUMX ( FILTER ( {T}, {T}[default_next_month] = 1 ), MAX ( {T}[balance_latest], 0 ) ), 1000000 )", INT),
    ("Watch-list Share", f"DIVIDE ( CALCULATE ( [Clients], {T}[watch_list] = 1 ), [Clients] )", PCT),
    ("Watch-list Recall", f"DIVIDE ( CALCULATE ( [Defaults], {T}[watch_list] = 1 ), [Defaults] )", PCT),
    ("Watch-list Precision", f"CALCULATE ( [Default Rate], {T}[watch_list] = 1 )", PCT),
]

types = ", ".join(f'{{"{c}", {M_TYPE[t]}}}' for c, (t, _) in COLUMNS.items())
m_query = [
    "let",
    f'    Source = Csv.Document(File.Contents(DataFolder & "{T}.csv"), [Delimiter=",", Columns={len(COLUMNS)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
    "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
    # en-US culture so "0.19565" parses on PCs with a comma decimal separator
    f'    Typed = Table.TransformColumnTypes(Headers, {{{types}}}, "en-US"),',
    *[f'    L{i} = Table.AddColumn({"Typed" if i == 0 else f"L{i - 1}"}, "{label}", each Text.AfterDelimiter([{band}], " "), type text),'
      for i, (band, label) in enumerate(LABELS.items())],
    f'    Watch = Table.AddColumn(L{len(LABELS) - 1}, "Watch list", each if [watch_list] = 1 then "Flagged" else "Not flagged", type text)',
    "in",
    "    Watch",
]
label_columns = [{"name": label, "dataType": "string", "sourceColumn": label, "summarizeBy": "none", "sortByColumn": band}
                 for band, label in LABELS.items()]
label_columns.append({"name": "Watch list", "dataType": "string", "sourceColumn": "Watch list",
                      "summarizeBy": "none", "sortByColumn": "watch_list"})
model = {
    "name": "SemanticModel",
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "tables": [{
            "name": T,
            "columns": [{"name": RENAMES.get(c, c), "dataType": t, "sourceColumn": c, "summarizeBy": s,
                         **({"isHidden": True} if c in LABELS else {})}
                        for c, (t, s) in COLUMNS.items()] + label_columns,
            "partitions": [{"name": T, "mode": "import", "source": {"type": "m", "expression": m_query}}],
            "measures": [{"name": n, "expression": e, "formatString": f} for n, e, f in MEASURES],
        }],
        "expressions": [{
            "name": "DataFolder", "kind": "m",
            "expression": f'"{HERE}\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
        }],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(["DataFolder", T])}],
    },
}

# ---------- report ----------
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def field(name):
    kind = "Measure" if name in {m[0] for m in MEASURES} else "Column"
    return kind, {kind: {"Expression": {"SourceRef": {"Source": "c"}}, "Property": name}}

def visual(vid, vtype, pos, roles=None, sort=None, title=None, objects=None):
    x, y, w, h = pos
    sv = {"visualType": vtype, "drillFilterOtherVisuals": True, "objects": objects or {}}
    if roles:
        names = list(dict.fromkeys(f for fs in roles.values() for f in fs))
        sv["projections"] = {r: [{"queryRef": f"{T}.{f}"} for f in fs] for r, fs in roles.items()}
        query = {"Version": 2, "From": [{"Name": "c", "Entity": T, "Type": 0}],
                 "Select": [{**field(f)[1], "Name": f"{T}.{f}", "NativeReferenceName": f} for f in names]}
        if sort:  # (field, 1 ascending | 2 descending)
            query["OrderBy"] = [{"Direction": sort[1], "Expression": field(sort[0])[1]}]
        sv["prototypeQuery"] = query
    if title:
        sv["vcObjects"] = {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                                     "fontColor": {"solid": {"color": lit(f"'{NAVY}'")}}}}]}
    cfg = {"name": vid, "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
           "singleVisual": sv}
    return {"x": x, "y": y, "z": 0, "width": w, "height": h, "config": json.dumps(cfg), "filters": "[]"}

def text(vid, pos, paragraphs):
    """paragraphs: list of (text, size_pt, bold)."""
    paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": NAVY if b else INK,
                                                       **({"fontWeight": "bold"} if b else {})}}]}
             for t, s, b in paragraphs]
    return visual(vid, "textbox", pos, objects={"general": [{"properties": {"paragraphs": paras}}]})

def title(vid, words):
    return text(vid, (20, 10, 1240, 50), [(words, 18, True)])

def card(vid, measure, x, y, w):
    return visual(vid, "card", (x, y, w, 110), {"Values": [measure]},
                  objects={"labels": [{"properties": {"labelDisplayUnits": lit("1D"), "color": {"solid": {"color": lit(f"'{COPPER}'")}}}}]})

def chart(vid, vtype, pos, category, ttl, extra=None, direction=1):
    roles = {"Category": [category], "Y": ["Default Rate"], **(extra or {})}
    return visual(vid, vtype, pos, roles, sort=(category, direction), title=ttl,
                  objects={"labels": [{"properties": {"show": lit("true")}}]})

def slicer(vid, column, y):
    return visual(vid, "slicer", (1040, y, 220, 195), {"Values": [column]})

heat = {"FillRule": {
    "Input": {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": "Default Rate"}},
    "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": "'#F6EDE4'"}}},
        "max": {"color": {"Literal": {"Value": "'#D9825B'"}}},  # light enough for dark text to stay readable
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}
big = {"fontSize": lit("14D")}
matrix = visual("p2_matrix", "pivotTable", (20, 70, 1240, 240),
                {"Rows": ["Repayment status"], "Columns": ["Credit utilisation"], "Values": ["Default Rate"]},
                sort=("Repayment status", 1), title="Default rate: latest repayment status × credit utilisation",
                # font size needs its own entry: entries with a data selector apply per cell only
                objects={"values": [{"properties": big}, {"properties": {"backColor": {"solid": {"color": {"expr": heat}}}},
                                     "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                                  "metadata": f"{T}.Default Rate"}}],
                         "columnHeaders": [{"properties": big}], "rowHeaders": [{"properties": big}],
                         "subTotals": [{"properties": big}]})

pages = [
    ("Portfolio overview", [
        title("p1_title", "About 1 in 5 clients defaults; clients late this month default at 2.3× the portfolio rate"),
        card("p1_c1", "Clients", 20, 70, 235), card("p1_c2", "Default Rate", 265, 70, 235),
        card("p1_c3", "Balance of Defaulters (NT$ m)", 510, 70, 235), card("p1_c4", "Watch-list Recall", 755, 70, 255),
        chart("p1_status", "clusteredColumnChart", (20, 195, 490, 505), "Repayment status",
              "Default rate by latest repayment status", {"Tooltips": ["Clients"]}),
        chart("p1_months", "lineChart", (520, 195, 490, 505), "Months late (last 6)",
              "Default rate by months late in the last 6"),
        slicer("p1_s1", "Credit limit (NT$)", 70), slicer("p1_s2", "Age band", 285), slicer("p1_s3", "Education", 500),
    ]),
    ("Risk drivers", [
        title("p2_title", "Repeated lateness and small limits carry most of the risk"),
        matrix,
        chart("p2_limit", "clusteredBarChart", (20, 325, 615, 375), "Credit limit (NT$)", "Default rate by credit limit (NT$)"),
        chart("p2_pay", "clusteredBarChart", (645, 325, 615, 375), "Share of bill paid",
              "Default rate by share of last bill paid"),
    ]),
    ("Early-warning watch list", [
        title("p3_title", "A one-line rule flags 22.7% of clients and catches 51.7% of next-month defaults"),
        card("p3_c1", "Watch-list Share", 20, 70, 405), card("p3_c2", "Watch-list Precision", 437, 70, 405),
        card("p3_c3", "Watch-list Recall", 855, 70, 405),
        chart("p3_rule", "clusteredColumnChart", (20, 195, 600, 505), "Watch list",
              "Default rate: flagged vs not flagged", {"Tooltips": ["Clients"]}),
        text("p3_text", (640, 195, 620, 505), [
            ("The rule", 14, True),
            ("Flag any account that is one or more months late this month.", 12, False),
            ("", 12, False),
            ("Recommendations", 14, True),
            ("1. Start collections on the watch list right away: reminders and payment plans "
             "before accounts roll into a second month.", 12, False),
            ("2. Use the months-late count in limit reviews: freeze limit increases for clients "
             "with 3 or more late months in the last 6.", 12, False),
            ("3. Encourage paying in full: offer auto-pay of the full balance and alerts at high utilisation.", 12, False),
            ("", 12, False),
            ("Data: UCI Default of Credit Card Clients (Taiwan, Apr–Sep 2005), 30,000 clients. "
             "Descriptive rates, not a predictive model.", 10, False),
        ]),
    ]),
]

theme_name = "credit_risk_theme.json"
report = {
    "config": json.dumps({
        "version": "5.65",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "type": 2, "version": "5.59"},
                            "customTheme": {"name": theme_name, "type": 1, "version": "5.59"}},
        "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "linguisticSchemaSyncVersion": 2,
    }),
    "layoutOptimization": 0,
    "resourcePackages": [
        {"resourcePackage": {"name": "SharedResources", "type": 2, "disabled": False,
                             "items": [{"type": 202, "path": "BaseThemes/CY24SU10.json", "name": "CY24SU10"}]}},
        {"resourcePackage": {"name": "RegisteredResources", "type": 1, "disabled": False,
                             "items": [{"type": 201, "path": theme_name, "name": theme_name}]}},
    ],
    "sections": [{"name": f"page{i + 1}", "displayName": name, "displayOption": 1, "width": 1280, "height": 720,
                  "ordinal": i, "config": "{}", "filters": "[]", "visualContainers": vcs}
                 for i, (name, vcs) in enumerate(pages)],
    "filters": "[]",
}

# ---------- write files ----------
def write(rel, obj):
    p = HERE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

rep, sm = f"{NAME}.Report", f"{NAME}.SemanticModel"
write(f"{NAME}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": rep}}],
                       "settings": {"enableAutoRecovery": True}})
write(f"{sm}/definition.pbism", {"version": "1.0", "settings": {}})
write(f"{sm}/model.bim", model)
write(f"{rep}/definition.pbir", {"version": "1.0",
                                 "datasetReference": {"byPath": {"path": f"../{sm}"}, "byConnection": None}})
write(f"{rep}/report.json", report)
res = HERE / rep / "StaticResources"
(res / "SharedResources/BaseThemes").mkdir(parents=True, exist_ok=True)
(res / "RegisteredResources").mkdir(parents=True, exist_ok=True)
shutil.copy(HERE / "basetheme/CY24SU10.json", res / "SharedResources/BaseThemes/CY24SU10.json")
shutil.copy(HERE / "theme.json", res / "RegisteredResources" / theme_name)

# self-check: every field a visual uses exists in the model, and every visual config is valid JSON
known = {RENAMES.get(c, c) for c in COLUMNS} | set(LABELS.values()) | {"Watch list"} | {m[0] for m in MEASURES}
for _, vcs in pages:
    for vc in vcs:
        for s in json.loads(vc["config"])["singleVisual"].get("prototypeQuery", {}).get("Select", []):
            assert s["NativeReferenceName"] in known, s["NativeReferenceName"]
print(f"Wrote {NAME}.pbip with {sum(len(v) for _, v in pages)} visuals on {len(pages)} pages. Data folder: {HERE}")
