import ssl
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import time
import pymongo
from pymongo import MongoClient
import uuid
# Sayfa konfigürasyonu
st.set_page_config(
    page_title="🦁 Beast Mode Coach",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Stilleri
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B35;
    }
    .chat-message {
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 70%;
    }
    .user-message {
        background-color: #FF6B35;
        color: white;
        margin-left: 30%;
    }
    .ai-message {
        background-color: #f0f2f6;
        color: #333;
        margin-right: 30%;
    }
    .exercise-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
    }
    .program-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sabitler
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MONGODB_URI = "mongodb+srv://dyaloshwester:b9eoq3Hriw3ncm65@cluster0.x6sungc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Beast Mode Verileri - Düzeltilmiş
BEAST_MODE_DATA = {
    'exercises': {
        'pike push-up': {'muscle_group': 'shoulders', 'difficulty': 'intermediate'},
        'diamond push-up': {'muscle_group': 'chest', 'difficulty': 'intermediate'},
        'bulgarian split squat': {'muscle_group': 'legs', 'difficulty': 'intermediate'},
        'single arm push-up': {'muscle_group': 'chest', 'difficulty': 'advanced'},
        'archer squat': {'muscle_group': 'legs', 'difficulty': 'advanced'},
        'l-sit hold': {'muscle_group': 'core', 'difficulty': 'advanced'},
        'hollow body hold': {'muscle_group': 'core', 'difficulty': 'intermediate'},
        'handstand wall walk': {'muscle_group': 'shoulders', 'difficulty': 'advanced'},
        'pistol squat': {'muscle_group': 'legs', 'difficulty': 'advanced'},
        'one arm plank': {'muscle_group': 'core', 'difficulty': 'advanced'},
        'hindu push-up': {'muscle_group': 'chest', 'difficulty': 'intermediate'},
        'burpee': {'muscle_group': 'full_body', 'difficulty': 'intermediate'},
        'push-up': {'muscle_group': 'chest', 'difficulty': 'beginner'},
        'pull-up': {'muscle_group': 'back', 'difficulty': 'intermediate'},
        'squat': {'muscle_group': 'legs', 'difficulty': 'beginner'},
        'plank': {'muscle_group': 'core', 'difficulty': 'beginner'}
    },
    'muscle_groups': {
        'chest': '🫴 Göğüs',
        'back': '🔙 Sırt', 
        'legs': '🦵 Bacak',
        'core': '💪 Core',
        'shoulders': '🤲 Omuz',
        'arms': '💪 Kol',
        'full_body': '🎯 Tüm Vücut'
    }
}

# MongoDB Bağlantısı
@st.cache_resource
def init_mongodb():
    try:
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            maxPoolSize=10,
            retryWrites=True
        )
        client.admin.command('ping')
        st.success("✅ MongoDB Atlas bağlantısı başarılı!")
        db = client['beast_mode']
        return db
    except Exception as e:
        st.error(f"❌ MongoDB bağlantı hatası: {e}")
        return None
    
    except Exception as e:
        st.error(f"MongoDB bağlantı hatası: {e}")
        print(f"Detaylı hata: {e}")
        return None, None

        if username == "demo" and password == "demo":
            return {
                '_id': "demo-user",
                'name': "Demo Kullanıcı",
                'username': "demo",
                'password': "demo",
                'weight': 70,
                'age': 25,
                'goal': "muscle_gain",
                'join_date': datetime.now(),
                'beast_mode_score': 75
            }
        return None
# Session State
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'exercise_log' not in st.session_state:
        st.session_state.exercise_log = []
    if 'beast_mode_score' not in st.session_state:
        st.session_state.beast_mode_score = 75
    if 'db' not in st.session_state:
        st.session_state.db = init_mongodb()

