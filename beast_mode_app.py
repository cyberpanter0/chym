import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

# Sayfa yapılandırması
st.set_page_config(
    page_title="🦁 Beast Mode Fitness Coach",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Mobil uyumlu
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF6B35;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .coach-response {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FF6B35;
        margin: 20px 0;
    }
    .stats-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #FF6B35;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
    }
    .protocol-section {
        background-color: #fff5f5;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Beast Mode veri seti
@st.cache_data
def load_beast_mode_data():
    return {
        "hafta_1_2": {
            "sabah_egzersizleri": [
                {"egzersiz": "Pike Push-up", "set_rep": "5x8-12", "notlar": "3sn negatif"},
                {"egzersiz": "Diamond Push-up", "set_rep": "5x6-10", "notlar": "2sn pause"},
                {"egzersiz": "Bulgarian Split Squat", "set_rep": "5x15/15", "notlar": "tempo: 3-1-2-1"},
                {"egzersiz": "Single Arm Push-up Progression", "set_rep": "4x5/5", "notlar": "duvar destekli"},
                {"egzersiz": "Archer Squat Progression", "set_rep": "4x8/8", "notlar": ""},
                {"egzersiz": "L-Sit Hold", "set_rep": "5x15-30sn", "notlar": ""},
                {"egzersiz": "Hollow Body Hold", "set_rep": "3x45-60sn", "notlar": ""},
                {"egzersiz": "Handstand Wall Walk", "set_rep": "4x5 adım", "notlar": ""}
            ],
            "aksam_egzersizleri": [
                {"egzersiz": "Pistol Squat Progression", "set_rep": "4x5/5", "notlar": ""},
                {"egzersiz": "One Arm Plank", "set_rep": "3x20sn/taraf", "notlar": ""},
                {"egzersiz": "Hindu Push-up", "set_rep": "3x12-15", "notlar": ""},
                {"egzersiz": "Burpee to Tuck Jump", "set_rep": "3x10", "notlar": ""}
            ]
        },
        "hafta_3_6": {
            "sabah_protokol": "Her hareket 6 set, 6-12 tekrar, 90sn dinlenme. Negatif faz 3-5sn",
            "aksam_protokol": "Süpersetler, 15-25 tekrar. Set arası 30sn, süperset arası 60sn. Tempo: patlayıcı yukarı, kontrollü aşağı"
        },
        "hafta_7_12": {
            "ileri_seviye_hareketler": [
                "One Arm Push-up (assisted → unassisted)",
                "Handstand Push-up (wall → freestanding)",
                "Pistol Squat (tam hareket)",
                "Muscle-up Progression",
                "Human Flag Progression",
                "Front Lever Progression",
                "Planche Progression"
            ]
        },
        "zorlanma_teknikleri": {
            "Time Under Tension (TUT)": "3sn yukarı, 2sn dur, 4sn aşağı, 1sn dur",
            "Cluster Sets": "6 tekrar → 15sn → 4 tekrar → 15sn → 2 tekrar",
            "Mechanical Drop Sets": "One Arm → Diamond → Normal → Knee Push-up (maks tekrar)",
            "Isometric Holds + Plyometrics": "10sn hold + 5 patlayıcı tekrar x 5 set"
        },
        "beslenme_plani": {
            "gunluk_program": [
                {"saat": "05:30", "icerik": "500ml su"},
                {"saat": "06:00", "icerik": "1 muz + kahve"},
                {"saat": "06:15-07:00", "icerik": "Sabah antrenmanı"},
                {"saat": "07:15", "icerik": "Protein shake + bal"},
                {"saat": "08:00", "icerik": "Kahvaltı"},
                {"saat": "11:00", "icerik": "Ara öğün"},
                {"saat": "13:30", "icerik": "Öğle yemeği"},
                {"saat": "16:00", "icerik": "Pre-workout atıştırmalık"},
                {"saat": "17:30-18:30", "icerik": "Akşam antrenmanı"},
                {"saat": "18:45", "icerik": "Süt + muz"},
                {"saat": "20:00", "icerik": "Akşam yemeği"},
                {"saat": "22:00", "icerik": "Casein + kuruyemiş"},
                {"saat": "22:30", "icerik": "Yatma"}
            ],
            "makrolar": {
                "protein": "150-170g",
                "karbonhidrat": "340-400g",
                "yag": "75-85g",
                "toplam_kalori": "2800-3200 kcal"
            }
        },
        "takviyeler": [
            {"isim": "Whey Protein", "dozaj": "30g (2x)"},
            {"isim": "Kreatin Monohydrate", "dozaj": "5g (18+ yaş)"},
            {"isim": "Multivitamin", "dozaj": "1 tablet"},
            {"isim": "Omega-3", "dozaj": "2-3g"},
            {"isim": "Magnezyum", "dozaj": "400mg"},
            {"isim": "Çinko", "dozaj": "15mg"},
            {"isim": "D3 Vitamini", "dozaj": "2000 IU"},
            {"isim": "Beta-Alanine", "dozaj": "3-5g (isteğe bağlı)"},
            {"isim": "L-Citrulline", "dozaj": "6-8g (isteğe bağlı)"},
            {"isim": "HMB", "dozaj": "3g (isteğe bağlı)"}
        ],
        "uyku_ve_dinlenme": {
            "program": [
                {"saat": "21:30", "aksiyon": "Ekranları kapat"},
                {"saat": "21:45", "aksiyon": "Sıcak duş al"},
                {"saat": "22:00", "aksiyon": "Magnezyum al"},
                {"saat": "22:15", "aksiyon": "Meditasyon/nefes"},
                {"saat": "22:30", "aksiyon": "Yatma"},
                {"saat": "07:00", "aksiyon": "Uyanış (8.5 saat uyku)"}
            ],
            "oda_kosullari": {
                "sicaklik": "16-18°C",
                "nem": "%30-50",
                "isik": "Tam karanlık",
                "ses": "Sessizlik (kulak tıkacı)"
            }
        }
    }

# Session state initialize
if 'daily_entries' not in st.session_state:
    st.session_state.daily_entries = []

if 'current_user' not in st.session_state:
    st.session_state.current_user = {
        'name': '',
        'weight': 70,  # Changed from 0 to 70 (default value within min_value range)
        'current_week': 1
    }

# Mesaj tipi analizi
def analyze_message_type(message):
    daily_keywords = [
        'bugün', 'uyudum', 'kiloyum', 'antrenman yaptım', 'yorgunum',
        'enerji', 'motivasyon', 'yedim', 'içtim', 'hissediyorum',
        'kendimi', 'durumum', 'günüm', 'sabah', 'akşam'
    ]
    
    query_keywords = [
        'hafta', 'beslenme', 'beast mode', 'egzersiz', 'antrenman',
        'takviye', 'uyku', 'protokol', 'program', 'zorlanma',
        'teknik', 'nasıl', 'ne zaman', 'kaç', 'hangi'
    ]
    
    message_lower = message.lower()
    daily_count = sum(1 for keyword in daily_keywords if keyword in message_lower)
    query_count = sum(1 for keyword in query_keywords if keyword in message_lower)
    
    return 'daily' if daily_count > query_count else 'query'

# İlgili veri getirme
def get_relevant_data(message, beast_mode_data):
    message_lower = message.lower()
    
    if any(x in message_lower for x in ['hafta 1', 'hafta 2', '1-2']):
        return beast_mode_data['hafta_1_2']
    elif any(x in message_lower for x in ['hafta 3', 'hafta 4', 'hafta 5', 'hafta 6', '3-6']):
        return beast_mode_data['hafta_3_6']
    elif any(x in message_lower for x in ['hafta 7', 'hafta 8', 'hafta 9', 'hafta 10', 'hafta 11', 'hafta 12', '7-12']):
        return beast_mode_data['hafta_7_12']
    elif any(x in message_lower for x in ['beslenme', 'yemek', 'makro']):
        return beast_mode_data['beslenme_plani']
    elif any(x in message_lower for x in ['takviye', 'supplement']):
        return beast_mode_data['takviyeler']
    elif any(x in message_lower for x in ['uyku', 'dinlenme', 'recovery']):
        return beast_mode_data['uyku_ve_dinlenme']
    elif any(x in message_lower for x in ['zorlanma', 'teknik', 'intensity']):
        return beast_mode_data['zorlanma_teknikleri']
    else:
        return beast_mode_data

# Groq API çağrısı
def call_groq_api(user_message, groq_api_key, context_data=None):
    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        
        if context_data:
            system_message = f"""Sen profesyonel bir fitness koçusun. Kullanıcı şu soruyu sordu: "{user_message}"
            
Aşağıda referans Beast Mode antrenman protokolü yer alıyor. Bu protokole göre net, motive edici, Türkçe bir yanıt ver.

Referans Veri:
{json.dumps(context_data, ensure_ascii=False, indent=2)}

Yanıtın özellikleri:
- Motive edici ve profesyonel ol
- Protokoldeki bilgileri referans al
- Kısa ve öz ol (max 200 kelime)
- Türkçe yanıt ver
- Emoji kullan"""
        else:
            system_message = f"""Sen profesyonel bir fitness koçusun ve kullanıcının kişisel antrenörüsün. 
            
Kullanıcı şu günlük mesajı yazdı: "{user_message}"

Beast Mode protokolünü takip eden birinin koçu olarak:
- Destekleyici ve motive edici ol
- Kısa ve öz yanıt ver (max 100 kelime)
- Türkçe yanıt ver
- Gerekirse tavsiye ver
- Pozitif yaklaş
- Emoji kullan"""
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return f"❌ API Hatası: {response.status_code}"
            
    except Exception as e:
        return f"❌ Hata: {str(e)}"

# Ana başlık
st.markdown('<h1 class="main-header">🦁 BEAST MODE FITNESS COACH</h1>', unsafe_allow_html=True)

# Sidebar - Kullanıcı bilgileri
with st.sidebar:
    st.header("👤 Profil Bilgileri")
    
    name = st.text_input("İsim", value=st.session_state.current_user['name'])
    # Fixed: Ensure the default value is within the min_value range
    weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=max(40, st.session_state.current_user.get('weight', 70)))
    current_week = st.selectbox("Hangi haftadasın?", [1,2,3,4,5,6,7,8,9,10,11,12], index=st.session_state.current_user.get('current_week', 1)-1)
    
    if st.button("Profili Güncelle"):
        st.session_state.current_user.update({
            'name': name,
            'weight': weight,
            'current_week': current_week
        })
        st.success("✅ Profil güncellendi!")

    st.markdown("---")
    
    # API Key girişi
    st.header("🔑 API Ayarları")
    groq_api_key = st.text_input("Groq API Key", type="password", help="Groq API anahtarınızı girin")
    
    if not groq_api_key:
        st.warning("⚠️ API anahtarı girin")

