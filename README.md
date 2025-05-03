# AI Mock Interviewer

An interactive mock interview app built using FastAPI (backend) and React + Vite (frontend). It uses GPT-based feedback generation and dynamic question flow.

---

## 🔧 Project Setup Instructions

### 📁 Clone the Repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>


#Backend Setup (FastAPI)
cd backend
python -m venv venv
source venv/bin/activate            # or venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
#Visit API: http://127.0.0.1:8000/docs

#Frontend Setup (React + Vite)
cd frontend
npm install --legacy-peer-deps
npm run dev
#App will be available at: http://localhost:5173

##Troubleshooting (Clean Install)
#If facing module import errors: (frontend)

rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
