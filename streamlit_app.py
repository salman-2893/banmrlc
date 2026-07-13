import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# 1. PAGE CONFIGURATION & SETUP
# ==============================================================================
st.set_page_config(
    page_title="Contingent Management Portal",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for interactive call/whatsapp buttons
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

# Define column schema globally based on your spreadsheet structure
COLUMN_LIST = [
    'timestamp', 'no', 'rk', 'trade', 'first', 'mid', 'last', 'full', 'bangla', 
    'email', 'phone', 'emgno', 'passno', 'passval', 'nid', 'bday', 'bplace', 
    'ret', 'joincon', 'last3', 'photo', 'joinsvc', 'svc', 'msn', 'bg ', 'appt', 
    'course', 'license', 'ht', 'emgrel', 'wife', 'child', 'wt', 'unit', 'home', 
    'ident', 'Contgt'
]

TARGET_SPREADSHEET = "https://docs.google.com/spreadsheets/d/1KyXeyMjlN8nPi6xKKgeJsy-d8p_npcBa002B1yOIB9Y/edit?usp=drivesdk"

# ==============================================================================
# 2. DATA CONNECTION & LIVE UTILITIES
# ==============================================================================
# Establish connection natively via st.connection
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10) # Cache for 10 seconds to balance speed and sheet accuracy
def fetch_live_data():
    try:
        # Read data directly using URL configuration mapping column rules
        data = conn.read(spreadsheet=TARGET_SPREADSHEET, usecols=COLUMN_LIST)
        # Clear any entirely empty structural placeholder rows
        data = data.dropna(subset=['no'])
        return data
    except Exception as e:
        st.error(f"Error fetching data from Google Sheets: {e}")
        return pd.DataFrame(columns=COLUMN_LIST)

df_master = fetch_live_data()

# Ensure standard ID keys are string parsed safely
if not df_master.empty:
    df_master['no'] = df_master['no'].astype(str)

# ==============================================================================
# 3. SIDEBAR NAVIGATION & FILTER INTERFACE
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/military-rank.png", width=80)
st.sidebar.title("Navigation Controls")

st.sidebar.subheader("🎯 Filter Criteria")

# Dynamic unique selections safely parsing empty records
unit_list = ["All"] + sorted(list(df_master['unit'].dropna().unique())) if not df_master.empty else ["All"]
rank_list = ["All"] + sorted(list(df_master['rk'].dropna().unique())) if not df_master.empty else ["All"]
trade_list = ["All"] + sorted(list(df_master['trade'].dropna().unique())) if not df_master.empty else ["All"]
license_list = ["All"] + sorted(list(df_master['license'].dropna().unique())) if not df_master.empty else ["All"]

sel_unit = st.sidebar.selectbox("Filter by Unit/Sub-Unit", unit_list)
sel_rank = st.sidebar.selectbox("Filter by Rank (Rk)", rank_list)
sel_trade = st.sidebar.selectbox("Filter by Trade/Corps", trade_list)
sel_license = st.sidebar.selectbox("Filter by License Profile", license_list)

# Execution of dynamic filter mapping logic
filtered_df = df_master.copy()
if sel_unit != "All":
    filtered_df = filtered_df[filtered_df['unit'] == sel_unit]
if sel_rank != "All":
    filtered_df = filtered_df[filtered_df['rk'] == sel_rank]
if sel_trade != "All":
    filtered_df = filtered_df[filtered_df['trade'] == sel_trade]
if sel_license != "All":
    filtered_df = filtered_df[filtered_df['license'] == sel_license]

