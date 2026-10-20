import React, { useState, useEffect } from 'react';
import {
  StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, SafeAreaView
} from 'react-native';

export default function App() {
  const [expression, setExpression] = useState('');
  const [solveType, setSolveType] = useState('solve');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('solver');

  // AI Tutor states
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { sender: 'ai', text: 'שלום! אני עוזר הלמידה האישי שלך ל-5 יחידות. איזה נושא תרצה להבין או לתרגל היום?' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // Quiz states
  const [quizTopic, setQuizTopic] = useState('חדווא');
  const [quizDifficulty, setQuizDifficulty] = useState('בינוני');
  const [quizData, setQuizData] = useState(null);
  const [studentAnswer, setStudentAnswer] = useState('');
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizEvaluation, setQuizEvaluation] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // History state
  const [historyData, setHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/history');
      const res = await response.json();
      if (res.status === 'success') {
        setHistoryData(res.history);
      }
    } catch (error) {
      console.log('Error fetching history');
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const handleSolve = async () => {
    if (!expression.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression, type: solveType })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ status: 'error', message: 'שגיאה בהתחברות לשרת' });
    } finally {
      setLoading(false);
    }
  };

  const handleAskTutor = async () => {
    if (!chatQuestion.trim()) return;
    
    const userMsg = chatQuestion;
    setChatMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatQuestion('');
    setChatLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/tutor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg, topic: 'general' })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setChatMessages(prev => [...prev, { sender: 'ai', text: data.reply }]);
      }
    } catch (error) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: 'מצטער, הייתה שגיאה בתקשורת עם השרת.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleGenerateQuiz = async () => {
    setQuizLoading(true);
    setQuizData(null);
    setQuizEvaluation(null);
    setStudentAnswer('');

    try {
      const response = await fetch('http://127.0.0.1:8000/generate-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: quizTopic, difficulty: quizDifficulty })
      });
      const res = await response.json();
      if (res.status === 'success') {
        setQuizData(res.data);
      }
    } catch (error) {
      alert('שגיאה ביצירת השאלה');
    } finally {
      setQuizLoading(false);
    }
  };

  const handleEvaluateQuiz = async () => {
    if (!studentAnswer.trim() || !quizData) return;
    setEvalLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/evaluate-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: quizData.question,
          student_answer: studentAnswer,
          correct_solution: quizData.solution,
          topic: quizTopic
        })
      });
      const res = await response.json();
      if (res.status === 'success') {
        setQuizEvaluation(res.evaluation);
      }
    } catch (error) {
      alert('שגיאה בהערכת התשובה');
    } finally {
      setEvalLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Math & Physics AI</Text>
        <Text style={styles.headerSubtitle}>5 יחידות לימוד | Database & Learning Analytics</Text>
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'solver' && styles.activeTab]}
          onPress={() => setActiveTab('solver')}
        >
          <Text style={[styles.tabText, activeTab === 'solver' && styles.activeTabText]}>פתרון</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'quiz' && styles.activeTab]}
          onPress={() => setActiveTab('quiz')}
        >
          <Text style={[styles.tabText, activeTab === 'quiz' && styles.activeTabText]}>תרגול</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'history' && styles.activeTab]}
          onPress={() => setActiveTab('history')}
        >
          <Text style={[styles.tabText, activeTab === 'history' && styles.activeTabText]}>התקדמות</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'tutor' && styles.activeTab]}
          onPress={() => setActiveTab('tutor')}
        >
          <Text style={[styles.tabText, activeTab === 'tutor' && styles.activeTabText]}>עוזר AI</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'formulas' && styles.activeTab]}
          onPress={() => setActiveTab('formulas')}
        >
          <Text style={[styles.tabText, activeTab === 'formulas' && styles.activeTabText]}>נוסחאות</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'solver' && (
          <View>
            <View style={styles.typeSelector}>
              <TouchableOpacity
                style={[styles.typeButton, solveType === 'solve' && styles.selectedType]}
                onPress={() => setSolveType('solve')}
              >
                <Text style={styles.typeText}>אלגברה</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.typeButton, solveType === 'derivative' && styles.selectedType]}
                onPress={() => setSolveType('derivative')}
              >
                <Text style={styles.typeText}>חדו"א</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.input}
              placeholder="הכנס משוואה/פונקציה..."
              value={expression}
              onChangeText={setExpression}
              placeholderTextColor="#888"
            />

            <TouchableOpacity style={styles.solveButton} onPress={handleSolve} disabled={loading}>
              {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.solveButtonText}>פתור צעד-אחר-צעד</Text>}
            </TouchableOpacity>

            {result && (
              <View style={styles.resultBox}>
                <Text style={styles.resultTitle}>שלבי פתרון:</Text>
                {result.status === 'success' ? (
                  result.steps.map((step, idx) => (
                    <View key={idx} style={styles.stepCard}>
                      <Text style={styles.stepText}>{step}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.errorText}>{result.message}</Text>
                )}
              </View>
            )}
          </View>
        )}

        {activeTab === 'quiz' && (
          <View>
            <Text style={styles.sectionTitle}>🎯 מנוע סימולציית תרגול אדפטיבית</Text>
            
            <View style={styles.quizConfig}>
              <Text style={styles.label}>בחר נושא:</Text>
              <View style={styles.typeSelector}>
                {['חדווא', 'אלגברה', 'גיאומטריה'].map(t => (
                  <TouchableOpacity
                    key={t}
                    style={[styles.typeButton, quizTopic === t && styles.selectedType]}
                    onPress={() => setQuizTopic(t)}
                  >
                    <Text style={styles.typeText}>{t}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>רמת קושי:</Text>
              <View style={styles.typeSelector}>
                {['קל', 'בינוני', '5 יחידות'].map(d => (
                  <TouchableOpacity
                    key={d}
                    style={[styles.typeButton, quizDifficulty === d && styles.selectedType]}
                    onPress={() => setQuizDifficulty(d)}
                  >
                    <Text style={styles.typeText}>{d}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.generateButton} onPress={handleGenerateQuiz} disabled={quizLoading}>
                {quizLoading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.generateButtonText}>צור שאלת תרגול</Text>}
              </TouchableOpacity>
            </View>

            {quizData && (
              <View style={styles.quizCard}>
                <Text style={styles.quizQuestionTitle}>שאלה:</Text>
                <Text style={styles.quizQuestionText}>{quizData.question}</Text>
                {quizData.hint && <Text style={styles.quizHint}>💡 רמז: {quizData.hint}</Text>}

                <TextInput
                  style={[styles.input, { marginTop: 12 }]}
                  placeholder="הקלד את תשובתך או דרך הפתרון..."
                  value={studentAnswer}
                  onChangeText={setStudentAnswer}
                  multiline
                />

                <TouchableOpacity style={styles.evalButton} onPress={handleEvaluateQuiz} disabled={evalLoading}>
                  {evalLoading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.evalButtonText}>בדוק את התשובה שלי</Text>}
                </TouchableOpacity>

                {quizEvaluation && (
                  <View style={styles.evalResultCard}>
                    <Text style={styles.evalTitle}>הערכת המורה הדיגיטלי:</Text>
                    <Text style={styles.evalText}>{quizEvaluation}</Text>
                  </View>
                )}
              </View>
            )}
          </View>
        )}

        {activeTab === 'history' && (
          <View>
            <Text style={styles.sectionTitle}>📊 היסטוריית תרגולים והתקדמות</Text>
            {historyLoading ? (
              <ActivityIndicator color="#2563EB" style={{ marginVertical: 20 }} />
            ) : historyData.length === 0 ? (
              <Text style={styles.infoText}>עדיין אין היסטוריית תרגולים. בצע תרגול בטאב 'תרגול'!</Text>
            ) : (
              historyData.map((item, idx) => (
                <View key={idx} style={styles.historyCard}>
                  <View style={styles.historyHeader}>
                    <Text style={styles.historyTopic}>{item.topic}</Text>
                    <Text style={styles.historyTime}>{item.timestamp}</Text>
                  </View>
                  <Text style={styles.historyQuestion}>שאלה: {item.question}</Text>
                  <Text style={styles.historyAnswer}>תשובתך: {item.student_answer}</Text>
                  <View style={styles.historyEvalBox}>
                    <Text style={styles.historyEvalText}>{item.evaluation}</Text>
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {activeTab === 'tutor' && (
          <View>
            <Text style={styles.sectionTitle}>🤖 AI Math Tutor - מורה פרטי אישי</Text>
            <View style={styles.chatBox}>
              {chatMessages.map((msg, index) => (
                <View
                  key={index}
                  style={[
                    styles.chatBubble,
                    msg.sender === 'user' ? styles.userBubble : styles.aiBubble
                  ]}
                >
                  <Text style={msg.sender === 'user' ? styles.userText : styles.aiText}>
                    {msg.text}
                  </Text>
                </View>
              ))}
              {chatLoading && <ActivityIndicator color="#2563EB" style={{ marginVertical: 10 }} />}
            </View>

            <View style={styles.chatInputContainer}>
              <TextInput
                style={styles.chatInput}
                placeholder="שאל שאלה (למשל: למה גוזרים פונקציה?)..."
                value={chatQuestion}
                onChangeText={setChatQuestion}
                placeholderTextColor="#888"
              />
              <TouchableOpacity style={styles.sendButton} onPress={handleAskTutor}>
                <Text style={styles.sendButtonText}>שלח</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {activeTab === 'formulas' && (
          <View>
            <Text style={styles.sectionTitle}>📐 גיאומטריה וטריגונומטריה</Text>
            <View style={styles.formulaCard}>
              <Text style={styles.formulaName}>משפט הקוסינוסים</Text>
              <Text style={styles.formulaCode}>c² = a² + b² - 2ab·cos(γ)</Text>
            </View>
            <View style={styles.formulaCard}>
              <Text style={styles.formulaName}>משפט הסינוסים</Text>
              <Text style={styles.formulaCode}>a / sin(α) = 2R</Text>
            </View>

            <Text style={styles.sectionTitle}>⚡ פיזיקה - מכניקה וחשמל</Text>
            <View style={styles.formulaCard}>
              <Text style={styles.formulaName}>חוק שני של ניוטון</Text>
              <Text style={styles.formulaCode}>F = m · a</Text>
            </View>
            <View style={styles.formulaCard}>
              <Text style={styles.formulaName}>חוק אוהם (חשמל)</Text>
              <Text style={styles.formulaCode}>V = I · R</Text>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  header: { backgroundColor: '#0F172A', padding: 20, alignItems: 'center' },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#FFF' },
  headerSubtitle: { fontSize: 13, color: '#94A3B8', marginTop: 4 },
  tabContainer: { flexDirection: 'row', backgroundColor: '#E2E8F0' },
  tabButton: { flex: 1, padding: 8, alignItems: 'center' },
  activeTab: { backgroundColor: '#2563EB' },
  tabText: { fontSize: 11, color: '#334155', fontWeight: '600' },
  activeTabText: { color: '#FFF' },
  content: { padding: 16 },
  typeSelector: { flexDirection: 'row', marginBottom: 12, gap: 8 },
  typeButton: { flex: 1, padding: 10, backgroundColor: '#CBD5E1', borderRadius: 8, alignItems: 'center' },
  selectedType: { backgroundColor: '#2563EB' },
  typeText: { color: '#FFF', fontWeight: 'bold', fontSize: 13 },
  input: { backgroundColor: '#FFF', borderRadius: 8, padding: 14, fontSize: 15, borderWidth: 1, borderColor: '#CBD5E1', marginBottom: 12, textAlign: 'right' },
  solveButton: { backgroundColor: '#10B981', padding: 14, borderRadius: 8, alignItems: 'center' },
  solveButtonText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  resultBox: { marginTop: 20 },
  resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#0F172A', marginBottom: 10, textAlign: 'right' },
  stepCard: { backgroundColor: '#FFF', padding: 14, borderRadius: 8, marginBottom: 8, borderRightWidth: 4, borderRightColor: '#10B981' },
  stepText: { fontSize: 15, color: '#334155', textAlign: 'right' },
  errorText: { color: '#EF4444', textAlign: 'center', fontSize: 16 },
  sectionTitle: { fontSize: 17, fontWeight: 'bold', color: '#0F172A', marginTop: 12, marginBottom: 12, textAlign: 'right' },
  formulaCard: { backgroundColor: '#FFF', padding: 14, borderRadius: 8, marginBottom: 8 },
  formulaName: { fontSize: 15, fontWeight: '600', color: '#0F172A', textAlign: 'right' },
  formulaCode: { fontSize: 14, color: '#2563EB', marginTop: 4, fontFamily: 'monospace', textAlign: 'right' },
  chatBox: { minHeight: 200, backgroundColor: '#FFF', borderRadius: 10, padding: 12, marginBottom: 12, borderWidth: 1, borderColor: '#E2E8F0' },
  chatBubble: { padding: 12, borderRadius: 8, marginBottom: 8, maxWidth: '85%' },
  userBubble: { backgroundColor: '#2563EB', alignSelf: 'flex-start' },
  aiBubble: { backgroundColor: '#F1F5F9', alignSelf: 'flex-end' },
  userText: { color: '#FFF', textAlign: 'right', fontSize: 14 },
  aiText: { color: '#0F172A', textAlign: 'right', fontSize: 14 },
  chatInputContainer: { flexDirection: 'row', gap: 8 },
  chatInput: { flex: 1, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 8, padding: 12, textAlign: 'right', fontSize: 14 },
  sendButton: { backgroundColor: '#2563EB', paddingHorizontal: 18, justifyContent: 'center', borderRadius: 8 },
  sendButtonText: { color: '#FFF', fontWeight: 'bold', fontSize: 14 },
  quizConfig: { backgroundColor: '#FFF', padding: 14, borderRadius: 10, marginBottom: 16, borderWidth: 1, borderColor: '#E2E8F0' },
  label: { fontSize: 14, fontWeight: 'bold', color: '#334155', marginBottom: 6, textAlign: 'right' },
  generateButton: { backgroundColor: '#8B5CF6', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 8 },
  generateButtonText: { color: '#FFF', fontWeight: 'bold', fontSize: 15 },
  quizCard: { backgroundColor: '#FFF', padding: 16, borderRadius: 10, borderWidth: 1, borderColor: '#CBD5E1' },
  quizQuestionTitle: { fontSize: 16, fontWeight: 'bold', color: '#0F172A', textAlign: 'right' },
  quizQuestionText: { fontSize: 15, color: '#1E293B', marginTop: 6, textAlign: 'right' },
  quizHint: { fontSize: 13, color: '#D97706', marginTop: 8, textAlign: 'right' },
  evalButton: { backgroundColor: '#2563EB', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 8 },
  evalButtonText: { color: '#FFF', fontWeight: 'bold', fontSize: 15 },
  evalResultCard: { marginTop: 14, padding: 14, backgroundColor: '#F0FDF4', borderRadius: 8, borderWidth: 1, borderColor: '#86EFAC' },
  evalTitle: { fontSize: 15, fontWeight: 'bold', color: '#166534', textAlign: 'right' },
  evalText: { fontSize: 14, color: '#14532D', marginTop: 6, textAlign: 'right' },
  historyCard: { backgroundColor: '#FFF', padding: 14, borderRadius: 8, marginBottom: 10, borderWidth: 1, borderColor: '#E2E8F0' },
  historyHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  historyTopic: { fontWeight: 'bold', color: '#2563EB' },
  historyTime: { fontSize: 12, color: '#94A3B8' },
  historyQuestion: { fontSize: 14, color: '#0F172A', textAlign: 'right' },
  historyAnswer: { fontSize: 13, color: '#475569', marginTop: 4, textAlign: 'right' },
  historyEvalBox: { marginTop: 8, padding: 8, backgroundColor: '#F8FAFC', borderRadius: 6 },
  historyEvalText: { fontSize: 13, color: '#1E293B', textAlign: 'right' },
  infoText: { textAlign: 'center', color: '#64748B', marginTop: 20, fontSize: 15 }
});