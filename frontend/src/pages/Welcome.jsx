import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaEnvelope, FaLock } from 'react-icons/fa';
import image from '/public/2207.i101.025.F.m004.c9.machine learning deep learning isometric.jpg';
import './Welcome.css';

const Welcome = () => {
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    navigate('/select-role');
  };

  return (
    <div className="welcome-container">
      <div className="left-panel">
        <img src={image} alt="AI Visual" className="ai-image" />
        <p className="image-credit">
          Image by{' '}
          <a href="https://www.freepik.com" target="_blank" rel="noopener noreferrer">
            macrovector on Freepik
          </a>
        </p>
      </div>

      <div className="right-panel">
        <div className="login-card">
          <h2 className="login-title">AI Mock Interviewer</h2>
          <p className="login-subtitle">
            Start here to prepare for your next interview with AI assistance
          </p>

          <form onSubmit={handleLogin}>
            <div className="input-group">
              <FaEnvelope className="input-icon" />
              <input type="email" placeholder="Enter your email" required />
            </div>

            <div className="input-group">
              <FaLock className="input-icon" />
              <input type="password" placeholder="Enter your password" required />
            </div>

            <div className="forgot-password">
              <a href="#">Forgot password?</a>
            </div>

            <button type="submit" className="login-btn">Login</button>

            <div className="signup-link">
              Don’t have an account? <a href="#">Signup now</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
