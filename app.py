import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- YAPI VE VERİTABANI ---
DB_NAME = "bookclub.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Buluşmalar Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT,
            voting_deadline TEXT,
            created_by TEXT,
            status TEXT DEFAULT 'Aktif'
        )
    ''')
    
    # Kitaplar Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER,
            title TEXT NOT NULL,
            author TEXT,
            suggested_by TEXT,
            date_suggested TEXT,
            notes TEXT,
            status TEXT DEFAULT 'Önerildi'
        )
    ''')
    
    # Geriye dönük uyumluluk (Eski tablolara sütun ekleme)
    try:
        c.execute("ALTER TABLE books ADD COLUMN meeting_id INTEGER")
    except sqlite3.OperationalError:
        pass
    
    # Oylar Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            voter_name TEXT,
            UNIQUE(book_id, voter_name),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    # Değerlendirme (Puan) Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            rater_name TEXT,
            score INTEGER,
            UNIQUE(book_id, rater_name)
        )
    ''')
    conn.commit()
    conn.close()

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(query, params)
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Aynı kişi aynı kitaba iki kez oy veremez
    finally:
        conn.close()

def fetch_data(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- KULLANICI ARAYÜZÜ ---
st.set_page_config(page_title="Kitap Kulübü", page_icon="📚", layout="wide")

init_db()

# Tema ve Stil
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Background Gradient */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 50%, #020617 100%);
    }

    /* Glassmorphism for sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Buttons with hover animation */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255,255,255,0.1);
        font-weight: 500;
        letter-spacing: 0.3px;
        background-color: rgba(99, 102, 241, 0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(99, 102, 241, 0.25);
        border-color: rgba(99, 102, 241, 0.5);
        background-color: rgba(99, 102, 241, 0.2);
    }
    
    /* Main Headers */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #a5b4fc, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(30, 41, 59, 0.4);
        padding: 10px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 16px;
        transition: all 0.3s ease;
        background-color: transparent;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.2) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
    }
    .stTabs [aria-selected="true"] div {
        color: #fff !important;
        font-weight: 600;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        border-radius: 8px;
        background-color: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Info Box */
    .stAlert {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

st.title("📚 Kitap Kulübü Merkezi")

MEMBERS = {
    "Abdullah": "💻",
    "Reyna": "👑",
    "Settar": "📖",
    "Kutay": "🥨",
    "Ecem": "⭐",
    "Ayşe": "✈️",
    "Yaman": "💪",
    "Aslı": "🏃‍♀️",
    "Buse": "🧴"
}

if 'username' not in st.session_state:
    st.session_state['username'] = ""

with st.sidebar:
    st.markdown("<h2 style='-webkit-text-fill-color: #f8fafc;'>👤 Profil</h2>", unsafe_allow_html=True)
    
    options = ["👀 Sen kimsin?"] + [f"{emoji} {name}" for name, emoji in MEMBERS.items()]
    
    default_index = 0
    if st.session_state['username'] in MEMBERS:
        default_index = list(MEMBERS.keys()).index(st.session_state['username']) + 1
        
    selected_profile = st.selectbox("Kendini seç:", options, index=default_index)
    
    if selected_profile != "👀 Sen kimsin?":
        name = selected_profile.split(" ", 1)[1]
        st.session_state['username'] = name
        st.success(f"Hoş geldin, {name}!")
    else:
        st.session_state['username'] = ""
        st.warning("Lütfen listeden kendini seç.")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 Ana Sayfa & Oylama", "📅 Yeni Buluşma Planla", "🏆 Seçilen Kitaplar", "🕰️ Geçmiş"])

with tab2:
    st.header("📅 Yeni Bir Buluşma ve Oylama Başlat")
    st.write("Kitap kulübü için yeni bir buluşma tarihi belirle.")
    
    with st.form("new_meeting_form", clear_on_submit=True):
        m_title = st.text_input("Buluşma Adı (Örn: Temmuz Ayı Kitap Kulübü)")
        
        col1, col2 = st.columns(2)
        with col1:
            m_date = st.date_input("Buluşma Tarihi")
        with col2:
            m_time = st.time_input("Buluşma Saati")
            
        submit_meeting = st.form_submit_button("Buluşmayı Oluştur ve Oylamayı Başlat")
        
        if submit_meeting:
            if not st.session_state['username']:
                st.error("Lütfen sol menüden adınızı girin!")
            elif not m_title:
                st.error("Buluşma adı zorunludur.")
            else:
                meeting_dt = f"{m_date} {m_time.strftime('%H:%M')}"
                
                # Yeni buluşma başlatıldığında eskilerini 'Tamamlandı' yapıyoruz
                execute_query("UPDATE meetings SET status = 'Tamamlandı' WHERE status = 'Aktif'")
                
                execute_query(
                    "INSERT INTO meetings (title, meeting_date, voting_deadline, created_by) VALUES (?, ?, '', ?)",
                    (m_title, meeting_dt, st.session_state['username'])
                )
                st.success("Yeni buluşma başarıyla oluşturuldu ve aktif hale getirildi!")
                st.rerun()

    active_m = fetch_data("SELECT * FROM meetings WHERE status = 'Aktif' ORDER BY id DESC LIMIT 1")
    if not active_m.empty:
        st.markdown("---")
        st.subheader("✏️ Aktif Buluşmayı Düzenle")
        act_id = active_m.iloc[0]['id']
        act_title = active_m.iloc[0]['title']
        act_date_str = active_m.iloc[0]['meeting_date']
        
        try:
            act_dt = datetime.strptime(act_date_str, "%Y-%m-%d %H:%M")
            def_d = act_dt.date()
            def_t = act_dt.time()
        except:
            def_d = datetime.now().date()
            def_t = datetime.now().time()
            
        with st.form("edit_meeting_form"):
            e_title = st.text_input("Buluşma Adı", value=act_title)
            c1, c2 = st.columns(2)
            with c1:
                e_date = st.date_input("Yeni Buluşma Tarihi", value=def_d)
            with c2:
                e_time = st.time_input("Yeni Buluşma Saati", value=def_t)
                
            if st.form_submit_button("Değişiklikleri Kaydet"):
                if not st.session_state['username']:
                    st.error("Lütfen sol menüden adınızı girin!")
                elif not e_title:
                    st.error("Buluşma adı zorunludur.")
                else:
                    new_dt = f"{e_date} {e_time.strftime('%H:%M')}"
                    execute_query("UPDATE meetings SET title = ?, meeting_date = ? WHERE id = ?", (e_title, new_dt, int(act_id)))
                    st.success("Aktif buluşma güncellendi!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Tüm Buluşmalar")
    df_m = fetch_data("SELECT id, title as 'Başlık', meeting_date as 'Buluşma Tarihi', status as 'Durum' FROM meetings ORDER BY id DESC")
    if not df_m.empty:
        # Renklendirme fonksiyonu
        def color_status_m(val):
            color = '#4ade80' if val == 'Aktif' else '#94a3b8'
            return f'color: {color}; font-weight: bold;'
        st.dataframe(df_m.style.map(color_status_m, subset=['Durum']), use_container_width=True, hide_index=True)


with tab1:
    st.header("🗳️ Kitap Önerileri ve Oylama")
    
    # Get active meeting
    active_meeting = fetch_data("SELECT * FROM meetings WHERE status = 'Aktif' ORDER BY id DESC LIMIT 1")
    
    if active_meeting.empty:
        st.warning("Şu an planlanmış aktif bir buluşma/oylama yok. Lütfen '📅 Yeni Buluşma Planla' sekmesine giderek bir etkinlik oluşturun.")
        
        # Sıradaki buluşma ve seçilen kitap bilgisi gösterimi
        latest_completed = fetch_data("SELECT * FROM meetings WHERE status = 'Tamamlandı' ORDER BY id DESC LIMIT 1")
        if not latest_completed.empty:
            comp_id = latest_completed.iloc[0]['id']
            comp_title = latest_completed.iloc[0]['title']
            comp_date = latest_completed.iloc[0]['meeting_date']
            
            # Bu buluşmada seçilen kitabı bul
            selected_book = fetch_data("SELECT * FROM books WHERE meeting_id = ? AND status = 'Seçildi' LIMIT 1", (int(comp_id),))
            
            if not selected_book.empty:
                b_title = selected_book.iloc[0]['title']
                b_author = selected_book.iloc[0]['author']
                b_sug = selected_book.iloc[0]['suggested_by']
                
                # Kalan süreyi hesapla
                days_left_str = ""
                try:
                    meeting_dt = datetime.strptime(comp_date, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    delta = meeting_dt - now
                    if delta.total_seconds() > 0:
                        days = delta.days
                        hours = delta.seconds // 3600
                        mins = (delta.seconds % 3600) // 60
                        days_left_str = f"⏳ Buluşmaya Kalan Süre: <b>{days} Gün, {hours} Saat, {mins} Dakika</b>"
                    else:
                        days_left_str = "⌛ Buluşma zamanı geldi/geçti!"
                except Exception as e:
                    days_left_str = ""
                
                st.markdown(f"""
                <div style="background-color: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 22px; margin-top: 25px; backdrop-filter: blur(10px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);">
                    <h3 style="margin-top: 0; color: #a5b4fc; font-weight: 700; background: -webkit-linear-gradient(45deg, #a5b4fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📖 Sıradaki Okuma ve Buluşma Bilgisi</h3>
                    <p style="font-size: 16px; margin-bottom: 8px; color: #f8fafc;"><b>Etkinlik:</b> {comp_title}</p>
                    <p style="font-size: 16px; margin-bottom: 8px; color: #f8fafc;"><b>Buluşma Tarihi:</b> {comp_date}</p>
                    <p style="font-size: 18px; color: #f8fafc; margin-bottom: 12px; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <b>Okunacak Kitap:</b> 📖 <i>{b_title}</i> - {b_author} <span style="font-size: 14px; color: #94a3b8; font-weight: normal;">(Öneren: {b_sug})</span>
                    </p>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 14px 0;">
                    <p style="font-size: 16px; color: #818cf8; font-weight: 600; margin: 0; display: flex; align-items: center; gap: 8px;">{days_left_str}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        m_id = active_meeting.iloc[0]['id']
        m_title = active_meeting.iloc[0]['title']
        m_date = active_meeting.iloc[0]['meeting_date']
        
        st.markdown(f"### 📍 Mevcut Etkinlik: {m_title} <span style='font-size:16px; color:#94a3b8;'>(Buluşma: {m_date})</span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🛑 Oylamayı Bitir & Kazananı Belirle", use_container_width=True, help="Oylamayı manuel olarak kapatır ve en çok oyu alanı kazanan ilan eder."):
                if not st.session_state['username']:
                    st.error("Bunun için ismini girmelisin!")
                else:
                    # Find winner
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("""
                        SELECT b.id, COUNT(v.id) as v_count 
                        FROM books b 
                        LEFT JOIN votes v ON b.id = v.book_id 
                        WHERE b.meeting_id = ? 
                        GROUP BY b.id 
                        ORDER BY v_count DESC, b.id ASC LIMIT 1
                    """, (int(m_id),))
                    winner = c.fetchone()
                    if winner:
                        c.execute("UPDATE books SET status = 'Seçildi' WHERE id = ?", (winner[0],))
                    c.execute("UPDATE meetings SET status = 'Tamamlandı' WHERE id = ?", (int(m_id),))
                    conn.commit()
                    conn.close()
                    st.success("Oylama tamamlandı ve kazanan belirlendi!")
                    st.rerun()

        with st.expander("💡 Bu Buluşma İçin Yeni Bir Kitap Öner", expanded=False):
            with st.form("suggest_form", clear_on_submit=True):
                colA, colB = st.columns(2)
                with colA:
                    book_title = st.text_input("Kitap Adı*")
                    book_author = st.text_input("Yazar*")
                with colB:
                    notes = st.text_area("Notlar / Neden bu kitap?", height=110)
                
                submit_suggestion = st.form_submit_button("Öneriyi Gönder")
                
                if submit_suggestion:
                    if not st.session_state['username']:
                        st.error("Lütfen sol menüden adınızı girin!")
                    elif not book_title or not book_author:
                        st.error("Lütfen kitap adı ve yazar alanlarını doldurun.")
                    else:
                        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        execute_query(
                            "INSERT INTO books (meeting_id, title, author, suggested_by, date_suggested, notes) VALUES (?, ?, ?, ?, ?, ?)",
                            (int(m_id), book_title, book_author, st.session_state['username'], date_now, notes)
                        )
                        st.success("Kitap başarıyla önerildi!")
                        st.rerun()

        st.markdown("---")
        
        query = """
        SELECT b.id, b.title, b.author, b.suggested_by, b.notes, b.status,
               COUNT(v.id) as vote_count,
               GROUP_CONCAT(v.voter_name, ', ') as voters
        FROM books b
        LEFT JOIN votes v ON b.id = v.book_id
        WHERE b.meeting_id = ?
        GROUP BY b.id
        ORDER BY vote_count DESC, b.id ASC
        """
        df_books = fetch_data(query, (int(m_id),))
        
        if df_books.empty:
            st.info("Bu buluşma için henüz kitap önerilmemiş.")
        else:
            total_votes = df_books['vote_count'].sum()
            
            for index, row in df_books.iterrows():
                is_selected = row['status'] == 'Seçildi'
                pct = int((row['vote_count'] / total_votes) * 100) if total_votes > 0 else 0
                
                # Dark Mode Compatible Poll Colors
                bg_color = "rgba(99, 102, 241, 0.15)" if is_selected else "rgba(30, 41, 59, 0.6)"
                bar_color = "#6366f1" if is_selected else "rgba(99, 102, 241, 0.4)"
                border_color = "rgba(99, 102, 241, 0.5)" if is_selected else "rgba(255, 255, 255, 0.05)"
                text_color = "#f8fafc"
                sub_text_color = "#94a3b8"
                badge_bg = "#6366f1"
                
                sel_badge = f"<span style='float:right; background:{badge_bg};color:white;padding:3px 8px;border-radius:10px;font-size:12px;margin-top:5px;box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);'>SEÇİLDİ</span>" if is_selected else ""
                voters_html = f"<div style='font-size: 13px; color: {sub_text_color}; margin-top: 6px; margin-left: 2px;'>👥 {row['voters']}</div>" if pd.notnull(row['voters']) and str(row['voters']).strip() != '' else ""
                note_text = f"<div style='font-size: 13px; color: {sub_text_color}; margin-top: 6px; margin-left: 2px; font-style: italic;'>💡 {row['suggested_by']}: {row['notes']}</div>" if pd.notnull(row['notes']) and str(row['notes']).strip() != '' else f"<div style='font-size: 13px; color: {sub_text_color}; margin-top: 6px; margin-left: 2px; font-style: italic;'>💡 Öneren: {row['suggested_by']}</div>"
                
                has_voted = st.session_state['username'] and st.session_state['username'] in (str(row['voters']).split(', ') if pd.notnull(row['voters']) and str(row['voters']).strip() != '' else [])
                
                html = f"""<div style="position: relative; background-color: {bg_color}; border-radius: 16px; padding: 14px 18px; margin-bottom: 8px; border: 1px solid {border_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.1); backdrop-filter: blur(8px);">
<div style="position: absolute; top: 0; left: 0; height: 100%; width: {pct}%; background-color: {bar_color}; opacity: 0.3; border-radius: 16px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);"></div>
<div style="position: relative; z-index: 1;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div style="font-size: 17px; color: {text_color}; font-weight: 600;">📖 {row['title']} <span style="font-size: 14px; color: {sub_text_color}; font-weight: 400;">- {row['author']}</span></div>
<div style="font-size: 14px; font-weight: 700; color: {text_color}; background-color: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 12px;">{row['vote_count']} Oy</div>
</div>
{sel_badge}
{note_text}
{voters_html}
</div>
</div>"""
                
                if not is_selected:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(html, unsafe_allow_html=True)
                    with col2:
                        st.write("") # Push button down slightly
                        if has_voted:
                            if st.button("❌ Geri Al", key=f"unvote_{row['id']}", use_container_width=True):
                                execute_query("DELETE FROM votes WHERE book_id = ? AND voter_name = ?", (row['id'], st.session_state['username']))
                                st.rerun()
                        else:
                            if st.button("🗳️ Oy Ver", key=f"vote_{row['id']}", use_container_width=True):
                                if not st.session_state['username']:
                                    st.error("İsim giriniz!")
                                else:
                                    execute_query("INSERT INTO votes (book_id, voter_name) VALUES (?, ?)", (row['id'], st.session_state['username']))
                                    st.rerun()
                else:
                    st.markdown(html, unsafe_allow_html=True)
                    
                if st.session_state['username'] and st.session_state['username'] == row['suggested_by'] and not is_selected:
                    with st.expander("⚙️ Önerini Düzenle veya Sil", expanded=False):
                        with st.form(f"edit_book_form_{row['id']}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                e_b_title = st.text_input("Kitap Adı", value=row['title'])
                            with c2:
                                e_b_author = st.text_input("Yazar", value=row['author'])
                            e_b_notes = st.text_area("Notlar", value=row['notes'] if row['notes'] else "")
                            
                            cc1, cc2 = st.columns(2)
                            with cc1:
                                if st.form_submit_button("💾 Değişiklikleri Kaydet", use_container_width=True):
                                    execute_query("UPDATE books SET title = ?, author = ?, notes = ? WHERE id = ?", (e_b_title, e_b_author, e_b_notes, row['id']))
                                    st.rerun()
                            with cc2:
                                if st.form_submit_button("🗑️ Öneriyi Sil", use_container_width=True):
                                    execute_query("DELETE FROM votes WHERE book_id = ?", (row['id'],))
                                    execute_query("DELETE FROM books WHERE id = ?", (row['id'],))
                                    st.rerun()
                                    
                st.write("")

with tab3:
    st.header("🎉 Okumak İçin Seçilen Kitaplar")
    st.write("Bu kısımda okumak için seçtiğimiz/okuduğumuz kitaplara 10 üzerinden puan vererek ne kadar beğenildiğini görebiliriz!")
    
    query = """
    SELECT b.id, m.title as meeting_title, b.title, b.author, b.suggested_by,
           AVG(r.score) as avg_score, COUNT(r.id) as rater_count
    FROM books b
    LEFT JOIN meetings m ON b.meeting_id = m.id
    LEFT JOIN ratings r ON b.id = r.book_id
    WHERE b.status IN ('Seçildi', 'Okundu') 
    GROUP BY b.id
    ORDER BY b.id DESC
    """
    df_selected = fetch_data(query)
    
    if df_selected.empty:
        st.info("Henüz seçilen bir kitap yok.")
    else:
        for index, row in df_selected.iterrows():
            if pd.isnull(row['title']):
                continue
            avg = round(row['avg_score'], 1) if pd.notnull(row['avg_score']) else 0
            count = row['rater_count']
            
            with st.expander(f"📖 {row['title']} - {row['author']} (⭐ {avg}/10)"):
                st.markdown(f"**Öneren:** {row['suggested_by']} | **Buluşma:** {row['meeting_title'] if row['meeting_title'] else 'Eski Sistem'}")
                st.markdown(f"**Ortalama Puan:** ⭐ {avg} *(Toplam {count} kişi puan verdi)*")
                
                # Puanlama kısmı
                col1, col2 = st.columns([3, 1])
                with col1:
                    user_score = st.slider("Bu kitaba puanın:", 1, 10, 5, key=f"slider_{row['id']}")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("Puanı Kaydet", key=f"rate_{row['id']}"):
                        if not st.session_state['username']:
                            st.error("Lütfen sol menüden adınızı giriniz!")
                        else:
                            # Varsa günceller, yoksa ekler
                            execute_query("INSERT OR REPLACE INTO ratings (book_id, rater_name, score) VALUES (?, ?, ?)", (row['id'], st.session_state['username'], user_score))
                            st.success("Puanın kaydedildi!")
                            st.rerun()


with tab4:
    st.header("📊 İstatistikler ve Geçmiş")
    
    st.subheader("🏆 Kimin Önerileri Daha Çok Seçildi?")
    chart_query = """
    SELECT suggested_by, COUNT(id) as count
    FROM books
    WHERE status IN ('Seçildi', 'Okundu')
    GROUP BY suggested_by
    ORDER BY count DESC
    """
    df_chart = fetch_data(chart_query)
    
    if not df_chart.empty:
        df_chart.set_index("suggested_by", inplace=True)
        st.bar_chart(df_chart, height=300)
    else:
        st.info("Henüz seçilen kitap olmadığı için grafik oluşturulamıyor.")
        
    st.markdown("---")
    st.subheader("🔍 Tüm Öneriler ve Detaylar")
    
    query = """
    SELECT IFNULL(m.title, 'Eski Sistem') as 'Buluşma', b.title as 'Kitap Adı', b.author as 'Yazar', 
           b.status as 'Durum', COUNT(v.id) as 'Oy Sayısı', GROUP_CONCAT(v.voter_name, ', ') as 'Oy Verenler'
    FROM books b
    LEFT JOIN meetings m ON b.meeting_id = m.id
    LEFT JOIN votes v ON b.id = v.book_id
    GROUP BY b.id
    ORDER BY b.id DESC
    """
    df_history = fetch_data(query)
    
    if df_history.empty:
        st.info("Kayıt bulunamadı.")
    else:
        def color_status(val):
            color = '#4ade80' if val == 'Seçildi' else '#fbbf24' if val == 'Önerildi' else '#f8fafc'
            return f'color: {color}; font-weight: bold;'
        st.dataframe(df_history.style.map(color_status, subset=['Durum']), use_container_width=True, hide_index=True)
