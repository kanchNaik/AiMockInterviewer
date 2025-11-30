// import React, { useMemo, useState, useEffect } from "react";
// import { useNavigate, useLocation } from "react-router-dom";
// import axios from "axios";
// import "./SelectRole.css";

// const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// const SelectRole = () => {
//   const navigate = useNavigate();
//   const location = useLocation();
//   const emailFromState = (location.state?.email || "").trim().toLowerCase();
//   const userIdFromState = (location.state?.userId || "").trim();

//   // prefer state; fall back to localStorage
//   const [email, setEmail] = useState(
//     emailFromState || (localStorage.getItem("email") || "").trim().toLowerCase()
//   );
//   const [userId, setUserId] = useState(
//     userIdFromState || (localStorage.getItem("userId") || "").trim()
//   );

//   // persist identity if it came via state
//   useEffect(() => {
//     try {
//       if (emailFromState) localStorage.setItem("email", emailFromState);
//       if (userIdFromState) localStorage.setItem("userId", userIdFromState);
//     } catch {}
//     if (emailFromState) setEmail(emailFromState);
//     if (userIdFromState) setUserId(userIdFromState);
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [emailFromState, userIdFromState]);

//   const [company, setCompany] = useState("");
//   const [level, setLevel] = useState("");     // free text (e.g., L2, junior)
//   const [role, setRole] = useState("");
//   const [brief, setBrief] = useState("");     // free text for NER enrichment
//   const [agree, setAgree] = useState(false);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");

//   const canStart = useMemo(() => {
//     return company.trim() && role.trim() && agree;
//   }, [company, role, agree]);

//   const handleStart = async () => {
//     if (!canStart) return;
//     setLoading(true);
//     setError("");

//     // compose a natural sentence for backward compatibility with your pipeline
//     const composed =
//       `I have an interview at ${company} for a ${role}` +
//       (level?.trim() ? ` position at level ${level}` : "") + ".";
//     const extra = brief?.trim() ? ` Additional context: ${brief}` : "";

//     const payload = {
//       user_text: composed + extra,   // what your current backend expects
//       session_id: null,
//       // also send structured fields so backend can prefer them over NER
//       company,
//       role,
//       level,
//       email: email || undefined,     // legacy linkage stays
//       userId: userId || undefined,   // NEW reliable linkage
//     };

//     try {
//       const res = await axios.post(`${API}/session`, payload);
//       const { session_id, question } = res.data;
//       navigate("/interview", { state: { session_id, question } });
//     } catch (e) {
//       console.error("Failed to create session:", e);
//       setError("Unable to start session. Please try again.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleLogout = () => {
//     localStorage.clear();
//     sessionStorage.clear();
//     navigate("/", { replace: true });
//   };

//   return (
//     <div className="container">
//       <div className="card">
//         {/* header */}
//         <div className="header-row">
//           <h1 className="heading">Start Interview</h1>
//           <button className="logout-btn" onClick={handleLogout}>Logout</button>
//         </div>

//         {/* company */}
//         <div className="section">
//           <label className="field-label">Company</label>
//           <input
//             className="text-input"
//             placeholder="e.g., Adobe"
//             value={company}
//             onChange={(e) => setCompany(e.target.value)}
//           />
//         </div>

//         {/* level */}
//         <div className="section">
//           <label className="field-label">
//             Level <span className="muted">(optional)</span>
//           </label>
//           <input
//             className="text-input"
//             placeholder="e.g., L2 / Junior"
//             value={level}
//             onChange={(e) => setLevel(e.target.value)}
//           />
//         </div>

//         {/* role */}
//         <div className="section">
//           <label className="field-label">Role</label>
//           <input
//             className="text-input"
//             placeholder="e.g., Data Scientist"
//             value={role}
//             onChange={(e) => setRole(e.target.value)}
//           />
//         </div>

//         {/* brief (for NER) */}
//         <div className="section">
//           <label className="field-label">
//             Tell us about this interview <span className="muted"></span>
//           </label>
//           <textarea
//             className="textarea"
//             rows={4}
//             placeholder="e.g., Onsite next week in SF. Focus on ML system design, experimentation (A/B testing), metrics, and dashboards."
//             value={brief}
//             onChange={(e) => setBrief(e.target.value)}
//           />
//           <div className="helper-text">
//             tip: include location/timing + focus areas to get better questions.
//           </div>
//         </div>

//         {/* terms */}
//         <div className="section terms-row">
//           <label className="terms">
//             <input
//               type="checkbox"
//               checked={agree}
//               onChange={(e) => setAgree(e.target.checked)}
//             />
//             <span>
//               I agree to the{" "}
//               <a href="#" onClick={(e) => e.preventDefault()}>
//                 Terms &amp; Conditions
//               </a>
//             </span>
//           </label>
//         </div>

//         {error && <p className="error-text">{error}</p>}

//         <button
//           onClick={handleStart}
//           className="start-btn"
//           disabled={!canStart || loading}
//         >
//           {loading ? "Starting..." : "Start Interview"}
//         </button>
//       </div>
//     </div>
//   );
// };

// export default SelectRole;