# ==============================================================================
# 4. REPORTLAB PDF EXPORT LOGIC
# ==============================================================================
def compile_pdf_report(dataframe):
    buffer = io.BytesIO()
    # Using landscape format for wide layout spreadsheets structures cleanly
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=15,
        textColor=colors.HexColor("#1C3144")
    )
    
    # Header Elements
    story.append(Paragraph("🎖️ Contingent Deployment & Operational Query Report", title_style))
    story.append(Paragraph(f"Report Generated On: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Total Rows Matching Parameters: {len(dataframe)} Record(s)", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Pick essential core high-value tracking fields to avoid clipping landscape letter size bounds
    pdf_cols = ['no', 'rk', 'trade', 'full', 'phone', 'unit', 'appt', 'license']
    table_data = [pdf_cols] # Column headers
    
    for _, row in dataframe.iterrows():
        row_cells = [str(row[c]) if pd.notna(row[c]) else "" for c in pdf_cols]
        table_data.append(row_cells)
        
    report_table = Table(table_data, repeatRows=1)
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1C3144")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0F4F8")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(report_table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 5. CORE WORKSPACE UI LAYOUT & TABS
# ==============================================================================
st.title("🎖️ Contingent Management & Search System Dashboard")
st.markdown("---")

# High efficiency performance metrics layout
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Master Database Roster", len(df_master))
with m2:
    st.metric("Active Filter Result Count", len(filtered_df))
with m3:
    unq_units = filtered_df['unit'].nunique() if not filtered_df.empty else 0
    st.metric("Represented Sub-Units Selected", unq_units)
with m4:
    lic_count = filtered_df[filtered_df['license'].notna() & (filtered_df['license'] != "")]['license'].count() if not filtered_df.empty else 0
    st.metric("Licensed Operators in View", int(lic_count))

st.markdown("---")

tab_dashboard, tab_directory, tab_editor = st.tabs([
    "📊 Search Dashboard & Analytics", 
    "📞 Interactive Phone/WhatsApp Directory", 
    "✏️ Record Modification & Entry Engine"
])

# ------------------------------------------------------------------------------
# TAB 1: SEARCH DASHBOARD & ANALYTICS
# ------------------------------------------------------------------------------
with tab_dashboard:
    st.subheader("📋 Search Results View")
    
    col_act1, col_act2 = st.columns([6, 2])
    with col_act2:
        if not filtered_df.empty:
            pdf_data = compile_pdf_report(filtered_df)
            st.download_button(
                label="📄 Export Printable PDF Report",
                data=pdf_data,
                file_name="Contingent_Filtered_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
    # Interactive Search View Layout Engine
    st.dataframe(filtered_df, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: INTERACTIVE PHONE/WHATSAPP DIRECTORY
# ------------------------------------------------------------------------------
with tab_directory:
    st.subheader("📱 Live Operations Communications Grid")
    
    if filtered_df.empty:
        st.warning("No personnel match your selected filters. Adjust parameters in the sidebar.")
    else:
        # Loop over individual filtered profiles
        for idx, row in filtered_df.iterrows():
            clean_name = f"{row['rk']} {row['full']}".strip() if pd.notna(row['full']) else f"Serial Key: {row['no']}"
            with st.expander(f"👤 {clean_name} — {row['appt']} ({row['unit']})"):
                c_details, c_actions = st.columns([2, 2])
                
                with c_details:
                    st.write(f"**Personal Army No / ID:** {row['no']}")
                    st.write(f"**Trade/Corps Matrix:** {row['trade']}")
                    st.write(f"**Assigned License Status:** {row['license'] if pd.notna(row['license']) else 'None Identified'}")
                    st.write(f"**Blood Group:** {row['bg '] if pd.notna(row['bg ']) else 'Unspecified'}")
                
                with c_actions:
                    raw_phone = str(row['phone']).strip() if pd.notna(row['phone']) else ""
                    # Normalize string representations for decimal adjustments out of floats
                    if raw_phone.endswith('.0'):
                        raw_phone = raw_phone[:-2]
                        
                    if raw_phone and raw_phone != "nan":
                        st.write(f"**Active Number:** `{raw_phone}`")
                        
                        # Build sanitized international links for WhatsApp
                        wa_phone = raw_phone.replace("+", "").replace(" ", "").strip()
                        # Fallback parsing default localized prefix string structure safely
                        if not wa_phone.startswith('88') and len(wa_phone) == 11:
                            wa_phone = "88" + wa_phone
                            
                        whatsapp_url = f"https://wa.me/{wa_phone}"
                        tel_url = f"tel:{raw_phone}"
                        
                        # Markdown injection for customized calling modules
                        buttons_html = f"""
                        <div style='margin-top: 10px;'>
                            <a class='contact-btn btn-tel' href='{tel_url}'>📞 Voice Call</a>
                            <a class='contact-btn btn-wa' href='{whatsapp_url}' target='_blank'>💬 WhatsApp Chat</a>
                        </div>
                        """
                        st.markdown(buttons_html, unsafe_allow_html=True)
                    else:
                        st.info("No primary contact number mapped for this operational profile.")

# ------------------------------------------------------------------------------
# TAB 3: RECORD MODIFICATION & ENTRY ENGINE
# ------------------------------------------------------------------------------
with tab_editor:
    st.subheader("✏️ Live Update Target Sheet Rows")
    
    if df_master.empty:
        st.error("Master database is empty or unavailable.")
    else:
        # Selection framework by identification numbers keys
        personnel_options = df_master.apply(
            lambda r: f"{r['no']} - {r['rk']} {r['full']} [{r['unit']}]", axis=1
        ).tolist()
        
        selected_record_str = st.selectbox("Select Personnel Record To Modify", personnel_options)
        
        # Pull extracted serial ID tracking reference
        target_no = selected_record_str.split(" - ")[0].strip()
        
        # Fetch individual row sequence metadata fields matching exact key target references
        row_idx = df_master[df_master['no'] == target_no].index[0]
        current_row_data = df_master.loc[row_idx]
        
        st.markdown("### Update Values Below:")
        
        # Dynamically build entry elements matching data layout
        form_cols = st.columns(3)
        updated_payload = {}
        
        for i, col_name in enumerate(COLUMN_LIST):
            # Pick columns layout order flow splits evenly mapping arrays
            col_target = form_cols[i % 3]
            current_val = current_row_data[col_name]
            
            # Format display configurations smoothly handling NaN strings representations out of null layers
            val_str = str(current_val) if pd.notna(current_val) else ""
            if val_str.endswith('.0') and col_name in ['no', 'phone', 'emgno', 'nid']:
                val_str = val_str[:-2]
                
            with col_target:
                # Set specific layout fields to read-only blocks to preserve relational integrity constraints
                if col_name in ['timestamp', 'no']:
                    updated_payload[col_name] = st.text_input(f"{col_name} (Read Only)", value=val_str, disabled=True)
                else:
                    updated_payload[col_name] = st.text_input(f"Modify: {col_name}", value=val_str)
        
        st.markdown("---")
        if st.button("💾 Save & Commit Changes Instantly", type="primary", use_container_width=True):
            with st.spinner("Writing corrections directly back to master cloud environment..."):
                try:
                    # Update local state dataframe before commit execution
                    for col_key, new_value in updated_payload.items():
                        df_master.at[row_idx, col_key] = new_value
                    
                    # Call execution engine back to the cloud target connection
                    conn.update(
                        spreadsheet=TARGET_SPREADSHEET,
                        data=df_master
                    )
                    
                    st.success("Changes successfully synchronized and locked directly to Google Sheets database! 🎉")
                    st.cache_data.clear() # Wipe frame configurations cache explicitly to force reload checks
                    
                except Exception as ex:
                    st.error(f"Failed to submit structural entries cleanly: {ex}")
