import React, { useState, useEffect } from 'react';
import { User, MessageCircle, BarChart3, Target, Calendar, LogOut, Eye, EyeOff, Plus, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';

const BeastModeFitnessApp = () => {
  // Embedded API Key
  const GROQ_API_KEY = "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";
  
  // State Management
  const [currentUser, setCurrentUser] = useState(null);
  const [showLogin, setShowLogin] = useState(true);
  const [isRegistering, setIsRegistering] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Form States
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ 
    name: '', username: '', password: '', weight: 70, age: 25, goal: 'muscle_gain' 
  });
  
  // Chat and Exercise States
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [exerciseLog, setExerciseLog] = useState([]);
  const [beastModeScore, setBeastModeScore] = useState(75);

  // Mock Database (In production, this would be MongoDB)
  const [users, setUsers] = useState([
    {
      id: 1,
      name: 'Han',
      username: 'han123',
      password: '123456',
      weight: 75,
      age: 25,
      goal: 'muscle_gain',
      joinDate: new Date('2024-01-15'),
      exerciseHistory: [
        { date: '2024-07-01', exercise: 'Push-up', sets: 4, reps: 15, muscleGroup: 'chest' },
        { date: '2024-07-01', exercise: 'Squat', sets: 3, reps: 20, muscleGroup: 'legs' },
        { date: '2024-06-30', exercise: 'Pull-up', sets: 3, reps: 8, muscleGroup: 'back' }
      ],
      chatHistory: [
        { date: '2024-07-02', message: 'Bugün çok yorgunum', response: 'Dinlenme de antrenmanın bir parçası Han! Bugün hafif bir yürüyüş yap.', type: 'general' }
      ]
    }
  ]);

  // Beast Mode Data
  const beastModeData = {
    exercises: {
      'push-up': { muscleGroup: 'chest', difficulty: 'beginner' },
      'pull-up': { muscleGroup: 'back', difficulty: 'intermediate' },
      'squat': { muscleGroup: 'legs', difficulty: 'beginner' },
      'plank': { muscleGroup: 'core', difficulty: 'beginner' },
      'burpee': { muscleGroup: 'full_body', difficulty: 'advanced' },
      'diamond push-up': { muscleGroup: 'chest', difficulty: 'intermediate' },
      'pistol squat': { muscleGroup: 'legs', difficulty: 'advanced' },
      'handstand': { muscleGroup: 'shoulders', difficulty: 'advanced' }
    },
    muscleGroups: {
      chest: '🫴 Göğüs',
      back: '🔙 Sırt', 
      legs: '🦵 Bacak',
      core: '💪 Core',
      shoulders: '🤲 Omuz',
      arms: '💪 Kol',
      full_body: '🎯 Tüm Vücut'
    }
  };

  // Analyze message type and extract exercise data
  const analyzeMessage = (message) => {
    const exerciseKeywords = ['antrenman', 'egzersiz', 'set', 'tekrar', 'squat', 'push-up', 'pull-up', 'plank', 'burpee'];
    const generalKeywords = ['yorgun', 'motivasyon', 'nasılım', 'hissediyorum', 'uyku', 'beslenme'];
    
    const messageLower = message.toLowerCase();
    const exerciseCount = exerciseKeywords.filter(keyword => messageLower.includes(keyword)).length;
    const generalCount = generalKeywords.filter(keyword => messageLower.includes(keyword)).length;
    
    // Extract exercise data if it's an exercise message
    let exerciseData = null;
    if (exerciseCount > generalCount) {
      const exercises = Object.keys(beastModeData.exercises);
      const foundExercise = exercises.find(ex => messageLower.includes(ex.toLowerCase()));
      
      if (foundExercise) {
        const setMatch = messageLower.match(/(\d+)\s*set/);
        const repMatch = messageLower.match(/(\d+)\s*tekrar/);
        
        exerciseData = {
          exercise: foundExercise,
          sets: setMatch ? parseInt(setMatch[1]) : 3,
          reps: repMatch ? parseInt(repMatch[1]) : 10,
          muscleGroup: beastModeData.exercises[foundExercise].muscleGroup
        };
      }
    }
    
    return {
      type: exerciseCount > generalCount ? 'exercise' : 'general',
      exerciseData
    };
  };

  // Call Groq API for AI coaching
  const callGroqAPI = async (message, messageType, userData) => {
    try {
      const systemPrompt = messageType === 'exercise' 
        ? `Sen profesyonel bir fitness koçusun. Kullanıcı egzersiz bilgisi paylaştı: "${message}". 
           Kullanıcı bilgileri: İsim: ${userData.name}, Kilo: ${userData.weight}kg, Yaş: ${userData.age}, Hedef: ${userData.goal}.
           Motive edici, kısa (max 100 kelime) Türkçe yanıt ver. Egzersiz hakkında teknik tavsiye ver.`
        : `Sen profesyonel bir fitness koçusun. Kullanıcı genel bir mesaj yazdı: "${message}".
           Kullanıcı bilgileri: İsim: ${userData.name}, Beast Mode Skoru: %${beastModeScore}.
           Destekleyici, motive edici, kısa (max 80 kelime) Türkçe yanıt ver. Soru sor ve tavsiye ver.`;

      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${GROQ_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'llama-3.3-70b-versatile',
          messages: [{ role: 'system', content: systemPrompt }],
          temperature: 0.7,
          max_tokens: 300
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.choices[0].message.content.trim();
      } else {
        return `❌ API Hatası (${response.status}). Tekrar deneyin.`;
      }
    } catch (error) {
      return `❌ Bağlantı hatası: ${error.message}`;
    }
  };

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const user = users.find(u => u.username === loginForm.username && u.password === loginForm.password);
    
    if (user) {
      setCurrentUser(user);
      setShowLogin(false);
      setChatHistory(user.chatHistory || []);
      setExerciseLog(user.exerciseHistory || []);
    } else {
      alert('❌ Kullanıcı adı veya şifre hatalı!');
    }
    
    setLoading(false);
  };

  // Handle Registration
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const newUser = {
      id: users.length + 1,
      ...registerForm,
      joinDate: new Date(),
      exerciseHistory: [],
      chatHistory: []
    };
    
    setUsers([...users, newUser]);
    setCurrentUser(newUser);
    setShowLogin(false);
    setLoading(false);
  };

  // Handle Chat Message
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    
    setLoading(true);
    
    const analysis = analyzeMessage(chatMessage);
    const aiResponse = await callGroqAPI(chatMessage, analysis.type, currentUser);
    
    const newChatEntry = {
      id: Date.now(),
      date: new Date().toISOString(),
      message: chatMessage,
      response: aiResponse,
      type: analysis.type
    };
    
    setChatHistory(prev => [...prev, newChatEntry]);
    
    // If it's an exercise, add to exercise log
    if (analysis.exerciseData) {
      const newExercise = {
        id: Date.now(),
        date: new Date().toISOString().split('T')[0],
        ...analysis.exerciseData
      };
      setExerciseLog(prev => [...prev, newExercise]);
      
      // Update Beast Mode Score
      setBeastModeScore(prev => Math.min(100, prev + 2));
    }
    
    setChatMessage('');
    setLoading(false);
  };

  // Calculate muscle group distribution
  const getMuscleGroupData = () => {
    const groups = {};
    exerciseLog.forEach(exercise => {
      const group = exercise.muscleGroup;
      groups[group] = (groups[group] || 0) + (exercise.sets * exercise.reps);
    });
    
    return Object.entries(groups).map(([group, volume]) => ({
      name: beastModeData.muscleGroups[group] || group,
      value: volume,
      color: getColorForMuscleGroup(group)
    }));
  };

  const getColorForMuscleGroup = (group) => {
    const colors = {
      chest: '#FF6B35', back: '#4ECDC4', legs: '#45B7D1',
      core: '#96CEB4', shoulders: '#FECA57', arms: '#FF9FF3',
      full_body: '#54A0FF'
    };
    return colors[group] || '#95A5A6';
  };

  // Get weekly progress data
  const getWeeklyProgress = () => {
    const last7Days = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const dayExercises = exerciseLog.filter(ex => ex.date === dateStr);
      const totalVolume = dayExercises.reduce((sum, ex) => sum + (ex.sets * ex.reps), 0);
      
      last7Days.push({
        date: date.toLocaleDateString('tr-TR', { month: 'short', day: 'numeric' }),
        volume: totalVolume,
        exercises: dayExercises.length
      });
    }
    return last7Days;
  };

  // Login/Register UI
  if (showLogin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-400 via-red-500 to-pink-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">🦁</div>
            <h1 className="text-2xl font-bold text-gray-800">Beast Mode Coach</h1>
            <p className="text-gray-600">Kişisel Fitness Antrenörün</p>
          </div>

          {!isRegistering ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kullanıcı Adı</label>
                <input
                  type="text"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Kullanıcı adınız"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent pr-10"
                    placeholder="Şifreniz"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 transition duration-200 disabled:opacity-50"
              >
                {loading ? '🔄 Giriş yapılıyor...' : '🚀 Giriş Yap'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setIsRegistering(true)}
                  className="text-orange-500 hover:text-orange-600 text-sm"
                >
                  Hesabın yok mu? Kayıt ol
                </button>
              </div>

              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600 font-medium">Demo Hesap:</p>
                <p className="text-xs text-blue-500">Kullanıcı: han123 | Şifre: 123456</p>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ad Soyad</label>
                <input
                  type="text"
                  value={registerForm.name}
                  onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Adınız"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kullanıcı Adı</label>
                <input
                  type="text"
                  value={registerForm.username}
                  onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Kullanıcı adı seçin"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
                <input
                  type="password"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Güvenli şifre oluşturun"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Kilo (kg)</label>
                  <input
                    type="number"
                    value={registerForm.weight}
                    onChange={(e) => setRegisterForm({...registerForm, weight: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    min="40"
                    max="200"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Yaş</label>
                  <input
                    type="number"
                    value={registerForm.age}
                    onChange={(e) => setRegisterForm({...registerForm, age: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    min="16"
                    max="80"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hedef</label>
                <select
                  value={registerForm.goal}
                  onChange={(e) => setRegisterForm({...registerForm, goal: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                >
                  <option value="muscle_gain">💪 Kas Kazanımı</option>
                  <option value="weight_loss">🔥 Kilo Verme</option>
                  <option value="endurance">🏃 Dayanıklılık</option>
                  <option value="strength">⚡ Güç Artırımı</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 transition duration-200 disabled:opacity-50"
              >
                {loading ? '🔄 Kayıt oluşturuluyor...' : '✨ Kayıt Ol'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setIsRegistering(false)}
                  className="text-orange-500 hover:text-orange-600 text-sm"
                >
                  Zaten hesabın var mı? Giriş yap
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    );
  }

  // Main Application UI
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🦁</span>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Beast Mode Coach</h1>
                <p className="text-sm text-gray-500">Hoşgeldin, {currentUser?.name}! 👋</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-500">{beastModeScore}%</div>
                <div className="text-xs text-gray-500">Beast Mode</div>
              </div>
              
              <button
                onClick={() => {
                  setCurrentUser(null);
                  setShowLogin(true);
                  setChatHistory([]);
                  setExerciseLog([]);
                }}
                className="flex items-center space-x-1 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition duration-200"
              >
                <LogOut size={18} />
                <span className="hidden sm:inline">Çıkış</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: '📊 Panel', icon: BarChart3 },
              { id: 'coach', label: '🤖 Koç', icon: MessageCircle },
              { id: 'exercises', label: '💪 Egzersizler', icon: Target },
              { id: 'progress', label: '📈 İlerleme', icon: TrendingUp }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition duration-200 ${
                  activeTab === id
                    ? 'border-orange-500 text-orange-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={18} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Beast Mode Skoru</p>
                    <p className="text-2xl font-bold text-orange-500">{beastModeScore}%</p>
                  </div>
                  <div className="text-3xl">🔥</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Toplam Antrenman</p>
                    <p className="text-2xl font-bold text-blue-500">{exerciseLog.length}</p>
                  </div>
                  <div className="text-3xl">💪</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Bu Hafta</p>
                    <p className="text-2xl font-bold text-green-500">
                      {exerciseLog.filter(ex => {
                        const exerciseDate = new Date(ex.date);
                        const weekAgo = new Date();
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        return exerciseDate >= weekAgo;
                      }).length}
                    </p>
                  </div>
                  <div className="text-3xl">📅</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Güncel Kilo</p>
                    <p className="text-2xl font-bold text-purple-500">{currentUser?.weight}kg</p>
                  </div>
                  <div className="text-3xl">⚖️</div>
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Weekly Volume Chart */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Haftalık İlerleme</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getWeeklyProgress()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="volume" stroke="#FF6B35" strokeWidth={3} name="Toplam Volüm" />
                    <Line type="monotone" dataKey="exercises" stroke="#4ECDC4" strokeWidth={2} name="Egzersiz Sayısı" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Muscle Group Distribution */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Kas Grubu Dağılımı</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getMuscleGroupData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getMuscleGroupData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Coach Tab */}
        {activeTab === 'coach' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              {/* Chat Header */}
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">🤖 AI Koçun ile Konuş</h2>
                <p className="text-gray-600 mt-1">Antrenman durumunu paylaş, sorular sor ve kişiselleştirilmiş tavsiyeler al!</p>
              </div>

              {/* Chat Messages */}
              <div className="p-6 max-h-96 overflow-y-auto space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🦁</div>
                    <p className="text-gray-500">Koçunla konuşmaya başla! Bugün nasılsın?</p>
                  </div>
                ) : (
                  chatHistory.map((chat, index) => (
                    <div key={index} className="space-y-3">
                      {/* User message */}
                      <div className="flex justify-end">
                        <div className="bg-orange-500 text-white rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
                          <p className="text-sm">{chat.message}</p>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-xs opacity-75">
                            <span className="text-xs opacity-75">{new Date(chat.date).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>
                            {chat.type === 'exercise' && <span className="text-xs opacity-75">💪</span>}
                          </div>
                        </div>
                      </div>

                      {/* AI Response */}
                      <div className="flex justify-start">
                        <div className="bg-gray-100 text-gray-800 rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
                          <p className="text-sm">{chat.response}</p>
                          <span className="text-xs text-gray-500 mt-1 block">🤖 AI Koç</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Chat Input */}
              <div className="p-6 border-t border-gray-200">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    placeholder="Mesajını yaz... (örn: 'Bugün 3 set 15 push-up yaptım' veya 'Çok yorgunum')"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    disabled={loading}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleChatSubmit(e);
                      }
                    }}
                  />
                  <button
                    onClick={handleChatSubmit}
                    disabled={loading || !chatMessage.trim()}
                    className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 transition duration-200"
                  >
                    {loading ? '🔄' : '📤'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Exercises Tab */}
        {activeTab === 'exercises' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">💪 Egzersiz Kayıtların</h2>
              
              {exerciseLog.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🏃‍♂️</div>
                  <p className="text-gray-500">Henüz egzersiz kaydın yok. Koçunla konuşarak başla!</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full table-auto">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tarih</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Egzersiz</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Kas Grubu</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Set</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tekrar</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Toplam</th>
                      </tr>
                    </thead>
                    <tbody>
                      {exerciseLog.map((exercise, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(exercise.date).toLocaleDateString('tr-TR')}
                          </td>
                          <td className="py-3 px-4 text-sm font-medium text-gray-900 capitalize">
                            {exercise.exercise}
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {beastModeData.muscleGroups[exercise.muscleGroup]}
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">{exercise.sets}</td>
                          <td className="py-3 px-4 text-sm text-gray-600">{exercise.reps}</td>
                          <td className="py-3 px-4 text-sm font-semibold text-orange-600">
                            {exercise.sets * exercise.reps}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Progress Tab */}
        {activeTab === 'progress' && (
          <div className="space-y-6">
            {/* Progress Overview */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">📈 İlerleme Analizi</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">{exerciseLog.length}</div>
                  <div className="text-sm text-gray-600">Toplam Egzersiz</div>
                </div>
                
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {exerciseLog.reduce((sum, ex) => sum + (ex.sets * ex.reps), 0)}
                  </div>
                  <div className="text-sm text-gray-600">Toplam Volüm</div>
                </div>
                
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{beastModeScore}%</div>
                  <div className="text-sm text-gray-600">Beast Mode Skoru</div>
                </div>
              </div>

              {/* Weekly Progress Chart */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Son 7 Günlük İlerleme</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getWeeklyProgress()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="volume" fill="#FF6B35" name="Günlük Volüm" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Goals and Achievements */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Hedefler ve Başarılar</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Haftalık Hedef</span>
                      <span className="text-sm text-gray-500">5/7 gün</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-orange-500 h-2 rounded-full" style={{width: '71%'}}></div>
                    </div>
                  </div>
                  
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Beast Mode</span>
                      <span className="text-sm text-gray-500">{beastModeScore}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-red-500 h-2 rounded-full" style={{width: `${beastModeScore}%`}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default BeastModeFitnessApp;
