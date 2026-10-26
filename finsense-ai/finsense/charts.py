import plotly.graph_objects as go
import streamlit as st

from finsense.data import inr
from finsense.theme import BLUE, GREEN, INK, LINE, OCHRE, PAGE, RED, RULE, SOFT, VIOLET

# The passbook inks first, then faded versions of them for long category lists.
CATEGORY_COLORS = [
    BLUE, RED, GREEN, VIOLET, OCHRE,
    "#6F86C4", "#D27A72", "#6E9C86", "#9A86C2", "#C2A060",
    "#8A8F9C", "#4A5060",
]


def _layout(fig, height=360, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=64, r=16, t=40, b=56),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans 3, sans-serif", color=INK, size=13),
        hoverlabel=dict(bgcolor=PAGE, bordercolor=LINE, font=dict(color=INK, family="Courier Prime, monospace")),
        showlegend=legend,
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(automargin=True, gridcolor=RULE, zerolinecolor=LINE, linecolor=INK, showgrid=False,
                     tickfont=dict(color=SOFT, family="Courier Prime, monospace", size=12))
    fig.update_yaxes(automargin=True, gridcolor=RULE, zerolinecolor=SOFT, linecolor=LINE, tickprefix="₹",
                     tickfont=dict(color=SOFT, family="Courier Prime, monospace", size=12))
    return fig


def show(fig):
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})


def cashflow(monthly):
    fig = go.Figure()
    fig.add_bar(x=monthly["Month"], y=monthly["Income"], name="Money in", marker_color=BLUE, marker_cornerradius=1)
    fig.add_bar(x=monthly["Month"], y=monthly["Expense"], name="Money out", marker_color=RED, marker_cornerradius=1)
    fig.add_scatter(
        x=monthly["Month"], y=monthly["Savings"], name="Net", mode="lines+markers",
        line=dict(color=INK, width=2, dash="dot"), marker=dict(size=5, color=INK),
    )
    fig.update_layout(barmode="group", bargap=0.25)
    return _layout(fig)


def category_donut(by_category):
    fig = go.Figure(go.Pie(
        labels=by_category.index, values=by_category.values, hole=0.62,
        marker=dict(colors=CATEGORY_COLORS, line=dict(color=PAGE, width=3)),
        textinfo="percent", hovertemplate="%{label}<br>₹%{value:,.0f}<extra></extra>",
        sort=True,
    ))
    fig.add_annotation(
        text=f"<b>{inr(by_category.sum())}</b><br><span style='color:{SOFT}'>total spent</span>",
        showarrow=False, font=dict(size=15),
    )
    fig = _layout(fig, height=440)
    fig.update_layout(legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", yanchor="top"),
                      margin=dict(l=8, r=8, t=8, b=8))
    return fig



def score_waterfall(health):
    comps = health["components"]
    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=["Perfect score"] + [c["name"] for c in comps] + ["Your score"],
        measure=["absolute"] + ["relative"] * len(comps) + ["total"],
        y=[100] + [-c["lost"] for c in comps] + [0],
        text=["100"] + [f"−{c['lost']:.0f}" if c["lost"] >= 0.5 else "0" for c in comps] + [str(health["score"])],
        textposition="outside",
        decreasing=dict(marker=dict(color=RED)),
        totals=dict(marker=dict(color=BLUE)),
        increasing=dict(marker=dict(color=GREEN)),
        connector=dict(line=dict(color=SOFT, dash="dot")),
        hovertemplate="%{x}<br>%{text} pts<extra></extra>",
    ))
    fig = _layout(fig, height=380, legend=False)
    fig.update_yaxes(tickprefix="", range=[0, 112], title="points")
    return fig


def pulse_line(pulse):
    fig = go.Figure()
    fig.add_scatter(x=pulse["Month"], y=pulse["Pulse"], name="Monthly", mode="markers",
                    marker=dict(color=SOFT, size=6, opacity=.5))
    fig.add_scatter(x=pulse["Month"], y=pulse["Trend"], name="3-month trend", mode="lines",
                    line=dict(color=BLUE, width=3, shape="spline"))
    fig = _layout(fig, height=300)
    fig.update_yaxes(tickprefix="", range=[-5, 105])
    return fig


def _band(fig, bands, color, name, dash=None):
    fig.add_scatter(x=bands["Month"], y=bands["P90"], mode="lines", line=dict(width=0),
                    showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=bands["Month"], y=bands["P10"], mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor=_alpha(color, 0.18), name=f"{name} (80% range)",
                    hoverinfo="skip")
    fig.add_scatter(x=bands["Month"], y=bands["P50"], mode="lines+markers", name=f"{name} (likely)",
                    line=dict(color=color, width=3, dash=dash), marker=dict(size=5),
                    hovertemplate="%{x}<br>₹%{y:,.0f}<extra>" + name + "</extra>")


def _alpha(hex_color, a):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def fan(baseline, scenario=None, goal=None):
    fig = go.Figure()
    _band(fig, baseline, SOFT, "Current habits", dash="dot")
    if scenario is not None:
        _band(fig, scenario, VIOLET, "Your scenario")
    if goal:
        fig.add_hline(y=goal, line=dict(color=OCHRE, dash="dash"),
                      annotation_text=f"Goal {inr(goal)}", annotation_font_color=OCHRE)
    fig.add_hline(y=0, line=dict(color=LINE))
    return _layout(fig, height=400)


