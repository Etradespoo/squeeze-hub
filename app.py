import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as _time
from functools import lru_cache
from typing import Dict, Tuple, Optional
from zoneinfo import ZoneInfo
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PLACEHOLDER = "--"
DEFAULT_SYMBOL = "NVDA"
DEFAULT_TIMEFRAME_INDEX = 5  # "1M"
DEFAULT_MONTHS_BACK = 12
MARKET_CACHE_TTL = 300
STATIC_DATA_TTL = 3600

# Market configurations
MARKET_CONFIG = {
    "NY": {"tz": "America/New_York", "open": _time(9, 30), "close": _time(16, 0)},
    "London": {"tz": "Europe/London", "open": _time(8, 0), "close": _time(16, 30)},
    "Asian": {"tz": "Asia/Tokyo", "open": _time(9, 0), "close": _time(15, 0)},
}

# Page config
st.set_page_config(
    page_title="Stock Fundamentals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Styles
st.markdown("""
<style>
  .stApp { background-color:#1e1e2e; color:#cdd6f4; }

  /* Header */
  .main-header { text-align:center; padding:2rem 0 1.25rem 0; }
  .main-header h1 { color:#89b4fa; font-size:2.5rem; font-weight:700; margin:0 0 .5rem 0; letter-spacing:1px; }
  .main-header p { color:#a6adc8; margin:0; }

  /* Stats box */
  .universal-stats {
    position: fixed; top: 20px; right: 20px; background-color: #313244; border-radius: 8px;
    padding: 1.14rem; border: 1px solid #45475a; width: 305px; z-index: 9999;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  }
  .stats-title {
    color: #89b4fa; font-size: 0.92rem; font-weight: 600; margin-bottom: 0.5rem;
    text-align: center; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .timer-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
  .timer-row:last-child { margin-bottom: 0; }
  .timer-item { text-align: center; flex: 1; padding: 0 0.25rem; }
  .timer-label { color: #a6adc8; font-size: 0.75rem; font-weight: 500; display: block; margin-bottom: 0.1rem; }
  .timer-value { color: #a6e3a1; font-size: 0.75rem; font-weight: 600; font-family: monospace; display: block; }
  .timer-value.active { color: #b4f7b4; }

  /* Input styling */
  .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
    background:#45475a; color:#cdd6f4; border:1px solid #6c7086; border-radius:8px; height:40px;
  }
  .stTextInput > div > div > input, .stNumberInput > div > div > input { padding:.75rem; }
  .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
    border-color:#89b4fa; box-shadow:0 0 0 2px rgba(137,180,250,.2);
  }
  .stTextInput > label, .stSelectbox > label, .stNumberInput > label {
    color:#a6adc8; font-weight:500; margin-bottom:.5rem;
  }

  /* Button styling - PROPERLY CENTERED */
  div[data-testid="stButton"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 0.5rem 0 !important;
  }
  div[data-testid="stButton"] > button {
    width: 160px !important; 
    background-color: #a6e3a1 !important; 
    border-color: #a6e3a1 !important;
    color: #0b0f14 !important; 
    font-weight: 600 !important; 
    font-size: 0.85rem !important;
    border-radius: 7px !important; 
    padding: 0.42rem 0.9rem !important;
  }
  div[data-testid="stButton"] > button:hover { 
    filter: brightness(0.95); 
  }

  /* Section styling */
  h3 { color:#89b4fa; margin:1.25rem 0 .75rem 0; }
  .section-divider { border:none; border-top:1px solid #45475a; margin:2rem 0 1.25rem 0; }
  .stDataFrame { background:transparent; }
  .stDataFrame, .stDataFrame * { border:none !important; }
</style>
""", unsafe_allow_html=True)

# Market timing functions
@lru_cache(maxsize=128)
def calculate_next_market_open(market_name: str, _h: int, _m: int, _wd: int) -> Tuple[bool, Optional[int]]:
    """Calculate market status and time until next open."""
    try:
        now_et = datetime.now(ZoneInfo("America/New_York"))
        config = MARKET_CONFIG.get(market_name)
        if not config:
            return False, None

        tz = ZoneInfo(config["tz"])
        now_local = now_et.astimezone(tz)
        
        # Skip weekends
        if now_local.weekday() > 4:
            next_day = now_local + timedelta(days=(7 - now_local.weekday()))
            next_open = datetime.combine(next_day.date(), config["open"], tzinfo=tz)
            return False, _minutes_until(next_open.astimezone(ZoneInfo("America/New_York")), now_et)

        local_open = datetime.combine(now_local.date(), config["open"], tzinfo=tz)
        local_close = datetime.combine(now_local.date(), config["close"], tzinfo=tz)

        if now_local < local_open:
            return False, _minutes_until(local_open.astimezone(ZoneInfo("America/New_York")), now_et)
        elif local_open <= now_local <= local_close:
            return True, None
        else:
            # Market closed, find next business day
            next_day = now_local + timedelta(days=1)
            while next_day.weekday() > 4:
                next_day += timedelta(days=1)
            next_open = datetime.combine(next_day.date(), config["open"], tzinfo=tz)
            return False, _minutes_until(next_open.astimezone(ZoneInfo("America/New_York")), now_et)

    except Exception as e:
        logger.error(f"Market calculation failed for {market_name}: {e}")
        return False, None

def _minutes_until(target_dt: datetime, now_dt: datetime) -> int:
    """Helper to calculate minutes between two datetime objects."""
    return max(0, int((target_dt - now_dt).total_seconds() // 60))

@st.cache_data(ttl=MARKET_CACHE_TTL)
def get_session_times() -> Dict[str, str]:
    """Get current market session times."""
    try:
        now = datetime.now()
        results = {}
        
        for market in MARKET_CONFIG.keys():
            is_open, minutes_until = calculate_next_market_open(
                market, now.hour, now.minute, now.weekday()
            )
            
            if is_open:
                results[market] = "Now"
                results[f"{market}_active"] = True
            else:
                results[market] = _format_duration(minutes_until)
                results[f"{market}_active"] = False
                
        return results
    except Exception as e:
        logger.error(f"Session times calculation failed: {e}")
        return {market: "Error" for market in MARKET_CONFIG.keys()} | \
               {f"{market}_active": False for market in MARKET_CONFIG.keys()}

def _format_duration(minutes: Optional[int]) -> str:
    """Format minutes into readable duration."""
    if not minutes or minutes <= 0:
        return "Now"
    
    days, remainder = divmod(minutes, 1440)
    hours, mins = divmod(remainder, 60)
    
    return f"{days}d {hours:02d}:{mins:02d}" if days else f"{hours:02d}:{mins:02d}"

@st.cache_data(ttl=STATIC_DATA_TTL)
def get_economic_calendar() -> Dict[str, str]:
    """Get economic calendar data (placeholder)."""
    return {"FOMC": "TBD", "NFP": "TBD", "CPI": "TBD"}

@st.cache_data(ttl=STATIC_DATA_TTL)
def get_dataframes(symbol: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate placeholder dataframes for the dashboard."""
    squeeze_df = pd.DataFrame({
        "Compression": ["Red Squeeze", "Black Squeeze", "Total"],
        "Total Squeezes": [PLACEHOLDER] * 3,
        "Fired Long": [PLACEHOLDER] * 3,
        "Fired Short": [PLACEHOLDER] * 3,
        "Avg Length of Squeeze": [PLACEHOLDER] * 3,
        "Avg Move Length": [PLACEHOLDER] * 3,
        "Avg Move %": [PLACEHOLDER] * 3,
        "% Fire w/ Trend": [PLACEHOLDER] * 3
    })
    
    fundamental_df = pd.DataFrame({
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
    
    options_df = pd.DataFrame({
        "Implied Volatility": [PLACEHOLDER],
        "Liquidity": [PLACEHOLDER],
        "Short Interest": [PLACEHOLDER],
        "Days to Cover": [PLACEHOLDER],
        "Total Open Interest": [PLACEHOLDER]
    })
    
    return squeeze_df, fundamental_df, options_df

# UI Components
def render_header():
    """Render the main dashboard header."""
    st.markdown("""
    <div class="main-header">
      <h1>Stock Fundamentals Dashboard</h1>
      <p>Clean, minimal analysis for your trading strategy</p>
    </div>
    """, unsafe_allow_html=True)

def render_stats_box(session_times: Dict[str, str], economic_data: Dict[str, str]):
    """Render the fixed position stats box."""
    html = '<div class="universal-stats"><div class="stats-title">Date Until</div>'
    
    # Economic events row
    html += '<div class="timer-row">'
    for event in ["FOMC", "NFP", "CPI"]:
        html += f'''<div class="timer-item">
            <div class="timer-label">{event}</div>
            <div class="timer-value">{economic_data[event]}</div>
        </div>'''
    html += '</div>'
    
    # Market sessions row
    html += '<div class="timer-row">'
    for market in MARKET_CONFIG.keys():
        active_class = ' active' if session_times.get(f'{market}_active', False) else ''
        html += f'''<div class="timer-item">
            <div class="timer-label">{market}</div>
            <div class="timer-value{active_class}">{session_times[market]}</div>
        </div>'''
    html += '</div></div>'
    
    st.markdown(html, unsafe_allow_html=True)

def render_inputs() -> Tuple[str, str, int]:
    """Render input controls and return values."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        symbol = st.text_input(
            "Stock Symbol", 
            value=DEFAULT_SYMBOL, 
            placeholder="e.g., AAPL, TSLA", 
            max_chars=10
        )
        
    with col2:
        timeframe = st.selectbox(
            "Timeframe", 
            ["30m", "1h", "4h", "1D", "1W", "1M", "3M", "6M", "1Y"], 
            index=DEFAULT_TIMEFRAME_INDEX
        )
        
    with col3:
        months_back = st.number_input(
            "Months Back", 
            min_value=1, 
            max_value=60, 
            value=DEFAULT_MONTHS_BACK, 
            step=1
        )
    
    return symbol.upper() if symbol else DEFAULT_SYMBOL, timeframe, months_back

def render_tables(symbol: str):
    """Render all data tables."""
    squeeze_df, fundamental_df, options_df = get_dataframes(symbol)
    
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    
    st.markdown("### Squeeze Data")
    st.dataframe(squeeze_df, use_container_width=True, hide_index=True)
    
    st.markdown("### Fundamental Analysis")
    st.dataframe(fundamental_df, use_container_width=True, hide_index=True)
    
    st.markdown("### Options & Interest Data")
    st.dataframe(options_df, use_container_width=True, hide_index=True)

def main():
    """Main application function."""
    render_header()
    
    # Get dynamic data
    session_times = get_session_times()
    economic_data = get_economic_calendar()
    render_stats_box(session_times, economic_data)
    
    # Input controls
    symbol, timeframe, months_back = render_inputs()
    
    # Create a new full-width container for the button
    # This breaks out of the column context and centers the button properly
    button_container = st.container()
    with button_container:
        # Use columns with specific ratios to center the button
        col1, col2, col3 = st.columns([5, 2, 5])
        with col2:
            if st.button("Go", type="primary", use_container_width=True):
                st.rerun()  # Optional: trigger a rerun when clicked
    
    # Data tables
    render_tables(symbol)

if __name__ == "__main__":
    main()