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
import logging
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
import asyncio
import aiohttp
from dataclasses import dataclass, field
from enum import Enum
import os
from contextlib import contextmanager

# Geliştirilmiş Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chym_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enum Classes for Better Type Safety
class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    CORE = "core"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    FULL_BODY = "full_body"

class WorkoutType(Enum):
    MORNING = "sabah"
    EVENING = "aksam"

class NutritionType(Enum):
    HYDRATION = "hydration"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"
    MEAL = "meal"
    SNACK = "snack"
    PRE_SLEEP = "pre_sleep"
    WORKOUT = "workout"
    SLEEP = "sleep"

# Data Classes for Better Structure
@dataclass
class Exercise:
    name: str
    muscle_group: MuscleGroup
    difficulty: DifficultyLevel
    calories_per_rep: float = 0.0
    calories_per_second: float = 0.0
    description: str = ""
    progressions: List[str] = field(default_factory=list)
    
    def get_display_name(self) -> str:
        return self.name.replace('_', ' ').title()

@dataclass
class WorkoutSet:
    exercise: str
    sets: int
    reps: str
    notes: str = ""
    rest: str = "60sn"
    tempo: str = "2-0-2-0"

@dataclass
class NutritionItem:
    time: str
    item: str
    type: NutritionType
    calories: int = 0

# Configuration Class
class Config:
    # API Keys - Gerçek uygulamada environment variables kullanın
    GROQ_API_KEY: str = "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"
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    MONGODB_URI: str = "mongodb+srv://dyaloshwester:b9eoq3Hriw3ncm65@cluster0.x6sungc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    # UI Configuration
    PAGE_TITLE: str = "🏋️‍♂️ CHYM - Beast Mode Coach"
    PAGE_ICON: str = "🏋️‍♂️"
    THEME_COLOR: str = "#FF6B35"
    SECONDARY_COLOR: str = "#F7931E"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/chym',
        'Report a bug': "https://github.com/your-repo/chym/issues",
        'About': "# CHYM Fitness App\nKişisel AI Fitness Koçunuz!"
    }
)

