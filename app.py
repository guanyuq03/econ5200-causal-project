import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Job Training Policy Dashboard", layout="wide")

st.title("Consulting Report: Causal Effect of Job Training on Earnings")
st.markdown(
    """
This dashboard summarizes the estimated causal effect of job training on post-program earnings
using the Lalonde dataset. It provides a simple **what-if scenario tool** based on the estimated
treatment effect from the notebook analysis.
"""
)

# -----------------------------
# Baseline estimates from notebook
# -----------------------------
baseline_options = {
    "Main DML": {
        "ate": 1244.8419,
        "ci_low": -373.3657,
        "ci_high": 2863.0496,
        "description": "Main DML estimate using Gradient Boosting nuisance models."
    },
    "Robust DML": {
        "ate": 991.8634,
        "ci_low": -586.2821,
        "ci_high": 2570.0088,
        "description": "Robustness estimate using Random Forest nuisance models."
    }
}

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("What-If Scenarios")

estimate_choice = st.sidebar.selectbox(
    "Choose baseline estimate",
    options=list(baseline_options.keys()),
    index=0
)

treatment_multiplier = st.sidebar.slider(
    "Treatment intensity multiplier",
    min_value=0.5,
    max_value=3.0,
    value=1.0,
    step=0.1
)

participants = st.sidebar.slider(
    "Number of participants",
    min_value=100,
    max_value=5000,
    value=1000,
    step=100
)

selected = baseline_options[estimate_choice]
baseline_ate = selected["ate"]
baseline_ci_low = selected["ci_low"]
baseline_ci_high = selected["ci_high"]

# Convert CI to SE using 95% CI approximation
baseline_se = (baseline_ci_high - baseline_ate) / 1.96

# -----------------------------
# Compute What-If Estimate
# -----------------------------
adjusted_ate = baseline_ate * treatment_multiplier
adjusted_se = baseline_se * treatment_multiplier
ci_lower = adjusted_ate - 1.96 * adjusted_se
ci_upper = adjusted_ate + 1.96 * adjusted_se

aggregate_effect = adjusted_ate * participants
aggregate_ci_lower = ci_lower * participants
aggregate_ci_upper = ci_upper * participants

# -----------------------------
# Display Results
# -----------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Estimated Effect per Participant", f"${adjusted_ate:,.0f}")
col2.metric("95% CI", f"[${ci_lower:,.0f}, ${ci_upper:,.0f}]")
col3.metric("Aggregate Effect", f"${aggregate_effect:,.0f}")

st.markdown(
    f"""
> **What-if interpretation:** If treatment intensity is multiplied by
> **{treatment_multiplier:.1f}x**, the estimated earnings effect changes to
> **${adjusted_ate:,.0f}** per participant
> (95% CI: **[${ci_lower:,.0f}, ${ci_upper:,.0f}]**).
> For **{participants:,}** participants, the aggregate earnings effect is
> **${aggregate_effect:,.0f}**
> (95% CI: **[${aggregate_ci_lower:,.0f}, ${aggregate_ci_upper:,.0f}]**).
"""
)

st.caption(selected["description"])

# -----------------------------
# Uncertainty Visualization
# -----------------------------
multipliers = np.arange(0.5, 3.1, 0.1)
ates = baseline_ate * multipliers
ses = baseline_se * multipliers

upper = ates + 1.96 * ses
lower = ates - 1.96 * ses

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=multipliers,
    y=upper,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=multipliers,
    y=lower,
    mode="lines",
    line=dict(width=0),
    fill="tonexty",
    fillcolor="rgba(26,35,126,0.20)",
    name="95% CI"
))
fig.add_trace(go.Scatter(
    x=multipliers,
    y=ates,
    mode="lines",
    line=dict(color="#1a237e", width=3),
    name="Estimated Effect"
))
fig.add_vline(
    x=treatment_multiplier,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Current: {treatment_multiplier:.1f}x"
)
fig.update_layout(
    title="What-If: Estimated Effect vs. Treatment Intensity",
    xaxis_title="Treatment Intensity Multiplier",
    yaxis_title="Estimated Causal Effect on Earnings ($)",
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Counterfactual Scenario
# -----------------------------
st.subheader("Counterfactual Scenario")

counterfactual_ate = baseline_ate * 2.0
counterfactual_ci_low = baseline_ci_low * 2.0
counterfactual_ci_high = baseline_ci_high * 2.0

st.write(
    f"If treatment intensity doubled, the estimated effect would be "
    f"**${counterfactual_ate:,.0f}** per participant "
    f"(95% CI: **[${counterfactual_ci_low:,.0f}, ${counterfactual_ci_high:,.0f}]**)."
)

# -----------------------------
# Interpretation Box
# -----------------------------
st.subheader("Interpretation")

if ci_lower > 0:
    st.success("Under this scenario, the confidence interval is entirely above zero, suggesting a clearly positive effect.")
elif ci_upper < 0:
    st.error("Under this scenario, the confidence interval is entirely below zero, suggesting a negative effect.")
else:
    st.warning("Under this scenario, the confidence interval still includes zero, so uncertainty remains substantial.")

st.markdown(
    """
This dashboard is a **policy scenario simulator**, not a re-estimated causal model.
It translates the notebook's causal estimates into an interactive decision tool.
"""
)