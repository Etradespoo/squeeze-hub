import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

# Market schedules (all times in ET)
MARKET_SCHEDULES = {
    "NY": {
        "open": (9, 30),
        "close": (16, 0),
        "days": list(range(5)),  # Monday-Friday
        "name": "NYSE"
    },
    "London": {
        "open": (3, 0),
        "close": (11, 30),
        "days": list(range(5)),  # Monday-Friday
        "name": "LSE"
    },
    "Asian": {
        "open": (19, 0),
        "close": (1, 0),
        "days": [6, 0, 1, 2, 3, 4],  # Sunday-Friday
        "name": "Tokyo"
    }
}

# Time constants
WEEKEND_TO_MONDAY = 3
SATURDAY_TO_MONDAY = 2
SUNDAY_TO_MONDAY = 1
NEXT_TRADING_DAY = 1

# UI Constants
PLACEHOLDER = "--"
DEFAULT_SYMBOL = "NVDA"
DEFAULT_TIMEFRAME_INDEX = 5  # "1M"
DEFAULT_MONTHS_BACK = 12

# Cache TTL (5 minutes for market times, longer for static data)
MARKET_CACHE_TTL = 300
STATIC_DATA_TTL = 3600

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Stock Fundamentals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# OPTIMIZED CSS (Consolidated and Minimized)
# ============================================================================

DASHBOARD_CSS = """
<style>
    /* Core Theme */
    .stApp { background-color: #1e1e2e; color: #cdd6f4; }
    
    /* Header */
    .main-header { text-align: center; padding: 2rem 0; margin-bottom: 2rem; }
    .main-header h1 { color: #89b4fa; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 1px; }
    .main-header p { color: #a6adc8; font-size: 1.1rem; margin: 0; }
    
    /* Universal Stats Box */
    .universal-stats {
        position: fixed; top: 20px; right: 20px;
        background-color: #313244; border-radius: 8px;
        padding: 1.14rem; border: 1px solid #45475a;
        width: 305px; z-index: 9999;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stats-title { color: #89b4fa; font-size: 0.92rem; font-weight: 600; margin-bottom: 0.5rem; text-align: center; text-transform: uppercase; letter-spacing: 0.5px; }
    .timer-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
    .timer-row:last-child { margin-bottom: 0; }
    .timer-item { text-align: center; flex: 1; padding: 0 0.25rem; }
    .timer-label { color: #a6adc8; font-size: 0.75rem; font-weight: 500; display: block; margin-bottom: 0.1rem; }
    .timer-value { color: #a6e3a1; font-size: 0.75rem; font-weight: 600; font-family: monospace; display: block; }
    .timer-value.active { color: #b4f7b4; }
    
    /* Input Styling */
    .input-container { background-color: #313244; border-radius: 12px; padding: 2rem; margin-bottom: 3rem; border: 1px solid #45475a; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background-color: #45475a; color: #cdd6f4;
        border: 1px solid #6c7086; border-radius: 8px;
        padding: 0.75rem; height: 40px;
    }
    .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
        border-color: #89b4fa;
        box-shadow: 0 0 0 2px rgba(137, 180, 250, 0.2);
    }
    .stSelectbox > div > div > div {
        background-color: #45475a; color: #cdd6f4;
        border: 1px solid #6c7086; border-radius: 8px; height: 40px;
    }
    
    /* Table Styling */
    .table-container { background-color: #313244; border-radius: 12px; padding: 2rem; border: 1px solid #45475a; margin-top: 2rem; }
    .stDataFrame { background-color: transparent; }
    
    /* Consolidated border removal for dataframes */
    .stDataFrame, .stDataFrame *, 
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] > div,
    .stDataFrame table, .stDataFrame thead, 
    .stDataFrame tbody, .stDataFrame tr, 
    .stDataFrame td, .stDataFrame th {
        border-bottom: none !important;
        border: none !important;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Labels */
    .stTextInput > label, .stSelectbox > label, .stNumberInput > label {
        color: #a6adc8; font-weight: 500; margin-bottom: 0.5rem;
    }
</style>
"""

st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

# ============================================================================
# OPTIMIZED MARKET TIME CALCULATIONS
# ============================================================================

