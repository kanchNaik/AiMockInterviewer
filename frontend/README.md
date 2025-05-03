# AI Mock Interviewer – Frontend (React + Vite + Tailwind)

This is the frontend of the AI Mock Interviewer app built using **React 19**, **Vite**, and **Tailwind CSS v4**.

---

## 🚀 How to Run (After Cloning from GitHub)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name/frontend
### 2. Ensure Node.js is Installed
#Recommended version: Node.js v18

#Check with:

node -v
npm -v
#If not installed, download from: https://nodejs.org/ or use 
nvm install 18
### 3. Install Dependencies
npm install --legacy-peer-deps
#✅ Axios and all other required packages are already listed in package.json.This command installs everything needed for the frontend.

### 4. Start the Dev Server

npm run dev

#App will be available at: http://localhost:5173
-----------------------------------------------------------------------------------

###  Clean Previous Install (if error faced for Import / SyntaxError (e.g. Cannot use import outside module))

        rm -rf node_modules package-lock.json
        #Install Dependencies

        npm install --legacy-peer-deps


🧰 Tailwind Setup Checklist--the file already added in the frontend folder
Make sure your main CSS file includes:

@tailwind base;
@tailwind components;
@tailwind utilities;
Ensure the following files exist:

tailwind.config.js

postcss.config.js

And confirm your CSS is imported in main.jsx.

✅ Stack Used
React 19

Vite

Tailwind CSS v4

React Router DOM

React Icons

❗ Troubleshooting
Tailwind not working?
Restart the dev server

Ensure all config files are present and correct

Use npm install with --legacy-peer-deps

Getting import/module errors?
Check that "type": "module" exists in package.json

Use correct Node.js version (v18)

📄 License
MIT License — free to use or modify