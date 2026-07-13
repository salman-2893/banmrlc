import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ==============================================================================
# 1. SECURITY CONFIGURATION (User & Password Setup)
# ==============================================================================
VALID_USERNAME = "MRLC1"
VALID_PASSWORD = "BanLogCoy@33" 

def check_password():
    """Returns True if the user has entered the correct credentials."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Display clean login screen panel
    st.title("🎖️ Contingent Portal Secure Login")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    with col2:
        user_input = st.text_input("Username / ID", key="username_box")
        pass_input = st.text_input("Password", type="password", key="password_box")
        
        if st.button("Access Dashboard", type="primary", use_container_width=True):
            if user_input == VALID_USERNAME and pass_input == VALID_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password. Please try again.")
    return False

# Stop execution and render login panel if validation check fails
if not check_password():
    st.stop()

# ==============================================================================
# 2. PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Log Coy Contingent Portal",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection for phone & WhatsApp click-actions
st.markdown("""
    <style>
    .contact-btn {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px 6px 4px 0px;
        border-radius: 4px;
        color: white !important;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        text-align: center;
    }
    .btn-wa { background-color: #25D366; }
    .btn-tel { background-color: #007bff; }
    .contact-btn:hover { opacity: 0.9; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

COLUMN_LIST = [
    'timestamp', 'no', 'rk', 'trade', 'first', 'mid', 'last', 'full', 'bangla', 
    'email', 'phone', 'emgno', 'passno', 'passval', 'nid', 'bday', 'bplace', 
    'ret', 'joincon', 'last3', 'photo', 'joinsvc', 'svc', 'msn', 'bg ', 'appt', 
    'course', 'license', 'ht', 'emgrel', 'wife', 'child', 'wt', 'unit', 'home', 
    'ident', 'Contgt'
]

TARGET_SPREADSHEET = "https://docs.google.com/spreadsheets/d/1KyXeyMjlN8nPi6xKKgeJsy-d8p_npcBa002B1yOIB9Y/export?format=csv"

# ==============================================================================
# 3. LIVE DATABASE INGESTION ENGINE
# ==============================================================================
@st.cache_data(ttl=5)
def fetch_live_data():
    try:
        data = pd.read_csv(TARGET_SPREADSHEET)
        for col in COLUMN_LIST:
            if col not in data.columns:
                data[col] = ""
        data = data[COLUMN_LIST]
        data = data.dropna(subset=['no'])
        return data
    except Exception as e:
        st.error(f"Data Fetch Failure: {e}")
        return pd.DataFrame(columns=COLUMN_LIST)

df_master = fetch_live_data()

if not df_master.empty:
    df_master['no'] = df_master['no'].astype(str)
    df_master['phone'] = df_master['phone'].astype(str).apply(lambda x: x[:-2] if x.endswith('.0') else x)

# ==============================================================================
# 4. E-COMMERCE STYLE MULTI-SELECT FILTER SIDEBAR
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/military-rank.png", width=70)
st.sidebar.title("Filter Options")

# Logout button inside sidebar
if st.sidebar.button("🔒 Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🛍️ Filter Profiles")

# Filter 1: Unit Roster Selection Matrix
all_units = sorted(list(df_master['unit'].dropna().astype(str).unique()))
sel_units = st.sidebar.multiselect("Select Units / Sub-Units", options=all_units, placeholder="All Sub-Units Active")

# Filter 2: Ranks Profile Filter
all_ranks = sorted(list(df_master['rk'].dropna().astype(str).unique()))
sel_ranks = st.sidebar.multiselect("Select Ranks (Rk)", options=all_ranks, placeholder="All Ranks Active")

# Filter 3: Trade / Corps Profile Filter
all_trades = sorted(list(df_master['trade'].dropna().astype(str).unique()))
sel_trades = st.sidebar.multiselect("Select Trades", options=all_trades, placeholder="All Trades Active")

# Filter 4: License Selection
all_licenses = sorted(list(df_master['license'].dropna().astype(str).unique()))
sel_licenses = st.sidebar.multiselect("Select Driver Licenses", options=all_licenses, placeholder="All Driver Licences Active")

# Execution of filtering multi-select logic mapping arrays
filtered_df = df_master.copy()

if sel_units:
    filtered_df = filtered_df[filtered_df['unit'].isin(sel_units)]
if sel_ranks:
    filtered_df = filtered_df[filtered_df['rk'].isin(sel_ranks)]
if sel_trades:
    filtered_df = filtered_df[filtered_df['trade'].isin(sel_trades)]
if sel_licenses:
    filtered_df = filtered_df[filtered_df['license'].isin(sel_licenses)]

# Text Search Input Box (Global Text Search Filter Bar)
search_query = st.text_input("🔍 Global Search (Type Name, Army No, Appt, or District to find results instantly):", "")
if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[
        filtered_df['full'].astype(str).str.lower().str.contains(q) |
        filtered_df['no'].astype(str).str.lower().str.contains(q) |
        filtered_df['appt'].astype(str).str.lower().str.contains(q) |
        filtered_df['home'].astype(str).str.lower().str.contains(q)
    ]

# ==============================================================================
# 5. FIXED FPDF2 REPORT GENERATION TOOL (Strict Streamlit Bytes Compliance)
# ==============================================================================
def compile_pdf_report(dataframe):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    
    # PDF Headers Layout
    pdf.cell(0, 10, "Filtered Contingent Operations Summary Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Matching Operational Records Found: {len(dataframe)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    
    # Table headers setup config
    pdf_cols = ['no', 'rk', 'trade', 'full', 'phone', 'unit', 'appt', 'license']
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(28, 49, 68)
    pdf.set_text_color(255, 255, 255)
    
    col_width = 34
    for col in pdf_cols:
        pdf.cell(col_width, 8, col.upper(), border=1, fill=True)
    pdf.ln()
    
    # Ingest rows details safely cleansing string formats
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    for _, row in dataframe.iterrows():
        for col in pdf_cols:
            val_str = str(row[col]) if pd.notna(row[col]) else ""
            if val_str == "nan":
                val_str = ""
            val_cleaned = val_str.encode('ascii', 'ignore').decode('ascii')
            pdf.cell(col_width, 7, val_cleaned[:20], border=1)
        pdf.ln()
        
    # Strictly export format out of memory stream to standard byte strings
    return bytes(pdf.output())

# ==============================================================================
# 6. APP BODY WORKSPACE INTERFACE
# ==============================================================================
st.markdown("### 📊 Operational Overview Metrics")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Master Roster Strengths", len(df_master))
with m2:
    st.metric("Filtered Records In View", len(filtered_df))
with m3:
    st.metric("Unique Units Represented", filtered_df['unit'].nunique() if not filtered_df.empty else 0)
with m4:
    lic_count = filtered_df[filtered_df['license'].notna() & (filtered_df['license'] != "")]['license'].count() if not filtered_df.empty else 0
    st.metric("Operators Filtered", int(lic_count))

st.markdown("---")

tab_dashboard, tab_directory, tab_editor = st.tabs([
    "📊 Dynamic Search Grid", 
    "📞 Communications Directory Grid", 
    "✏️ Direct Database Entry"
])

# ------------------------------------------------------------------------------
# TAB 1: DASHBOARD AND ON-CLICK PDF DOWNLOAD
# ------------------------------------------------------------------------------
with tab_dashboard:
    st.subheader("📋 Search Engine Query Output")
    
    if not filtered_df.empty:
        # Using a click-delayed lambda execution eliminates upfront bytearray loading crashes
        st.download_button(
            label="📥 Download Current Filtered List as PDF Report",
            data=compile_pdf_report(filtered_df),
            file_name="Filtered_Contingent_Report.pdf",
            mime="application/pdf",
            type="primary"
        )
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.dataframe(filtered_df, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: INTERACTIVE DIRECTORY
# ------------------------------------------------------------------------------
with tab_directory:
    st.subheader("📱 Quick Action Call / WhatsApp Panel")
    if filtered_df.empty:
        st.info("No records match structural settings parameters.")
    else:
        for idx, row in filtered_df.iterrows():
            p_name = f"{row['rk']} {row['full']}".strip() if pd.notna(row['full']) else f"ID Key: {row['no']}"
            with st.expander(f"👤 {p_name} — {row['appt']} ({row['unit']})"):
                d_left, d_right = st.columns(2)
                with d_left:
                    st.write(f"**Personal ID No:** {row['no']}")
                    st.write(f"**Trade/Corps Matrix:** {row['trade']}")
                    st.write(f"**Assigned License Matrix:** {row['license'] if pd.notna(row['license']) else 'None'}")
                with d_right:
                    raw_phone = str(row['phone']).strip()
                    if raw_phone and raw_phone != "nan" and raw_phone != "":
                        st.write(f"**Active Contact Details:** `{raw_phone}`")
                        wa_phone = raw_phone.replace("+", "").replace(" ", "").strip()
                        if not wa_phone.startswith('88') and len(wa_phone) == 11:
                            wa_phone = "88" + wa_phone
                            
                        st.markdown(f"""
                        <div style='margin-top: 5px;'>
                            <a class='contact-btn btn-tel' href='tel:{raw_phone}'>📞 Call Phone</a>
                            <a class='contact-btn btn-wa' href='https://wa.me/{wa_phone}' target='_blank'>💬 WhatsApp</a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No active phone mapped for this profile record.")

# ------------------------------------------------------------------------------
# TAB 3: MASTER LOGISTICS DATA EDITOR LINK
# ------------------------------------------------------------------------------
with tab_editor:
    st.subheader("✏️ Master Database Update Portal")
    st.info("Click the primary dashboard button tool connection module down below to execute changes directly on the sheet.")
    st.markdown('[🔗 Open Live Google Sheet Database to Edit Info](https://docs.google.com/spreadsheets/d/1KyXeyMjlN8nPi6xKKgeJsy-d8p_npcBa002B1yOIB9Y/edit)')