@lru_cache(maxsize=128)
def calculate_next_market_open(market_name: str, current_hour: int, current_minute: int, 
                              current_weekday: int) -> Tuple[bool, Optional[int]]:
    """
    Calculate if market is open and minutes until next open.
    Cached by input parameters to avoid recalculation.
    
    Returns: (is_open, minutes_until_next_open)
    """
    schedule = MARKET_SCHEDULES.get(market_name)
    if not schedule:
        return False, None
    
    open_hour, open_minute = schedule["open"]
    close_hour, close_minute = schedule["close"]
    
    # Convert current time to minutes since midnight
    current_minutes = current_hour * 60 + current_minute
    open_minutes = open_hour * 60 + open_minute
    close_minutes = close_hour * 60 + close_minute
    
    # Special handling for Asian market (crosses midnight)
    if market_name == "Asian":
        if current_weekday == 6 and current_minutes >= open_minutes:  # Sunday evening
            return True, None
        elif current_weekday in range(5):  # Monday-Friday
            if current_minutes <= close_minutes or current_minutes >= open_minutes:
                return True, None
    else:
        # Standard markets (NY, London)
        if current_weekday in schedule["days"]:
            if open_minutes <= current_minutes <= close_minutes:
                return True, None
    
    # Calculate minutes until next open
    minutes_to_next = calculate_minutes_to_next_open(
        market_name, current_weekday, current_minutes, open_minutes
    )
    
    return False, minutes_to_next

def calculate_minutes_to_next_open(market_name: str, weekday: int, 
                                  current_minutes: int, open_minutes: int) -> int:
    """Calculate minutes until next market open."""
    schedule = MARKET_SCHEDULES[market_name]
    
    # If it's a trading day and before open
    if weekday in schedule["days"] and current_minutes < open_minutes:
        return open_minutes - current_minutes
    
    # Calculate days until next trading day
    if weekday == 4:  # Friday
        days_ahead = WEEKEND_TO_MONDAY
    elif weekday == 5:  # Saturday
        days_ahead = SATURDAY_TO_MONDAY
    elif weekday == 6:  # Sunday
        if market_name == "Asian" and current_minutes < open_minutes:
            return open_minutes - current_minutes  # Opens Sunday evening
        days_ahead = SUNDAY_TO_MONDAY
    else:  # Monday-Thursday
        days_ahead = NEXT_TRADING_DAY
    
    # Convert to minutes
    return (days_ahead * 1440) + open_minutes - current_minutes

@st.cache_data(ttl=MARKET_CACHE_TTL)
def get_session_times() -> Dict[str, str]:
    """
    Get formatted time until market sessions.
    Cached for 5 minutes to reduce computation.
    """
    try:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()
        
        results = {}
        
        for market in ["NY", "London", "Asian"]:
            is_open, minutes_until = calculate_next_market_open(
                market, current_hour, current_minute, current_weekday
            )
            
            if is_open:
                results[market] = "Now"
                results[f"{market}_active"] = True
            else:
                results[market] = format_time_duration(minutes_until)
                results[f"{market}_active"] = False
        
        return results
        
    except Exception as e:
        logger.error(f"Market time calculation failed: {e}")
        return {
            "NY": "Error", "London": "Error", "Asian": "Error",
            "NY_active": False, "London_active": False, "Asian_active": False
        }

def format_time_duration(minutes: Optional[int]) -> str:
    """Format minutes into readable duration."""
    if minutes is None or minutes <= 0:
        return "Now"
    
    days = minutes // 1440
    hours = (minutes % 1440) // 60
    mins = minutes % 60
    
    if days > 0:
        return f"{days}d {hours:02d}:{mins:02d}"
    return f"{hours:02d}:{mins:02d}"

# ============================================================================
# ECONOMIC CALENDAR (Placeholder)
# ============================================================================

@st.cache_data(ttl=STATIC_DATA_TTL)
def get_economic_calendar() -> Dict[str, str]:
    """
    Get economic calendar data.
    TODO: Implement actual data source integration.
    """
    return {"FOMC": "TBD", "NFP": "TBD", "CPI": "TBD"}

# ============================================================================
# DATA CREATION (Optimized with module-level caching)
# ============================================================================

# Pre-create static DataFrames at module level
SQUEEZE_DATA = pd.DataFrame({
    "Compression": ["Red Squeeze", "Black Squeeze", "Total"],
    "Total Squeezes": [PLACEHOLDER] * 3,
    "Fired Long": [PLACEHOLDER] * 3,
    "Fired Short": [PLACEHOLDER] * 3,
    "Avg Length of Squeeze": [PLACEHOLDER] * 3,
    "Avg Move Length": [PLACEHOLDER] * 3,
    "Avg Move %": [PLACEHOLDER] * 3,
    "% Fire w/ Trend": [PLACEHOLDER] * 3
})

FUNDAMENTAL_DATA = pd.DataFrame({
    "% Change (3 Years)": [PLACEHOLDER],
    "% Change (1 Year)": [PLACEHOLDER],
    "% Change (3 Months)": [PLACEHOLDER],
    "% Change (1 Month)": [PLACEHOLDER],
    "% Change (10 Days)": [PLACEHOLDER],
    "EPS Growth (Quarterly)": [PLACEHOLDER],
    "EPS Growth (Annual)": [PLACEHOLDER],
    "Revenue Growth (Quarterly)": [PLACEHOLDER],
    "Revenue Growth (Annual)": [PLACEHOLDER],
    "Upcoming Earnings Date": [PLACEHOLDER]
})