# Geliştirilmiş ve Modernize Edilmiş CSS
def load_css():
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root Variables */
        :root {
            --primary-color: #FF6B35;
            --secondary-color: #F7931E;
            --accent-color: #667eea;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --dark-color: #343a40;
            --light-color: #f8f9fa;
            --border-radius: 12px;
            --border-radius-lg: 16px;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            --box-shadow-lg: 0 8px 32px rgba(0,0,0,0.15);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Global Styles */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main Container */
        .main-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            padding: 2.5rem 2rem;
            border-radius: var(--border-radius-lg);
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: var(--box-shadow-lg);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .main-header p {
            font-size: 1.1rem;
            opacity: 0.9;
            margin: 0;
        }
        
        /* Metric Cards */
        .metric-card {
            background: white;
            padding: 2rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            border: 1px solid rgba(0,0,0,0.05);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 4px;
            background: linear-gradient(180deg, var(--primary-color), var(--secondary-color));
        }
        
        .metric-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 1rem;
            color: var(--dark-color);
            opacity: 0.7;
            font-weight: 500;
        }
        
        /* Chat Messages */
        .chat-container {
            max-height: 600px;
            overflow-y: auto;
            padding: 1rem;
            background: var(--light-color);
            border-radius: var(--border-radius);
            margin: 1rem 0;
        }
        
        .chat-message {
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: var(--border-radius-lg);
            max-width: 80%;
            animation: slideIn 0.3s ease;
            position: relative;
        }
        
        @keyframes slideIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            margin-left: auto;
            margin-right: 0;
            box-shadow: 0 6px 20px rgba(255, 107, 53, 0.3);
        }
        
        .ai-message {
            background: white;
            color: var(--dark-color);
            margin-left: 0;
            margin-right: auto;
            box-shadow: var(--box-shadow);
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        /* Exercise Cards */
        .exercise-card {
            background: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            border: 1px solid rgba(0,0,0,0.08);
            margin: 1rem 0;
            transition: var(--transition);
            position: relative;
        }
        
        .exercise-card:hover {
            border-color: var(--primary-color);
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.15);
            transform: translateY(-4px);
        }
        
        .exercise-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 0.5rem;
        }
        
        .exercise-details {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        
        .exercise-detail {
            background: var(--light-color);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        /* Program Cards */
        .program-card {
            background: linear-gradient(135deg, var(--accent-color) 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: var(--border-radius-lg);
            margin: 1rem 0;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .program-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 10s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* Progress Bars */
        .progress-container {
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 24px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, var(--success-color), #20c997);
            height: 100%;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 10px;
            position: relative;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-success {
            background: linear-gradient(135deg, var(--success-color), #20c997);
            color: white;
        }
        
        .badge-warning {
            background: linear-gradient(135deg, var(--warning-color), #fd7e14);
            color: white;
        }
        
        .badge-danger {
            background: linear-gradient(135deg, var(--danger-color), #e74c3c);
            color: white;
        }
        
        /* Loading Animation */
        .loading-spinner {
            border: 4px solid rgba(255, 107, 53, 0.1);
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 2rem;
            }
            
            .chat-message {
                max-width: 90%;
            }
            
            .metric-card {
                padding: 1.5rem;
            }
            
            .exercise-details {
                flex-direction: column;
                gap: 0.5rem;
            }
        }
        
        /* Sidebar Styling */
        .css-1d391kg {
            background: linear-gradient(180deg, var(--primary-color), var(--secondary-color));
        }
        
        .css-1d391kg .css-1v0mbdj {
            color: white;
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--light-color);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary-color);
        }
        
        /* Stale Element Protection */
        .stale-element-protection {
            pointer-events: none;
            opacity: 0.6;
        }
        
        /* Success Messages */
        .success-message {
            background: linear-gradient(135deg, var(--success-color), #20c997);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        
        /* Error Messages */
        .error-message {
            background: linear-gradient(135deg, var(--danger-color), #e74c3c);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
        }
        
        /* Info Messages */
        .info-message {
            background: linear-gradient(135deg, var(--accent-color), #764ba2);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)

# Geliştirilmiş Exercise Data Structure
class ExerciseDatabase:
    def __init__(self):
        self.exercises = self._initialize_exercises()
        self.muscle_groups = self._initialize_muscle_groups()
        self.difficulty_levels = self._initialize_difficulty_levels()
    
    def _initialize_exercises(self) -> Dict[str, Exercise]:
        exercises_data = {
            'pike_push_up': Exercise(
                name='pike_push_up',
                muscle_group=MuscleGroup.SHOULDERS,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=0.8,
                description='Omuz kaslarını güçlendiren etkili handstand progression hareketi',
                progressions=['wall_handstand', 'handstand_push_up', 'freestanding_handstand']
            ),
            'diamond_push_up': Exercise(
                name='diamond_push_up',
                muscle_group=MuscleGroup.CHEST,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=0.9,
                description='Triceps ve iç göğüs kaslarını hedefleyen push-up varyasyonu',
                progressions=['archer_push_up', 'one_arm_push_up', 'maltese_push_up']
            ),
            'bulgarian_split_squat': Exercise(
                name='bulgarian_split_squat',
                muscle_group=MuscleGroup.LEGS,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=1.2,
                description='Unilateral bacak gücü ve denge geliştiren egzersiz',
                progressions=['jump_split_squat', 'weighted_bulgarian_split_squat', 'pistol_squat']
            ),
            'single_arm_push_up': Exercise(
                name='single_arm_push_up',
                muscle_group=MuscleGroup.CHEST,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_rep=2.0,
                description='En zorlu push-up varyasyonu - tek kol ile yapılan push-up',
                progressions=['maltese_push_up', 'planche_push_up']
            ),
            'archer_squat': Exercise(
                name='archer_squat',
                muscle_group=MuscleGroup.LEGS,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_rep=1.5,
                description='Tek bacak squat progressionu - lateral güç geliştirici',
                progressions=['pistol_squat', 'shrimp_squat', 'dragon_squat']
            ),
            'l_sit_hold': Exercise(
                name='l_sit_hold',
                muscle_group=MuscleGroup.CORE,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_second=0.2,
                description='Core gücü, hip flexor esnekliği ve denge geliştiren static hold',
                progressions=['v_sit', 'manna_hold', 'front_lever']
            ),
            'hollow_body_hold': Exercise(
                name='hollow_body_hold',
                muscle_group=MuscleGroup.CORE,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_second=0.15,
                description='Core stabilizasyonu ve anterior chain gücü',
                progressions=['hollow_body_rocks', 'dragon_flag', 'front_lever']
            ),
            'handstand_wall_walk': Exercise(
                name='handstand_wall_walk',
                muscle_group=MuscleGroup.SHOULDERS,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_rep=1.8,
                description='Handstand progression - omuz gücü ve propriosepsiyon',
                progressions=['freestanding_handstand', 'handstand_push_up', 'handstand_walk']
            ),
            'pistol_squat': Exercise(
                name='pistol_squat',
                muscle_group=MuscleGroup.LEGS,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_rep=2.2,
                description='Tek bacak squat - unilateral güç ve mobility',
                progressions=['jumping_pistol_squat', 'weighted_pistol_squat', 'shrimp_squat']
            ),
            'one_arm_plank': Exercise(
                name='one_arm_plank',
                muscle_group=MuscleGroup.CORE,
                difficulty=DifficultyLevel.ADVANCED,
                calories_per_second=0.25,
                description='Asimetrik core stabilizasyonu ve anti-rotation',
                progressions=['one_arm_one_leg_plank', 'side_plank_variations']
            ),
            'hindu_push_up': Exercise(
                name='hindu_push_up',
                muscle_group=MuscleGroup.CHEST,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=1.1,
                description='Flow movement - göğüs, omuz ve core kombine hareket',
                progressions=['dive_bomber_push_up', 'hindu_push_up_to_downward_dog']
            ),
            'burpee': Exercise(
                name='burpee',
                muscle_group=MuscleGroup.FULL_BODY,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=1.5,
                description='Tüm vücut kondisyon ve metabolik egzersiz',
                progressions=['burpee_box_jump', 'burpee_pull_up', 'burpee_tuck_jump']
            ),
            'push_up': Exercise(
                name='push_up',
                muscle_group=MuscleGroup.CHEST,
                difficulty=DifficultyLevel.BEGINNER,
                calories_per_rep=0.7,
                description='Temel üst vücut güç egzersizi',
                progressions=['incline_push_up', 'diamond_push_up', 'archer_push_up']
            ),
            'pull_up': Exercise(
                name='pull_up',
                muscle_group=MuscleGroup.BACK,
                difficulty=DifficultyLevel.INTERMEDIATE,
                calories_per_rep=1.3,
                description='Sırt kasları ve biceps geliştiren temel çekme hareketi',
                progressions=['weighted_pull_up', 'one_arm_pull_up', 'muscle_up']
            ),
            'squat': Exercise(
                name='squat',
                muscle_group=MuscleGroup.LEGS,
                difficulty=DifficultyLevel.BEGINNER,
                calories_per_rep=0.8,
                description='Temel bacak egzersizi - quadriceps, glutes ve hamstrings',
                progressions=['jump_squat', 'pistol_squat', 'shrimp_squat']
            ),
            'plank': Exercise(
                name='plank',
                muscle_group=MuscleGroup.CORE,
                difficulty=DifficultyLevel.BEGINNER,
                calories_per_second=0.1,
                description='Core stabilizasyonu ve postural strength',
                progressions=['side_plank', 'plank_to_push_up', 'one_arm_plank']
            )
        }
        return exercises_data
    
    def _initialize_muscle_groups(self) -> Dict[MuscleGroup, Dict[str, str]]:
        return {
            MuscleGroup.CHEST: {'emoji': '🫴', 'name': 'Göğüs', 'color': '#FF6B35'},
            MuscleGroup.BACK: {'emoji': '🔙', 'name': 'Sırt', 'color': '#36A2EB'},
            MuscleGroup.LEGS: {'emoji': '🦵', 'name': 'Bacak', 'color': '#4BC0C0'},
            MuscleGroup.CORE: {'emoji': '💪', 'name': 'Core', 'color': '#FFCE56'},
            MuscleGroup.SHOULDERS: {'emoji': '🤲', 'name': 'Omuz', 'color': '#9966FF'},
            MuscleGroup.ARMS: {'emoji': '💪', 'name': 'Kol', 'color': '#FF9F40'},
            MuscleGroup.FULL_BODY: {'emoji': '🎯', 'name': 'Tüm Vücut', 'color': '#FF6384'}
        }
    
    def _initialize_difficulty_levels(self) -> Dict[DifficultyLevel, Dict[str, Any]]:
        return {
            DifficultyLevel.BEGINNER: {'level': 1, 'color': '#28a745', 'emoji': '🟢', 'name': 'Başlangıç'},
            DifficultyLevel.INTERMEDIATE: {'level': 2, 'color': '#ffc107', 'emoji': '🟡', 'name': 'Orta'},
            DifficultyLevel.ADVANCED: {'level': 3, 'color': '#dc3545', 'emoji': '🔴', 'name': 'İleri'}
        }
    
    def get_exercise(self, exercise_name: str) -> Optional[Exercise]:
        return self.exercises.get(exercise_name.lower().replace(' ', '_').replace('-', '_'))
    
    def get_exercises_by_muscle_group(self, muscle_group: MuscleGroup) -> List[Exercise]:
        return [ex for ex in self.exercises.values() if ex.muscle_group == muscle_group]
    
    def get_exercises_by_difficulty(self, difficulty: DifficultyLevel) -> List[Exercise]:
        return [ex for ex in self.exercises.values() if ex.difficulty == difficulty]
    
    def search_exercises(self, query: str) -> List[Exercise]:
        query = query.lower()
        return [ex for ex in self.exercises.values() 
                if query in ex.name.lower() or query in ex.description.lower()]

# Geliştirilmiş Workout Program Structure
class WorkoutProgram:
    def __init__(self):
        self.program_data = self._initialize_program_data()
    
    def _initialize_program_data(self) -> Dict[str, Dict[str, List[WorkoutSet]]]:
        return {
            'hafta_1_2': {
                'sabah': [
                    WorkoutSet('pike_push_up', 5, '8-12', '3sn negatif', '60-90sn', '3-0-1-0'),
                    WorkoutSet('diamond_push_up', 5, '6-10', '2sn pause', '60-90sn', '2-2-1-0'),
                    WorkoutSet('bulgarian_split_squat', 5, '15/15', 'tempo: 3-1-2-1', '90sn', '3-1-2-1'),
                    WorkoutSet('single_arm_push_up', 4, '5/5', 'duvar destekli', '120sn', '2-0-2-0'),
                    WorkoutSet('archer_squat', 4, '8/8', 'kontrollü hareket', '90sn', '3-1-2-1'),
                    WorkoutSet('l_sit_hold', 5, '15-30sn', 'progression odaklı', '90sn', 'static'),
                    WorkoutSet('hollow_body_hold', 3, '45-60sn', 'nefes kontrol', '60sn', 'static'),
                    WorkoutSet('handstand_wall_walk', 4, '5 adım', 'omuz mobility', '120sn', 'controlled')
                ],
                'aksam': [
                    WorkoutSet('pistol_squat', 4, '5/5', 'progression', '120sn', '3-1-2-1'),
                    WorkoutSet('one_arm_plank', 3, '20sn/taraf', 'core activation', '90sn', 'static'),
                    WorkoutSet('hindu_push_up', 3, '12-15', 'flow movement', '60sn', 'smooth'),
                    WorkoutSet('burpee', 3, '10', 'to tuck jump', '90sn', 'explosive')
                ]
            },
    'hafta_3_4': {
        'sabah': [
            {
                'exercise': 'pike push-up', 
                'sets': 6, 
                'reps': '10-15', 
                'notes': '4sn negatif',
                'rest': '60-90sn',
                'tempo': '4-0-1-0'
            },
            {
                'exercise': 'diamond push-up', 
                'sets': 6, 
                'reps': '8-12', 
                'notes': '3sn pause',
                'rest': '60-90sn',
                'tempo': '3-3-1-0'
            },
            {
                'exercise': 'bulgarian split squat', 
                'sets': 6, 
                'reps': '18/18', 
                'notes': 'ağırlık ekle',
                'rest': '90sn',
                'tempo': '3-1-2-1'
            }
        ]
    }
}

# Geliştirilmiş Beslenme Planı
NUTRITION_PLAN = {
    'schedule': {
        '05:30': {'item': '500ml su', 'type': 'hydration', 'calories': 0},
        '06:00': {'item': '1 muz + kahve', 'type': 'pre_workout', 'calories': 120},
        '06:15-07:00': {'item': 'Sabah antrenmanı', 'type': 'workout', 'calories': -300},
        '07:15': {'item': 'Protein shake + bal', 'type': 'post_workout', 'calories': 200},
        '08:00': {'item': 'Kahvaltı', 'type': 'meal', 'calories': 500},
        '11:00': {'item': 'Ara öğün', 'type': 'snack', 'calories': 200},
        '13:30': {'item': 'Öğle yemeği', 'type': 'meal', 'calories': 600},
        '16:00': {'item': 'Pre-workout atıştırmalık', 'type': 'pre_workout', 'calories': 150},
        '17:30-18:30': {'item': 'Akşam antrenmanı', 'type': 'workout', 'calories': -400},
        '18:45': {'item': 'Süt + muz', 'type': 'post_workout', 'calories': 180},
        '20:00': {'item': 'Akşam yemeği', 'type': 'meal', 'calories': 700},
        '22:00': {'item': 'Casein + kuruyemiş', 'type': 'pre_sleep', 'calories': 250},
        '22:30': {'item': 'Yatma', 'type': 'sleep', 'calories': 0}
    },
    'meal_suggestions': {
        'kahvalti': [
            'Yumurta + avokado + tam tahıl ekmek',
            'Protein pancake + meyve',
            'Overnight oats + protein tozu',
            'Menemen + peynir + domates'
        ],
        'ara_ogun': [
            'Yunan yoğurtu + nuts',
            'Protein bar + meyve',
            'Kuruyemiş karışımı',
            'Süt + hurma'
        ],
        'ogle': [
            'Tavuk + quinoa + sebze',
            'Somon + tatlı patates + salata',
            'Köfte + bulgur + yogurt',
            'Ton balığı + avokado toast'
        ],
        'aksam': [
            'Biftek + patates + brokoli',
            'Tavuk + pirinç + sebze',
            'Balık + quinoa + ıspanak',
            'Köri + nohut + pirinç'
        ]
    }
}

# Geliştirilmiş Supplement Planı
SUPPLEMENTS = [
    {
        'name': 'Whey Protein', 
        'dosage': '30g (2x)', 
        'timing': 'Post-workout & Evening',
        'benefits': 'Kas protein sentezi',
        'priority': 'high'
    },
    {
        'name': 'Kreatin Monohydrate', 
        'dosage': '5g (18+ yaş)', 
        'timing': 'Her zaman',
        'benefits': 'Güç ve performans',
        'priority': 'high'
    },
    {
        'name': 'Multivitamin', 
        'dosage': '1 tablet', 
        'timing': 'Sabah',
        'benefits': 'Genel sağlık',
        'priority': 'medium'
    },
    {
        'name': 'Omega-3', 
        'dosage': '2-3g', 
        'timing': 'Yemekle',
        'benefits': 'İnflamasyon kontrolü',
        'priority': 'high'
    },
    {
        'name': 'Magnezyum', 
        'dosage': '400mg', 
        'timing': 'Akşam',
        'benefits': 'Kas gevşemesi, uyku',
        'priority': 'medium'
    },
    {
        'name': 'Çinko', 
        'dosage': '15mg', 
        'timing': 'Aç karnına',
        'benefits': 'Bağışıklık, testosteron',
        'priority': 'medium'
    },
    {
        'name': 'D3 Vitamini', 
        'dosage': '2000 IU', 
        'timing': 'Sabah',
        'benefits': 'Kemik sağlığı, hormonlar',
        'priority': 'high'
    }
]

# Geliştirilmiş Utility Functions
def hash_password(password: str) -> str:
    """Güvenli şifre hash'leme"""
    salt = "beast_mode_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Şifre doğrulama"""
    return hash_password(password) == hashed_password

def calculate_beast_score(user_data: Dict, recent_workouts: List = None) -> int:
    """Beast Mode skoru hesapla"""
    base_score = 50
    
    # Yaş faktörü
    age = user_data.get('age', 25)
    if age < 25:
        base_score += 10
    elif age > 35:
        base_score -= 5
    
    # Antrenman sıklığı
    if recent_workouts:
        workout_count = len(recent_workouts)
        base_score += min(workout_count * 5, 25)
    
    # Hedef faktörü
    goal = user_data.get('goal', 'general')
    if goal == 'muscle_gain':
        base_score += 5
    elif goal == 'strength':
        base_score += 10
    
    return min(max(base_score, 0), 100)

def format_exercise_name(exercise: str) -> str:
    """Egzersiz adını formatla"""
    return exercise.replace('_', ' ').replace('-', ' ').title()

def get_exercise_emoji(exercise: str) -> str:
    """Egzersiz için emoji getir"""
    muscle_group = BEAST_MODE_DATA['exercises'].get(exercise, {}).get('muscle_group', 'full_body')
    return BEAST_MODE_DATA['muscle_groups'].get(muscle_group, {}).get('emoji', '💪')

def calculate_workout_calories(exercises: List[Dict]) -> float:
    """Antrenman kalori hesapla"""
    total_calories = 0
    for ex in exercises:
        exercise_name = ex.get('exercise', '')
        sets = ex.get('sets', 1)
        reps = ex.get('reps', 10)
        
        # Reps string olabilir ("8-12" gibi)
        if isinstance(reps, str):
            reps = int(reps.split('-')[0]) if '-' in reps else 10
        
        exercise_data = BEAST_MODE_DATA['exercises'].get(exercise_name, {})
        calories_per_rep = exercise_data.get('calories_per_rep', 0.5)
        
        total_calories += sets * reps * calories_per_rep
    
    return round(total_calories, 1)

# Geliştirilmiş MongoDB İşlemleri
@st.cache_resource
def init_mongodb():
    """MongoDB bağlantısını başlat"""
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=10,
            retryWrites=True
        )
        
        # Ping test
        client.admin.command('ping')
        logger.info("MongoDB Atlas bağlantısı başarılı")
        
        db = client['beast_mode']
        setup_collections(db)
        
        return db
        
    except Exception as e:
        logger.error(f"MongoDB bağlantı hatası: {str(e)}")
        st.error(f"❌ MongoDB bağlantı hatası: {str(e)}")
        return None

def setup_collections(db):
    """MongoDB koleksiyonlarını ve index'lerini ayarla"""
    try:
        collections_config = {
            'users': [
                ('username', 1, {'unique': True}),
                ('email', 1, {'unique': True, 'sparse': True}),
                ('created_at', -1)
            ],
            'chats': [
                ('user_id', 1),
                ('timestamp', -1),
                (['user_id', 'session_id'], 1)
            ],
            'workouts': [
                ('user_id', 1),
                ('date', -1),
                (['user_id', 'date'], 1)
            ],
            'progress': [
                ('user_id', 1),
                ('date', -1),
                (['user_id', 'date'], 1, {'unique': True})
            ]
        }
        
        for collection_name, indexes in collections_config.items():
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
            
            collection = db[collection_name]
            
            for index_config in indexes:
                try:
                    if len(index_config) == 2:
                        field, direction = index_config
                        collection.create_index([(field, direction)])
                    elif len(index_config) == 3:
                        field, direction, options = index_config
                        if isinstance(field, list):
                            collection.create_index([(f, direction) for f in field], **options)
                        else:
                            collection.create_index([(field, direction)], **options)
                except pymongo.errors.DuplicateKeyError:
                    pass  # Index zaten mevcut
                except Exception as e:
                    logger.warning(f"Index oluşturma hatası: {e}")
        
        logger.info("MongoDB koleksiyonları hazırlandı")
        
    except Exception as e:
        logger.error(f"Koleksiyon ayarlama hatası: {e}")

# Geliştirilmiş Session State
def init_session_state():
    """Session state'i başlat"""
    default_values = {
        'authenticated': False,
        'current_user': None,
        'chat_history': [],
        'exercise_log': [],
        'beast_mode_score': 75,
        'db': None,
        'chat_session_id': None,
        'loading': False,
        'last_workout_date': None,
        'weekly_stats': {},
        'notification_settings': {
            'workout_reminder': True,
            'meal_reminder': True,
            'progress_update': True
        }
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # MongoDB bağlantısını başlat
    if st.session_state.db is None:
        st.session_state.db = init_mongodb()
    
    # Chat session ID oluştur
    if st.session_state.chat_session_id is None:
        st.session_state.chat_session_id = str(uuid.uuid4())

# Geliştirilmiş Kullanıcı İşlemleri
def save_user_to_db(user_data: Dict) -> bool:
    """Kullanıcıyı veritabanına kaydet"""
    if not st.session_state.db:
        return False
    
    try:
        # Şifreyi hash'le
        user_data['password'] = hash_password(user_data['password'])
        user_data['created_at'] = datetime.now()
        user_data['updated_at'] = datetime.now()
        user_data['beast_mode_score'] = calculate_beast_score(user_data)
        user_data['total_workouts'] = 0
        user_data['streak_days'] = 0
        user_data['last_login'] = datetime.now()
        
        result = st.session_state.db.users.insert_one(user_data)
        
        if result.inserted_id:
            logger.info(f"Yeni kullanıcı kaydedildi: {user_data['username']}")
            return True
            
        return False
        
    except pymongo.errors.DuplicateKeyError:
        st.error("❌ Bu kullanıcı adı veya email zaten kullanılıyor!")
        return False
    except Exception as e:
        logger.error(f"Kullanıcı kayıt hatası: {e}")
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
            'model': 'gemma2-9b-it',  # Daha hızlı ve yeterli model adı
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"{message}\n{conversation_context}"}
            ],
            'temperature': 0.8,         # Daha tutarlı ve hızlı
            'max_tokens': 500           # Kısa ve hızlı yanıtlar için
        }

        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=7)
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

# Fallback Response
def get_fallback_response(message_type):
    """API hatası durumunda fallback yanıt"""
    fallback_responses = {
        'exercise': "💪 Harika bir antrenman! Devam et, seni gururla izliyorum!",
        'nutrition': "🍎 Beslenme konusunda harika gidiyorsun! Sağlıklı seçimler yapıyorsun.",
        'motivation': "🦁 Sen bir BEAST'sin! Her adım seni hedefine yaklaştırıyor!",
        'progress': "📈 İlerleme süreci harika! Sabırlı ol, sonuçlar gelecek!",
        'general': "🤖 Şu an yanıt veremiyorum ama seni desteklemeye devam ediyorum!"
    }
    return fallback_responses.get(message_type, fallback_responses['general'])

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
            # Session'u temizle
            for key in list(st.session_state.keys()):
                if key not in ['db']:  # DB bağlantısını koru
                    del st.session_state[key]
            init_session_state()
            st.rerun()
    
    st.divider()
    
    # Tabs
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

# Dashboard Tab - Optimize edilmiş
def dashboard_tab():
    col1, col2, col3, col4 = st.columns(4)
    
    # Güvenli metrikler
    total_workouts = len(st.session_state.exercise_log) if st.session_state.exercise_log else 0
    
    with col1:
        st.metric("Beast Mode", f"{st.session_state.beast_mode_score}%", "🔥")
    
    with col2:
        st.metric("Toplam Antrenman", total_workouts, "💪")
    
    with col3:
        try:
            user_created = st.session_state.current_user.get('created_at', datetime.now())
            if isinstance(user_created, str):
                user_created = datetime.now()
            weeks_passed = max(1, (datetime.now() - user_created).days // 7)
            st.metric("Program Haftası", f"{min(weeks_passed, 24)}/24", "📅")
        except:
            st.metric("Program Haftası", "1/24", "📅")
    
    with col4:
        today_exercises = 0
        if st.session_state.exercise_log:
            today_exercises = len([ex for ex in st.session_state.exercise_log 
                                  if ex.get('date', datetime.now()).date() == datetime.now().date()])
        st.metric("Bugün Yapılan", today_exercises, "🎯")
    
    st.divider()
    
    # Haftalık ilerleme grafiği
    st.subheader("📈 Haftalık İlerleme")
    
    # Güvenli veri oluşturma
    try:
        progress_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            exercises_count = 0
            if st.session_state.exercise_log:
                exercises_count = len([ex for ex in st.session_state.exercise_log 
                                      if ex.get('date', datetime.now()).date() == date.date()])
            progress_data.append({
                'Tarih': date.strftime('%d/%m'),
                'Egzersiz': exercises_count,
                'Beast Mode': min(100, max(0, st.session_state.beast_mode_score - (6-i) * 2))
            })
        
        df = pd.DataFrame(progress_data)
        
        if not df.empty:
            fig = px.line(df, x='Tarih', y=['Egzersiz', 'Beast Mode'], 
                         title="Son 7 Günlük İlerleme")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning("Grafik yüklenemedi. Veri biriktikçe görünecek.")
    
    # Son aktiviteler
    st.subheader("🔥 Son Aktiviteler")
    
    if st.session_state.exercise_log:
        recent_exercises = st.session_state.exercise_log[-5:]
        for exercise in reversed(recent_exercises):
            exercise_name = exercise.get('exercise', 'Bilinmeyen').replace('_', ' ').title()
            exercise_date = exercise.get('date', datetime.now())
            if isinstance(exercise_date, str):
                exercise_date = datetime.now()
            
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{exercise_name}</strong> - 
                {exercise.get('sets', 0)} set × {exercise.get('reps', 0)} tekrar
                <br><small>{exercise_date.strftime('%d/%m/%Y %H:%M')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz egzersiz kaydı yok. Koç ile konuşarak başla! 💪")

# Coach Tab - Optimize edilmiş
def coach_tab():
    st.subheader("🤖 Beast Mode Koçun")
    st.write("AI koçun ile konuş, antrenman kaydet ve motivasyon al!")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Chat geçmişini güvenli şekilde göster
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history[-10:]:  # Son 10 mesaj
                user_msg = chat.get('message', '')
                ai_msg = chat.get('response', '')
                
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>Sen:</strong> {user_msg}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>🦁 Koç:</strong> {ai_msg}
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
            try:
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
                if analysis.get('exercise_data'):
                    exercise_data = analysis['exercise_data']
                    exercise_data['date'] = datetime.now()
                    st.session_state.exercise_log.append(exercise_data)
                    
                    # Beast Mode skoru güncelle
                    st.session_state.beast_mode_score = min(100, 
                        st.session_state.beast_mode_score + 2)
                
                # MongoDB'ye kaydet
                try:
                    if st.session_state.db and st.session_state.current_user:
                        save_chat_to_db(
                            st.session_state.current_user['_id'], 
                            user_message, 
                            ai_response, 
                            analysis['type']
                        )
                except Exception as db_error:
                    pass  # DB hatası sessiz geçsin
                
                st.rerun()
            except Exception as e:
                st.error(f"Mesaj gönderme hatası: {str(e)}")
    
    # Hızlı eylemler
    st.subheader("⚡ Hızlı Eylemler")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💪 Bugünün Programını Tamamladım", use_container_width=True):
            response = "🔥 Harika iş çıkardın! Beast Mode'un yükseliyor. Dinlenme ve beslenmeyi ihmal etme. Yarın daha güçlü olacaksın! 💪"
            st.session_state.chat_history.append({
                'message': "Bugünün programını tamamladım!",
                'response': response,
                'timestamp': datetime.now(),
                'type': 'achievement'
            })
            st.session_state.beast_mode_score = min(100, st.session_state.beast_mode_score + 5)
            st.rerun()
    
    with col2:
        if st.button("😴 Yorgun Hissediyorum", use_container_width=True):
            response = "💤 Dinlenme de antrenmanın bir parçası! Bugün hafif yapabilir veya dinlenebilirsin. Vücudunu dinle, zorlamaya gerek yok. Yarın daha fresh olacaksın! 🌟"
            st.session_state.chat_history.append({
                'message': "Çok yorgun hissediyorum",
                'response': response,
                'timestamp': datetime.now(),
                'type': 'support'
            })
            st.rerun()
    
    with col3:
        if st.button("🎯 Motivasyona İhtiyacım Var", use_container_width=True):
            response = "🦁 Sen bir BEAST'sin! Her tekrar seni hedefine yaklaştırıyor. 6 ay sonraki haline bir düşün - o güçlü, kendinden emin versiyonun seni bekliyor! Şimdi kalk ve bir hareket yap! 🔥💪"
            st.session_state.chat_history.append({
                'message': "Motivasyona ihtiyacım var",
                'response': response,
                'timestamp': datetime.now(),
                'type': 'motivation'
            })
            st.rerun()

# Program Tab - Optimize edilmiş
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
            exercise_name = exercise['exercise'].replace('_', ' ').replace('-', ' ').title()
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{i}. {exercise_name}</strong><br>
                <span style="color: #FF6B35;">{exercise['sets']} set × {exercise['reps']} tekrar</span><br>
                <small>{exercise['notes']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🌆 Akşam Antrenmanı (18:00)")
        for i, exercise in enumerate(DAILY_PROGRAM['hafta_1_2']['aksam'], 1):
            exercise_name = exercise['exercise'].replace('_', ' ').replace('-', ' ').title()
            st.markdown(f"""
            <div class="exercise-card">
                <strong>{i}. {exercise_name}</strong><br>
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

# Beslenme Tab - Optimize edilmiş
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

# Takviyeler Tab - Optimize edilmiş
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

# Progress Tab - Optimize edilmiş
def progress_tab():
    st.subheader("📈 İlerleme Takibi")
    
    # Güvenli istatistikler
    total_workouts = len(st.session_state.exercise_log) if st.session_state.exercise_log else 0
    total_sets = sum(ex.get('sets', 0) for ex in st.session_state.exercise_log) if st.session_state.exercise_log else 0
    total_reps = sum(ex.get('reps', 0) * ex.get('sets', 0) for ex in st.session_state.exercise_log) if st.session_state.exercise_log else 0
    
    # Genel istatistikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Antrenman", total_workouts, "💪")
    with col2:
        st.metric("Toplam Set", total_sets, "🔥")
    with col3:
        st.metric("Toplam Tekrar", total_reps, "⚡")
    with col4:
        streak_days = 7  # Örnek değer
        st.metric("Seri (Gün)", streak_days, "🏆")
    
    st.divider()
    
    # Kas gruplarına göre dağılım
    if st.session_state.exercise_log:
        st.subheader("🎯 Kas Grupları Dağılımı")
        
        try:
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
        except Exception as e:
            st.warning("Kas grupları grafiği yüklenemedi.")
    
    # Günlük aktivite takvimi
    st.subheader("📅 Aktivite Takvimi")
    
    try:
        # Son 21 günlük aktivite (3 hafta)
        activity_calendar = {}
        for i in range(21):
            date = datetime.now() - timedelta(days=20-i)
            date_str = date.strftime('%Y-%m-%d')
            
            daily_exercises = 0
            if st.session_state.exercise_log:
                daily_exercises = len([ex for ex in st.session_state.exercise_log 
                                      if ex.get('date', datetime.now()).date() == date.date()])
            
            activity_calendar[date_str] = daily_exercises
        
        # Heatmap benzeri görsel
        cols = st.columns(7)
        
        for i, (date_str, count) in enumerate(activity_calendar.items()):
            col_index = i % 7
            
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
    except Exception as e:
        st.warning("Aktivite takvimi yüklenemedi.")
    
    # Hedefler
    st.subheader("🎯 Hedefler ve Başarılar")
    
    goals = [
        {"name": "İlk 30 Antrenman", "current": total_workouts, "target": 30, "icon": "🏃"},
        {"name": "1000 Push-up", "current": min(1000, total_reps), "target": 1000, "icon": "💪"},
        {"name": "500 Squat", "current": min(500, total_reps // 2), "target": 500, "icon": "🦵"},
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
    try:
        init_session_state()
        
        # MongoDB koleksiyonlarını ayarla
        if st.session_state.db:
            setup_collections(st.session_state.db)
        
        if not st.session_state.authenticated:
            login_page()
        else:
            main_app()
    except Exception as e:
        st.error(f"Uygulama hatası: {str(e)}")
        st.info("Sayfa yenileniyor...")
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()
