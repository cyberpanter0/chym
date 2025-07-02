import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import time

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
</style>
""", unsafe_allow_html=True)

# Sabitler ve Yapılandırma
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Beast Mode Verileri
BEAST_MODE_DATA = {
    'exercises': {
        'push-up': {'muscleGroup': 'chest', 'difficulty': 'beginner'},
        'pull-up': {'muscleGroup': 'back', 'difficulty': 'intermediate'},
        'squat': {'muscleGroup': 'legs', 'difficulty': 'beginner'},
        'plank': {'muscleGroup': 'core', 'difficulty': 'beginner'},
        'burpee': {'muscleGroup': 'full_body', 'difficulty': 'advanced'},
        'diamond push-up': {'muscleGroup': 'chest', 'difficulty': 'intermediate'},
        'pistol squat': {'muscleGroup': 'legs', 'difficulty': 'advanced'},
        'handstand': {'muscleGroup': 'shoulders', 'difficulty': 'advanced'}
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

# Session State Başlatma
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'users' not in st.session_state:
        st.session_state.users = [
            {
                'id': 1,
                'name': 'Han',
                'username': 'han123',
                'password': '123456',
                'weight': 75,
                'age': 25,
                'goal': 'muscle_gain',
                'join_date': datetime(2024, 1, 15),
                'exercise_history': [
                    {'date': '2024-07-01', 'exercise': 'push-up', 'sets': 4, 'reps': 15, 'muscle_group': 'chest'},
                    {'date': '2024-07-01', 'exercise': 'squat', 'sets': 3, 'reps': 20, 'muscle_group': 'legs'},
                    {'date': '2024-06-30', 'exercise': 'pull-up', 'sets': 3, 'reps': 8, 'muscle_group': 'back'}
                ],
                'chat_history': []
            }
        ]
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'exercise_log' not in st.session_state:
        st.session_state.exercise_log = []
    if 'beast_mode_score' not in st.session_state:
        st.session_state.beast_mode_score = 75

# Mesaj Analizi
def analyze_message(message):
    exercise_keywords = ['antrenman', 'egzersiz', 'set', 'tekrar', 'squat', 'push-up', 'pull-up', 'plank', 'burpee']
    general_keywords = ['yorgun', 'motivasyon', 'nasılım', 'hissediyorum', 'uyku', 'beslenme']
    
    message_lower = message.lower()
    exercise_count = sum(1 for keyword in exercise_keywords if keyword in message_lower)
    general_count = sum(1 for keyword in general_keywords if keyword in message_lower)
    
    exercise_data = None
    if exercise_count > general_count:
        exercises = list(BEAST_MODE_DATA['exercises'].keys())
        found_exercise = next((ex for ex in exercises if ex.lower() in message_lower), None)
        
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

# Groq API Çağrısı
def call_groq_api(message, message_type, user_data):
    try:
        system_prompt = ""
        if message_type == 'exercise':
            system_prompt = f"""Sen profesyonel bir fitness koçusun. Kullanıcı egzersiz bilgisi paylaştı: "{message}". 
                           Kullanıcı bilgileri: İsim: {user_data['name']}, Kilo: {user_data['weight']}kg, Yaş: {user_data['age']}, Hedef: {user_data['goal']}.
                           Motive edici, kısa (max 100 kelime) Türkçe yanıt ver. Egzersiz hakkında teknik tavsiye ver."""
        else:
            system_prompt = f"""Sen profesyonel bir fitness koçusun. Kullanıcı genel bir mesaj yazdı: "{message}".
                           Kullanıcı bilgileri: İsim: {user_data['name']}, Beast Mode Skoru: %{st.session_state.beast_mode_score}.
                           Destekleyici, motive edici, kısa (max 80 kelime) Türkçe yanıt ver. Soru sor ve tavsiye ver."""

        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'system', 'content': system_prompt}],
            'temperature': 0.7,
            'max_tokens': 300
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return f"❌ API Hatası ({response.status_code}). Tekrar deneyin."
            
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"

# Giriş/Kayıt Ekranı
def login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🦁 Beast Mode Coach</h1>
        <p>Kişisel Fitness Antrenörün</p>
    </div>
    """, unsafe_allow_html=True)
    
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
                    user = next((u for u in st.session_state.users 
                               if u['username'] == username and u['password'] == password), None)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.exercise_log = user['exercise_history']
                        st.session_state.chat_history = user.get('chat_history', [])
                        st.success("✅ Giriş başarılı!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı!")
            
            st.info("📝 Demo Hesap: Kullanıcı: han123 | Şifre: 123456")
        
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
                    ("muscle_gain", "💪 Kas Kazanımı"),
                    ("weight_loss", "🔥 Kilo Verme"),
                    ("endurance", "🏃 Dayanıklılık"),
                    ("strength", "⚡ Güç Artırımı")
                ], format_func=lambda x: x[1])
                
                register_button = st.form_submit_button("✨ Kayıt Ol", use_container_width=True)
                
                if register_button:
                    if name and new_username and new_password:
                        new_user = {
                            'id': len(st.session_state.users) + 1,
                            'name': name,
                            'username': new_username,
                            'password': new_password,
                            'weight': weight,
                            'age': age,
                            'goal': goal[0],
                            'join_date': datetime.now(),
                            'exercise_history': [],
                            'chat_history': []
                        }
                        
                        st.session_state.users.append(new_user)
                        st.session_state.authenticated = True
                        st.session_state.current_user = new_user
                        st.session_state.exercise_log = []
                        st.session_state.chat_history = []
                        st.success("✅ Kayıt başarılı!")
                        time.sleep(1)
                        st.rerun()
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
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Panel", "🤖 Koç", "💪 Egzersizler", "📈 İlerleme"])
    
    with tab1:
        dashboard_tab()
    
    with tab2:
        coach_tab()
    
    with tab3:
        exercises_tab()
    
    with tab4:
        progress_tab()

