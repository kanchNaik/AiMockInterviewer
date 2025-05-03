import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './SelectRole.css';

const SelectRole = () => {
  const [company, setCompany] = useState('');
  const [level, setLevel] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const companies = ['Google', 'Meta', 'Amazon', 'OpenAI'];
  const levels = ['L1', 'L2', 'L3', 'L4'];
  const roles = ['Data Analyst', 'Data Scientist', 'ML Engineer'];

  const handleStart = async () => {
    if (!company || !level || !role) {
      alert('Please select company, level, and role before starting.');
      return;
    }

    setLoading(true);

    // make user_text more natural for NER to parse
    const user_text = `I have an interview at ${company} for a ${role} position at level ${level}`;

    try {
      const response = await axios.post('http://127.0.0.1:8000/session', {
        user_text,
        session_id: null,
      });

      const { session_id, question } = response.data;
      navigate('/interview', { state: { session_id, question } });
    } catch (error) {
      console.error('Failed to create session:', error);
      alert('Error: Unable to start session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h1 className="heading">Customize Your Mock Interview</h1>

        <div className="section">
          <h2>Select Your Company</h2>
          <div className="company-grid">
            {companies.map((c) => (
              <button
                key={c}
                className={`btn company-btn ${company === c ? 'selected' : ''}`}
                onClick={() => setCompany(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="section">
          <h2>Select Your Level</h2>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="dropdown"
          >
            <option value="">-- Select Level --</option>
            {levels.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>

        <div className="section">
          <h2>Select Your Role</h2>
          <div className="role-grid">
            {roles.map((r) => (
              <button
                key={r}
                className={`btn role-btn ${role === r ? 'selected' : ''}`}
                onClick={() => setRole(r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <p className="preview">
          {company && level && role
            ? `Preview: Prep for ${company} ${level} ${role}`
            : 'Please select all options to see your interview preview.'}
        </p>

        <button onClick={handleStart} className="start-btn" disabled={loading}>
          {loading ? 'Starting...' : 'Start Interview'}
        </button>
      </div>
    </div>
  );
};

export default SelectRole;
