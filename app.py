from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st

st.set_page_config(page_title="EcoDevice | Green Computing", page_icon="🌿", layout="wide")

DEFAULTS = {"latest": None, "baseline": None, "history": [], "actions": [], "experiments": []}
for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
<style>
.stApp{background:radial-gradient(ellipse at 8% 0%,rgba(27,124,82,.22),transparent 40%),linear-gradient(145deg,#07120f,#0b1112 58%,#0c1b14);color:#effaf3}
.block-container{padding-top:1.2rem;max-width:1550px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10251b,#171b1d)}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(22,53,39,.9),rgba(15,27,23,.85));border:1px solid #315543;border-radius:16px;padding:15px 16px}
[data-testid="stMetricValue"]{color:#f3fff7}
.eco-hero{padding:1.8rem 2rem;border-radius:22px;background:linear-gradient(115deg,#10392c,#17694b,#143d30);border:1px solid #397354;margin-bottom:1rem;box-shadow:0 12px 35px #0003}
.eco-hero h1{color:#f4fff8;font-size:2.65rem;margin:0 0 .25rem}
.eco-hero p{color:#d2ecdf;margin:.15rem 0}
.section-note{color:#a9c5b5;font-size:.92rem}
div[data-testid="stPlotlyChart"]{border:1px solid #203b2d;border-radius:14px;padding:5px;background:rgba(12,26,20,.45)}
</style>
""", unsafe_allow_html=True)


def process_snapshot():
    rows = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "memory_percent", "status"]):
        try:
            info = proc.info
            mi = info.get("memory_info")
            rows.append({
                "PID": info.get("pid"),
                "Process": info.get("name") or "Unknown",
                "CPU (%)": round(proc.cpu_percent(interval=None), 1),
                "Memory (MB)": round(mi.rss / (1024 ** 2), 1) if mi else 0.0,
                "Memory (%)": round(info.get("memory_percent") or 0.0, 2),
                "Status": info.get("status") or "Unknown",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            continue
    df = pd.DataFrame(rows, columns=["PID", "Process", "CPU (%)", "Memory (MB)", "Memory (%)", "Status"])
    if not df.empty:
        df = df.sort_values(["Memory (MB)", "CPU (%)"], ascending=False).reset_index(drop=True)
    return df


def take_snapshot():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": float(cpu), "ram": float(mem.percent),
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "processes": process_snapshot(),
    }


def refresh():
    snap = take_snapshot()
    st.session_state.latest = snap
    st.session_state.history.append({
        "Timestamp": snap["timestamp"], "CPU utilization (%)": snap["cpu"],
        "RAM utilization (%)": snap["ram"], "RAM used (GB)": snap["ram_used_gb"],
        "Processes observed": len(snap["processes"]),
    })
    st.session_state.history = st.session_state.history[-500:]


def download_csv(df, filename, label):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"),
                       file_name=filename, mime="text/csv")


def chart_theme(fig, height=330):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=15, r=15, t=55, b=15),
        font=dict(color="#e4f2e9"), legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    return fig


with st.sidebar:
    st.header("⚙️ Monitoring settings")
    cpu_limit = st.slider("Flag process above CPU (%)", 5, 100, 50, 5)
    memory_limit = st.slider("Flag process above memory (MB)", 100, 8000, 500, 100)
    name_filter = st.text_input("Filter process name", placeholder="e.g. Chrome")
    st.caption("Thresholds are review heuristics, not proof that a process is wasteful.")
    if st.button("🔄 Refresh system snapshot", type="primary", use_container_width=True):
        refresh()
        st.rerun()
    st.caption("Measurements come from the computer running this app.")

if st.session_state.latest is None:
    refresh()
data = st.session_state.latest
processes = data["processes"]

st.markdown("""
<div class="eco-hero">
<h1>🌿 EcoDevice</h1>
<p><b>GREEN COMPUTING INTELLIGENCE</b> · Device Efficiency &amp; Resource Optimization</p>
<p style="margin-top:.6rem">Observe your system. Understand resource use. Make more responsible computing choices.</p>
</div>
""", unsafe_allow_html=True)
st.warning("CPU/RAM reductions do not directly prove electricity savings. Claim measured energy savings only with a power meter or suitable hardware energy telemetry.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("CPU UTILIZATION", f'{data["cpu"]:.1f}%', help="System CPU utilization at the latest snapshot.")
m2.metric("RAM UTILIZATION", f'{data["ram"]:.1f}%')
m3.metric("MEMORY IN USE", f'{data["ram_used_gb"]:.2f} GB', f'of {data["ram_total_gb"]:.2f} GB')
m4.metric("PROCESSES OBSERVED", f'{len(processes):,}')
st.caption(f'● Latest snapshot: {data["timestamp"]}')

overview, monitor, eco, lab, sdg = st.tabs([
    "🌱 Overview", "🖥️ Process Monitor", "♻️ Eco Actions", "🧪 Experiment Lab", "🎯 SDG Impact"
])

with overview:
    st.subheader("Resource intelligence")
    st.markdown('<p class="section-note">Visual snapshots of your computer’s current resource profile and recent readings.</p>', unsafe_allow_html=True)
    hist = pd.DataFrame(st.session_state.history)
    g1, g2 = st.columns([1, 1])
    with g1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=data["cpu"], number={"suffix":"%"},
            title={"text":"CPU load"}, gauge={"axis":{"range":[0,100]},
            "bar":{"color":"#55d68b"}, "bgcolor":"#13271d",
            "steps":[{"range":[0,50],"color":"#1a4934"},{"range":[50,80],"color":"#6b6125"},{"range":[80,100],"color":"#63302e"}],
            "threshold":{"line":{"color":"#f3fff7","width":3},"thickness":.8,"value":cpu_limit}}
        ))
        chart_theme(fig, 300)
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=data["ram"], number={"suffix":"%"},
            title={"text":"RAM pressure"}, gauge={"axis":{"range":[0,100]},
            "bar":{"color":"#63c6a0"}, "bgcolor":"#13271d",
            "steps":[{"range":[0,50],"color":"#1a4934"},{"range":[50,80],"color":"#6b6125"},{"range":[80,100],"color":"#63302e"}]}
        ))
        chart_theme(fig, 300)
        st.plotly_chart(fig, use_container_width=True)
    if not hist.empty:
        g3, g4 = st.columns(2)
        with g3:
            fig = px.line(hist, x="Timestamp", y="CPU utilization (%)", markers=True, title="CPU trend", color_discrete_sequence=["#5de29a"])
            fig.update_traces(line_width=3, marker_size=7)
            chart_theme(fig, 320)
            st.plotly_chart(fig, use_container_width=True)
        with g4:
            fig = px.line(hist, x="Timestamp", y="RAM utilization (%)", markers=True, title="RAM trend", color_discrete_sequence=["#68c9d8"])
            fig.update_traces(line_width=3, marker_size=7)
            chart_theme(fig, 320)
            st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Memory allocation")
        mem_df = pd.DataFrame({"Category":["Used","Available"],"GB":[data["ram_used_gb"],max(data["ram_total_gb"]-data["ram_used_gb"],0)]})
        fig = px.pie(mem_df, names="Category", values="GB", hole=.68, color_discrete_sequence=["#4dd38b","#253c31"])
        fig.update_traces(textinfo="label+percent", textfont_size=13)
        chart_theme(fig, 310)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Highest memory consumers")
        top = processes.head(8).sort_values("Memory (MB)") if not processes.empty else processes
        if not top.empty:
            fig = px.bar(top, x="Memory (MB)", y="Process", orientation="h", title="Top 8 processes by RAM",
                         color="Memory (MB)", color_continuous_scale=["#22543d","#48d597"])
            fig.update_layout(coloraxis_showscale=False)
            chart_theme(fig, 310)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No process data available.")
    st.subheader("Snapshot history")
    st.dataframe(hist.tail(12), use_container_width=True, hide_index=True)
    download_csv(hist, "ecodevice_history.csv", "⬇️ Export snapshot history CSV")

with monitor:
    st.subheader("Process Monitor")
    df = processes.copy()
    if name_filter.strip():
        df = df[df["Process"].str.contains(name_filter.strip(), case=False, na=False)]
    sort_by = st.selectbox("Sort processes by", ["Memory (MB)", "CPU (%)", "Memory (%)", "Process", "PID"])
    ascending = st.checkbox("Sort ascending", value=False)
    if not df.empty:
        df = df.sort_values(sort_by, ascending=ascending, kind="stable")
    flagged = df[(df["CPU (%)"] >= cpu_limit) | (df["Memory (MB)"] >= memory_limit)] if not df.empty else df
    x, y, z = st.columns(3)
    x.metric("Matching processes", len(df))
    y.metric("Above review thresholds", len(flagged))
    z.metric("Memory in filtered list", f'{df["Memory (MB)"].sum()/1024:.2f} GB' if not df.empty else "0 GB")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True, height=430)
        with st.expander("View processes above thresholds"):
            st.dataframe(flagged, use_container_width=True, hide_index=True)
        download_csv(df, "ecodevice_processes.csv", "⬇️ Export process list CSV")
    else:
        st.info("No matching processes. Clear the sidebar filter.")

with eco:
    st.subheader("Eco Actions")
    st.write("Recommendations are for human review. EcoDevice does not automatically terminate processes or change system settings.")
    recs = [
        ("Close unused browser tabs", "Review inactive tabs and save any work before closing them."),
        ("Quit unused applications", "Close apps you do not need after saving your work."),
        ("Review startup applications", "Disable only startup items you recognize and no longer need."),
        ("Use power-saving settings", "Try the operating system’s built-in energy-saving mode."),
        ("Use sleep when appropriate", "Avoid leaving a device actively running when it is not needed."),
        ("Remove unused software", "Uninstall applications you no longer use, where appropriate."),
    ]
    for i, (title, detail) in enumerate(recs):
        with st.container(border=True):
            l, r = st.columns([5, 1])
            l.markdown(f"**{i+1:02d} · {title}**")
            l.write(detail)
            if r.button("Log action", key=f"action_{i}"):
                st.session_state.actions.append({"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Action":title,"Status":"Logged by user"})
                st.success("Action logged.")
    actions_df = pd.DataFrame(st.session_state.actions, columns=["Timestamp","Action","Status"])
    st.subheader("Action log")
    if actions_df.empty:
        st.info("Log an action above to create an activity record.")
    else:
        st.dataframe(actions_df, use_container_width=True, hide_index=True)
        download_csv(actions_df, "ecodevice_actions.csv", "⬇️ Export eco-action log CSV")
        if st.button("Clear action log"):
            st.session_state.actions = []
            st.rerun()

with lab:
    st.subheader("Experiment Lab")
    st.write("Save a baseline, make one controlled change, refresh the system snapshot, and compare readings under similar conditions.")
    base, current = st.columns(2)
    old = st.session_state.baseline
    with base:
        st.markdown("#### 📌 Baseline")
        if old:
            st.metric("Baseline CPU", f'{old["cpu"]:.1f}%')
            st.metric("Baseline RAM", f'{old["ram"]:.1f}%')
            st.caption(old["timestamp"])
        else:
            st.info("Save a baseline to start an experiment.")
        if st.button("Save current snapshot as baseline"):
            st.session_state.baseline = {"timestamp":data["timestamp"],"cpu":data["cpu"],"ram":data["ram"],"ram_used_gb":data["ram_used_gb"],"process_count":len(processes)}
            st.success("Baseline saved.")
            st.rerun()
    with current:
        st.markdown("#### ⚡ Latest reading")
        st.metric("Latest CPU", f'{data["cpu"]:.1f}%')
        st.metric("Latest RAM", f'{data["ram"]:.1f}%')
        st.metric("Process count", len(processes))
    old = st.session_state.baseline
    if old:
        compare = pd.DataFrame([
            {"Metric":"CPU utilization (%)","Baseline":old["cpu"],"Latest":data["cpu"]},
            {"Metric":"RAM utilization (%)","Baseline":old["ram"],"Latest":data["ram"]},
            {"Metric":"RAM used (GB)","Baseline":old["ram_used_gb"],"Latest":data["ram_used_gb"]},
            {"Metric":"Process count","Baseline":old["process_count"],"Latest":len(processes)},
        ])
        compare["Change"] = (compare["Latest"] - compare["Baseline"]).round(2)
        fig = px.bar(compare, x="Metric", y=["Baseline","Latest"], barmode="group", title="Baseline vs latest snapshot",
                     color_discrete_sequence=["#397c59","#68d9a0"])
        chart_theme(fig, 360)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(compare, use_container_width=True, hide_index=True)
        st.caption("A lower reading is not proof of electricity savings.")
        experiment_name = st.text_input("Experiment name", placeholder="e.g. Closed unused browser tabs")
        notes = st.text_area("What did you change? Note other conditions too.")
        if st.button("Save experiment result", type="primary"):
            st.session_state.experiments.append({
                "Recorded at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Experiment":experiment_name.strip() or "Unnamed experiment","Notes":notes.strip(),
                "Baseline CPU (%)":old["cpu"],"Latest CPU (%)":data["cpu"],"CPU change (points)":round(data["cpu"]-old["cpu"],2),
                "Baseline RAM (%)":old["ram"],"Latest RAM (%)":data["ram"],"RAM change (points)":round(data["ram"]-old["ram"],2),
                "Baseline RAM used (GB)":old["ram_used_gb"],"Latest RAM used (GB)":data["ram_used_gb"],
                "Baseline process count":old["process_count"],"Latest process count":len(processes)})
            st.success("Experiment recorded.")
            st.rerun()
    exp_df = pd.DataFrame(st.session_state.experiments)
    st.subheader("Experiment records")
    if exp_df.empty:
        st.info("No experiments recorded yet.")
    else:
        st.dataframe(exp_df, use_container_width=True, hide_index=True)
        download_csv(exp_df, "ecodevice_experiments.csv", "⬇️ Export experiments CSV")

with sdg:
    st.subheader("SDG Impact Mapping")
    st.caption("Qualitative project contribution; this is not official SDG certification or measured impact.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🎓 SDG 4")
        st.markdown("**Quality Education**")
        st.write("Enables hands-on learning about operating-system resources, monitoring, charts and data interpretation.")
        st.progress(75, text="Learning & awareness")
    with c2:
        st.markdown("### 🏭 SDG 9")
        st.markdown("**Industry, Innovation and Infrastructure**")
        st.write("Demonstrates software-based resource monitoring and structured comparison for digital infrastructure.")
        st.progress(75, text="Monitoring innovation")
    with c3:
        st.markdown("### 🏙️ SDG 11")
        st.markdown("**Sustainable Cities and Communities**")
        st.write("Indirectly promotes responsible device-use habits and awareness of digital sustainability.")
        st.progress(50, text="Responsible-computing awareness")
    sdg_df = pd.DataFrame([
        {"SDG":"4 — Quality Education","Evidence to collect":"Demonstration, learning outcomes, experiment notes"},
        {"SDG":"9 — Industry, Innovation and Infrastructure","Evidence to collect":"Resource snapshots, charts, exported comparisons"},
        {"SDG":"11 — Sustainable Cities and Communities","Evidence to collect":"Logged actions and a discussion of indirect impact"},
    ])
    st.dataframe(sdg_df, use_container_width=True, hide_index=True)
    download_csv(sdg_df, "ecodevice_sdg_mapping.csv", "⬇️ Export SDG mapping CSV")
    st.info("SDG 11 is an indirect link. Present it as awareness and responsible digital behavior, not direct measured urban impact.")

st.divider()
st.subheader("📦 Export Center")
hist_df = pd.DataFrame(st.session_state.history, columns=["Timestamp","CPU utilization (%)","RAM utilization (%)","RAM used (GB)","Processes observed"])
e1, e2, e3, e4 = st.columns(4)
with e1:
    download_csv(hist_df, "ecodevice_history.csv", "Download history CSV")
with e2:
    download_csv(pd.DataFrame(st.session_state.actions, columns=["Timestamp","Action","Status"]), "ecodevice_actions.csv", "Download actions CSV")
with e3:
    download_csv(pd.DataFrame(st.session_state.experiments), "ecodevice_experiments.csv", "Download experiments CSV")
with e4:
    download_csv(pd.DataFrame([{"Timestamp":data["timestamp"],"CPU (%)":data["cpu"],"RAM (%)":data["ram"],"RAM used (GB)":data["ram_used_gb"],"RAM total (GB)":data["ram_total_gb"],"Processes":len(processes)}]), "ecodevice_current_snapshot.csv", "Download current snapshot")
st.caption("Records are held in the current Streamlit session. Export CSVs if you need to preserve them after closing the app.")