# Günlük Program
DAILY_PROGRAM = {
    'hafta_1_2': {
        'sabah': [
            {'exercise': 'pike push-up', 'sets': 5, 'reps': '8-12', 'notes': '3sn negatif'},
            {'exercise': 'diamond push-up', 'sets': 5, 'reps': '6-10', 'notes': '2sn pause'},
            {'exercise': 'bulgarian split squat', 'sets': 5, 'reps': '15/15', 'notes': 'tempo: 3-1-2-1'},
            {'exercise': 'single arm push-up', 'sets': 4, 'reps': '5/5', 'notes': 'duvar destekli'},
            {'exercise': 'archer squat', 'sets': 4, 'reps': '8/8', 'notes': ''},
            {'exercise': 'l-sit hold', 'sets': 5, 'reps': '15-30sn', 'notes': ''},
            {'exercise': 'hollow body hold', 'sets': 3, 'reps': '45-60sn', 'notes': ''},
            {'exercise': 'handstand wall walk', 'sets': 4, 'reps': '5 adım', 'notes': ''}
        ],
        'aksam': [
            {'exercise': 'pistol squat', 'sets': 4, 'reps': '5/5', 'notes': 'progression'},
            {'exercise': 'one arm plank', 'sets': 3, 'reps': '20sn/taraf', 'notes': ''},
            {'exercise': 'hindu push-up', 'sets': 3, 'reps': '12-15', 'notes': ''},
            {'exercise': 'burpee', 'sets': 3, 'reps': '10', 'notes': 'to tuck jump'}
        ]
    }
}

NUTRITION_PLAN = {
    '05:30': '500ml su',
    '06:00': '1 muz + kahve',
    '06:15-07:00': 'Sabah antrenmanı',
    '07:15': 'Protein shake + bal',
    '08:00': 'Kahvaltı',
    '11:00': 'Ara öğün',
    '13:30': 'Öğle yemeği',
    '16:00': 'Pre-workout atıştırmalık',
    '17:30-18:30': 'Akşam antrenmanı',
    '18:45': 'Süt + muz',
    '20:00': 'Akşam yemeği',
    '22:00': 'Casein + kuruyemiş',
    '22:30': 'Yatma'
}

SUPPLEMENTS = [
    {'name': 'Whey Protein', 'dosage': '30g (2x)'},
    {'name': 'Kreatin Monohydrate', 'dosage': '5g (18+ yaş)'},
    {'name': 'Multivitamin', 'dosage': '1 tablet'},
    {'name': 'Omega-3', 'dosage': '2-3g'},
    {'name': 'Magnezyum', 'dosage': '400mg'},
    {'name': 'Çinko', 'dosage': '15mg'},
    {'name': 'D3 Vitamini', 'dosage': '2000 IU'}
]

# Mesaj Analizi - Düzeltilmiş
def analyze_message(message):
    exercise_keywords = ['antrenman', 'egzersiz', 'set', 'tekrar', 'squat', 'push-up', 'pull-up', 'plank', 'burpee']
    general_keywords = ['yorgun', 'motivasyon', 'nasılım', 'hissediyorum', 'uyku', 'beslenme']
    
    message_lower = message.lower()
    exercise_count = sum(1 for keyword in exercise_keywords if keyword in message_lower)
    general_count = sum(1 for keyword in general_keywords if keyword in message_lower)
    
    exercise_data = None
    if exercise_count > general_count:
        exercises = list(BEAST_MODE_DATA['exercises'].keys())
        found_exercise = None
        
        # Egzersiz ismi bul
        for ex in exercises:
            if ex.lower() in message_lower:
                found_exercise = ex
                break
        
        if found_exercise:
            import re
            set_match = re.search(r'(\d+)\s*set', message_lower)
            rep_match = re.search(r'(\d+)\s*tekrar', message_lower)
            
            exercise_data = {
                'exercise': found_exercise,
                'sets': int(set_match.group(1)) if set_match else 3,
                'reps': int(rep_match.group(1)) if rep_match else 10,
                'muscle_group': BEAST_MODE_DATA['exercises'][found_exercise]['muscle_group']
            }
    
    return {
        'type': 'exercise' if exercise_count > general_count else 'general',
        'exercise_data': exercise_data
    }

