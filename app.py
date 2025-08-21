import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Page configuration
st.set_page_config(
    page_title="Stock Fundamentals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #89b4fa;
        font-size: 2.5rem;
        font-weight: 300;
        margin-bottom: 0.5rem;
        letter-spacing: 1px;
    }
    
    .main-header p {
        color: #a6adc8;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Universal stats styling */
    .universal-stats {
        background-color: #313244;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #45475a;
    }
    
    .stat-item {
        text-align: center;
        padding: 0.5rem;
    }
    
    .stat-label {
        color: #a6adc8;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stat-value {
        color: #cdd6f4;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Session clocks styling */
    .session-clocks {
        background-color: #313244;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #45475a;
    }
    
    .clock-item {
        text-align: center;
        padding: 0.5rem;
    }
    
    .clock-session {
        color: #89b4fa;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .clock-time {
        color: #a6e3a1;
        font-size: 1.0rem;
        font-weight: 500;
    }
    
    .clock-subtitle {
        color: #a6adc8;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
    .input-container {
        background-color: #313244;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 3rem;
        border: 1px solid #45475a;
    }
    
    /* Custom input styling */
    .stTextInput > div > div > input {
        background-color: #45475a;
        color: #cdd6f4;
        border: 1px solid #6c7086;
        border-radius: 8px;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #89b4fa;
        box-shadow: 0 0 0 2px rgba(137, 180, 250, 0.2);
    }
    
    .stSelectbox > div > div > div {
        background-color: #45475a;
        color: #cdd6f4;
        border: 1px solid #6c7086;
        border-radius: 8px;
    }
    
    .stNumberInput > div > div > input {
        background-color: #45475a;
        color: #cdd6f4;
        border: 1px solid #6c7086;
        border-radius: 8px;
        padding: 0.75rem;
    }
    
    /* Table styling */
    .table-container {
        background-color: #313244;
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #45475a;
        margin-top: 2rem;
    }
    
    .stDataFrame {
        background-color: transparent;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Input labels */
    .stTextInput > label, .stSelectbox > label, .stNumberInput > label {
        color: #a6adc8;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to calculate time until market sessions
def get_session_times():
    now = datetime.now(pytz.UTC)
    
    # Session times (market open times in UTC)
    ny_open = now.replace(hour=14, minute=30, second=0, microsecond=0)  # 9:30 AM EST
    london_open = now.replace(hour=8, minute=0, second=0, microsecond=0)  # 8:00 AM GMT
    asian_open = now.replace(hour=0, minute=0, second=0, microsecond=0)  # 9:00 AM JST (previous day)
    
    # If session time has passed today, add a day
    if now > ny_open:
        ny_open += timedelta(days=1)
    if now > london_open:
        london_open += timedelta(days=1)
    if now > asian_open:
        asian_open += timedelta(days=1)
    
    # Calculate time differences
    ny_delta = ny_open - now
    london_delta = london_open - now
    asian_delta = asian_open - now
    
    def format_delta(delta):
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    
    return {
        "NY": format_delta(ny_delta),
        "London": format_delta(london_delta),
        "Asian": format_delta(asian_delta)
    }

# Header
st.markdown("""
<div class="main-header">
    <h1>Stock Fundamentals Dashboard</h1>
    <p>Clean, minimal analysis for your trading strategy</p>
</div>
""", unsafe_allow_html=True)

# Universal Stats Section
st.markdown('<div class="universal-stats">', unsafe_allow_html=True)
st.markdown("**Universal Stats**")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div class="stat-item">
        <div class="stat-label">Date Until</div>
        <div class="stat-value">Empty</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-item">
        <div class="stat-label">FOMC</div>
        <div class="stat-value">Empty</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-item">
        <div class="stat-label">NFP</div>
        <div class="stat-value">Empty</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-item">
        <div class="stat-label">CPI</div>
        <div class="stat-value">Empty</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    # Session clocks in the 5th column
    session_times = get_session_times()
    st.markdown(f"""
    <div class="clock-item">
        <div class="clock-session">Market Sessions</div>
        <div class="clock-time">NY: {session_times['NY']}</div>
        <div class="clock-time">LON: {session_times['London']}</div>
        <div class="clock-time">ASIA: {session_times['Asian']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input section
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    symbol = st.text_input(
        "Stock Symbol",
        value="NVDA",
        placeholder="Enter symbol (e.g., AAPL, TSLA)",
        help="Enter the stock ticker symbol"
    )

with col2:
    timeframe = st.selectbox(
        "Timeframe",
        options=["30m", "1h", "4h", "1D", "1W", "1M", "3M", "6M", "1Y"],
        index=5,
        help="Select the chart timeframe"
    )

with col3:
    months_back = st.number_input(
        "Months Back",
        min_value=1,
        max_value=60,
        value=12,
        help="Number of months of historical data"
    )

# Create sample dataframe structure
table_data = {
    "Metric": ["Revenue Growth", "Profit Margin", "Strategy Score"],
    "Current": ["Empty", "Empty", "Empty"],
    "1M Ago": ["Empty", "Empty", "Empty"],
    "3M Ago": ["Empty", "Empty", "Empty"],
    "6M Ago": ["Empty", "Empty", "Empty"],
    "1Y Ago": ["Empty", "Empty", "Empty"],
    "Trend": ["Empty", "Empty", "Empty"]
}

df = pd.DataFrame(table_data)

# Table section
st.markdown("### 📈 Fundamentals Analysis")

# Display the dataframe with custom styling
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# Footer space
st.markdown("<br><br>", unsafe_allow_html=True)