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

# Sabit değerler
GROQ_API_KEY = "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"
MONGODB_URI = "mongodb+srv://emo36kars:wRhNGbc6LPX26.c@cluster0.zttnhmt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB bağlantısı
@st.cache_resource
def init_mongodb():
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.chym_fitness
        return db
    except Exception as e:
        st.error(f"MongoDB bağlantı hatası: {e}")
        return None

# Groq AI istemcisi
@st.cache_resource
def init_groq():
    return Groq(api_key=GROQ_API_KEY)

# Şifre hashleme
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        "05:30": "500ml su",
        "06:00": "1 muz + kahve",
        "07:15": "Protein shake + bal",
        "08:00": "Kahvaltı",
        "11:00": "Ara öğün",
        "13:30": "Öğle yemeği",
        "16:00": "Pre-workout atıştırmalık",
        "18:45": "Süt + muz",
        "20:00": "Akşam yemeği",
        "22:00": "Casein + kuruyemiş"
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
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        st.subheader("Giriş Yap")
        username = st.text_input("Kullanıcı Adı", key="login_username")
        password = st.text_input("Şifre", type="password", key="login_password")
        
        if st.button("Giriş Yap"):
            if username and password:
                user = db.users.find_one({
                    "username": username,
                    "password": hash_password(password)
                })
                if user:
                    st.session_state.user_id = str(user["_id"])
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre yanlış!")
    
    with tab2:
        st.subheader("Kayıt Ol")
        new_username = st.text_input("Kullanıcı Adı", key="register_username")
        new_password = st.text_input("Şifre", type="password", key="register_password")
        full_name = st.text_input("Ad Soyad")
        age = st.number_input("Yaş", min_value=15, max_value=80, value=25)
        weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=70)
        height = st.number_input("Boy (cm)", min_value=140, max_value=220, value=170)
        
        if st.button("Kayıt Ol"):
            if new_username and new_password and full_name:
                # Kullanıcı var mı kontrol et
                if db.users.find_one({"username": new_username}):
                    st.error("Bu kullanıcı adı zaten kullanılıyor!")
                else:
                    # Yeni kullanıcı oluştur
                    user_data = {
                        "username": new_username,
                        "password": hash_password(new_password),
                        "full_name": full_name,
                        "age": age,
                        "weight": weight,
                        "height": height,
                        "created_at": datetime.now(),
                        "program_week": 1
                    }
                    result = db.users.insert_one(user_data)
                    st.session_state.user_id = str(result.inserted_id)
                    st.success("Kayıt başarılı! Hoş geldiniz!")
                    st.rerun()
            else:
                st.error("Lütfen tüm alanları doldurun!")
    
    return False, None

# AI Koç
def ai_coach_response(user_message, user_data=None):
    client = init_groq()
    
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
        return f"Ups! Şu an biraz yorgunum 😅 Tekrar dener misin? Hata: {str(e)}"

