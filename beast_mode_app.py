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
                              {chat.type === 'exercise' ? '💪 Egzersiz' : '💭 Genel'}
                            </span>
                            <span className="text-xs opacity-75">
                              {new Date(chat.date).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* AI response */}
                      <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs lg:max-w-md">
                          <p className="text-sm text-gray-800">{chat.response}</p>
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
                    placeholder="Örn: Bugün 20 push-up 3 set yaptım! veya Çok yorgunum..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    disabled={loading}
                    onKeyPress={(e) => e.key === 'Enter' && handleChatSubmit(e)}
                  />
                  <button
                    onClick={handleChatSubmit}
                    disabled={loading || !chatMessage.trim()}
                    className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '⏳' : '📤'}
                  </button>
                </div>
                
                <div className="mt-3 flex flex-wrap gap-2">
                  {['Bugün nasılım?', '20 push-up yaptım', 'Motivasyon lazım', 'Beslenme tavsiyen var mı?'].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setChatMessage(suggestion)}
                      className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition duration-200"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Exercises Tab */}
        {activeTab === 'exercises' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">💪 Egzersiz Kütüphanesi</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(beastModeData.exercises).map(([exercise, data]) => (
                  <div key={exercise} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition duration-200">
                    <h3 className="font-semibold text-gray-900 capitalize mb-2">{exercise}</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Kas Grubu:</span>
                        <span className="text-sm font-medium">{beastModeData.muscleGroups[data.muscleGroup]}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Zorluk:</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          data.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                          data.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {data.difficulty === 'beginner' ? 'Başlangıç' :
                           data.difficulty === 'intermediate' ? 'Orta' : 'İleri'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Exercises */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">📋 Son Egzersizlerin</h2>
                <button className="flex items-center space-x-1 px-3 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition duration-200">
                  <Plus size={16} />
                  <span>Egzersiz Ekle</span>
                </button>
              </div>

              {exerciseLog.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🏋️</div>
                  <p className="text-gray-500">Henüz egzersiz kaydın yok. Koçunla konuşarak başla!</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Tarih</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Egzersiz</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Set</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Tekrar</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Kas Grubu</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-600">Volüm</th>
                      </tr>
                    </thead>
                    <tbody>
                      {exerciseLog.slice().reverse().map((exercise, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(exercise.date).toLocaleDateString('tr-TR')}
                          </td>
                          <td className="py-3 px-4 text-sm font-medium text-gray-900 capitalize">
                            {exercise.exercise}
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">{exercise.sets}</td>
                          <td className="py-3 px-4 text-sm text-gray-600">{exercise.reps}</td>
                          <td className="py-3 px-4 text-sm">
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                              {beastModeData.muscleGroups[exercise.muscleGroup]}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm font-medium text-orange-600">
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
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Beast Mode Score Progress */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">🔥 Beast Mode Skoru</h3>
                  <div className="relative">
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div 
                        className="bg-gradient-to-r from-orange-400 to-red-500 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${beastModeScore}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-sm text-gray-600 mt-1">
                      <span>0%</span>
                      <span className="font-bold text-orange-600">{beastModeScore}%</span>
                      <span>100%</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">{exerciseLog.length}</div>
                      <div className="text-sm text-gray-600">Toplam Egzersiz</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {Math.floor((Date.now() - new Date(currentUser?.joinDate).getTime()) / (1000 * 60 * 60 * 24))}
                      </div>
                      <div className="text-sm text-gray-600">Gün Aktif</div>
                    </div>
                  </div>
                </div>

                {/* Weekly Summary */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">📅 Bu Hafta</h3>
                  <div className="space-y-3">
                    {getWeeklyProgress().map((day, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-sm font-medium text-gray-700">{day.date}</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">{day.exercises} egzersiz</span>
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${Math.min(100, (day.volume / 50) * 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Charts */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Detaylı İstatistikler</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Volume by Muscle Group */}
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-3">Kas Grubu Performansı</h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={getMuscleGroupData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#FF6B35" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Exercise Distribution */}
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-3">Egzersiz Dağılımı</h4>
                  <div className="space-y-2">
                    {Object.entries(
                      exerciseLog.reduce((acc, ex) => {
                        acc[ex.exercise] = (acc[ex.exercise] || 0) + 1;
                        return acc;
                      }, {})
                    ).map(([exercise, count]) => (
                      <div key={exercise} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm font-medium capitalize">{exercise}</span>
                        <span className="text-sm text-gray-600">{count} kez</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Achievement Badges */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🏆 Başarılarım</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { 
                    icon: '🔥', 
                    title: 'İlk Adım', 
                    desc: 'İlk egzersizini tamamladın',
                    earned: exerciseLog.length > 0
                  },
                  { 
                    icon: '💪', 
                    title: 'Güçlü Başlangıç', 
                    desc: '5 egzersiz tamamladın',
                    earned: exerciseLog.length >= 5
                  },
                  { 
                    icon: '🎯', 
                    title: 'Odaklanmış', 
                    desc: 'Aynı kas grubunda 3 egzersiz',
                    earned: Object.values(
                      exerciseLog.reduce((acc, ex) => {
                        acc[ex.muscleGroup] = (acc[ex.muscleGroup] || 0) + 1;
                        return acc;
                      }, {})
                    ).some(count => count >= 3)
                  },
                  { 
                    icon: '🦁', 
                    title: 'Beast Mode', 
                    desc: '%80 Beast Mode skoruna ulaştın',
                    earned: beastModeScore >= 80
                  }
                ].map((badge, index) => (
                  <div 
                    key={index} 
                    className={`text-center p-4 rounded-lg border-2 transition duration-200 ${
                      badge.earned 
                        ? 'border-yellow-300 bg-yellow-50' 
                        : 'border-gray-200 bg-gray-50 opacity-50'
                    }`}
                  >
                    <div className="text-3xl mb-2">{badge.icon}</div>
                    <h4 className="font-medium text-gray-900 text-sm">{badge.title}</h4>
                    <p className="text-xs text-gray-600 mt-1">{badge.desc}</p>
                    {badge.earned && (
                      <div className="text-xs text-yellow-600 font-medium mt-2">✓ Kazanıldı</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default BeastModeFitnessApp;
