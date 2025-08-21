import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
    
    /* Universal stats styling - compact top right box */
    .universal-stats {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #313244;
        border-radius: 8px;
        padding: 0.75rem;
        border: 1px solid #45475a;
        width: 200px;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .stats-title {
        color: #89b4fa;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .timer-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    
    .timer-row:last-child {
        margin-bottom: 0;
    }
    
    .timer-item {
        text-align: center;
        flex: 1;
        padding: 0 0.25rem;
    }
    
    .timer-label {
        color: #a6adc8;
        font-size: 0.65rem;
        font-weight: 500;
        display: block;
        margin-bottom: 0.1rem;
    }
    
    .timer-value {
        color: #a6e3a1;
        font-size: 0.65rem;
        font-weight: 600;
        font-family: monospace;
        display: block;
    }
    
    /* Input section styling */
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
    try:
        now = datetime.now()
        
        # Simplified session times (approximated for demo)
        ny_open = now.replace(hour=9, minute=30, second=0, microsecond=0)  # 9:30 AM EST
        london_open = now.replace(hour=8, minute=0, second=0, microsecond=0)  # 8:00 AM GMT
        asian_open = now.replace(hour=23, minute=0, second=0, microsecond=0)  # 11:00 PM (Asian open)
        
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
    except:
        # Fallback values if calculation fails
        return {
            "NY": "10:28",
            "London": "08:55", 
            "Asian": "23:58"
        }

# Header
st.markdown("""
<div class="main-header">
    <h1>Stock Fundamentals Dashboard</h1>
    <p>Clean, minimal analysis for your trading strategy</p>
</div>
""", unsafe_allow_html=True)

# Universal Stats Box (top right corner)
session_times = get_session_times()
st.markdown(f"""
<div class="universal-stats">
    <div class="stats-title">Date Until</div>
    <div class="timer-row">
        <div class="timer-item">
            <div class="timer-label">FOMC</div>
            <div class="timer-value">00:00</div>
        </div>
        <div class="timer-item">
            <div class="timer-label">NFP</div>
            <div class="timer-value">00:00</div>
        </div>
        <div class="timer-item">
            <div class="timer-label">CPI</div>
            <div class="timer-value">00:00</div>
        </div>
    </div>
    <div class="timer-row">
        <div class="timer-item">
            <div class="timer-label">NY</div>
            <div class="timer-value">{session_times['NY']}</div>
        </div>
        <div class="timer-item">
            <div class="timer-label">London</div>
            <div class="timer-value">{session_times['London']}</div>
        </div>
        <div class="timer-item">
            <div class="timer-label">Asian</div>
            <div class="timer-value">{session_times['Asian']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

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

# Create sample dataframe structure for Squeeze Data
squeeze_data = {
    "Compression": ["Red Squeeze", "Black Squeeze", "Total"],
    "Total Squeezes": ["Empty", "Empty", "Empty"],
    "Fired Long": ["Empty", "Empty", "Empty"],
    "Fired Short": ["Empty", "Empty", "Empty"],
    "Avg Length of Squeeze": ["Empty", "Empty", "Empty"],
    "Avg Move Length": ["Empty", "Empty", "Empty"],
    "Avg Move %": ["Empty", "Empty", "Empty"],
    "% Fire w/ Trend": ["Empty", "Empty", "Empty"]
}

df_squeeze = pd.DataFrame(squeeze_data)

# Create dataframe for Fundamental Analysis
fundamental_data = {
    "% Change (3 Years)": ["Empty"],
    "% Change (1 Year)": ["Empty"],
    "% Change (3 Months)": ["Empty"],
    "% Change (1 Month)": ["Empty"],
    "% Change (10 Days)": ["Empty"],
    "EPS Growth (Quarterly)": ["Empty"],
    "EPS Growth (Annual)": ["Empty"],
    "Revenue Growth (Quarterly)": ["Empty"],
    "Revenue Growth (Annual)": ["Empty"],
    "Upcoming Earnings Date": ["Empty"]
}

df_fundamental = pd.DataFrame(fundamental_data)

# Create dataframe for Options & Interest Data
options_data = {
    "Implied Volatility": ["Empty"],
    "Liquidity": ["Empty"],
    "Short Interest": ["Empty"],
    "Days to Cover": ["Empty"],
    "Total Open Interest": ["Empty"]
}

df_options = pd.DataFrame(options_data)

# Squeeze Data Table
st.markdown("### 🎯 Squeeze Data")

# Display the squeeze dataframe
st.dataframe(
    df_squeeze,
    use_container_width=True,
    hide_index=True
)

# Fundamental Analysis Table
st.markdown("### 📊 Fundamental Analysis")

# Display the fundamental dataframe
st.dataframe(
    df_fundamental,
    use_container_width=True,
    hide_index=True
)

# Options & Interest Data Table
st.markdown("### 📈 Options & Interest Data")

# Display the options dataframe
st.dataframe(
    df_options,
    use_container_width=True,
    hide_index=True
)

# Footer space
st.markdown("<br><br>", unsafe_allow_html=True)