# Ana uygulama
def main():
    st.set_page_config(
        page_title="Chym - AI Fitness Koçu",
        page_icon="💪",
        layout="wide"
    )
    
    st.title("💪 Chym - AI Fitness Koçu")
    st.markdown("*Kişiselleştirilmiş fitness programın ve AI koçun burada!*")
    
    # Kullanıcı giriş kontrolü
    is_logged_in, user_id = user_auth()
    
    if not is_logged_in:
        st.info("Lütfen giriş yapın veya kayıt olun.")
        return
    
    # MongoDB ve kullanıcı bilgilerini al
    db = init_mongodb()
    if not db:
        st.error("Veritabanı bağlantısı kurulamadı!")
        return
    
    user_data = db.users.find_one({"_id": pymongo.ObjectId(user_id)})
    
    # Çıkış butonu
    if st.button("Çıkış Yap", key="logout"):
        st.session_state.user_id = None
        st.rerun()
    
    st.markdown(f"**Hoş geldin, {user_data['full_name']}!** 🎉")
    
    # Ana menü
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard", 
        "📋 Programım", 
        "📊 Takibim", 
        "🤖 AI Koç", 
        "⚙️ Ayarlar"
    ])
    
    with tab1:
        st.header("Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Program Haftası", f"{user_data.get('program_week', 1)}/12")
        
        with col2:
            st.metric("Kilo", f"{user_data.get('weight', 0)} kg")
        
        with col3:
            st.metric("Yaş", f"{user_data.get('age', 0)}")
        
        with col4:
            bmi = user_data.get('weight', 0) / ((user_data.get('height', 170) / 100) ** 2)
            st.metric("BMI", f"{bmi:.1f}")
        
        # Bugünün programı
        st.subheader("Bugünün Programı")
        program_week = user_data.get('program_week', 1)
        
        if program_week <= 2:
            st.success("**Hafta 1-2 Programı**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Sabah Antrenmanı (06:00)**")
                for exercise, sets in PERSONAL_PROGRAM["hafta_1_2"]["sabah"].items():
                    st.write(f"• {exercise}: {sets}")
            
            with col2:
                st.markdown("**Akşam Antrenmanı (18:00)**")
                for exercise, sets in PERSONAL_PROGRAM["hafta_1_2"]["aksam"].items():
                    st.write(f"• {exercise}: {sets}")
        
        elif program_week <= 6:
            st.success("**Hafta 3-6 Programı**")
            st.write("**Sabah:** " + PERSONAL_PROGRAM["hafta_3_6"]["sabah"])
            st.write("**Akşam:** " + PERSONAL_PROGRAM["hafta_3_6"]["aksam"])
        
        else:
            st.success("**Hafta 7-12 - İleri Seviye Programı**")
            for exercise in PERSONAL_PROGRAM["hafta_7_12"]["ileri_seviye"]:
                st.write(f"• {exercise}")
        
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
        new_week = st.selectbox("Program Haftası", range(1, 13), index=program_week-1)
        
        if new_week != program_week:
            db.users.update_one(
                {"_id": pymongo.ObjectId(user_id)},
                {"$set": {"program_week": new_week}}
            )
            st.success(f"Program haftası {new_week} olarak güncellendi!")
            st.rerun()
        
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
            workout_data = {
                "user_id": user_id,
                "type": workout_type,
                "date": workout_date,
                "duration": duration,
                "intensity": intensity,
                "notes": notes,
                "created_at": datetime.now()
            }
            db.workouts.insert_one(workout_data)
            st.success("Antrenman kaydedildi! 🎉")
        
        # Ağırlık takibi
        st.subheader("Ağırlık Takibi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_weight = st.number_input("Yeni Kilo (kg)", min_value=40.0, max_value=200.0, value=float(user_data.get('weight', 70)))
            weight_date = st.date_input("Tarih", datetime.now(), key="weight_date")
        
        if st.button("Ağırlık Kaydet"):
            weight_data = {
                "user_id": user_id,
                "weight": new_weight,
                "date": weight_date,
                "created_at": datetime.now()
            }
            db.weight_logs.insert_one(weight_data)
            
            # Kullanıcının mevcut kilosunu güncelle
            db.users.update_one(
                {"_id": pymongo.ObjectId(user_id)},
                {"$set": {"weight": new_weight}}
            )
            
            st.success("Ağırlık kaydedildi!")
        
        # Grafik görüntüleme
        st.subheader("İstatistikler")
        
        # Ağırlık grafiği
        weight_logs = list(db.weight_logs.find({"user_id": user_id}).sort("date", 1))
        
        if weight_logs:
            df_weight = pd.DataFrame(weight_logs)
            df_weight['date'] = pd.to_datetime(df_weight['date'])
            
            fig = px.line(df_weight, x='date', y='weight', 
                         title='Ağırlık Değişimi', 
                         labels={'weight': 'Kilo (kg)', 'date': 'Tarih'})
            st.plotly_chart(fig, use_container_width=True)
        
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
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}"):
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
            new_age = st.number_input("Yaş", min_value=15, max_value=80, value=user_data.get('age', 25))
            new_weight = st.number_input("Kilo (kg)", min_value=40, max_value=200, value=user_data.get('weight', 70))
        
        with col2:
            new_height = st.number_input("Boy (cm)", min_value=140, max_value=220, value=user_data.get('height', 170))
            new_program_week = st.selectbox("Program Haftası", range(1, 13), index=user_data.get('program_week', 1)-1)
        
        if st.button("Profil Güncelle"):
            update_data = {
                "full_name": new_name,
                "age": new_age,
                "weight": new_weight,
                "height": new_height,
                "program_week": new_program_week,
                "updated_at": datetime.now()
            }
            
            db.users.update_one(
                {"_id": pymongo.ObjectId(user_id)},
                {"$set": update_data}
            )
            
            st.success("Profil güncellendi!")
            st.rerun()
        
        # Veri silme
        st.subheader("Veri Yönetimi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Antrenman Verilerini Sil", type="secondary"):
                db.workouts.delete_many({"user_id": user_id})
                st.success("Antrenman verileri silindi!")
        
        with col2:
            if st.button("Ağırlık Verilerini Sil", type="secondary"):
                db.weight_logs.delete_many({"user_id": user_id})
                st.success("Ağırlık verileri silindi!")
        
        # Hesap silme
        st.subheader("Hesap Yönetimi")
        
        if st.button("Hesabı Sil", type="secondary"):
            # Tüm kullanıcı verilerini sil
            db.users.delete_one({"_id": pymongo.ObjectId(user_id)})
            db.workouts.delete_many({"user_id": user_id})
            db.weight_logs.delete_many({"user_id": user_id})
            
            st.session_state.user_id = None
            st.success("Hesap silindi!")
            st.rerun()

if __name__ == "__main__":
    main()
