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
import re
import hashlib

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
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sabitler
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MONGODB_URI = "mongodb+srv://dyaloshwester:b9eoq3Hriw3ncm65@cluster0.x6sungc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Beast Mode Verileri
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

# Utility Functions
def hash_password(password):
    """Şifreyi hash'le"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Şifreyi doğrula"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password

# MongoDB Bağlantısı
@st.cache_resource
def init_mongodb():
    try:
        # Özel SSL bağlamı oluştur
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # MongoDB bağlantı ayarları
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            ssl_context=ssl_context,  # Özel SSL bağlamını kullan
            serverSelectionTimeoutMS=30000,  # Timeout süresini artır
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            maxPoolSize=10
        )
        
        # Test bağlantısı
        client.admin.command('ping')
        st.success("✅ MongoDB Atlas bağlantısı başarılı!")
        db = client['beast_mode']
        return db
    except Exception as e:
        st.error(f"❌ MongoDB bağlantı hatası: {str(e)}")
        # Offline moda geç
        return create_offline_db()

def create_offline_db():
    """Offline demo veritabanı oluştur"""
    st.warning("⚠️ MongoDB bağlantısı başarısız - Offline demo modunda çalışıyor")

def setup_collections(db):
    """MongoDB koleksiyonlarını ve index'lerini ayarla"""
    try:
        # Users koleksiyonu
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
        
        # Username için unique index
        try:
            db.users.create_index('username', unique=True)
        except:
            pass  # Index zaten varsa devam et
        
        # Chats koleksiyonu
        if 'chats' not in db.list_collection_names():
            db.create_collection('chats')
        
        # User_id ve timestamp için index
        try:
            db.chats.create_index([('user_id', 1), ('timestamp', -1)])
        except:
            pass
        
        # Workouts koleksiyonu
        if 'workouts' not in db.list_collection_names():
            db.create_collection('workouts')
        
        try:
            db.workouts.create_index([('user_id', 1), ('date', -1)])
        except:
            pass
        
        # Progress koleksiyonu
        if 'progress' not in db.list_collection_names():
            db.create_collection('progress')
        
        try:
            db.progress.create_index([('user_id', 1), ('date', -1)])
        except:
            pass
        
    except Exception as e:
        st.error(f"Koleksiyon ayarlama hatası: {e}")

# Session State Initialization
def init_session_state():
    default_values = {
        'authenticated': False,
        'current_user': None,
        'chat_history': [],
        'exercise_log': [],
        'beast_mode_score': 75,
        'db': None,
        'chat_session_id': None
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # MongoDB bağlantısını başlat
    if st.session_state.db is None:
        st.session_state.db = init_mongodb()

# MongoDB İşlemleri
def save_user_to_db(user_data):
    """Kullanıcıyı veritabanına kaydet"""
    if not st.session_state.db:
        return False
    
    try:
        # Şifreyi hash'le
        user_data['password'] = hash_password(user_data['password'])
        user_data['created_at'] = datetime.now()
        user_data['updated_at'] = datetime.now()
        
        result = st.session_state.db.users.insert_one(user_data)
        return bool(result.inserted_id)
    except pymongo.errors.DuplicateKeyError:
        st.error("❌ Bu kullanıcı adı zaten kullanılıyor!")
        return False
    except Exception as e:
        st.error(f"❌ Kayıt hatası: {e}")
        return False

def get_user_from_db(username, password):
    """Kullanıcıyı veritabanından getir"""
    if not st.session_state.db:
        # Offline demo mode
        if username == "demo" and password == "demo":
            return {
                '_id': "demo-user",
                'name': "Demo Kullanıcı",
                'username': "demo",
                'password': "demo",
                'weight': 70,
                'age': 25,
                'goal': "muscle_gain",
                'created_at': datetime.now(),
                'beast_mode_score': 75
            }
        return None
    
    try:
        user = st.session_state.db.users.find_one({'username': username})
        
        if user and verify_password(password, user['password']):
            return user
        return None
    except Exception as e:
        st.error(f"❌ Giriş hatası: {e}")
        return None

def save_chat_to_db(user_id, message, response, message_type='general'):
    """Chat'i veritabanına kaydet"""
    if not st.session_state.db:
        return False
    
    try:
        chat_data = {
            'user_id': user_id,
            'session_id': st.session_state.chat_session_id,
            'message': message,
            'response': response,
            'message_type': message_type,
            'timestamp': datetime.now()
        }
        
        result = st.session_state.db.chats.insert_one(chat_data)
        return bool(result.inserted_id)
    except Exception as e:
        st.error(f"❌ Chat kayıt hatası: {e}")
        return False

def get_user_chats(user_id, limit=20):
    """Kullanıcının chat geçmişini getir"""
    if not st.session_state.db:
        return []
    
    try:
        chats = list(st.session_state.db.chats.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit))
        
        return chats
    except Exception as e:
        st.error(f"❌ Chat yükleme hatası: {e}")
        return []

