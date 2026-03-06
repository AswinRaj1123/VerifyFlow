export default function ConfidenceBadge({ confidence }) {
  const getStyles = () => {
    if (confidence > 75) {
      return 'bg-green-100 text-green-800 border-green-200';
    } else if (confidence >= 40) {
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    } else {
      return 'bg-red-100 text-red-800 border-red-200';
    }
  };

  const getLabel = () => {
    if (confidence > 75) return 'High';
    if (confidence >= 40) return 'Medium';
    return 'Low';
  };

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStyles()}`}>
      {confidence}% {getLabel()}
    </span>
  );
}