# Groq API - Hafızalı
def call_groq_api(message, message_type, user_data, chat_history=None):
    try:
        # Hafıza için son 10 mesajı al
        recent_chats = chat_history[-10:] if chat_history else []
        conversation_context = ""
        
        if recent_chats:
            conversation_context = "\n\nÖnceki konuşmalar:\n"
            for chat in recent_chats:
                conversation_context += f"Kullanıcı: {chat['message']}\nKoç: {chat['response']}\n\n"
        
        if message_type == 'exercise':
            system_prompt = f"""Sen profesyonel bir fitness koçusun. Samimi ve motive edici konuş, robot gibi değil.
                           Kullanıcı: {user_data['name']}, Kilo: {user_data['weight']}kg, Yaş: {user_data['age']}, Beast Mode: %{st.session_state.beast_mode_score}
                           
                           Kullanıcı mesajı: "{message}"
                           {conversation_context}
                           
                           Kısa (max 80 kelime), samimi ve motive edici Türkçe yanıt ver. Teknik tavsiye ekle."""
        else:
            system_prompt = f"""Sen profesyonel bir fitness koçusun. Samimi ve destekleyici konuş.
                           Kullanıcı: {user_data['name']}, Beast Mode: %{st.session_state.beast_mode_score}
                           
                           Kullanıcı mesajı: "{message}"
                           {conversation_context}
                           
                           Kısa (max 70 kelime), samimi Türkçe yanıt ver. Soru sor ve tavsiye ver."""

        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'system', 'content': system_prompt}],
            'temperature': 0.8,
            'max_tokens': 200
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return f"❌ API Hatası ({response.status_code}). Tekrar deneyin."
            
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"

# MongoDB İşlemleri
def save_user_to_db(user_data):
    if st.session_state.db:
        try:
            st.session_state.db.users.insert_one(user_data)
            return True
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")
            return False
    return False

def get_user_from_db(username, password):
    if st.session_state.db:
        try:
            user = st.session_state.db.users.find_one({
                'username': username, 
                'password': password
            })
            return user
        except Exception as e:
            st.error(f"Giriş hatası: {e}")
            return None
    return None

def save_chat_to_db(user_id, chat_data):
    if st.session_state.db:
        try:
            st.session_state.db.chats.insert_one({
                'user_id': user_id,
                'timestamp': datetime.now(),
                **chat_data
            })
        except Exception as e:
            st.error(f"Chat kayıt hatası: {e}")

def get_user_chats(user_id):
    if st.session_state.db:
        try:
            chats = list(st.session_state.db.chats.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(10))
            return chats
        except Exception as e:
            st.error(f"Chat yükleme hatası: {e}")
            return []
    return []