def save_workout_to_db(user_id, workout_data):
    """Antrenman verisini kaydet"""
    if not st.session_state.db:
        return False
    
    try:
        workout_data['user_id'] = user_id
        workout_data['timestamp'] = datetime.now()
        
        result = st.session_state.db.workouts.insert_one(workout_data)
        return bool(result.inserted_id)
    except Exception as e:
        st.error(f"❌ Antrenman kayıt hatası: {e}")
        return False

def update_user_progress(user_id, progress_data):
    """Kullanıcı ilerlemesini güncelle"""
    if not st.session_state.db:
        return False
    
    try:
        progress_data['user_id'] = user_id
        progress_data['date'] = datetime.now().date()
        progress_data['timestamp'] = datetime.now()
        
        # Upsert: eğer bugünkü kayıt varsa güncelle, yoksa ekle
        result = st.session_state.db.progress.update_one(
            {'user_id': user_id, 'date': progress_data['date']},
            {'$set': progress_data},
            upsert=True
        )
        
        return True
    except Exception as e:
        st.error(f"❌ İlerleme kayıt hatası: {e}")
        return False

# Mesaj Analizi
def analyze_message(message):
    """Mesajı analiz et ve türünü belirle"""
    exercise_keywords = ['antrenman', 'egzersiz', 'set', 'tekrar', 'squat', 'push-up', 'pull-up', 'plank', 'burpee', 'workout']
    nutrition_keywords = ['beslenme', 'diyet', 'protein', 'karbonhidrat', 'yemek', 'kahvaltı', 'öğle', 'akşam']
    motivation_keywords = ['motivasyon', 'yorgun', 'üşengeç', 'isteksiz', 'energy', 'enerji']
    progress_keywords = ['ilerleme', 'gelişim', 'kilo', 'kas', 'güç', 'dayanıklılık']
    
    message_lower = message.lower()
    
    # Keyword sayılarını hesapla
    exercise_count = sum(1 for keyword in exercise_keywords if keyword in message_lower)
    nutrition_count = sum(1 for keyword in nutrition_keywords if keyword in message_lower)
    motivation_count = sum(1 for keyword in motivation_keywords if keyword in message_lower)
    progress_count = sum(1 for keyword in progress_keywords if keyword in message_lower)
    
    # En yüksek skoru belirle
    max_count = max(exercise_count, nutrition_count, motivation_count, progress_count)
    
    if max_count == 0:
        return {'type': 'general', 'exercise_data': None}
    
    if exercise_count == max_count:
        return {'type': 'exercise', 'exercise_data': extract_exercise_data(message)}
    elif nutrition_count == max_count:
        return {'type': 'nutrition', 'exercise_data': None}
    elif motivation_count == max_count:
        return {'type': 'motivation', 'exercise_data': None}
    elif progress_count == max_count:
        return {'type': 'progress', 'exercise_data': None}
    else:
        return {'type': 'general', 'exercise_data': None}

def extract_exercise_data(message):
    """Mesajdan egzersiz verisini çıkar"""
    message_lower = message.lower()
    exercises = list(BEAST_MODE_DATA['exercises'].keys())
    
    found_exercise = None
    for ex in exercises:
        if ex.lower() in message_lower or ex.replace('-', ' ').lower() in message_lower:
            found_exercise = ex
            break
    
    if found_exercise:
        set_match = re.search(r'(\d+)\s*set', message_lower)
        rep_match = re.search(r'(\d+)\s*tekrar', message_lower)
        
        return {
            'exercise': found_exercise,
            'sets': int(set_match.group(1)) if set_match else 3,
            'reps': int(rep_match.group(1)) if rep_match else 10,
            'muscle_group': BEAST_MODE_DATA['exercises'][found_exercise]['muscle_group']
        }
    
    return None