OPTIONS_DATA = pd.DataFrame({
    "Implied Volatility": [PLACEHOLDER],
    "Liquidity": [PLACEHOLDER],
    "Short Interest": [PLACEHOLDER],
    "Days to Cover": [PLACEHOLDER],
    "Total Open Interest": [PLACEHOLDER]
})

@st.cache_data(ttl=STATIC_DATA_TTL)
def get_dataframes(symbol: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Get dataframes for display. In production, would fetch real data based on symbol.
    Returns copies to prevent mutation.
    """
    # In production, fetch real data based on symbol
    # For now, return copies of static data
    return SQUEEZE_DATA.copy(), FUNDAMENTAL_DATA.copy(), OPTIONS_DATA.copy()

# ============================================================================
# UI RENDERING
# ============================================================================

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>Stock Fundamentals Dashboard</h1>
        <p>Clean, minimal analysis for your trading strategy</p>
    </div>
    """, unsafe_allow_html=True)

def render_stats_box(session_times: Dict[str, str], economic_data: Dict[str, str]):
    """Render the universal stats box."""
    # Build HTML using string concatenation (more efficient than f-strings for static content)
    html = '<div class="universal-stats"><div class="stats-title">Date Until</div>'
    
    # Economic data row
    html += '<div class="timer-row">'
    for key in ["FOMC", "NFP", "CPI"]:
        html += f'''<div class="timer-item">
            <div class="timer-label">{key}</div>
            <div class="timer-value">{economic_data[key]}</div>
        </div>'''
    html += '</div>'
    
    # Market times row
    html += '<div class="timer-row">'
    for market in ["NY", "London", "Asian"]:
        active_class = ' active' if session_times.get(f'{market}_active', False) else ''
        html += f'''<div class="timer-item">
            <div class="timer-label">{market}</div>
            <div class="timer-value{active_class}">{session_times[market]}</div>
        </div>'''
    html += '</div></div>'
    
    st.markdown(html, unsafe_allow_html=True)

def render_input_section() -> Tuple[str, str, int]:
    """Render input controls and return values."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        symbol = st.text_input(
            "Stock Symbol",
            value=DEFAULT_SYMBOL,
            placeholder="Enter symbol (e.g., AAPL, TSLA)",
            help="Enter the stock ticker symbol",
            max_chars=10,
            key="symbol_input"
        )
        # Only uppercase if not empty
        symbol = symbol.upper() if symbol else DEFAULT_SYMBOL
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe",
            options=["30m", "1h", "4h", "1D", "1W", "1M", "3M", "6M", "1Y"],
            index=DEFAULT_TIMEFRAME_INDEX,
            help="Select the chart timeframe",
            key="timeframe_select"
        )
    
    with col3:
        months_back = st.number_input(
            "Months Back",
            min_value=1,
            max_value=60,
            value=DEFAULT_MONTHS_BACK,
            step=1,
            help="Number of months of historical data",
            key="months_input"
        )
    
    return symbol, timeframe, months_back

def render_data_tables(symbol: str):
    """Render the data tables."""
    # Get dataframes
    df_squeeze, df_fundamental, df_options = get_dataframes(symbol)
    
    # Calculate optimal heights based on content
    squeeze_height = min(50 + len(df_squeeze) * 35, 200)
    
    # Squeeze Data
    st.markdown("### Squeeze Data")
    st.dataframe(
        df_squeeze,
        use_container_width=True,
        hide_index=True,
        height=squeeze_height
    )
    
    # Fundamental Analysis
    st.markdown("### Fundamental Analysis")
    st.dataframe(
        df_fundamental,
        use_container_width=True,
        hide_index=True,
        height=80  # Single row
    )
    
    # Options & Interest Data
    st.markdown("### Options & Interest Data")
    st.dataframe(
        df_options,
        use_container_width=True,
        hide_index=True,
        height=80  # Single row
    )

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Render header
    render_header()
    
    # Get market and economic data
    session_times = get_session_times()
    economic_data = get_economic_calendar()
    
    # Render stats box
    render_stats_box(session_times, economic_data)
    
    # Render input section and get values
    symbol, timeframe, months_back = render_input_section()
    
    # Store in session state for persistence
    if 'symbol' not in st.session_state:
        st.session_state.symbol = symbol
    if 'timeframe' not in st.session_state:
        st.session_state.timeframe = timeframe
    if 'months_back' not in st.session_state:
        st.session_state.months_back = months_back
    
    # Render data tables
    render_data_tables(symbol)
    
    # Footer space
    st.markdown("<br><br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()