def radar_timeline(scanned):
    normal = scanned[~scanned["Flagged"]]
    flagged = scanned[scanned["Flagged"]]
    fig = go.Figure()
    fig.add_scatter(
        x=normal["Date"], y=normal["Amount"], mode="markers", name="Normal",
        marker=dict(color=_alpha(BLUE, 0.3), size=6),
        customdata=normal[["Category"]],
        hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]} · ₹%{y:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=flagged["Date"], y=flagged["Amount"], mode="markers", name="Flagged",
        marker=dict(color=RED, size=12, line=dict(color=PAGE, width=1.5), symbol="diamond"),
        customdata=flagged[["Category", "Radar_Score"]].assign(
            Why=flagged["Reasons"].apply(lambda r: "<br>• ".join(r))
        ),
        hovertemplate="%{x|%d %b %Y}<br><b>%{customdata[0]} · ₹%{y:,.0f}</b>"
                      "<br>Radar score %{customdata[1]}<br>• %{customdata[2]}<extra></extra>",
    )
    return _layout(fig, height=420)


def heatmap(grid):
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=list(grid.columns), y=list(grid.index),
        colorscale=[[0, PAGE], [0.5, "#9DB0DE"], [1, BLUE]],
        hovertemplate="%{y} · %{x}<br>avg ₹%{z:,.0f} / day<extra></extra>",
        colorbar=dict(tickprefix="₹", outlinewidth=0),
        xgap=4, ygap=4,
    ))
    fig = _layout(fig, height=320, legend=False)
    fig.update_yaxes(tickprefix="", autorange="reversed")
    return fig


def category_trend(cat_matrix, top_n=5):
    top = cat_matrix.sum().sort_values(ascending=False).head(top_n).index
    fig = go.Figure()
    labels = cat_matrix.index.strftime("%b %Y")
    for i, cat in enumerate(top):
        series = cat_matrix[cat].rolling(3, min_periods=1).mean()
        fig.add_scatter(x=labels, y=series, name=cat, mode="lines",
                        line=dict(color=CATEGORY_COLORS[i % len(CATEGORY_COLORS)], width=2.5, shape="spline"))
    return _layout(fig, height=360)


# ------------------------------------------------------------
# Card fraud lab
# ------------------------------------------------------------

def importance_bars(importance, top_n=10):
    top = importance.head(top_n)[::-1]
    fig = go.Figure(go.Bar(
        x=top.values * 100, y=top.index, orientation="h",
        marker=dict(color=BLUE, cornerradius=4),
        hovertemplate="%{y}: %{x:.1f}% of the model's decisions<extra></extra>",
    ))
    fig = _layout(fig, height=340, legend=False)
    fig.update_xaxes(ticksuffix="%", tickprefix="")
    fig.update_yaxes(tickprefix="")
    return fig


def probability_histogram(proba, labels, threshold):
    fig = go.Figure()
    if labels is not None:
        fig.add_histogram(x=proba[labels == 0] * 100, name="Genuine", marker_color=_alpha(BLUE, .7),
                          xbins=dict(start=0, end=100, size=5))
        fig.add_histogram(x=proba[labels == 1] * 100, name="Fraud", marker_color=_alpha(RED, .85),
                          xbins=dict(start=0, end=100, size=5))
    else:
        fig.add_histogram(x=proba * 100, name="Payments", marker_color=_alpha(BLUE, .7),
                          xbins=dict(start=0, end=100, size=5))
    fig.add_vline(x=threshold * 100, line=dict(color=OCHRE, dash="dash"),
                  annotation_text="your threshold", annotation_font_color=OCHRE)
    fig.update_layout(barmode="overlay")
    fig = _layout(fig, height=320)
    fig.update_yaxes(type="log", tickprefix="", title="payments (log scale)")
    fig.update_xaxes(ticksuffix="%", title="fraud probability")
    return fig


def hour_profile(genuine_share, fraud_share):
    hours = [f"{h:02d}" for h in range(24)]
    fig = go.Figure()
    fig.add_scatter(x=hours, y=genuine_share.values * 100, name="Genuine", mode="lines",
                    line=dict(color=BLUE, width=3, shape="spline"))
    fig.add_scatter(x=hours, y=fraud_share.values * 100, name="Fraud", mode="lines",
                    line=dict(color=RED, width=3, shape="spline", dash="dot"))
    fig = _layout(fig, height=300)
    fig.update_yaxes(tickprefix="", ticksuffix="%", title="share of payments")
    fig.update_xaxes(title="hour of day")
    return fig


def payment_profile(profile):
    """One row per feature: genuine 1–99% band, genuine typical, fraud typical, this payment."""
    fig = go.Figure()
    y = profile["Feature"]
    for _, r in profile.iterrows():
        fig.add_shape(type="line", x0=r["Genuine low"], x1=r["Genuine high"], y0=r["Feature"], y1=r["Feature"],
                      line=dict(color=_alpha(BLUE, .35), width=10))
    fig.add_scatter(x=profile["Genuine typical"], y=y, mode="markers", name="Typical genuine",
                    marker=dict(color=BLUE, size=9, symbol="line-ns", line=dict(width=3, color=BLUE)))
    fig.add_scatter(x=profile["Fraud typical"], y=y, mode="markers", name="Typical fraud",
                    marker=dict(color=_alpha(RED, .55), size=10, symbol="x"))
    fig.add_scatter(x=profile["This payment"], y=y, mode="markers", name="This payment",
                    marker=dict(color=INK, size=13, symbol="diamond", line=dict(color=PAGE, width=1.5)))
    fig = _layout(fig, height=60 + 38 * len(profile))
    fig.update_yaxes(tickprefix="", autorange="reversed")
    fig.update_xaxes(tickprefix="", title="value (shaded band = where 98% of genuine payments sit)")
    return fig
