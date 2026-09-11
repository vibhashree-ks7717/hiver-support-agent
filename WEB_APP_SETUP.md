# 🌐 Web App Setup Guide

Create a beautiful web interface for your AI Support Agent.

---

## 📋 **What You Need**

1. `app.py` - Flask backend
2. `index.html` - Web interface
3. `response_database.json` - (already have this)

---

## 🚀 **Setup (5 minutes)**

### **Step 1: Install Flask**

```powershell
pip install flask
```

### **Step 2: Create Folder Structure**

In `C:\Users\User\support_agent\`, create:

```
support_agent/
├── app.py                          ← Download this
├── response_database.json          ← Already have
└── templates/
    └── index.html                  ← Download this
```

**How to create the templates folder:**

```powershell
cd C:\Users\User\support_agent
mkdir templates
```

### **Step 3: Put Files in Right Places**

- Download `app.py` → Put in `C:\Users\User\support_agent\`
- Download `index.html` → Put in `C:\Users\User\support_agent\templates\`

Verify:
```powershell
ls
# Should show: app.py, response_database.json, templates folder

ls templates\
# Should show: index.html
```

---

## ⚡ **Run the Web App**

```powershell
cd C:\Users\User\support_agent

python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
Press CTRL+C to quit
```

---

## 🌐 **Open in Browser**

1. **Open your browser**
2. **Go to:** `http://localhost:5000`
3. **Start chatting!**

---

## 💬 **What You Can Do**

Type customer messages and see:

- ✅ Intent classification
- ✅ AI-generated replies
- ✅ Escalation detection
- ✅ Confidence scores
- ✅ Processing time
- ✅ Live statistics

---

## 📊 **Dashboard Features**

**Left Sidebar Shows:**
- Total messages processed
- Auto-handled count
- Escalated count
- Average confidence
- Auto-handle rate

**Chat Interface Shows:**
- User message input
- Agent replies
- Intent classification
- Confidence percentage
- Escalation badge (if needed)
- Processing time

---

## 🎨 **Customize It**

### **Change Colors**

Edit `index.html` line 22:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

Change `#667eea` and `#764ba2` to any hex colors.

### **Change Brand Name**

Edit `app.py` line 125:
```python
agent = SupportAgent('response_database.json', brand_name='Support')
```

Change `'Support'` to your brand name.

### **Add More Test Messages**

Edit `index.html` line 297:
```html
<p style="font-size: 12px; margin-top: 10px; color: #bbb;">Try: "Where is my order?" or "I want to return this product"</p>
```

---

## 🔧 **Troubleshooting**

### **Error: "Module 'flask' not found"**

```powershell
pip install flask
```

### **Error: "Address already in use"**

Flask is already running. Kill it:
```powershell
# Close all PowerShell windows and try again
```

Or use different port:
```python
# In app.py, change last line:
app.run(debug=True, port=5001)  # Changed to 5001
```

Then open: `http://localhost:5001`

### **Error: "TemplateNotFound: index.html"**

The file is in wrong place. Must be:
```
C:\Users\User\support_agent\templates\index.html
```

Not: `C:\Users\User\support_agent\index.html`

### **Connection Refused**

Make sure Flask is running:
```powershell
# You should see: Running on http://127.0.0.1:5000
```

---

## 📱 **Mobile Support**

Works on phones! Open:
- `http://[your-computer-ip]:5000`

Get your IP:
```powershell
ipconfig
# Look for "IPv4 Address"
```

Then on phone browser:
```
http://192.168.x.x:5000
```

---

## 🚀 **Next: Deploy to Cloud**

Once it works locally, deploy to:

**Free Options:**
- Heroku (free tier ended, but $7/month now)
- PythonAnywhere (free tier available)
- Replit (free)
- Railway (free tier)

**Production Options:**
- AWS
- Google Cloud
- Microsoft Azure

---

## 📝 **API Endpoints**

The backend has two endpoints:

### **POST /api/chat**
Send a customer message
```
Request: { "message": "Where is my order?" }
Response: {
  "success": true,
  "intent": "Order Status",
  "confidence": 90,
  "reply": "Thank you! Could you...",
  "escalate": false,
  "processing_time_ms": 0.15
}
```

### **GET /api/stats**
Get statistics
```
Response: {
  "total_messages": 5,
  "auto_handled": 4,
  "escalated": 1,
  "auto_handle_rate": 80.0,
  "avg_confidence": 88.0
}
```

---

## ✅ **Checklist**

- [ ] Downloaded `app.py`
- [ ] Downloaded `index.html`
- [ ] Created `templates/` folder
- [ ] Put `index.html` in `templates/` folder
- [ ] Installed Flask: `pip install flask`
- [ ] Run: `python app.py`
- [ ] Opened: `http://localhost:5000`
- [ ] Can see chat interface
- [ ] Can send messages
- [ ] Gets replies
- [ ] Stats update

---

**You now have a working web app!** 🎉

Test it, customize it, and prepare to deploy!
