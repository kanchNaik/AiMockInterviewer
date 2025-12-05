// src/pages/ForgotPassword.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import image from "/public/2207.i101.025.F.m004.c9.machine learning deep learning isometric.jpg";
import "./Welcome.css"; // reuse same css

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/auth/forgot-password`, { email });

      setMessage(
        res.data.message || "If this email exists, you can now reset your password."
      );

      const token = res.data.token;
      if (token) {
        // for this project: go straight to reset screen with token + email
        navigate("/reset-password", { state: { token, email } });
      }
    } catch (err) {
      if (err.response?.data?.detail) setError(err.response.data.detail);
      else setError("Something went wrong. Try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="welcome-container">
      {/* left image panel */}
      <div className="left-panel">
        <img src={image} alt="AI Visual" className="ai-image" />
        <p className="image-credit">
          Image by{" "}
          <a
            href="https://www.freepik.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            macrovector on Freepik
          </a>
        </p>
      </div>

      {/* right form panel */}
      <div className="right-panel">
        <div className="login-card">
          <h2 className="login-title">Forgot Password?</h2>
          <p className="login-subtitle">
            enter your email and click below to reset your password
          </p>

          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <input
                type="email"
                placeholder="enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {message && <p style={{ color: "green" }}>{message}</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Checking..." : "Click to Reset Password"}
            </button>

            <div className="signup-link">
              remembered your password?{" "}
              <a onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
                back to login
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;