// src/pages/ResetPassword.jsx
import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import "./Welcome.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ResetPassword = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const tokenFromState = location.state?.token || "";
  const emailFromState = location.state?.email || "";

  const [token, setToken] = useState(tokenFromState);
  const [email, setEmail] = useState(emailFromState);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!token) {
      setError("Reset token is missing.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/reset-password`, {
        token,
        email: email || undefined,
        new_password: password,
      });

      setMessage(res.data.message || "Password reset successful.");
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
      if (err.response?.data?.detail) setError(err.response.data.detail);
      else setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="welcome-container">
      <div className="right-panel" style={{ margin: "0 auto" }}>
        <div className="login-card">
          <h2 className="login-title">Reset Password</h2>
          <p className="login-subtitle">enter your new password below</p>

          <form onSubmit={handleSubmit}>
            {!tokenFromState && (
              <div className="input-group">
                <input
                  type="text"
                  placeholder="enter reset token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </div>
            )}

            {!emailFromState && (
              <div className="input-group">
                <input
                  type="email"
                  placeholder="enter your email (optional)"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            )}

            <div className="input-group">
              <input
                type="password"
                placeholder="new password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="input-group">
              <input
                type="password"
                placeholder="confirm new password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
              />
            </div>

            {message && <p style={{ color: "green" }}>{message}</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Resetting..." : "Reset Password"}
            </button>

            <div className="signup-link">
              back to{" "}
              <a onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
                login
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