# Giriş/Kayıt Ekranı
def login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🦁 Beast Mode Coach</h1>
        <p>6 Aylık Kişisel Fitness Dönüşümün</p>
    </div>
    """, unsafe_allow_html=True)
    
    # MongoDB durumu
    if st.session_state.db:
        st.success("✅ MongoDB bağlantısı aktif")
    else:
        st.error("❌ MongoDB bağlantısı başarısız - Offline modda çalışıyor")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🚀 Giriş Yap", "✨ Kayıt Ol"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Giriş Yap")
                username = st.text_input("Kullanıcı Adı")
                password = st.text_input("Şifre", type="password")
                login_button = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
                
                if login_button:
                    user = get_user_from_db(username, password)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.chat_history = get_user_chats(user['_id'])
                        st.success("✅ Giriş başarılı!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı!")
            
            st.info("📝 Demo: MongoDB bağlantısı yoksa test hesabı oluşturun")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("Kayıt Ol")
                name = st.text_input("Ad Soyad")
                new_username = st.text_input("Kullanıcı Adı")
                new_password = st.text_input("Şifre", type="password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=70)
                with col_b:
                    age = st.number_input("Yaş", min_value=16, max_value=80, value=25)
                
                goal = st.selectbox("Hedef", [
                    "muscle_gain",
                    "weight_loss", 
                    "endurance",
                    "strength"
                ])
                
                register_button = st.form_submit_button("✨ Kayıt Ol", use_container_width=True)
                
                if register_button:
                    if name and new_username and new_password:
                        new_user = {
                            '_id': str(uuid.uuid4()),
                            'name': name,
                            'username': new_username,
                            'password': new_password,
                            'weight': weight,
                            'age': age,
                            'goal': goal,
                            'join_date': datetime.now(),
                            'beast_mode_score': 75
                        }
                        
                        if save_user_to_db(new_user):
                            st.session_state.authenticated = True
                            st.session_state.current_user = new_user
                            st.session_state.chat_history = []
                            st.success("✅ Kayıt başarılı!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Kayıt başarısız!")
                    else:
                        st.error("❌ Lütfen tüm alanları doldurun!")

# Ana Uygulama
def main_app():
    user = st.session_state.current_user
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">🦁</span>
            <div>
                <h2 style="margin: 0;">Beast Mode Coach</h2>
                <p style="margin: 0; color: #666;">Hoşgeldin, {user['name']}! 👋</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Beast Mode", f"{st.session_state.beast_mode_score}%", "🔥")
    
    with col3:
        if st.button("🚪 Çıkış", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
    
    st.divider()
    
    # Tabs - Yeni düzenleme
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Panel", "🤖 Koç", "💪 Program", "🍎 Beslenme", "💊 Takviyeler", "📈 İlerleme"
    ])
    
    with tab1:
        dashboard_tab()
    
    with tab2:
        coach_tab()
    
    with tab3:
        program_tab()
    
    with tab4:
        nutrition_tab()
    
    with tab5:
        supplements_tab()
    
    with tab6:
        progress_tab()

# Program Tab - Yeni
def program_tab():
    st.subheader("💪 Beast Mode Programın")
    st.write("6 aylık dönüşüm programının detayları")
    
    # Program aşamaları
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="program-card">
            <h3>🔥 Hafta 1-2</h3>
            <p>Temel Hareketler</p>
            <p><strong>Sabah:</strong> 8 egzersiz</p>
            <p><strong>Akşam:</strong> 4 egzersiz</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="program-card">
            <h3>⚡ Hafta 3-6</h3>
            <p>Güç + Dayanıklılık</p>
            <p><strong>Sabah:</strong> Güç odaklı</p>
            <p><strong>Akşam:</strong> Metabolik</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="program-card">
            <h3>🚀 Hafta 7-12</h3>
            <p>İleri Seviye</p>
            <p><strong>One Arm Push-up</strong></p>
            <p><strong>Handstand Push-up</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Günlük program detayları
    st.subheader("📅 Bugünün Programı (Hafta 1-2)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌅 Sabah Antrenmanı (06:00)")
        for i, exercise in enumerate(DAILY_PROGRAM['hafta_1_2']['sabah'], 1):
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{i}. {exercise['exercise'].title()}</strong><br>
                <span style="color: #FF6B35;">{exercise['sets']} set × {exercise['reps']} tekrar</span><br>
                <small>{exercise['notes']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🌆 Akşam Antrenmanı (18:00)")
        for i, exercise in enumerate(DAILY_PROGRAM['hafta_1_2']['aksam'], 1):
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{i}. {exercise['exercise'].title()}</strong><br>
                <span style="color: #FF6B35;">{exercise['sets']} set × {exercise['reps']} tekrar</span><br>
                <small>{exercise['notes']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Zorlanma teknikleri
    st.subheader("🎯 Zorlanma Teknikleri")
    
    techniques = {
        'Time Under Tension (TUT)': '3sn yukarı, 2sn dur, 4sn aşağı, 1sn dur',
        'Cluster Sets': '6 tekrar → 15sn → 4 tekrar → 15sn → 2 tekrar',
        'Mechanical Drop Sets': 'One Arm → Diamond → Normal → Knee Push-up (maks tekrar)',
        'Isometric Holds + Plyometrics': '10sn hold + 5 patlayıcı tekrar x 5 set'
    }
    
    for technique, description in techniques.items():
        st.markdown(f"**{technique}:** {description}")

# Beslenme Tab - Yeni
def nutrition_tab():
    st.subheader("🍎 Beast Mode Beslenme Planı")
    
    # Makro hedefler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Protein", "150-170g", "💪")
    with col2:
        st.metric("Karbonhidrat", "340-400g", "🍞")
    with col3:
        st.metric("Yağ", "75-85g", "🥑")
    with col4:
        st.metric("Toplam Kalori", "2800-3200", "🔥")
    
    st.divider()
    
    # Günlük beslenme programı
    st.subheader("📅 Günlük Beslenme Programı")
    
    for time, food in NUTRITION_PLAN.items():
        if 'antrenman' in food.lower():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FF6B35, #F7931E); 
                        color: white; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                <strong>{time}</strong> → {food}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**{time}** → {food}")
    
    st.divider()
    
    # Uyku ve dinlenme
    st.subheader("😴 Uyku & Dinlenme")
    
    sleep_schedule = {
        '21:30': 'Ekranları kapat',
        '21:45': 'Sıcak duş al',
        '22:00': 'Magnezyum al',
        '22:15': 'Meditasyon/nefes',
        '22:30': 'Yatma',
        '07:00': 'Uyanış (8.5 saat uyku)'
    }
    
    for time, action in sleep_schedule.items():
        st.markdown(f"**{time}** → {action}")
    
    # Oda koşulları
    st.markdown("**Oda Koşulları:**")
    st.markdown("• Sıcaklık: 16-18°C • Nem: %30-50 • Işık: Tam karanlık • Ses: Sessizlik")

# Takviyeler Tab - Yeni
def supplements_tab():
    st.subheader("💊 Beast Mode Takviyeleri")
    st.write("Performans ve iyileşmeyi destekleyen takviyeler")
    
    # Temel takviyeler
    st.markdown("### 🔥 Temel Takviyeler")
    for supplement in SUPPLEMENTS:
        st.markdown(f"**{supplement['name']}:** {supplement['dosage']}")
    
    st.divider()
    
    # Opsiyonel takviyeler
    st.markdown("### ⚡ Opsiyonel Takviyeler (İsteğe Bağlı)")
    optional_supplements = [
        {'name': 'Beta-Alanine', 'dosage': '3-5g', 'benefit': 'Kas dayanıklılığı'},
        {'name': 'L-Citrulline', 'dosage': '6-8g', 'benefit': 'Pompa ve dolaşım'},
        {'name': 'HMB', 'dosage': '3g', 'benefit': 'Kas kaybını önler'}
    ]
    
    for supplement in optional_supplements:
        st.markdown(f"**{supplement['name']}:** {supplement['dosage']} - *{supplement['benefit']}*")
    
    st.info("💡 Takviyeleri kullanmadan önce doktorunuza danışın. 18 yaş altı için kreatin önerilmez.")

# Dashboard Tab - Güncellenmiş
def dashboard_tab():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Beast Mode", f"{st.session_state.beast_mode_score}%", "🔥")
    
    with col2:
        st.metric("Toplam Antrenman", len(st.session_state.exercise_log), "💪")
    
    with col3:
        weeks_passed = max(1, (datetime.now() - datetime(2024, 1, 1)).days // 7)
        st.metric("Program Haftası", f"{min(weeks_passed, 24)}/24", "📅")
    
    with col4:
        today_exercises = len([ex for ex in st.session_state.exercise_log 
                              if ex.get('date', datetime.now()).date() == datetime.now().date()])
        st.metric("Bugün Yapılan", today_exercises, "🎯")
    
    st.divider()
    
    # Haftalık ilerleme grafiği
    st.subheader("📈 Haftalık İlerleme")
    
    # Örnek veri oluştur
    progress_data = []
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        exercises_count = len([ex for ex in st.session_state.exercise_log 
                              if ex.get('date', datetime.now()).date() == date.date()])
        progress_data.append({
            'Tarih': date.strftime('%d/%m'),
            'Egzersiz': exercises_count,
            'Beast Mode': min(100, st.session_state.beast_mode_score + (i * 2))
        })
    
    df = pd.DataFrame(progress_data)
    
    if not df.empty:
        fig = px.line(df, x='Tarih', y=['Egzersiz', 'Beast Mode'], 
                     title="Son 7 Günlük İlerleme")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Son aktiviteler
    st.subheader("🔥 Son Aktiviteler")
    
    if st.session_state.exercise_log:
        recent_exercises = st.session_state.exercise_log[-5:]
        for exercise in reversed(recent_exercises):
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{exercise.get('exercise', 'Bilinmeyen').title()}</strong> - 
                {exercise.get('sets', 0)} set × {exercise.get('reps', 0)} tekrar
                <br><small>{exercise.get('date', datetime.now()).strftime('%d/%m/%Y %H:%M')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz egzersiz kaydı yok. Koç ile konuşarak başla! 💪")

# Coach Tab - Güncellenmiş
def coach_tab():
    st.subheader("🤖 Beast Mode Koçun")
    st.write("AI koçun ile konuş, antrenman kaydet ve motivasyon al!")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Chat geçmişini göster
        for chat in st.session_state.chat_history:
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>Sen:</strong> {chat['message']}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="chat-message ai-message">
                <strong>🦁 Koç:</strong> {chat['response']}
            </div>
            """, unsafe_allow_html=True)
    
    # Mesaj input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_input("Koçuna bir şeyler söyle...", 
                                       placeholder="Örn: 20 push-up 3 set yaptım!")
        
        with col2:
            send_button = st.form_submit_button("📨 Gönder", use_container_width=True)
        
        if send_button and user_message:
            # Mesajı analiz et
            analysis = analyze_message(user_message)
            
            # AI yanıtı al
            ai_response = call_groq_api(
                user_message, 
                analysis['type'], 
                st.session_state.current_user,
                st.session_state.chat_history
            )
            
            # Chat geçmişine ekle
            chat_entry = {
                'message': user_message,
                'response': ai_response,
                'timestamp': datetime.now(),
                'type': analysis['type']
            }
            
            st.session_state.chat_history.append(chat_entry)
            
            # Egzersiz verisini kaydet
            if analysis['exercise_data']:
                st.session_state.exercise_log.append({
                    **analysis['exercise_data'],
                    'date': datetime.now()
                })
                
                # Beast Mode skoru güncelle
                st.session_state.beast_mode_score = min(100, 
                    st.session_state.beast_mode_score + 2)
            
            # MongoDB'ye kaydet
            if st.session_state.db and st.session_state.current_user:
                save_chat_to_db(st.session_state.current_user['_id'], chat_entry)
            
            st.rerun()
    
    # Hızlı eylemler
    st.subheader("⚡ Hızlı Eylemler")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💪 Bugünün Programını Tamamladım", use_container_width=True):
            st.session_state.chat_history.append({
                'message': "Bugünün programını tamamladım!",
                'response': "🔥 Harika iş çıkardın! Beast Mode'un yükseliyor. Dinlenme ve beslenmeyi ihmal etme. Yarın daha güçlü olacaksın! 💪",
                'timestamp': datetime.now(),
                'type': 'achievement'
            })
            st.session_state.beast_mode_score = min(100, st.session_state.beast_mode_score + 5)
            st.rerun()
    
    with col2:
        if st.button("😴 Yorgun Hissediyorum", use_container_width=True):
            st.session_state.chat_history.append({
                'message': "Çok yorgun hissediyorum",
                'response': "💤 Dinlenme de antrenmanın bir parçası! Bugün hafif yapabilir veya dinlenebilirsin. Vücudunu dinle, zorlamaya gerek yok. Yarın daha fresh olacaksın! 🌟",
                'timestamp': datetime.now(),
                'type': 'support'
            })
            st.rerun()
    
    with col3:
        if st.button("🎯 Motivasyona İhtiyacım Var", use_container_width=True):
            st.session_state.chat_history.append({
                'message': "Motivasyona ihtiyacım var",
                'response': "🦁 Sen bir BEAST'sin! Her tekrar seni hedefine yaklaştırıyor. 6 ay sonraki haline bir düşün - o güçlü, kendinden emin versiyonun seni bekliyor! Şimdi kalk ve bir hareket yap! 🔥💪",
                'timestamp': datetime.now(),
                'type': 'motivation'
            })
            st.rerun()

