import streamlit as st
import pymongo
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import hashlib
import json
import time
from bson import ObjectId

# Page config - daha modern görünüm
st.set_page_config(
    page_title="Chym - AI Fitness Koçu",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS stilleri
st.markdown("""
<style>
    /* Ana tema renkleri */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 0;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .workout-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .nutrition-card {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        background: rgba(255,255,255,0.9);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 2rem;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 2rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .exercise-item {
        background: rgba(255,255,255,0.1);
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #fff;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        height: 20px;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .stats-container {
        background: rgba(255,255,255,0.05);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sabit değerler
GROQ_API_KEY = "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"
MONGODB_URI = "mongodb+srv://emo36kars:fitness123@cluster0.zttnhmt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB bağlantısı
@st.cache_resource
def init_mongodb():
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.chym_fitness
        return db
    except Exception as e:
        st.error(f"🔴 MongoDB bağlantı hatası: {e}")
        return None

# Groq AI istemcisi
@st.cache_resource
def init_groq():
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"🔴 Groq AI bağlantı hatası: {e}")
        return None

# Şifre hashleme
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Veri tiplerini MongoDB'ye uygun hale getirme
def sanitize_data(data):
    """MongoDB'ye uygun veri tiplerini düzelt"""
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    elif hasattr(data, 'item'):  # numpy types
        return data.item()
    elif hasattr(data, 'date'):  # datetime.date objects
        return datetime.combine(data, datetime.min.time())
    else:
        return data

# Kişiselleştirilmiş program verisi
PERSONAL_PROGRAM = {
    "hafta_1_2": {
        "sabah": {
            "Pike Push-up": "5x8-12 (3sn negatif)",
            "Diamond Push-up": "5x6-10 (2sn pause)",
            "Bulgarian Split Squat": "5x15/15 (tempo: 3-1-2-1)",
            "Single Arm Push-up Progression": "4x5/5 (duvar destekli)",
            "Archer Squat Progression": "4x8/8",
            "L-Sit Hold": "5x15-30sn",
            "Hollow Body Hold": "3x45-60sn",
            "Handstand Wall Walk": "4x5 adım"
        },
        "aksam": {
            "Pistol Squat Progression": "4x5/5",
            "One Arm Plank": "3x20sn/taraf",
            "Hindu Push-up": "3x12-15",
            "Burpee to Tuck Jump": "3x10"
        }
    },
    "hafta_3_6": {
        "sabah": "Güç Odaklı: Her hareket 6 set, 6-12 tekrar, 90sn dinlenme",
        "aksam": "Dayanıklılık + Metabolik: Süpersetler, 15-25 tekrar"
    },
    "hafta_7_12": {
        "ileri_seviye": [
            "One Arm Push-up (assisted → unassisted)",
            "Handstand Push-up (wall → freestanding)",
            "Pistol Squat (tam hareket)",
            "Muscle-up Progression",
            "Human Flag Progression",
            "Front Lever Progression",
            "Planche Progression"
        ]
    },
    "beslenme": {
        "05:30": "500ml su 💧",
        "06:00": "1 muz + kahve ☕",
        "07:15": "Protein shake + bal 🥤",
        "08:00": "Kahvaltı 🍳",
        "11:00": "Ara öğün 🍎",
        "13:30": "Öğle yemeği 🍽️",
        "16:00": "Pre-workout atıştırmalık 🥜",
        "18:45": "Süt + muz 🥛",
        "20:00": "Akşam yemeği 🍖",
        "22:00": "Casein + kuruyemiş 🌰"
    },
    "makrolar": {
        "protein": "150-170g",
        "karbonhidrat": "340-400g",
        "yag": "75-85g",
        "kalori": "2800-3200 kcal"
    }
}

# Kullanıcı kayıt/giriş
def user_auth():
    db = init_mongodb()
    if not db:
        return False, None
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if st.session_state.user_id:
        return True, st.session_state.user_id
    
    # Modern giriş ekranı
    st.markdown("""
    <div class="main-header">
        <h1>💪 Chym - AI Fitness Koçu</h1>
        <p>Kişiselleştirilmiş fitness programın ve AI koçun burada!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])
        
        with tab1:
            with st.container():
                st.markdown("### 👋 Tekrar Hoş Geldin!")
                username = st.text_input("👤 Kullanıcı Adı", key="login_username")
                password = st.text_input("🔒 Şifre", type="password", key="login_password")
                
                if st.button("🚀 Giriş Yap", use_container_width=True):
                    if username and password:
                        try:
                            user = db.users.find_one({
                                "username": username,
                                "password": hash_password(password)
                            })
                            if user:
                                st.session_state.user_id = str(user["_id"])
                                st.success("🎉 Giriş başarılı!")
                                st.rerun()
                            else:
                                st.error("❌ Kullanıcı adı veya şifre yanlış!")
                        except Exception as e:
                            st.error(f"🔴 Giriş sırasında bir hata oluştu: {e}")
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun!")
        
        with tab2:
            with st.container():
                st.markdown("### 🆕 Aramıza Katıl!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("👤 Kullanıcı Adı", key="register_username")
                    new_password = st.text_input("🔒 Şifre", type="password", key="register_password")
                    full_name = st.text_input("🏷️ Ad Soyad")
                
                with col2:
                    age = st.number_input("🎂 Yaş", min_value=15, max_value=80, value=25)
                    weight = st.number_input("⚖️ Kilo (kg)", min_value=40, max_value=200, value=70)
                    height = st.number_input("📏 Boy (cm)", min_value=140, max_value=220, value=170)
                
                if st.button("✨ Kayıt Ol", use_container_width=True):
                    if new_username and new_password and full_name:
                        try:
                            # Kullanıcı var mı kontrol et
                            if db.users.find_one({"username": new_username}):
                                st.error("❌ Bu kullanıcı adı zaten kullanılıyor!")
                            else:
                                # Yeni kullanıcı oluştur
                                user_data = {
                                    "username": new_username,
                                    "password": hash_password(new_password),
                                    "full_name": full_name,
                                    "age": int(age),
                                    "weight": float(weight),
                                    "height": int(height),
                                    "created_at": datetime.now(),
                                    "program_week": 1
                                }
                                
                                # Veri tiplerini sanitize et
                                user_data = sanitize_data(user_data)
                                
                                result = db.users.insert_one(user_data)
                                st.session_state.user_id = str(result.inserted_id)
                                st.success("🎉 Kayıt başarılı! Hoş geldiniz!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"🔴 Kayıt sırasında bir hata oluştu: {e}")
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun!")
    
    return False, None

# AI Koç
def ai_coach_response(user_message, user_data=None):
    client = init_groq()
    if not client:
        return "😔 Maalesef şu an AI koç servisine erişemiyorum. Lütfen daha sonra tekrar deneyin."
    
    system_prompt = f"""
    Sen Chym fitness uygulamasının AI koçusun. Adın Coach Alex. 
    Çok samimi, arkadaş canlısı ve motivasyonu yüksek birisisin.
    Kullanıcıya sanki yıllardır tanıdığın bir arkadaşınmış gibi davran.
    
    Kullanıcının kişisel fitness programı:
    {json.dumps(PERSONAL_PROGRAM, indent=2, ensure_ascii=False)}
    
    Kullanıcı bilgileri: {user_data if user_data else "Henüz mevcut değil"}
    
    Türkçe konuş ve emoji kullan. Çok samimi ol, bazen şakacı ol.
    Fitness konularında uzman tavsiyeleri ver ama samimi dille.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1000,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"😅 Ups! Şu an biraz yorgunum. Tekrar dener misin? Hata: {str(e)}"

# Dashboard widget'ları
def render_metric_card(title, value, icon, color="primary"):
    st.markdown(f"""
    <div class="metric-card">
        <h3>{icon} {title}</h3>
        <h2>{value}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_workout_card(title, exercises, time_info=""):
    st.markdown(f"""
    <div class="workout-card">
        <h3>🏋️ {title} {time_info}</h3>
        <div class="stats-container">
    """, unsafe_allow_html=True)
    
    for exercise, sets in exercises.items():
        st.markdown(f"""
        <div class="exercise-item">
            <strong>{exercise}:</strong> {sets}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def render_nutrition_card():
    st.markdown("""
    <div class="nutrition-card">
        <h3>🍎 Beslenme Takibi</h3>
        <div class="stats-container">
    """, unsafe_allow_html=True)
    
    current_time = datetime.now().strftime("%H:%M")
    
    for meal_time, meal in PERSONAL_PROGRAM["beslenme"].items():
        status = "✅" if current_time > meal_time else "⏰"
        st.markdown(f"""
        <div class="exercise-item">
            {status} <strong>{meal_time}:</strong> {meal}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# Ana uygulama
def main():
    # Kullanıcı giriş kontrolü
    is_logged_in, user_id = user_auth()
    
    if not is_logged_in:
        st.info("👆 Lütfen giriş yapın veya kayıt olun.")
        return
    
    # MongoDB ve kullanıcı bilgilerini al
    db = init_mongodb()
    if not db:
        st.error("🔴 Veritabanı bağlantısı kurulamadı!")
        return
    
    try:
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            st.error("❌ Kullanıcı bulunamadı!")
            st.session_state.user_id = None
            st.rerun()
            return
    except Exception as e:
        st.error(f"🔴 Kullanıcı bilgileri alınamadı: {e}")
        return
    
    # Sidebar - Kullanıcı profili
    with st.sidebar:
        st.markdown(f"""
        <div class="main-header">
            <h2>👋 Hoş geldin!</h2>
            <h3>{user_data['full_name']}</h3>
            <p>Hafta {user_data.get('program_week', 1)}/12</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Hızlı istatistikler
        st.markdown("### 📊 Hızlı Bakış")
        
        try:
            height_m = user_data.get('height', 170) / 100
            weight_kg = user_data.get('weight', 70)
            bmi = weight_kg / (height_m ** 2)
            
            if bmi < 18.5:
                bmi_status = "Zayıf"
            elif bmi < 25:
                bmi_status = "Normal"
            elif bmi < 30:
                bmi_status = "Kilolu"
            else:
                bmi_status = "Obez"
            
            st.metric("BMI", f"{bmi:.1f}", f"{bmi_status}")
        except:
            st.metric("BMI", "N/A")
        
        st.metric("Yaş", f"{user_data.get('age', 0)}")
        st.metric("Kilo", f"{user_data.get('weight', 0)} kg")
        st.metric("Boy", f"{user_data.get('height', 0)} cm")
        
        # Çıkış butonu
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()
    
    # Ana içerik
    st.markdown(f"""
    <div class="main-header">
        <h1>💪 Chym Fitness Dashboard</h1>
        <p>Bugün de harika bir antrenman günü!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ana menü
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard", 
        "📋 Programım", 
        "📊 Takibim", 
        "🤖 AI Koç", 
        "⚙️ Ayarlar"
    ])
    
    with tab1:
        # Bugünün programı
        program_week = user_data.get('program_week', 1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if program_week <= 2:
                render_workout_card("Sabah Antrenmanı", PERSONAL_PROGRAM["hafta_1_2"]["sabah"], "(06:00)")
            else:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ Sabah Antrenmanı (06:00)</h3>
                    <div class="stats-container">
                        <div class="exercise-item">
                            <strong>Güç Odaklı:</strong> Her hareket 6 set, 6-12 tekrar, 90sn dinlenme
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if program_week <= 2:
                render_workout_card("Akşam Antrenmanı", PERSONAL_PROGRAM["hafta_1_2"]["aksam"], "(18:00)")
            else:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ Akşam Antrenmanı (18:00)</h3>
                    <div class="stats-container">
                        <div class="exercise-item">
                            <strong>Dayanıklılık + Metabolik:</strong> Süpersetler, 15-25 tekrar
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Beslenme takibi
        render_nutrition_card()
        
        # Günlük motivasyon
        st.markdown("""
        <div class="workout-card">
            <h3>🔥 Günlük Motivasyon</h3>
            <div class="stats-container">
                <div class="exercise-item">
                    <strong>Bugünün sözü:</strong> "Başarı, sürekli çaba göstermenin sonucudur. Sen yapabilirsin! 💪"
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📋 Kişisel Programım")
        
        program_week = user_data.get('program_week', 1)
        
        # Hafta seçici
        col1, col2 = st.columns([3, 1])
        with col1:
            new_week = st.selectbox(
                "Program Haftası", 
                range(1, 13), 
                index=program_week-1, 
                key="program_week_selector"
            )
        
        with col2:
            if new_week != program_week:
                if st.button("🔄 Güncelle"):
                    try:
                        db.users.update_one(
                            {"_id": ObjectId(user_id)},
                            {"$set": {"program_week": new_week}}
                        )
                        st.success("✅ Program haftası güncellendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"🔴 Program haftası güncellenirken hata: {e}")
        
        # Program progress bar
        progress = (new_week - 1) / 12
        st.markdown(f"""
        <div class="progress-bar" style="width: {progress*100}%"></div>
        <p style="text-align: center; margin-top: 0.5rem;">
            <strong>Program İlerleme:</strong> {new_week}/12 hafta (%{progress*100:.0f})
        </p>
        """, unsafe_allow_html=True)
        
        # Program detayları
        if new_week <= 2:
            st.markdown("#### 🎯 Hafta 1-2: Temel Hareket Kalıpları")
            
            col1, col2 = st.columns(2)
            
            with col1:
                render_workout_card("Sabah Antrenmanı", PERSONAL_PROGRAM["hafta_1_2"]["sabah"], "(06:00)")
            
            with col2:
                render_workout_card("Akşam Antrenmanı", PERSONAL_PROGRAM["hafta_1_2"]["aksam"], "(18:00)")
        
        elif new_week <= 6:
            st.markdown("#### 🚀 Hafta 3-6: Yoğunluk Artışı")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ Sabah (Güç Odaklı)</h3>
                    <div class="stats-container">
                        <div class="exercise-item">
                            <strong>Format:</strong> Her hareket 6 set, 6-12 tekrar, 90sn dinlenme
                        </div>
                        <div class="exercise-item">
                            <strong>Teknik:</strong> Negatif faz 3-5sn
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ Akşam (Dayanıklılık + Metabolik)</h3>
                    <div class="stats-container">
                        <div class="exercise-item">
                            <strong>Format:</strong> Süpersetler, 15-25 tekrar
                        </div>
                        <div class="exercise-item">
                            <strong>Dinlenme:</strong> Set arası 30sn, süperset arası 60sn
                        </div>
                        <div class="exercise-item">
                            <strong>Tempo:</strong> Patlayıcı yukarı, kontrollü aşağı
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.markdown("#### 🏆 Hafta 7-12: İleri Seviye Hareketler")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ İleri Seviye Hareketler</h3>
                    <div class="stats-container">
                """, unsafe_allow_html=True)
                
                for i, exercise in enumerate(PERSONAL_PROGRAM["hafta_7_12"]["ileri_seviye"][:4]):
                    st.markdown(f"""
                    <div class="exercise-item">
                        <strong>{i+1}.</strong> {exercise}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="workout-card">
                    <h3>🏋️ İleri Seviye Hareketler</h3>
                    <div class="stats-container">
                """, unsafe_allow_html=True)
                
                for i, exercise in enumerate(PERSONAL_PROGRAM["hafta_7_12"]["ileri_seviye"][4:]):
                    st.markdown(f"""
                    <div class="exercise-item">
                        <strong>{i+5}.</strong> {exercise}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Beslenme planı
        st.markdown("### 🍎 Beslenme Planı")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="nutrition-card">
                <h3>🕐 Günlük Beslenme</h3>
                <div class="stats-container">
            """, unsafe_allow_html=True)
            
            for meal_time, meal in PERSONAL_PROGRAM["beslenme"].items():
                st.markdown(f"""
                <div class="exercise-item">
                    <strong>{meal_time}:</strong> {meal}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="nutrition-card">
                <h3>🎯 Makro Hedefler</h3>
                <div class="stats-container">
            """, unsafe_allow_html=True)
            
            for macro, amount in PERSONAL_PROGRAM["makrolar"].items():
                st.markdown(f"""
                <div class="exercise-item">
                    <strong>{macro.title()}:</strong> {amount}</div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### 📊 Fitness Takibim")
        
        # İlerleme grafikleri
        col1, col2 = st.columns(2)
        
        with col1:
            # Haftalık ilerleme
            weeks = list(range(1, 13))
            progress_data = [w * 8.33 for w in weeks]  # Her hafta %8.33 ilerleme
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weeks,
                y=progress_data,
                mode='lines+markers',
                name='İlerleme',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="📈 Haftalık İlerleme",
                xaxis_title="Hafta",
                yaxis_title="İlerleme (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title_font=dict(color='#667eea', size=16)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Kilo takibi (örnek veri)
            dates = pd.date_range(start='2024-01-01', periods=12, freq='W')
            weights = [user_data.get('weight', 70) - i*0.5 for i in range(12)]
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=dates,
                y=weights,
                mode='lines+markers',
                name='Kilo',
                line=dict(color='#f093fb', width=3),
                marker=dict(size=8)
            ))
            
            fig2.update_layout(
                title="⚖️ Kilo Takibi",
                xaxis_title="Tarih",
                yaxis_title="Kilo (kg)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title_font=dict(color='#f093fb', size=16)
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Antrenman geçmişi
        st.markdown("### 🏋️ Antrenman Geçmişi")
        
        # Bugünün antrenman kaydı
        col1, col2, col3 = st.columns(3)
        
        with col1:
            workout_completed = st.checkbox("✅ Sabah antrenmanı tamamlandı")
        
        with col2:
            workout_rating = st.slider("⭐ Antrenman zorluğu", 1, 10, 7)
        
        with col3:
            if st.button("💾 Kaydet"):
                try:
                    workout_data = {
                        "user_id": user_id,
                        "date": datetime.now().date(),
                        "workout_type": "sabah",
                        "completed": workout_completed,
                        "rating": workout_rating,
                        "created_at": datetime.now()
                    }
                    
                    workout_data = sanitize_data(workout_data)
                    db.workouts.insert_one(workout_data)
                    st.success("✅ Antrenman kaydedildi!")
                except Exception as e:
                    st.error(f"🔴 Kayıt sırasında hata: {e}")
        
        # Beslenme takibi
        st.markdown("### 🍽️ Beslenme Takibi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            protein_intake = st.number_input("🥩 Protein (g)", min_value=0, max_value=300, value=150)
            carb_intake = st.number_input("🍞 Karbonhidrat (g)", min_value=0, max_value=500, value=340)
        
        with col2:
            fat_intake = st.number_input("🥑 Yağ (g)", min_value=0, max_value=150, value=75)
            water_intake = st.number_input("💧 Su (L)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
        
        if st.button("💾 Beslenme Kaydet"):
            try:
                nutrition_data = {
                    "user_id": user_id,
                    "date": datetime.now().date(),
                    "protein": protein_intake,
                    "carbs": carb_intake,
                    "fat": fat_intake,
                    "water": water_intake,
                    "created_at": datetime.now()
                }
                
                nutrition_data = sanitize_data(nutrition_data)
                db.nutrition.insert_one(nutrition_data)
                st.success("✅ Beslenme verileri kaydedildi!")
            except Exception as e:
                st.error(f"🔴 Kayıt sırasında hata: {e}")
        
        # Makro hedefler vs gerçek
        st.markdown("### 🎯 Makro Hedefler vs Gerçek")
        
        targets = {
            "Protein": {"hedef": 160, "gerçek": protein_intake},
            "Karbonhidrat": {"hedef": 370, "gerçek": carb_intake},
            "Yağ": {"hedef": 80, "gerçek": fat_intake}
        }
        
        for macro, values in targets.items():
            progress = min(values["gerçek"] / values["hedef"], 1.0)
            st.markdown(f"""
            <div class="stats-container">
                <h4>{macro}: {values["gerçek"]}g / {values["hedef"]}g</h4>
                <div class="progress-bar" style="width: {progress*100}%"></div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 🤖 AI Koç - Coach Alex")
        
        # Chat geçmişi
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat mesajlarını göster
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>Sen:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>Coach Alex:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
        
        # Yeni mesaj gönder
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_input("💬 Coach Alex'e mesaj gönder...", key="chat_input")
        
        with col2:
            if st.button("📤 Gönder"):
                if user_message:
                    # Kullanıcı mesajını ekle
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_message
                    })
                    
                    # AI yanıtını al
                    with st.spinner("Coach Alex düşünüyor..."):
                        ai_response = ai_coach_response(user_message, user_data)
                    
                    # AI yanıtını ekle
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })
                    
                    st.rerun()
        
        # Hızlı sorular
        st.markdown("### 💡 Hızlı Sorular")
        
        quick_questions = [
            "Bugünkü antrenmanım nasıl olmalı?",
            "Protein alımımı nasıl artırabilirim?",
            "Motivasyonum düştü, yardım et!",
            "Hangi egzersizleri daha iyi yapabilirim?",
            "Beslenme planım doğru mu?"
        ]
        
        cols = st.columns(3)
        for i, question in enumerate(quick_questions):
            with cols[i % 3]:
                if st.button(question, key=f"quick_q_{i}"):
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": question
                    })
                    
                    with st.spinner("Coach Alex düşünüyor..."):
                        ai_response = ai_coach_response(question, user_data)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })
                    
                    st.rerun()
        
        # Chat geçmişini temizle
        if st.button("🗑️ Sohbet Geçmişini Temizle"):
            st.session_state.chat_history = []
            st.rerun()
    
    with tab5:
        st.markdown("### ⚙️ Profil Ayarları")
        
        # Profil güncelleme
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Kişisel Bilgiler")
            
            new_full_name = st.text_input("Ad Soyad", value=user_data.get('full_name', ''))
            new_age = st.number_input("Yaş", min_value=15, max_value=80, value=user_data.get('age', 25))
            new_weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=user_data.get('weight', 70))
            new_height = st.number_input("Boy (cm)", min_value=140, max_value=220, value=user_data.get('height', 170))
        
        with col2:
            st.markdown("#### 🎯 Hedefler")
            
            fitness_goal = st.selectbox(
                "Fitness Hedefin",
                ["Kas Artışı", "Kilo Verme", "Dayanıklılık", "Güç Artışı", "Genel Sağlık"],
                index=0
            )
            
            activity_level = st.selectbox(
                "Aktivite Seviyesi",
                ["Sedanter", "Az Aktif", "Orta Aktif", "Çok Aktif", "Ekstra Aktif"],
                index=2
            )
            
            daily_goal = st.selectbox(
                "Günlük Hedef",
                ["Temel Egzersizler", "Orta Seviye", "İleri Seviye", "Profesyonel"],
                index=1
            )
        
        # Güncelleme butonu
        if st.button("💾 Profili Güncelle", use_container_width=True):
            try:
                update_data = {
                    "full_name": new_full_name,
                    "age": int(new_age),
                    "weight": float(new_weight),
                    "height": int(new_height),
                    "fitness_goal": fitness_goal,
                    "activity_level": activity_level,
                    "daily_goal": daily_goal,
                    "updated_at": datetime.now()
                }
                
                update_data = sanitize_data(update_data)
                
                db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
                
                st.success("✅ Profil başarıyla güncellendi!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"🔴 Profil güncellenirken hata: {e}")
        
        # Veri analizi
        st.markdown("### 📊 Veri Analizi")
        
        if st.button("📈 Detaylı Analiz Göster"):
            try:
                # Antrenman istatistikleri
                workout_stats = list(db.workouts.find({"user_id": user_id}))
                nutrition_stats = list(db.nutrition.find({"user_id": user_id}))
                
                if workout_stats:
                    st.markdown("#### 🏋️ Antrenman İstatistikleri")
                    total_workouts = len(workout_stats)
                    completed_workouts = sum(1 for w in workout_stats if w.get('completed', False))
                    avg_rating = sum(w.get('rating', 0) for w in workout_stats) / total_workouts if total_workouts > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        render_metric_card("Toplam Antrenman", total_workouts, "🏋️")
                    
                    with col2:
                        render_metric_card("Tamamlanan", completed_workouts, "✅")
                    
                    with col3:
                        render_metric_card("Ortalama Puan", f"{avg_rating:.1f}/10", "⭐")
                
                if nutrition_stats:
                    st.markdown("#### 🍽️ Beslenme İstatistikleri")
                    avg_protein = sum(n.get('protein', 0) for n in nutrition_stats) / len(nutrition_stats)
                    avg_carbs = sum(n.get('carbs', 0) for n in nutrition_stats) / len(nutrition_stats)
                    avg_fat = sum(n.get('fat', 0) for n in nutrition_stats) / len(nutrition_stats)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        render_metric_card("Ortalama Protein", f"{avg_protein:.0f}g", "🥩")
                    
                    with col2:
                        render_metric_card("Ortalama Karb", f"{avg_carbs:.0f}g", "🍞")
                    
                    with col3:
                        render_metric_card("Ortalama Yağ", f"{avg_fat:.0f}g", "🥑")
                
                if not workout_stats and not nutrition_stats:
                    st.info("📊 Henüz analiz edilecek veri yok. Antrenman ve beslenme kayıtlarınızı tutmaya başlayın!")
                    
            except Exception as e:
                st.error(f"🔴 Veri analizi sırasında hata: {e}")
        
        # Hesap yönetimi
        st.markdown("### 🔐 Hesap Yönetimi")
        
        st.warning("⚠️ Dikkat: Bu işlemler geri alınamaz!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Tüm Verileri Sil"):
                if st.checkbox("Emin misin? Tüm veriler silinecek!"):
                    try:
                        db.workouts.delete_many({"user_id": user_id})
                        db.nutrition.delete_many({"user_id": user_id})
                        st.success("✅ Tüm veriler silindi!")
                    except Exception as e:
                        st.error(f"🔴 Veri silme sırasında hata: {e}")
        
        with col2:
            if st.button("❌ Hesabı Sil"):
                if st.checkbox("Emin misin? Hesap tamamen silinecek!"):
                    try:
                        db.users.delete_one({"_id": ObjectId(user_id)})
                        db.workouts.delete_many({"user_id": user_id})
                        db.nutrition.delete_many({"user_id": user_id})
                        st.session_state.user_id = None
                        st.success("✅ Hesap silindi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"🔴 Hesap silme sırasında hata: {e}")
        
        # Uygulama bilgileri
        st.markdown("### ℹ️ Uygulama Bilgileri")
        
        st.info("""
        **Chym Fitness App v1.0**
        
        🏋️ Kişiselleştirilmiş fitness programları
        🤖 AI koç desteği
        📊 Detaylı takip sistemi
        🍎 Beslenme planları
        
        Geliştirici: Chym Team
        """)

if __name__ == "__main__":
    main()