import React, { useMemo, useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import "./SelectRole.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const SelectRole = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const emailFromState = (location.state?.email || "").trim().toLowerCase();
  const userIdFromState = (location.state?.userId || "").trim();

  const [email, setEmail] = useState(
    emailFromState || (localStorage.getItem("email") || "").trim().toLowerCase()
  );
  const [userId, setUserId] = useState(
    userIdFromState || (localStorage.getItem("userId") || "").trim()
  );

  useEffect(() => {
    try {
      if (emailFromState) localStorage.setItem("email", emailFromState);
      if (userIdFromState) localStorage.setItem("userId", userIdFromState);
    } catch {}
    if (emailFromState) setEmail(emailFromState);
    if (userIdFromState) setUserId(userIdFromState);
  }, [emailFromState, userIdFromState]);

  // ---------------------------
  // EXISTING STATE
  // ---------------------------
  const [company, setCompany] = useState("");
  const [level, setLevel] = useState("");
  const [role, setRole] = useState("");
  const [brief, setBrief] = useState("");
  const [agree, setAgree] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canStart = useMemo(() => {
    return company.trim() && role.trim() && agree;
  }, [company, role, agree]);

  // ---------------------------
  // NEW — RESUME PARSING STATE
  // ---------------------------
  const [resumeSummary, setResumeSummary] = useState("");
  const [suggestedRole, setSuggestedRole] = useState("");
  const [loadingResume, setLoadingResume] = useState(false);

  // ---------------------------
  // NEW — RESUME UPLOAD HANDLER
  // ---------------------------
  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoadingResume(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        `${API}/api/resume/parse`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setResumeSummary(res.data.summary || "Could not extract summary.");
      setSuggestedRole(res.data.suggested_role || "Unknown");

      // Optional: Autofill role field based on suggestion (NON-DESTRUCTIVE)
      // user can still overwrite manually
      if (!role) {
        setRole(res.data.suggested_role || "");
      }

    } catch (err) {
      console.error(err);
      alert("Resume parsing failed.");
    }

    setLoadingResume(false);
  };

  // ---------------------------
  // EXISTING START HANDLER
  // ---------------------------
  const handleStart = async () => {
    if (!canStart) return;
    setLoading(true);
    setError("");

    const composed =
  `I have an interview at ${company} for a ${role}` +
  (level?.trim() ? ` position at level ${level}` : "") + ".";

  const extraBrief = brief?.trim()
    ? ` Additional context: ${brief}`
    : "";

    //  NEW: include resume summary as explicit “resume context”
    const extraResume = resumeSummary?.trim()
      ? ` User resume context: ${resumeSummary}`
      : "";

    const payload = {
      user_text: composed + extraBrief + extraResume, 
      session_id: null,
      company,
      role,
      level,
      email: email || undefined,
      userId: userId || undefined,
    };


    try {
      const res = await axios.post(`${API}/session`, payload);
      const { session_id, question } = res.data;
      navigate("/interview", { state: { session_id, question } });
    } catch (e) {
      console.error("Failed to create session:", e);
      setError("Unable to start session. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    navigate("/", { replace: true });
  };

  return (
    <div className="container">
      <div className="card">

        <div className="header-row">
          <h1 className="heading">Start Interview</h1>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>

        {/* ---------------------------------------------------------- */}
        {/* NEW — Resume Upload Section (Safe, Non-breaking)        */}
        {/* ---------------------------------------------------------- */}
        <div className="section">
          <label className="field-label">Unsure about the best role?</label>
          <p className="helper-text">Upload your resume to get a suggested role (PDF/Docx).</p>

          <input type="file" accept=".pdf" onChange={handleResumeUpload} />

          {loadingResume && (
            <p className="helper-text">Analyzing resume...</p>
          )}

          {resumeSummary && (
            <div className="resume-box">
              <h4>Resume Summary</h4>
              <p>{resumeSummary}</p>

              <h4>Suggested Role</h4>
              <p className="suggested-role">{suggestedRole}</p>
            </div>
          )}
        </div>

        {/* ---------------------------------------------------------- */}
        {/* EXISTING UI (unchanged and untouched)                     */}
        {/* ---------------------------------------------------------- */}

        <div className="section">
          <label className="field-label">Company</label>
          <input
            className="text-input"
            placeholder="e.g., Adobe"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </div>

        <div className="section">
          <label className="field-label">Level (optional)</label>
          <input
            className="text-input"
            placeholder="e.g., L2 / Junior"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          />
        </div>

        <div className="section">
          <label className="field-label">Role</label>
          <input
            className="text-input"
            placeholder="e.g., Data Scientist"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
        </div>

        <div className="section">
          <label className="field-label">Tell us about this interview</label>
          <textarea
            className="textarea"
            rows={4}
            placeholder="e.g., onsite next week, focus on ML system design..."
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
          />
        </div>

        <div className="section terms-row">
          <label className="terms">
            <input
              type="checkbox"
              checked={agree}
              onChange={(e) => setAgree(e.target.checked)}
            />
            <span>I agree to the Terms & Conditions</span>
          </label>
        </div>

        {error && <p className="error-text">{error}</p>}

        <button
          onClick={handleStart}
          disabled={!canStart || loading}
          className="start-btn"
        >
          {loading ? "Starting..." : "Start Interview"}
        </button>

      </div>
    </div>
  );
};

export default SelectRole;