# Progress Tab - Yeni
def progress_tab():
    st.subheader("📈 İlerleme Takibi")
    
    # Genel istatistikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_workouts = len(st.session_state.exercise_log)
        st.metric("Toplam Antrenman", total_workouts, "💪")
    
    with col2:
        if st.session_state.exercise_log:
            total_sets = sum(ex.get('sets', 0) for ex in st.session_state.exercise_log)
            st.metric("Toplam Set", total_sets, "🔥")
        else:
            st.metric("Toplam Set", 0, "🔥")
    
    with col3:
        if st.session_state.exercise_log:
            total_reps = sum(ex.get('reps', 0) * ex.get('sets', 0) for ex in st.session_state.exercise_log)
            st.metric("Toplam Tekrar", total_reps, "⚡")
        else:
            st.metric("Toplam Tekrar", 0, "⚡")
    
    with col4:
        streak_days = 7  # Örnek değer
        st.metric("Seri (Gün)", streak_days, "🏆")
    
    st.divider()
    
    # Kas gruplarına göre dağılım
    if st.session_state.exercise_log:
        st.subheader("🎯 Kas Grupları Dağılımı")
        
        muscle_groups = {}
        for exercise in st.session_state.exercise_log:
            muscle_group = exercise.get('muscle_group', 'other')
            muscle_groups[muscle_group] = muscle_groups.get(muscle_group, 0) + 1
        
        # Türkçe çeviri
        muscle_group_turkish = {
            'chest': 'Göğüs',
            'back': 'Sırt',
            'legs': 'Bacak',
            'core': 'Core',
            'shoulders': 'Omuz',
            'arms': 'Kol',
            'full_body': 'Tüm Vücut'
        }
        
        muscle_data = []
        for group, count in muscle_groups.items():
            muscle_data.append({
                'Kas Grubu': muscle_group_turkish.get(group, group.title()),
                'Antrenman': count
            })
        
        df_muscle = pd.DataFrame(muscle_data)
        
        if not df_muscle.empty:
            fig_pie = px.pie(df_muscle, values='Antrenman', names='Kas Grubu',
                           title="Kas Grupları Dağılımı")
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Günlük aktivite takvimi
    st.subheader("📅 Aktivite Takvimi")
    
    # Son 30 günlük aktivite
    activity_calendar = {}
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        date_str = date.strftime('%Y-%m-%d')
        
        daily_exercises = len([ex for ex in st.session_state.exercise_log 
                              if ex.get('date', datetime.now()).date() == date.date()])
        
        activity_calendar[date_str] = daily_exercises
    
    # Heatmap benzeri görsel
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    for i, (date_str, count) in enumerate(list(activity_calendar.items())[-21:]):  # Son 3 hafta
        col_index = i % 7
        cols = [col1, col2, col3, col4, col5, col6, col7]
        
        with cols[col_index]:
            if count > 0:
                st.markdown(f"""
                <div style="background: #FF6B35; color: white; padding: 0.5rem; 
                           border-radius: 4px; text-align: center; margin: 0.2rem 0;">
                    <small>{datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m')}</small><br>
                    <strong>{count}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f0f0f0; padding: 0.5rem; 
                           border-radius: 4px; text-align: center; margin: 0.2rem 0;">
                    <small>{datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m')}</small><br>
                    <span>0</span>
                </div>
                """, unsafe_allow_html=True)
    
    # Hedefler
    st.subheader("🎯 Hedefler ve Başarılar")
    
    goals = [
        {"name": "İlk 30 Antrenman", "current": total_workouts, "target": 30, "icon": "🏃"},
        {"name": "1000 Push-up", "current": 750, "target": 1000, "icon": "💪"},
        {"name": "500 Squat", "current": 320, "target": 500, "icon": "🦵"},
        {"name": "Beast Mode %90", "current": st.session_state.beast_mode_score, "target": 90, "icon": "🦁"}
    ]
    
    for goal in goals:
        progress = min(100, (goal["current"] / goal["target"]) * 100)
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; 
                   border-left: 4px solid #FF6B35; margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><strong>{goal['icon']} {goal['name']}</strong></span>
                <span>{goal['current']}/{goal['target']}</span>
            </div>
            <div style="background: #f0f0f0; border-radius: 10px; height: 10px; margin-top: 0.5rem;">
                <div style="background: #FF6B35; width: {progress}%; height: 100%; border-radius: 10px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Ana fonksiyon
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