# Dashboard Tab
def dashboard_tab():
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Beast Mode Skoru", f"{st.session_state.beast_mode_score}%", "🔥")
    
    with col2:
        st.metric("Toplam Antrenman", len(st.session_state.exercise_log), "💪")
    
    with col3:
        week_ago = datetime.now() - timedelta(days=7)
        weekly_exercises = sum(1 for ex in st.session_state.exercise_log 
                             if datetime.strptime(ex['date'], '%Y-%m-%d') >= week_ago)
        st.metric("Bu Hafta", weekly_exercises, "📅")
    
    with col4:
        st.metric("Güncel Kilo", f"{st.session_state.current_user['weight']}kg", "⚖️")
    
    st.divider()
    
    # Charts
    if st.session_state.exercise_log:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Haftalık İlerleme")
            weekly_data = get_weekly_progress()
            if weekly_data:
                fig = px.line(weekly_data, x='date', y='volume', 
                            title="Günlük Egzersiz Volümü")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Kas Grubu Dağılımı")
            muscle_data = get_muscle_group_data()
            if muscle_data:
                fig = px.pie(muscle_data, values='value', names='name',
                           title="Kas Grubu Volüm Dağılımı")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📈 Egzersiz geçmişin oluştukça grafikler burada görünecek!")

# Coach Tab
def coach_tab():
    st.subheader("🤖 AI Koçun ile Konuş")
    st.write("Antrenman durumunu paylaş, sorular sor ve kişiselleştirilmiş tavsiyeler al!")
    
    # Chat History
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem;">🦁</div>
                <p style="color: #666;">Koçunla konuşmaya başla! Bugün nasılsın?</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for chat in st.session_state.chat_history:
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <p>{chat['message']}</p>
                    <small>{datetime.fromisoformat(chat['date']).strftime('%H:%M')} 
                    {'💪' if chat['type'] == 'exercise' else ''}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # AI response
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <p>{chat['response']}</p>
                    <small>🤖 AI Koç</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Chat Input
    with st.form("chat_form", clear_on_submit=True):
        message = st.text_area("Mesajını yaz...", 
                              placeholder="örn: 'Bugün 3 set 15 push-up yaptım' veya 'Çok yorgunum'",
                              height=100)
        send_button = st.form_submit_button("📤 Gönder", use_container_width=True)
        
        if send_button and message.strip():
            with st.spinner("🤖 AI Koç düşünüyor..."):
                analysis = analyze_message(message)
                ai_response = call_groq_api(message, analysis['type'], st.session_state.current_user)
                
                new_chat = {
                    'id': len(st.session_state.chat_history) + 1,
                    'date': datetime.now().isoformat(),
                    'message': message,
                    'response': ai_response,
                    'type': analysis['type']
                }
                
                st.session_state.chat_history.append(new_chat)
                
                # Egzersiz ise log'a ekle
                if analysis['exercise_data']:
                    new_exercise = {
                        'id': len(st.session_state.exercise_log) + 1,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        **analysis['exercise_data']
                    }
                    st.session_state.exercise_log.append(new_exercise)
                    
                    # Beast Mode Score artır
                    st.session_state.beast_mode_score = min(100, st.session_state.beast_mode_score + 2)
                
                st.rerun()