# Ana içerik alanı
tab1, tab2, tab3, tab4 = st.tabs(["💬 Koçum", "📋 Beast Mode Protokolü", "📊 İstatistikler", "📈 İlerleme"])

# TAB 1: Ana Chat
with tab1:
    st.subheader("🤖 Kişisel Antrenörünle Konuş")
    
    # Chat arayüzü
    user_message = st.text_area(
        "Bugün nasılsın? Mesajını yaz...",
        height=100,
        placeholder="Örnek: Bugün çok yorgunum, motivasyonum düşük..."
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📤 Gönder", use_container_width=True):
            if user_message and groq_api_key:
                with st.spinner("🤔 Koçun düşünüyor..."):
                    beast_mode_data = load_beast_mode_data()
                    message_type = analyze_message_type(user_message)
                    
                    if message_type == 'daily':
                        ai_response = call_groq_api(user_message, groq_api_key)
                    else:
                        relevant_data = get_relevant_data(user_message, beast_mode_data)
                        ai_response = call_groq_api(user_message, groq_api_key, relevant_data)
                    
                    # Session state'e kaydet
                    entry = {
                        'timestamp': datetime.now(),
                        'message': user_message,
                        'response': ai_response,
                        'type': message_type
                    }
                    st.session_state.daily_entries.append(entry)
                    
                    # Yanıtı göster
                    st.markdown(f'<div class="coach-response"><strong>🦁 Beast Mode Koçu:</strong><br>{ai_response}</div>', unsafe_allow_html=True)
            elif not groq_api_key:
                st.error("❌ Lütfen API anahtarınızı girin!")
            else:
                st.error("❌ Lütfen bir mesaj yazın!")
    
    with col2:
        if st.button("🗑️ Temizle", use_container_width=True):
            st.rerun()
    
    # Son mesajları göster
    if st.session_state.daily_entries:
        st.subheader("💭 Son Konuşmalar")
        for i, entry in enumerate(reversed(st.session_state.daily_entries[-5:])):
            with st.expander(f"{entry['timestamp'].strftime('%H:%M')} - {entry['message'][:50]}..."):
                st.write(f"**Sen:** {entry['message']}")
                st.write(f"**Koç:** {entry['response']}")

# TAB 2: Beast Mode Protokolü
with tab2:
    st.subheader("📋 Beast Mode Antrenman Protokolü")
    
    beast_mode_data = load_beast_mode_data()
    
    # Hafta seçimi
    selected_week = st.selectbox("Hangi haftayı görmek istiyorsun?", 
                                ["Hafta 1-2: Temel", "Hafta 3-6: Güç", "Hafta 7-12: İleri"])
    
    if "1-2" in selected_week:
        data = beast_mode_data['hafta_1_2']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
            st.markdown("### 🌅 Sabah Egzersizleri")
            for ex in data['sabah_egzersizleri']:
                st.markdown(f"**{ex['egzersiz']}**")
                st.markdown(f"📊 {ex['set_rep']}")
                if ex['notlar']:
                    st.markdown(f"📝 {ex['notlar']}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
            st.markdown("### 🌙 Akşam Egzersizleri")
            for ex in data['aksam_egzersizleri']:
                st.markdown(f"**{ex['egzersiz']}**")
                st.markdown(f"📊 {ex['set_rep']}")
                if ex['notlar']:
                    st.markdown(f"📝 {ex['notlar']}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif "3-6" in selected_week:
        data = beast_mode_data['hafta_3_6']
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
            st.markdown("### 🌅 Sabah Protokolü")
            st.markdown(data['sabah_protokol'])
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
            st.markdown("### 🌙 Akşam Protokolü")
            st.markdown(data['aksam_protokol'])
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # 7-12
        data = beast_mode_data['hafta_7_12']
        
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.markdown("### 🔥 İleri Seviye Hareketler")
        for movement in data['ileri_seviye_hareketler']:
            st.markdown(f"• {movement}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Beslenme bölümü
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥗 Beslenme Programı")
        nutrition = beast_mode_data['beslenme_plani']
        
        st.markdown("**📅 Günlük Program:**")
        for meal in nutrition['gunluk_program']:
            st.markdown(f"**{meal['saat']}** - {meal['icerik']}")
    
    with col2:
        st.markdown("### 💊 Takviyeler")
        for supplement in beast_mode_data['takviyeler']:
            st.markdown(f"• **{supplement['isim']}**: {supplement['dozaj']}")

# TAB 3: İstatistikler
with tab3:
    st.subheader("📊 Günlük İstatistikler")
    
    if st.session_state.daily_entries:
        # Genel istatistikler
        total_entries = len(st.session_state.daily_entries)
        today_entries = len([e for e in st.session_state.daily_entries 
                           if e['timestamp'].date() == datetime.now().date()])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("📝 Toplam Giriş", total_entries)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("📅 Bugün", today_entries)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            daily_entries = [e for e in st.session_state.daily_entries 
                           if e['type'] == 'daily']
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("💭 Günlük Mesaj", len(daily_entries))
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Son girişler
        st.markdown("### 📋 Son Girişler")
        for entry in reversed(st.session_state.daily_entries[-10:]):
            st.markdown(f"**{entry['timestamp'].strftime('%d/%m %H:%M')}** - {entry['message'][:100]}...")
    
    else:
        st.info("📈 Henüz giriş yok. Koçunla konuşmaya başla!")

# TAB 4: İlerleme Grafiği
with tab4:
    st.subheader("📈 İlerleme Takibi")
    
    if st.session_state.daily_entries:
        # Günlük aktivite grafiği
        df_entries = pd.DataFrame([
            {
                'date': entry['timestamp'].date(),
                'hour': entry['timestamp'].hour,
                'type': entry['type']
            }
            for entry in st.session_state.daily_entries
        ])
        
        # Günlük giriş sayısı
        daily_counts = df_entries.groupby('date').size().reset_index()
        daily_counts.columns = ['Tarih', 'Giriş Sayısı']
        
        fig = px.line(daily_counts, x='Tarih', y='Giriş Sayısı', 
                     title='📊 Günlük Aktivite Trendi',
                     markers=True)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Saatlik dağılım
        if len(df_entries) > 5:
            hourly_dist = df_entries.groupby('hour').size().reset_index()
            hourly_dist.columns = ['Saat', 'Mesaj Sayısı']
            
            fig2 = px.bar(hourly_dist, x='Saat', y='Mesaj Sayısı',
                         title='🕐 Hangi Saatlerde Daha Aktifsin?')
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.info("📊 Grafik için veri bekleniyor. Koçunla konuşmaya başla!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8rem;'>
    🦁 Beast Mode Fitness Coach - Kişisel Antrenör Asistanı<br>
    💪 Her gün daha güçlü ol!
    </div>
    """, 
    unsafe_allow_html=True
)