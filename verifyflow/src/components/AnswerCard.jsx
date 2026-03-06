import { useState, useEffect } from 'react';
import ConfidenceBadge from './ConfidenceBadge';

export default function AnswerCard({ question, index, onUpdate, isSelected, onSelectToggle }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedAnswer, setEditedAnswer] = useState(question.answer || '');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setEditedAnswer(question.answer || '');
  }, [question.answer]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdate(question.id, editedAnswer);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save answer:', error);
      alert('Failed to save answer. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedAnswer(question.answer || '');
    setIsEditing(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header with checkbox and question number */}
      <div className="flex items-start gap-4 mb-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelectToggle(question.id)}
          className="mt-1 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <div className="flex-1">
          <div className="flex items-start justify-between gap-4 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              Q{index + 1}. {question.original_text}
            </h3>
            {question.confidence > 0 && (
              <ConfidenceBadge confidence={question.confidence} />
            )}
          </div>

          {/* Answer section */}
          <div className="mt-3">
            {isEditing ? (
              <div>
                <textarea
                  value={editedAnswer}
                  onChange={(e) => setEditedAnswer(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y min-h-[120px]"
                  placeholder="Enter answer..."
                />
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                  >
                    {isSaving ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={handleCancel}
                    disabled={isSaving}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-gray-700 whitespace-pre-wrap bg-gray-50 px-4 py-3 rounded-lg border border-gray-200">
                  {question.answer || (
                    <span className="text-gray-400 italic">No answer generated yet</span>
                  )}
                </p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  ✏️ Edit Answer
                </button>
              </div>
            )}
          </div>

          {/* Citations */}
          {question.citations && question.citations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-600 mb-2">Citations:</p>
              <ul className="space-y-1">
                {question.citations.map((citation, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    <span className="italic">{citation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Edited flag */}
          {question.is_edited && (
            <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
              <span>✏️</span>
              <span className="italic">Edited by user</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
