import { useState } from 'react';
import SessionDetail from './components/SessionDetail';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(1); // Demo: Replace with actual session ID
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Simple demo - in production, implement proper auth flow
  const handleLogin = () => {
    // For demo purposes - in real app, call api.login()
    localStorage.setItem('access_token', 'your-jwt-token-here');
    setIsLoggedIn(true);
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">VerifyFlow</h1>
          <p className="text-gray-600 mb-6">
            Structured Questionnaire Answering Tool
          </p>
          <button
            onClick={handleLogin}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Login to Continue
          </button>
          <p className="mt-4 text-sm text-gray-500 text-center">
            For demo: This will bypass auth
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <SessionDetail sessionId={sessionId} />
    </div>
  );
}

export default App;
