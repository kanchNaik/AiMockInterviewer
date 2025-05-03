import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Interview.css';

const Interview = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { session_id, question: initialQuestion } = location.state || {};

  const [sessionId, setSessionId] = useState(session_id);
  const [currentQuestion, setCurrentQuestion] = useState(initialQuestion);
  const [userAnswer, setUserAnswer] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNextPrompt, setShowNextPrompt] = useState(false);

  useEffect(() => {
    if (!session_id || !initialQuestion) {
      navigate('/');
    }
  }, [session_id, initialQuestion, navigate]);

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) return;
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/interview/answer', {
        session_id: sessionId,
        text: userAnswer,
      });

      const { feedback, question: nextQ } = res.data;

      setChatHistory([
        ...chatHistory,
        {
          question: currentQuestion,
          answer: userAnswer,
          feedback,
        },
      ]);
      setCurrentQuestion(nextQ);
      setUserAnswer('');
      setShowNextPrompt(true);
    } catch (err) {
      console.error('Error submitting answer:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = () => {
    setShowNextPrompt(false);
  };

  const handleEndInterview = () => {
    navigate('/');
  };

  return (
    <div className="interview-container">
      <h1 className="interview-title">AI Mock Interview</h1>

      <div className="chat-box">
        {chatHistory.map((item, idx) => (
          <div key={idx} className="chat-block">
            <div><strong>Question:</strong> {item.question}</div>
            <div><strong>You:</strong> {item.answer}</div>
            <div><strong>Feedback:</strong> {item.feedback}</div>
          </div>
        ))}

        {!showNextPrompt && currentQuestion && (
          <div className="chat-block">
            <div><strong>Question:</strong> {currentQuestion}</div>
            <textarea
              rows="4"
              className="answer-box"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="Type your answer here..."
            />
            <button onClick={handleSubmitAnswer} disabled={loading} className="submit-btn">
              {loading ? 'Submitting...' : 'Submit Answer'}
            </button>
          </div>
        )}

        {showNextPrompt && (
          <div className="next-prompt">
            <p>Would you like to continue to the next question?</p>
            <div className="next-buttons">
              <button onClick={handleNextQuestion} disabled={loading} className="next-btn">
                Yes, next question
              </button>
              <button onClick={handleEndInterview} className="next-btn">
                No, end interview
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Interview;