# Exercises Tab
def exercises_tab():
    st.subheader("💪 Egzersiz Kayıtların")
    
    if not st.session_state.exercise_log:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem;">🏃‍♂️</div>
            <p style="color: #666;">Henüz egzersiz kaydın yok. Koçunla konuşarak başla!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Egzersiz tablosu
        df = pd.DataFrame(st.session_state.exercise_log)
        df['Tarih'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')
        df['Egzersiz'] = df['exercise'].str.title()
        df['Kas Grubu'] = df['muscle_group'].map(BEAST_MODE_DATA['muscle_groups'])
        df['Set'] = df['sets']
        df['Tekrar'] = df['reps']
        df['Toplam'] = df['sets'] * df['reps']
        
        display_df = df[['Tarih', 'Egzersiz', 'Kas Grubu', 'Set', 'Tekrar', 'Toplam']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Özet istatistikler
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Toplam Egzersiz", len(df))
        
        with col2:
            st.metric("Toplam Volüm", df['Toplam'].sum())
        
        with col3:
            most_trained = df['Kas Grubu'].value_counts().index[0] if len(df) > 0 else "N/A"
            st.metric("En Çok Çalışılan", most_trained)

# Progress Tab
def progress_tab():
    st.subheader("📈 İlerleme Analizi")
    
    # Özet kartlar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #FF6B35;">{}</h3>
            <p>Toplam Egzersiz</p>
        </div>
        """.format(len(st.session_state.exercise_log)), unsafe_allow_html=True)
    
    with col2:
        total_volume = sum(ex['sets'] * ex['reps'] for ex in st.session_state.exercise_log)
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #4ECDC4;">{}</h3>
            <p>Toplam Volüm</p>
        </div>
        """.format(total_volume), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #45B7D1;">{}%</h3>
            <p>Beast Mode Skoru</p>
        </div>
        """.format(st.session_state.beast_mode_score), unsafe_allow_html=True)
    
    st.divider()
    
    # İlerleme grafikleri
    if st.session_state.exercise_log:
        # Haftalık ilerleme
        st.subheader("Son 7 Günlük İlerleme")
        weekly_data = get_weekly_progress()
        if weekly_data:
            fig = px.bar(weekly_data, x='date', y='volume',
                        title="Günlük Egzersiz Volümü")
            st.plotly_chart(fig, use_container_width=True)
        
        # Hedefler ve başarılar
        st.subheader("🎯 Hedefler ve Başarılar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Haftalık Hedef**: 5/7 gün")
            progress_value = min(weekly_data[-1]['volume'] / 50 if weekly_data else 0, 1)
            st.progress(progress_value)
        
        with col2:
            st.write(f"**Beast Mode**: {st.session_state.beast_mode_score}%")
            st.progress(st.session_state.beast_mode_score / 100)
    else:
        st.info("📊 Egzersiz geçmişin oluştukça ilerleme analizin burada görünecek!")

# Yardımcı Fonksiyonlar
def get_weekly_progress():
    if not st.session_state.exercise_log:
        return []
    
    weekly_data = []
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        date_str = date.strftime('%Y-%m-%d')
        
        day_exercises = [ex for ex in st.session_state.exercise_log if ex['date'] == date_str]
        total_volume = sum(ex['sets'] * ex['reps'] for ex in day_exercises)
        
        weekly_data.append({
            'date': date.strftime('%d.%m'),
            'volume': total_volume,
            'exercises': len(day_exercises)
        })
    
    return weekly_data

def get_muscle_group_data():
    if not st.session_state.exercise_log:
        return []
    
    groups = {}
    for exercise in st.session_state.exercise_log:
        group = exercise['muscle_group']
        groups[group] = groups.get(group, 0) + (exercise['sets'] * exercise['reps'])
    
    return [
        {
            'name': BEAST_MODE_DATA['muscle_groups'].get(group, group),
            'value': volume
        }
        for group, volume in groups.items()
    ]

# Ana Uygulama Akışı
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
