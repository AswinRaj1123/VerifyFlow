import { useState, useEffect } from 'react';
import { api } from '../api';
import AnswerCard from './AnswerCard';

export default function SessionDetail({ sessionId }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedQuestions, setSelectedQuestions] = useState(new Set());
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  const loadSession = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSessionDetail(sessionId);
      setSession(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAll = async () => {
    if (!confirm('Generate answers for all questions? This may take a few minutes.')) {
      return;
    }

    try {
      setIsGenerating(true);
      await api.generateAnswers(sessionId);
      await loadSession(); // Reload to get updated answers
      alert('✅ All answers generated successfully!');
    } catch (err) {
      alert('❌ Failed to generate answers: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerateSelected = async () => {
    if (selectedQuestions.size === 0) {
      alert('Please select at least one question to regenerate');
      return;
    }

    if (!confirm(`Regenerate ${selectedQuestions.size} selected question(s)?`)) {
      return;
    }

    try {
      setIsGenerating(true);
      await api.regenerateSelected(sessionId, Array.from(selectedQuestions));
      await loadSession();
      setSelectedQuestions(new Set()); // Clear selection
      alert(`✅ Successfully regenerated ${selectedQuestions.size} answers!`);
    } catch (err) {
      alert('❌ Failed to regenerate: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUpdateQuestion = async (questionId, answer) => {
    await api.updateQuestion(questionId, answer);
    // Update local state
    setSession(prev => ({
      ...prev,
      questions: prev.questions.map(q =>
        q.id === questionId ? { ...q, answer, is_edited: true } : q
      )
    }));
  };

  const handleSelectToggle = (questionId) => {
    setSelectedQuestions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedQuestions.size === session.questions.length) {
      setSelectedQuestions(new Set());
    } else {
      setSelectedQuestions(new Set(session.questions.map(q => q.id)));
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await api.exportSession(sessionId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `questionnaire-session-${sessionId}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      alert('✅ Document exported successfully!');
    } catch (err) {
      alert('❌ Failed to export: ' + err.message);
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading session...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Session</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadSession}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const hasQuestions = session.questions && session.questions.length > 0;
  const hasAnswers = hasQuestions && session.questions.some(q => q.answer);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{session.title}</h1>
              <p className="mt-1 text-sm text-gray-500">
                Session ID: {session.id} • Status: <span className="font-medium">{session.status}</span>
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Questions: {session.questions.length} • References: {session.references.length}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleExport}
                disabled={!hasAnswers || isExporting}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isExporting ? 'Exporting...' : '📄 Export to Word'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action Bar */}
        {hasQuestions && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  {selectedQuestions.size === session.questions.length
                    ? '☑ Deselect All'
                    : '☐ Select All'}
                </button>
                {selectedQuestions.size > 0 && (
                  <span className="text-sm text-gray-600">
                    {selectedQuestions.size} selected
                  </span>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleRegenerateSelected}
                  disabled={selectedQuestions.size === 0 || isGenerating}
                  className="px-5 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isGenerating ? '⏳ Regenerating...' : '🔄 Regenerate Selected'}
                </button>
                <button
                  onClick={handleGenerateAll}
                  disabled={isGenerating}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium"
                >
                  {isGenerating ? '⏳ Generating...' : '✨ Generate All Answers'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Questions List */}
        {hasQuestions ? (
          <div className="space-y-4">
            {session.questions.map((question, index) => (
              <AnswerCard
                key={question.id}
                question={question}
                index={index}
                onUpdate={handleUpdateQuestion}
                isSelected={selectedQuestions.has(question.id)}
                onSelectToggle={handleSelectToggle}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">📝</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              No Questions Yet
            </h3>
            <p className="text-gray-500">
              Upload a questionnaire file to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
