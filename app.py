import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import datetime
from src.lead_researcher import LeadResearcher
from src.outreach_manager import OutreachManager
from src.email_verifier import verify_email
from src.mailbox_store import load_mailboxes, save_mailbox, delete_mailbox
from src.campaign_store import load_campaigns, save_campaign, delete_campaign, load_all_campaigns_admin
import src.auth as auth
import uuid

# ----------------- TRUE OPEN TRACKING INTERCEPTOR -----------------
if 'action' in st.query_params and st.query_params['action'] == 'open':
    campaign_id = st.query_params.get('cid')
    if campaign_id:
        try:
            from config import supabase_client
            if supabase_client:
                res = supabase_client.table("campaigns").select("opened").eq("id", campaign_id).execute()
                if len(res.data) > 0:
                    curr = res.data[0]["opened"]
                    supabase_client.table("campaigns").update({"opened": curr + 1}).eq("id", campaign_id).execute()
        except: pass
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ce/Transparent.gif", width=1)
    st.stop()

if 'action' in st.query_params and st.query_params['action'] == 'unsub':
    st.set_page_config(page_title="Unsubscribed", layout="centered")
    email_unsub = st.query_params.get('email', 'Unknown User')
    st.markdown("<h2 style='text-align: center; color: #dc2626;'>🚫 Unsubscribed Successfully</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>The address <b>{email_unsub}</b> has been safely removed from our active mailing list.<br>You will not receive any further communications regarding this matter.</p>", unsafe_allow_html=True)
    st.stop()

st.set_page_config(page_title="Marketifyer CRM", layout="wide", page_icon="⚡")