# Groq API - Doğal Konuşma
def call_groq_api(message, message_type, user_data, chat_history=None):
    """Groq API'ye doğal konuşma isteği gönder"""
    try:
        # Son konuşmaları al
        recent_chats = (chat_history[-5:] if chat_history else [])
        conversation_context = ""
        
        if recent_chats:
            conversation_context = "\n\nÖnceki konuşmalar:\n"
            for chat in recent_chats:
                conversation_context += f"Sen: {chat.get('response', '')}\nKullanıcı: {chat.get('message', '')}\n"
        
        # Mesaj türüne göre sistem promptu
        base_personality = (
            f"Sen {user_data['name']} adlı kişinin kişisel fitness koçusun. "
            f"Samimi, arkadaşça ve motive edici konuş. Robot gibi değil, gerçek bir insan gibi davran. "
            f"emoji kullan, esprili ol. "
            f"öğrencin önemli şeyler hakkında birşey sorduğunda bilimsel olarak düşün ama ona normalce anlat. "
            f"Ciddi ama samimi ol. "
            f"Kullanıcı bilgileri: {user_data['age']} yaşında, {user_data['weight']}kg, Beast Mode skoru: %{st.session_state.beast_mode_score}"
        )
        
        if message_type == 'exercise':
            system_prompt = (
                f"{base_personality}\n\n"
                "Antrenman konusunda konuşuyorsunuz. Teknik bilgi ver ama sıkıcı olma. "
                "Kişisel deneyimlerini paylaşıyormuş gibi konuş."
            )
        elif message_type == 'nutrition':
            system_prompt = (
                f"{base_personality}\n\n"
                "Beslenme konusunda konuşuyorsunuz. Pratik tavsiyeler ver, ezber bilgi verme. samimi davran "
                "Gerçek hayattan örnekler kullan."
            )
        elif message_type == 'motivation':
            system_prompt = (
                f"{base_personality}\n\n"
                "Motivasyon konusunda konuşuyorsunuz. Empati kurup destekle. "
                "Kendi zorlandığın anlardan bahset. Samimi ol."
            )
        else:
            system_prompt = (
                f"{base_personality}\n\n"
                "Genel sohbet ediyorsunuz. Rahat ol, arkadaşça konuş. "
                "Merak et, soru sor"
            )

        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama3-70b-8192',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"{message}\n{conversation_context}"}
            ],
                'temperature': 0.9,
                'max_tokens': 500
        }

        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return get_fallback_response(message_type)
            
    except Exception as e:
        return get_fallback_response(message_type)

# Giriş/Kayıt Ekranı
def login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🦁 Beast Mode Coach</h1>
        <p>6 Aylık Kişisel Fitness Dönüşümün Başlasın!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Bağlantı durumu
    connection_status = st.empty()
    if st.session_state.db:
        connection_status.success("✅ Veritabanı bağlantısı aktif")
    else:
        connection_status.warning("⚠️ Veritabanı bağlantısı yok - Demo modda çalışıyor")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🚀 Giriş Yap", "✨ Kayıt Ol"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=True):
                st.subheader("Hoş Geldin!")
                username = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adını gir")
                password = st.text_input("Şifre", type="password", placeholder="Şifreni gir")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_button = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
                with col_b:
                    demo_button = st.form_submit_button("🎮 Demo Dene", use_container_width=True)
                
                if demo_button:
                    username, password = "demo", "demo"
                    login_button = True
                
                if login_button:
                    if username and password:
                        with st.spinner("Giriş yapılıyor..."):
                            user = get_user_from_db(username, password)
                        
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.current_user = user
                            st.session_state.chat_session_id = str(uuid.uuid4())
                            
                            # Chat geçmişini yükle
                            if st.session_state.db:
                                st.session_state.chat_history = get_user_chats(user['_id'])
                            
                            st.success("✅ Hoş geldin! Hemen başlayalım 🦁")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Kullanıcı adı veya şifre hatalı!")
                    else:
                        st.error("❌ Lütfen kullanıcı adı ve şifre girin!")
        
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                st.subheader("Aramıza Katıl!")
                name = st.text_input("Ad Soyad", placeholder="Adın ve soyadın")
                new_username = st.text_input("Kullanıcı Adı", placeholder="Benzersiz kullanıcı adı")
                new_password = st.text_input("Şifre", type="password", placeholder="Güvenli şifre")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=70)
                with col_b:
                    age = st.number_input("Yaş", min_value=16, max_value=80, value=25)
                
                goal = st.selectbox("Hedefin Ne?", [
                    ("muscle_gain", "💪 Kas Kazanmak"),
                    ("weight_loss", "🔥 Kilo Vermek"), 
                    ("endurance", "🏃 Dayanıklılık"),
                    ("strength", "⚡ Güç Artırmak")
                ], format_func=lambda x: x[1])
                
                register_button = st.form_submit_button("✨ Hemen Başla!", use_container_width=True)
                
                if register_button:
                    if name and new_username and new_password:
                        if len(new_password) < 4:
                            st.error("❌ Şifre en az 4 karakter olmalı!")
                        else:
                            new_user = {
                                '_id': str(uuid.uuid4()),
                                'name': name,
                                'username': new_username,
                                'password': new_password,
                                'weight': weight,
                                'age': age,
                                'goal': goal[0],
                                'beast_mode_score': 75
                            }
                            
                            with st.spinner("Hesap oluşturuluyor..."):
                                if save_user_to_db(new_user):
                                    st.session_state.authenticated = True
                                    st.session_state.current_user = new_user
                                    st.session_state.chat_session_id = str(uuid.uuid4())
                                    st.session_state.chat_history = []
                                    st.success("✅ Hoş geldin! Beast Mode başlıyor 🦁")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Kayıt başarısız! Farklı kullanıcı adı dene.")
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
