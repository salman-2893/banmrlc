import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Contingent Management Portal",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Buttons
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

# Standard shared link parsed directly as a flat dataset source
TARGET_SPREADSHEET = "https://docs.google.com/spreadsheets/d/1KyXeyMjlN8nPi6xKKgeJsy-d8p_npcBa002B1yOIB9Y/export?format=csv"

# 2. FETCH DATA FROM GOOGLE SHEET
@st.cache_data(ttl=10)
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
        st.error(f"Could not load data. Make sure your Google Sheet sharing settings are set to 'Anyone with the link can view'. Error: {e}")
        return pd.DataFrame(columns=COLUMN_LIST)

df_master = fetch_live_data()

if not df_master.empty:
    df_master['no'] = df_master['no'].astype(str)

# 3. SIDEBAR FILTERS
st.sidebar.image("https://img.icons8.com/color/96/military-rank.png", width=80)
st.sidebar.title("App Filters")

unit_list = ["All"] + sorted(list(df_master['unit'].dropna().astype(str).unique())) if not df_master.empty else ["All"]
rank_list = ["All"] + sorted(list(df_master['rk'].dropna().astype(str).unique())) if not df_master.empty else ["All"]
trade_list = ["All"] + sorted(list(df_master['trade'].dropna().astype(str).unique())) if not df_master.empty else ["All"]
license_list = ["All"] + sorted(list(df_master['license'].dropna().astype(str).unique())) if not df_master.empty else ["All"]

sel_unit = st.sidebar.selectbox("Filter by Unit", unit_list)
sel_rank = st.sidebar.selectbox("Filter by Rank (Rk)", rank_list)
sel_trade = st.sidebar.selectbox("Filter by Trade/Corps", trade_list)
sel_license = st.sidebar.selectbox("Filter by License Profile", license_list)

filtered_df = df_master.copy()
if sel_unit != "All":
    filtered_df = filtered_df[filtered_df['unit'] == sel_unit]
if sel_rank != "All":
    filtered_df = filtered_df[filtered_df['rk'] == sel_rank]
if sel_trade != "All":
    filtered_df = filtered_df[filtered_df['trade'] == sel_trade]
if sel_license != "All":
    filtered_df = filtered_df[filtered_df['license'] == sel_license]

# 4. COMPUTE PDF LOGIC
def compile_pdf_report(dataframe):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('RepTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor("#1C3144"))
    
    story.append(Paragraph("🎖️ Contingent Deployment & Operational Query Report", title_style))
    story.append(Paragraph(f"Total Rows Matching Parameters: {len(dataframe)} Record(s)", styles['Normal']))
    story.append(Spacer(1, 15))
    
    pdf_cols = ['no', 'rk', 'trade', 'full', 'phone', 'unit', 'appt', 'license']
    table_data = [pdf_cols]
    
    for _, row in dataframe.iterrows():
        row_cells = [str(row[c]) if pd.notna(row[c]) else "" for c in pdf_cols]
        table_data.append(row_cells)
        
    report_table = Table(table_data, repeatRows=1)
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1C3144")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0F4F8")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    story.append(report_table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# 5. USER INTERFACE LAYOUT
st.title("🎖️ Contingent Search & Operations Dashboard")
st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Roster Database", len(df_master))
with m2:
    st.metric("Filtered Records Matching", len(filtered_df))
with m3:
    st.metric("Unique Units Mapped", filtered_df['unit'].nunique() if not filtered_df.empty else 0)
with m4:
    lic_count = filtered_df[filtered_df['license'].notna() & (filtered_df['license'] != "")]['license'].count() if not filtered_df.empty else 0
    st.metric("Licensed Personnel", int(lic_count))

st.markdown("---")

tab_dashboard, tab_directory, tab_editor = st.tabs([
    "📊 Search Dashboard & Analytics", 
    "📞 Interactive Phone/WhatsApp Directory", 
    "✏️ Edit Database Entries"
])

with tab_dashboard:
    st.subheader("📋 Dynamic Search Results Grid")
    if not filtered_df.empty:
        pdf_data = compile_pdf_report(filtered_df)
        st.download_button(
            label="📄 Export Printable PDF Report",
            data=pdf_data,
            file_name="Contingent_Filtered_Report.pdf",
            mime="application/pdf"
        )
    st.dataframe(filtered_df, use_container_width=True)

with tab_directory:
    st.subheader("📱 Live Operations Communications Directory")
    if filtered_df.empty:
        st.warning("No personnel match your selected filters.")
    else:
        for idx, row in filtered_df.iterrows():
            clean_name = f"{row['rk']} {row['full']}".strip() if pd.notna(row['full']) else f"ID: {row['no']}"
            with st.expander(f"👤 {clean_name} — {row['appt']} ({row['unit']})"):
                c_details, c_actions = st.columns(2)
                with c_details:
                    st.write(f"**Army No / ID:** {row['no']}")
                    st.write(f"**Trade/Corps:** {row['trade']}")
                    st.write(f"**License Profile:** {row['license'] if pd.notna(row['license']) else 'None'}")
                    st.write(f"**Blood Group:** {row['bg '] if pd.notna(row['bg ']) else 'Unspecified'}")
                with c_actions:
                    raw_phone = str(row['phone']).strip() if pd.notna(row['phone']) else ""
                    if raw_phone.endswith('.0'):
                        raw_phone = raw_phone[:-2]
                    if raw_phone and raw_phone != "nan":
                        st.write(f"**Phone:** `{raw_phone}`")
                        wa_phone = raw_phone.replace("+", "").replace(" ", "").strip()
                        if not wa_phone.startswith('88') and len(wa_phone) == 11:
                            wa_phone = "88" + wa_phone
                        
                        st.markdown(f"""
                        <div style='margin-top: 5px;'>
                            <a class='contact-btn btn-tel' href='tel:{raw_phone}'>📞 Call Direct</a>
                            <a class='contact-btn btn-wa' href='https://wa.me/{wa_phone}' target='_blank'>💬 WhatsApp</a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No phone profile saved.")

with tab_editor:
    st.subheader("✏️ Live Database Management")
    st.info("To add entries or change record values directly, use the verified primary master data link below:")
    st.markdown('[🔗 Open Live Google Sheet Database to Edit Info](https://docs.google.com/spreadsheets/d/1KyXeyMjlN8nPi6xKKgeJsy-d8p_npcBa002B1yOIB9Y/edit)')