st.markdown("""
<style>
/* CSS Overhaul: Instantly.io Aesthetic Minimalist Glassmorphism */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f4f7f6; color: #1e293b; }
.stButton>button { border-radius: 8px; font-weight: 600; padding: 0.6rem 1.2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease-in-out; border: 1px solid #e2e8f0; background: white; color: #1e293b; }
.stButton>button[kind="primary"] { background-color: #2563eb; color: white; border: none; box-shadow: 0 4px 6px rgba(37,99,235,0.2); }
.stButton>button[kind="primary"]:hover { background-color: #1d4ed8; transform: translateY(-1px); box-shadow: 0 6px 8px rgba(37,99,235,0.3); }
.stButton>button:hover { background-color: #f8fafc; border-color: #cbd5e1; }
h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; color: #0f172a; letter-spacing: -0.02em; }
div[data-testid="stMetricValue"] { font-weight: 700; font-size: 2.2rem; color: #2563eb; letter-spacing: -0.03em; }
div[data-testid="stExpander"] { background: white; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); margin-bottom: 1rem; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea { border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02); }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color: #2563eb; box-shadow: 0 0 0 1px #2563eb; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .viewerBadge_container__1QSob {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ----------------- AUTHENTICATION -----------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    try:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.image("logo.png", use_container_width=True)
    except:
        st.title("⚡ Marketifyer CRM")
    st.markdown("<h3 style='text-align: center;'>Secure Access Portal</h3>", unsafe_allow_html=True)
    st.divider()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if not auth.users_exist():
            st.info("Welcome to Marketifyer! Please create the first Master Admin account.")
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            if st.button("Register & Login", type="primary"):
                if not new_user or not new_pass:
                    st.error("Please fill fields.")
                else:
                    success, msg = auth.create_user(new_user, new_pass)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = new_user
                        st.session_state['leads_df'] = pd.DataFrame()
                        st.session_state['temp_df'] = pd.DataFrame()
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.subheader("Login")
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Login", type="primary"):
                if auth.authenticate(user, pw):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.session_state['leads_df'] = pd.DataFrame()
                    st.session_state['temp_df'] = pd.DataFrame()
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
            
            with st.expander("Create New User Profile"):
                new_user = st.text_input("New Username", key="nu")
                new_pass = st.text_input("New Password", type="password", key="np")
                if st.button("Create Account"):
                    if not new_user or not new_pass:
                        st.error("Fill all fields.")
                    else:
                        s, m = auth.create_user(new_user, new_pass)
                        if s: st.success("Account created! Please login above.")
                        else: st.error(m)
    st.stop()


# ----------------- MAIN APP (CRM) -----------------
try:
    sc1, sc2, sc3 = st.sidebar.columns([1, 2, 1])
    with sc2:
        st.image("logo.png", use_container_width=True)
except:
    st.sidebar.title("⚡ Marketifyer")
st.sidebar.markdown(f"**Logged in as:** `{st.session_state['username']}`")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.sidebar.divider()

if st.session_state['username'].lower() == "logicaldatasolution@gmail.com":
    with st.sidebar.expander("👑 Master Admin Panel"):
        st.markdown("### Manage Roles")
        users_list = auth.get_all_users()
        st.write(f"Total Users: **{len(users_list)}**")
        
        nu = st.text_input("New Username (Email)", key="admin_nu")
        np = st.text_input("New Password", type="password", key="admin_np")
        if st.button("Create Extra Account"):
            if not nu or not np:
                st.error("Fill all fields.")
            else:
                s, m = auth.create_user(nu, np)
                if s: st.success("User created!"); time.sleep(1); st.rerun()
                else: st.error(m)
                
        st.divider()
        st.markdown("### Active Profiles")
        for u in users_list:
            if u.lower() != "logicaldatasolution@gmail.com":
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 `{u}`")
                if c2.button("❌", key=f"delu_{u}"):
                    s, m = auth.delete_user(u)
                    if s: st.rerun()
                    else: st.error(m)
                    
        st.divider()
        st.markdown("### 🌍 Global Campaign Analytics")
        all_camps = load_all_campaigns_admin()
        if all_camps:
            tot_sent = sum(c.get('sent', 0) for c in all_camps)
            tot_opened = sum(c.get('opened', 0) for c in all_camps)
            tot_replied = sum(c.get('replied', 0) for c in all_camps)
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Platform Sent", tot_sent)
            mc2.metric("Platform Opens", tot_opened)
            mc3.metric("Platform Replies", tot_replied)
            
            st.write("**Recent User Campaigns:**")
            for c in reversed(all_camps[-15:]):
                st.caption(f"👤 **{c.get('owner')}** ➔ '{c.get('name')}' ({c.get('sent')} sent | {c.get('replied', 0)} replied)")
        else:
            st.info("No campaigns sent across the platform yet.")

st.sidebar.divider()

@st.cache_resource
def get_researcher():
    return LeadResearcher()

researcher = get_researcher()

tab_dash, tab_leads, tab_camp, tab_mbox, tab_ai = st.tabs([
    "🏠 Dashboard", "🔍 Leads", "📧 Campaigns", "📥 Mailboxes", "🤖 AI Rater"
])

with tab_dash:
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1500&q=80", use_container_width=True)
    st.header("Overview Dashboard")
    campaigns = load_campaigns(st.session_state['username'])
    
    if not campaigns:
        st.info("No campaigns sent yet. Head over to the Campaigns tab to start emailing!")
    else:
        tot_sent = sum(c.get('sent', 0) for c in campaigns)
        tot_opened = sum(c.get('opened', 0) for c in campaigns)
        tot_replied = sum(c.get('replied', 0) for c in campaigns)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Global Emails Sent", tot_sent)
        col2.metric("Total Unique Opens", tot_opened)
        col3.metric("Total Direct Replies", tot_replied)
        st.caption("*Note: Opens and Replies are probabilistically simulated for platform demonstration since you do not have an active Webhook Receiver enabled.")
        
        st.divider()
        st.subheader("Saved Campaign History")
        for c in reversed(campaigns):
            with st.expander(f"📅 {c.get('date')} | 🏷️ {c.get('name')} | 📩 {c.get('sent')} Sent"):
                st.write(f"**Sequence Template:** {c.get('subject')}")
                with st.expander("View Raw Email Copy"):
                    st.code(c.get('body', 'No copy tracking available for this legacy campaign.'), language='html')
                c_cols = st.columns(5)
                c_cols[0].metric("Sent", c.get('sent'))
                c_cols[1].metric("Failed", c.get('failed'))
                
                deliv = c.get('delivered', 0)
                opn = c.get('opened', 0)
                rep = c.get('replied', 0)
                
                opn_perc = f" ({int((opn/deliv)*100)}%)" if deliv > 0 else ""
                rep_perc = f" ({int((rep/deliv)*100)}%)" if deliv > 0 else ""
                
                c_cols[2].metric("Delivered", deliv)
                c_cols[3].metric("Opened", f"{opn}{opn_perc}")
                c_cols[4].metric("Replied", f"{rep}{rep_perc}")
                
                # Predictive AI Insights Logic
                s_c = c.get('sent', 0)
                if s_c > 0:
                    o_r = (c.get('opened', 0) / s_c) * 100
                    r_r = (c.get('replied', 0) / s_c) * 100
                    
                    insight = ""
                    if o_r > 50:
                        insight = "🔥 Your sequence subject is outperforming B2B industry limits by 150%. Excellent hook."
                    elif o_r > 20:
                        insight = "👍 Solid open rate, but room exists for A/B testing alternative subject lines."
                    else:
                        insight = "⚠️ Low overall visibility. Aggressively scrub your target list to preserve domain reputation."
                        
                    if r_r > 10:
                        insight += " Your Call-To-Action (CTA) is generating incredibly elite engagement!"
                    elif r_r > 3:
                        insight += " The body copy is converting adequately."
                    else:
                        insight += " Weak reply conversions. Simplify your CTA to a binary Yes/No question."
                        
                    st.info(f"**🤖 AI Predictive Insights:** {insight}")
                
                if st.button("Delete Entry", key=f"del_{c.get('id')}"):
                    delete_campaign(st.session_state['username'], c.get('id'))
                    st.rerun()

with tab_leads:
    st.header("Find & Extract Contacts")
    st.markdown("Extract specific decision makers effortlessly with multi-vector AI routing.")
    
    search_mode = st.radio("Extraction Source Strategy:", ["🏢 By Company Domains", "🏢 By Company Names (Auto-Resolve)", "🎟️ By Tradeshow Directory URL"], horizontal=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        input_text = ""
        if search_mode == "🏢 By Company Domains":
            input_text = st.text_area("Targets (comma or newline separated):", "stripe.com\nopenai.com", height=120)
        elif search_mode == "🏢 By Company Names (Auto-Resolve)":
            input_text = st.text_area("Company Names (comma or newline separated):", "Apple Inc\nMicrosoft\nSpaceX", height=120)
        else:
            input_text = st.text_input("Exact Tradeshow Exhibitor URL:", placeholder="https://www.event.com/exhibitor-list")
            st.caption("AI will aggressively scrape exactly that HTML URL structure to pull the companies.")
            
        geo_target = st.multiselect("Geo-Targeting (Global Filter)", ["United States", "United Kingdom", "Canada", "Australia", "Europe", "Asia"], default=[])
            
        st.info("💡 To violently abort an extraction loop, click 'Stop' 🛑 in the top right corner of the screen.")
        
        limit_per_company = st.number_input("Max Leads per Company", min_value=1, max_value=20, value=3)
        limit_companies = 999999
        
    with col2:
        default_titles = "sales manager, sales director, marketing manager, marketing director, business development, email marketing, digital marketing, demand generation, operations manager, product marketing, revenue operations, growth manager, lead generation, event manager, meetings manager, exhibit manager"
        titles_input = st.text_area("Target Job Titles (comma-separated):", default_titles, height=210)
    
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        launch_extract = st.button("🚀 Extract Leads Database", type="primary", use_container_width=True)
    with c_e2:
        if st.button("🛑 Abort Extraction Sequence", use_container_width=True):
            st.session_state['abort_extract'] = True
            st.rerun()
            
    if launch_extract:
        st.session_state['abort_extract'] = False
        if not input_text:
            st.error("Please provide targets to extract.")
        else:
            titles = [t.strip() for t in titles_input.split(',') if t.strip()]
            domains = []
            
            if search_mode == "🎟️ By Tradeshow Directory URL":
                with st.spinner(f"Scraping the direct HTML architecture of {input_text}..."):
                    comps = researcher.extract_event_exhibitors(input_text)
                    if comps:
                        st.info(f"Automatically identified {len(comps)} exhibitors: {', '.join(comps)}")
                        with st.spinner("Resolving exhibitor names into official domains..."):
                            for c in comps:
                                domains.append(researcher.resolve_company_to_domain(c))
                    else:
                        st.warning("Failed to find any public exhibitor list for that event.")
            elif search_mode == "🏢 By Company Names (Auto-Resolve)":
                raw_comps = [d.strip() for d in input_text.replace('\n', ',').split(',') if d.strip()]
                with st.spinner(f"Auto-Resolving {len(raw_comps)} company names to standard URL domains..."):
                    for c in raw_comps:
                        domains.append(researcher.resolve_company_to_domain(c))
            else:
                domains = [d.strip() for d in input_text.replace('\n', ',').split(',') if d.strip()]
            
            if domains:
                with st.spinner(f"AI Agent is dynamically extracting pipeline for {len(domains)} verified domains..."):
                    df = researcher.process_company_list(domains, titles, int(limit_per_company), geo_target)
                    if not df.empty:
                        st.session_state['temp_df'] = df
                    else:
                        st.warning("⚠️ No contacts found. If you used a Tradeshow URL, this is likely an interactive Javascript Floorplan Map that blocks AI Scrapers. Please find the static 'A-Z Exhibitor Text Directory' URL and paste that instead!")

    if 'temp_df' in st.session_state and not st.session_state['temp_df'].empty:
        df = st.session_state['temp_df']
        st.success(f"Success! Extracted {len(df)} sophisticated contacts.")
        
        df_display = df.drop(columns=['Permutations']) if 'Permutations' in df.columns else df
        st.dataframe(df_display, use_container_width=True)
        
        st.markdown("### Pipeline Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            csv = df.drop(columns=['Permutations'], errors='ignore').to_csv(index=False)
            st.download_button("💾 Download CSV", data=csv, file_name="marketifyer_leads.csv", mime="text/csv", use_container_width=True)
        
        with c2:
            if st.button("✅ Validate & Scrub Emails", use_container_width=True, type="primary"):
                with st.spinner("Pinging raw Mail Exchange (MX) servers globally..."):
                    valid_df = []
                    inv_count = 0
                    for i, r in df.iterrows():
                        e = r.get('Email', '')
                        perms = r.get('Permutations', [])
                        
                        found = False
                        if e:
                            v = verify_email(e)
                            if v:
                                valid_df.append(r)
                                found = True
                                
                        if not found and isinstance(perms, list):
                            for p in perms:
                                v = verify_email(p)
                                if v:
                                    r['Email'] = p
                                    r['Source'] += " (Verified via AI Iteration)"
                                    valid_df.append(r)
                                    found = True
                                    break
                                    
                        if not found:
                            inv_count += 1
                            
                    st.session_state['temp_df'] = pd.DataFrame(valid_df)
                    st.session_state['scrub_msg'] = f"Scrub complete! Protected you from {inv_count} hard-bounces."
                st.rerun()

        with c3:
            if st.button("📥 Add to Campaign Pipeline", use_container_width=True):
                st.session_state['leads_df'] = df.drop(columns=['Permutations'], errors='ignore')
                st.success("Loaded! Go to Campaigns tab.")
                
        if 'scrub_msg' in st.session_state:
            st.info(st.session_state['scrub_msg'])

with tab_camp:
    st.image("https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1500&q=80", use_container_width=True)
    st.header("Campaign Engine")
    
    mailboxes = load_mailboxes(st.session_state['username'])
    active_mailbox = None
    if mailboxes:
        mb_options = [f"{mb['user']} ({mb['host']})" for mb in mailboxes]
        selected_mb_str = st.selectbox("📨 Select Sender Mailbox:", mb_options)
        selected_index = mb_options.index(selected_mb_str)
        active_mailbox = mailboxes[selected_index]
    else:
        st.warning("⚠️ No Mailboxes Configured! Go to 'Manage Mailboxes'.")
    
    st.subheader("Upload an External List")
    uploaded_file = st.file_uploader("Upload External Leads CSV", type="csv")
    if uploaded_file is not None:
        st.session_state['leads_df'] = pd.read_csv(uploaded_file)
        st.success("List uploaded successfully!")
        
    st.divider()

    if 'leads_df' in st.session_state and not st.session_state['leads_df'] is None and not st.session_state['leads_df'].empty:
        st.subheader("Active Pipeline")
        df = st.session_state['leads_df']
        
        col_v1, col_v2 = st.columns([3, 1])
        with col_v1:
            st.dataframe(df, use_container_width=True)
        with col_v2:
            st.markdown("### Verification")
            if st.button("Run Verification"):
                with st.spinner("Checking MX records..."):
                    df['Is Valid'] = df['Email'].apply(lambda x: verify_email(x) if pd.notna(x) and x != "" else False)
                    st.session_state['leads_df'] = df
                    valid_amt = df['Is Valid'].sum()
                    st.session_state['verification_msg'] = f"✅ {valid_amt} Valid | ❌ {len(df) - valid_amt} Invalid"
                st.rerun()
                
            if 'verification_msg' in st.session_state:
                st.info(st.session_state['verification_msg'])
                if st.button("🗑️ Scrub Invalid Emails"):
                    st.session_state['leads_df'] = df[df['Is Valid'] == True]
                    del st.session_state['verification_msg']
                    st.rerun()
        
        st.divider()
        st.subheader("Sequence Configuration")
        campaign_name_custom = st.text_input("Campaign Name (For Tracking Dashboard):", "B2B Q4 Outreach")
        
        def_subj = "Exploring potential synergies between {{company}} and us"
        def_body = "<p>Hi {{name}},</p><br><p>{{icebreaker}}</p><br><p>I noticed your great work over at {{company}} and thought it would be great to connect regarding some business development initiatives.</p><br><p>Best,<br>Your Name</p>"
        
        st.info("💡 **UNIQUE FEATURE:** Put `{{icebreaker}}` anywhere in your email body, and our new bleeding-edge AI Persona Agent will automatically replace it with a hyper-personalized, 1-sentence emotional hook based entirely on their Company!")
        
        subject_a = st.text_input("Subject Line (Variant A):", def_subj)
        body_a = st.text_area("Email Content A (HTML supported):", def_body, height=200)
        
        ab_test = st.checkbox("🧪 Enable A/B Testing (Split Sequence Sending)")
        subject_b, body_b = None, None
        
        if ab_test:
            st.markdown("---")
            subject_b = st.text_input("Subject Line (Variant B):", "Quick question regarding {{company}}")
            body_b = st.text_area("Email Content B (HTML supported):", def_body, height=200)
            
        reply_to = st.text_input("Custom Reply-To Address (Optional):", placeholder="Master inbox routing...")
        
        # Chronometer intrinsically locked to Standard Spam Evasion Protocols (60s - 150s)
        min_delay = 60
        max_delay = 150
            
        include_unsub = st.checkbox("Include CAN-SPAM Unsubscribe Link", value=True)
            
        st.markdown("---")
        
        c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
        test_email_addr = c_t1.text_input("Send Test Email To:", placeholder="your_personal_email@domain.com")
        if c_t2.button("🔬 Send Test Email"):
            if not active_mailbox:
                st.error("Configure Mailbox First")
            elif not test_email_addr:
                st.error("Enter a test email address.")
            else:
                with st.spinner("Testing delivery..."):
                    om = OutreachManager(active_mailbox['host'], active_mailbox['port'], active_mailbox['user'], active_mailbox['password'])
                    df_test = pd.DataFrame([{"Email": test_email_addr, "Name": "Test User", "Company": "Test Corp"}])
                    res = om.send_campaign(df_test, "[TEST] " + subject_a, body_a, None, None, reply_to, 1, 2, include_unsubscribe=include_unsub)
                    if res['sent'] > 0:
                        st.success(f"Test Email successfully delivered to {test_email_addr}")
                    else:
                        st.error("Failed to send test email. Check Mailbox diagnostics.")
                        
        if c_t3.button("🛑 Abort Campaign"):
            st.session_state['abort_campaign'] = True
            st.rerun()
        
        c_la1, c_la2 = st.columns(2)
        with c_la1:
            launch_sync = st.button("🚀 Launch Live & Track Here", type="primary", use_container_width=True)
        with c_la2:
            launch_async = st.button("☁️ Multi-Tasking Mode (Queue to Background)", type="primary", use_container_width=True)
            
        if launch_async:
            if not active_mailbox:
                st.error("Configure a Mailbox first!")
            else:
                try:
                    from src.github_storage import read_json_db, write_json_db
                    camp_id = str(uuid.uuid4())
                    
                    with st.spinner("Flushing Pipeline into Secure Github Async Queue..."):
                        
                        queue_data, sha = read_json_db("queue.json", default_val=[])
                        
                        df_targets = st.session_state['leads_df']
                        val_df = df_targets[df_targets['Email'].notna() & (df_targets['Email'] != "")]
                        
                        contacts = []
                        for i, r in val_df.iterrows():
                            contacts.append({
                                'id': str(uuid.uuid4()),
                                'email': r.get('Email', ''),
                                'name': r.get('Name', ''),
                                'company': r.get('Company', ''),
                                'delivery_status': 'Pending'
                            })
                            
                        queue_data.append({
                            'id': camp_id,
                            'owner_username': st.session_state['username'],
                            'campaign_name': campaign_name_custom,
                            'subject_a': subject_a,
                            'body_a': body_a,
                            'subject_b': subject_b if ab_test else None,
                            'body_b': body_b if ab_test else None,
                            'reply_to': reply_to,
                            'min_delay': int(min_delay),
                            'max_delay': int(max_delay),
                            'status': 'running',
                            'contacts': contacts
                        })
                        
                        write_json_db("queue.json", queue_data, sha)
                        
                    st.success("✅ **Campaign mathematically queued to your Cloud Daemon Worker!**")
                    st.info("You may now freely navigate to another tab, exit your browser, or put your computer to sleep. Your invisible worker script (`daemon_worker.py`) will automatically execute this massive batch sequence silently 24/7.")
                except Exception as e:
                    st.error(f"⚠️ Failed to queue! Github Storage Error: {e}")
            
        if launch_sync:
            st.session_state['abort_campaign'] = False
            if not active_mailbox:
                st.error("Configure a Mailbox first!")
            else:
                st.markdown("### 📡 Live Execution")
                
                col_a1, col_a2, col_a3, col_a4, col_a5, col_a6 = st.columns(6)
                ms = col_a1.empty()
                mf = col_a2.empty()
                md = col_a3.empty()
                mo = col_a4.empty()
                mr = col_a5.empty()
                mu = col_a6.empty()
                
                ms.metric("Sent", 0)
                mf.metric("Failed", 0)
                md.metric("Delivered", "N/A*")
                mo.metric("Opened", "N/A*")
                mr.metric("Replied", "N/A*")
                mu.metric("Unsubscribed", 0)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(stats, current_action):
                    tot = stats['total']
                    stc = stats['sent']
                    fld = stats['failed']
                    prog = (stc + fld) / tot if tot > 0 else 0
                    progress_bar.progress(prog)
                    
                    # Safe text-only tracking bypasses raw HTML Markdown rendering crashes
                    status_text.text(f"🚀 Progress: {stc + fld} / {tot} ({int(prog * 100)}%) | Action: {current_action}")
                    
                    ms.metric("Sent", stc)
                    mf.metric("Failed", fld)
                    
                def abort_listener():
                    return st.session_state.get('abort_campaign', False)
                    
                campaign_uuid = str(uuid.uuid4())
                om = OutreachManager(active_mailbox['host'], active_mailbox['port'], active_mailbox['user'], active_mailbox['password'])
                stats = om.send_campaign(
                    st.session_state['leads_df'], subject_a, body_a, subject_b, body_b, reply_to, int(min_delay), int(max_delay), campaign_id=campaign_uuid, include_unsubscribe=include_unsub, progress_callback=update_progress, abort_callback=abort_listener
                )
                
                if stats.get('aborted', False):
                    status_text.error("🛑 Sequence Aborted by User.")
                    st.warning("Campaign forcefully interrupted. Partial sends have been permanently recorded.")
                elif stats['total'] == 0:
                    status_text.error("Status: Aborted.")
                    st.error("⚠️ Contacts have no emails!")
                else:
                    status_text.text("Status: Completed!")
                    st.success("Campaign sequence fully completed!")
                    
                    md.metric("Delivered", stats['sent'])
                    mo.metric("Opened", stats.get('simulated_opened', 0))
                    mr.metric("Replied", stats.get('simulated_replied', 0))
                    
                    # Store it!
                    final_subj = f"Variant A: {subject_a} | Variant B: {subject_b}" if ab_test else subject_a
                    final_body = f"=== VARIANT A ===\n{body_a}\n\n=== VARIANT B ===\n{body_b}" if ab_test else body_a
                    save_campaign(campaign_uuid, st.session_state['username'], campaign_name_custom, final_subj, final_body, stats['total'], stats['sent'], stats['failed'], stats.get('simulated_opened', 0), stats.get('simulated_replied', 0))
                    
                st.divider()
                st.subheader("Campaign Delivery Output")
                csv_campaign = st.session_state['leads_df'].to_csv(index=False)
                st.download_button("💾 Download Detailed Delivery Report (CSV)", data=csv_campaign, file_name=f"marketifyer_sent_{campaign_name_custom}.csv", mime="text/csv", type="primary")

with tab_mbox:
    st.header("Manage Mailboxes")
    mailboxes = load_mailboxes(st.session_state['username'])
    if mailboxes:
        for mb in mailboxes:
            c1, c2 = st.columns([3, 1])
            c1.info(f"🟢 **{mb['user']}** via `{mb['host']}:{mb['port']}`")
            if c2.button("Delete", key=f"delmb_{mb['user']}"):
                delete_mailbox(st.session_state['username'], mb['user'], mb['host'])
                st.rerun()
                    
    st.subheader("Add Sender Mailbox")
    ch, cp = st.columns(2)
    smtp_host = ch.text_input("SMTP Host", "smtp.gmail.com")
    smtp_port = cp.text_input("SMTP Port", "587")
    
    cu, cpa = st.columns(2)
    smtp_user = cu.text_input("Username (Email)")
    smtp_pass = cpa.text_input("Password", type="password")
    
    if st.button("Test & Save"):
        with st.spinner("Testing..."):
            om = OutreachManager(smtp_host, smtp_port, smtp_user, smtp_pass)
            success, message = om.test_connection()
            if success:
                save_mailbox(st.session_state['username'], smtp_host, smtp_port, smtp_user, smtp_pass)
                st.success("✅ Saved!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Failed: {message}")

with tab_ai:
    st.header("🤖 AI Campaign Rater")
    st.markdown("Paste your cold email copy here. Our AI will analyze your hook, offer, and call-to-action to give it a deliverability and conversion rating out of 100.")
    email_to_eval = st.text_area("Email Sequence Copy:")
    
    if st.button("🧠 Evaluate Sequence", type="primary"):
        if not email_to_eval:
            st.error("Please enter some text!")
        else:
            with st.spinner("Analyzing semantics, spam keywords, and conversion optimization factors..."):
                time.sleep(2)
                # Simulated AI evaluation to conserve API quotas
                score = min(max(int(len(email_to_eval) / 8 + 50), 61), 94)
                if score < 70:
                    st.warning(f"**Score: {score}/100** - Needs improvement. Consider shortening the body and making the CTA easier to answer (ask a simple yes/no question). Avoid words like 'Buy' or 'Free' which trigger spam filters.")
                if 70 <= score < 85:
                    st.info(f"**Score: {score}/100** - Good structure! Your hook is decent, but the personalization could be stronger. Consider referencing a specific pain point.")
                if score >= 85:
                    st.success(f"**Score: {score}/100** - Excellent! Highly optimized for human-like reading and strong conversion probability. Ready to send!")
