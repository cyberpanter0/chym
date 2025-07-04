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
        
        # Beslenme hatırlatıcısı
        st.subheader("Beslenme Hatırlatıcısı")
        current_time = datetime.now().strftime("%H:%M")
        
        for meal_time, meal in PERSONAL_PROGRAM["beslenme"].items():
            if current_time > meal_time:
                st.write(f"✅ {meal_time}: {meal}")
            else:
                st.write(f"⏰ {meal_time}: {meal}")
                break
    
    with tab2:
        st.header("Kişisel Programım")
        
        program_week = user_data.get('program_week', 1)
        
        # Hafta seçici
        new_week = st.selectbox("Program Haftası", range(1, 13), index=program_week-1, key="program_week_selector")
        
        if new_week != program_week:
            try:
                db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"program_week": new_week}}
                )
                st.success(f"Program haftası {new_week} olarak güncellendi!")
                st.rerun()
            except Exception as e:
                st.error(f"Program haftası güncellenirken hata: {e}")
        
        # Program detayları
        if new_week <= 2:
            st.success("**Hafta 1-2: Temel Hareket Kalıpları**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Sabah Antrenmanı (06:00)")
                for exercise, sets in PERSONAL_PROGRAM["hafta_1_2"]["sabah"].items():
                    st.write(f"**{exercise}:** {sets}")
            
            with col2:
                st.markdown("### Akşam Antrenmanı (18:00)")
                for exercise, sets in PERSONAL_PROGRAM["hafta_1_2"]["aksam"].items():
                    st.write(f"**{exercise}:** {sets}")
        
        elif new_week <= 6:
            st.success("**Hafta 3-6: Yoğunluk Artışı**")
            st.markdown("### Sabah (Güç Odaklı)")
            st.write(PERSONAL_PROGRAM["hafta_3_6"]["sabah"])
            st.write("• Negatif faz 3-5sn")
            
            st.markdown("### Akşam (Dayanıklılık + Metabolik)")
            st.write(PERSONAL_PROGRAM["hafta_3_6"]["aksam"])
            st.write("• Set arası 30sn, süperset arası 60sn")
            st.write("• Tempo: patlayıcı yukarı, kontrollü aşağı")
        
        else:
            st.success("**Hafta 7-12: İleri Seviye Hareketler**")
            for exercise in PERSONAL_PROGRAM["hafta_7_12"]["ileri_seviye"]:
                st.write(f"• {exercise}")
        
        # Beslenme planı
        st.subheader("Beslenme Planı")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Günlük Beslenme")
            for meal_time, meal in PERSONAL_PROGRAM["beslenme"].items():
                st.write(f"**{meal_time}:** {meal}")
        
        with col2:
            st.markdown("### Makro Hedefler")
            for macro, amount in PERSONAL_PROGRAM["makrolar"].items():
                st.write(f"**{macro.title()}:** {amount}")
    
    with tab3:
        st.header("Takibim")
        
        # Antrenman kaydı
        st.subheader("Antrenman Kaydet")
        
        col1, col2 = st.columns(2)
        
        with col1:
            workout_type = st.selectbox("Antrenman Tipi", ["Sabah", "Akşam"])
            workout_date = st.date_input("Tarih", datetime.now())
            
        with col2:
            duration = st.number_input("Süre (dakika)", min_value=5, max_value=180, value=45)
            intensity = st.slider("Yoğunluk", 1, 10, 7)
        
        notes = st.text_area("Notlar")
        
        if st.button("Antrenman Kaydet"):
            try:
                workout_data = {
                    "user_id": user_id,
                    "type": workout_type,
                    "date": datetime.combine(workout_date, datetime.min.time()),
                    "duration": int(duration),
                    "intensity": int(intensity),
                    "notes": notes,
                    "created_at": datetime.now()
                }
                
                # Veri tiplerini sanitize et
                workout_data = sanitize_data(workout_data)
                
                db.workouts.insert_one(workout_data)
                st.success("Antrenman kaydedildi! 🎉")
            except Exception as e:
                st.error(f"Antrenman kaydedilirken hata: {e}")
        
        # Ağırlık takibi
        st.subheader("Ağırlık Takibi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_weight = st.number_input("Yeni Kilo (kg)", min_value=40.0, max_value=200.0, value=float(user_data.get('weight', 70)))
            weight_date = st.date_input("Tarih", datetime.now(), key="weight_date")
        
        if st.button("Ağırlık Kaydet"):
            try:
                weight_data = {
                    "user_id": user_id,
                    "weight": float(new_weight),
                    "date": datetime.combine(weight_date, datetime.min.time()),
                    "created_at": datetime.now()
                }
                
                # Veri tiplerini sanitize et
                weight_data = sanitize_data(weight_data)
                
                db.weight_logs.insert_one(weight_data)
                
                # Kullanıcının mevcut kilosunu güncelle
                db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"weight": float(new_weight)}}
                )
                
                st.success("Ağırlık kaydedildi!")
            except Exception as e:
                st.error(f"Ağırlık kaydedilirken hata: {e}")
        
        # Grafik görüntüleme
        st.subheader("İstatistikler")
        
        try:
            # Ağırlık grafiği
            weight_logs = list(db.weight_logs.find({"user_id": user_id}).sort("date", 1))
            
            if weight_logs:
                df_weight = pd.DataFrame(weight_logs)
                df_weight['date'] = pd.to_datetime(df_weight['date'])
                
                fig = px.line(df_weight, x='date', y='weight', 
                             title='Ağırlık Değişimi', 
                             labels={'weight': 'Kilo (kg)', 'date': 'Tarih'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz ağırlık kaydı yok.")
            
            # Antrenman istatistikleri
            workouts = list(db.workouts.find({"user_id": user_id}).sort("date", -1).limit(30))
            
            if workouts:
                df_workouts = pd.DataFrame(workouts)
                df_workouts['date'] = pd.to_datetime(df_workouts['date'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Haftalık antrenman sayısı
                    workout_counts = df_workouts.groupby(df_workouts['date'].dt.isocalendar().week).size()
                    fig = px.bar(x=workout_counts.index, y=workout_counts.values,
                               title='Haftalık Antrenman Sayısı',
                               labels={'x': 'Hafta', 'y': 'Antrenman Sayısı'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Ortalama yoğunluk
                    avg_intensity = df_workouts.groupby('date')['intensity'].mean()
                    fig = px.line(x=avg_intensity.index, y=avg_intensity.values,
                                title='Ortalama Antrenman Yoğunluğu',
                                labels={'x': 'Tarih', 'y': 'Yoğunluk'})
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz antrenman kaydı yok.")
        
        except Exception as e:
            st.error(f"İstatistikler yüklenirken hata: {e}")
    
    with tab4:
        st.header("AI Koçun - Coach Alex")
        
        # Chat geçmişi
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            for i, (role, message) in enumerate(st.session_state.chat_history):
                if role == "user":
                    st.markdown(f"**Sen:** {message}")
                else:
                    st.markdown(f"**Coach Alex:** {message}")
        
        # Mesaj gönderme
        user_message = st.text_input("Coach Alex'e mesaj gönder...", key="chat_input")
        
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("Gönder", key="send_message"):
                if user_message:
                    st.session_state.chat_history.append(("user", user_message))
                    
                    # AI yanıtı al
                    with st.spinner("Coach Alex düşünüyor..."):
                        ai_response = ai_coach_response(user_message, user_data)
                        st.session_state.chat_history.append(("assistant", ai_response))
                    
                    st.rerun()
        
        with col2:
            if st.button("Sohbeti Temizle", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Hızlı sorular
        st.subheader("Hızlı Sorular")
        
        quick_questions = [
            "Bugünkü antrenmanım nasıl olmalı?",
            "Motivasyonum düştü, ne yapmalıyım?",
            "Beslenme konusunda tavsiye ver",
            "Hangi egzersizi daha iyi yapabilirim?",
            "Bu hafta nasıl gidiyor?"
        ]
        
        cols = st.columns(len(quick_questions))
        for i, question in enumerate(quick_questions):
            with cols[i]:
                if st.button(question, key=f"quick_{i}"):
                    st.session_state.chat_history.append(("user", question))
                    
                    with st.spinner("Coach Alex düşünüyor..."):
                        ai_response = ai_coach_response(question, user_data)
                        st.session_state.chat_history.append(("assistant", ai_response))
                    
                    st.rerun()
    
    with tab5:
        st.header("Ayarlar")
        
        # Profil güncelleme
        st.subheader("Profil Bilgileri")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Ad Soyad", value=user_data.get('full_name', ''))
            new_age = st.number_input("Yaş", min_value=15, max_value=80, value=int(user_data.get('age', 25)))
            new_weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=int(user_data.get('weight', 70)))
        
        with col2:
            new_height = st.number_input("Boy (cm)", min_value=140, max_value=220, value=int(user_data.get('height', 170)))
            new_program_week = st.selectbox("Program Haftası", range(1, 13), index=int(user_data.get('program_week', 1))-1, key="settings_program_week")
        
        if st.button("Profil Güncelle"):
            try:
                update_data = {
                    "full_name": new_name,
                    "age": int(new_age),
                    "weight": float(new_weight),
                    "height": int(new_height),
                    "program_week": int(new_program_week),
                    "updated_at": datetime.now()
                }
                
                # Veri tiplerini sanitize et
                update_data = sanitize_data(update_data)
                
                db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
                
                st.success("Profil güncellendi!")
                st.rerun()
            except Exception as e:
                st.error(f"Profil güncellenirken hata: {e}")
        
        # Veri silme
        st.subheader("Veri Yönetimi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Antrenman Verilerini Sil", type="secondary"):
                try:
                    db.workouts.delete_many({"user_id": user_id})
                    st.success("Antrenman verileri silindi!")
                except Exception as e:
                    st.error(f"Antrenman verileri silinirken hata: {e}")
        
        with col2:
            if st.button("Ağırlık Verilerini Sil", type="secondary"):
                try:
                    db.weight_logs.delete_many({"user_id": user_id})
                    st.success("Ağırlık verileri silindi!")
                except Exception as e:
                    st.error(f"Ağırlık verileri silinirken hata: {e}")
        
        # Hesap silme
        st.subheader("Hesap Yönetimi")
        
        if st.button("Hesabı Sil", type="secondary"):
            # Tüm kullanıcı verilerini sil
            db.users.delete_one({"_id": ObjectId(user_id)})
            db.workouts.delete_many({"user_id": user_id})
            db.weight_logs.delete_many({"user_id": user_id})
            
            st.session_state.user_id = None
            st.success("Hesap silindi!")
            st.rerun()

if __name__ == "__main__":
    main()
