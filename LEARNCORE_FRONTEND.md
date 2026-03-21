# LearnCore Frontend Documentation

## Overview

LearnCore is a modern AI-powered interactive learning platform with a clean, dark interface inspired by Claude.ai and ChatGPT. The frontend is built with React and integrates with your FastAPI backend.

## ✨ Features Implemented

### 🎨 Design
- **Dark Theme**: Clean, minimalist dark design (#0d0d0d, #141414, #111111)
- **Brand Colors**: Purple accent (#8885FF) with orange gradient (#FA9042)
- **Typography**: Geist font family for modern, readable text
- **Responsive Layout**: Two-column layout with fixed 264px sidebar
- **Animations**: Smooth transitions, fade-up animations, pulsing effects

### 🔐 Authentication
- **Login Page**: Email/password + Telegram OAuth button
- **Demo Mode**: Built-in demo credentials (demo@learncore.dev / demo)
- **Cookie-based Auth**: JWT access_token, refresh_token, CSRF protection
- **Protected Routes**: Automatic redirect to login if not authenticated

### 📚 Course Interface

#### Sidebar
- Course module tree with 6+ modules
- Collapsible module groups
- Module states: completed (✓ green), active (● purple), locked (🔒 gray)
- Lesson progress indicators: done (green dot), current (pulsing purple), upcoming (gray)
- User avatar with gradient and logout button
- Auto-expand active modules

#### Main Chat Area
- **Three Modes**:
  - 🎓 **Lecture**: Ask questions about lesson material
  - 📝 **Exam**: Answer AI questions to test knowledge
  - 💬 **Consultant**: Free-form discussion about course topics
- **Chat Interface**:
  - AI messages: Left-aligned, dark bubble (#1c1c1c), LC avatar with gradient
  - User messages: Right-aligned, purple bubble (#8885FF)
  - Markdown support: **bold**, `inline code`
  - Streaming responses with SSE support
  - Auto-scroll to bottom
  - Loading animation (3 bouncing dots)

#### Input Area
- Auto-expanding textarea (max 120px)
- Send button with hover effects
- Context-aware placeholders and hints
- Enter to send, Shift+Enter for new line

### 🔌 Backend Integration

The frontend is ready to integrate with your FastAPI backend. API client is configured for:

#### Auth Endpoints
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/register` - User registration
- `GET /api/auth/telegram/callback` - Telegram OAuth
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout (with CSRF)
- `POST /api/auth/refresh` - Refresh token

#### Course/Content Endpoints
- `GET /api/modules` - Get all modules with lessons
- `GET /api/modules/{id}` - Get specific module
- `GET /api/lessons/{id}` - Get lesson details
- `GET /api/lessons/{id}/content` - Get lesson content

#### Progress Endpoints
- `GET /api/progress` - Get user progress
- `GET /api/progress/stats` - Get progress statistics
- `POST /api/progress/lessons/{id}/complete` - Mark lesson complete

#### AI Chat Endpoints
- `POST /api/chat/lecture` - Lecture mode (supports SSE streaming)
- `POST /api/chat/exam/start` - Start exam session
- `POST /api/chat/exam/finish` - Finish exam and submit answer
- `POST /api/chat/consultant` - Consultant mode (supports SSE)
- `GET /api/chat/sessions` - Get chat sessions
- `GET /api/chat/sessions/{id}` - Get specific session

### 🎭 Mock Data & Fallback

The frontend includes mock data for demonstration when backend is not connected:
- 6 sample modules (Основы LLM, Промпт-инжиниринг, RAG-архитектура, etc.)
- Realistic lesson content in Russian
- Mock AI responses for chat interactions
- Automatic fallback from API errors to mock data

## 🚀 Demo Credentials

**Email**: `demo@learncore.dev`  
**Password**: `demo`

The demo account works without backend connection using localStorage flag.

## 📁 File Structure

```
/app/frontend/src/
├── pages/
│   ├── LoginPage.js          # Authentication page
│   └── MainPage.js            # Main learning interface
├── components/
│   ├── Sidebar.js             # Course module tree
│   ├── ChatArea.js            # Message display area
│   └── InputArea.js           # Message input with mode hints
├── context/
│   └── AuthContext.js         # Auth state management
├── utils/
│   ├── api.js                 # Axios client with CSRF handling
│   ├── sse.js                 # Server-Sent Events for streaming
│   └── mockData.js            # Demo data and fallback content
├── App.js                     # Main app with routing
├── index.js                   # Entry point
├── index.css                  # Global styles with Geist fonts
└── App.css                    # App-specific styles
```

## 🔧 Technical Details

### CSRF Protection
All state-changing requests automatically include `x-csrf-token` header from cookies.

### SSE Streaming
Lecture and Consultant modes support Server-Sent Events for real-time streaming responses:
- Parses `data: ` events
- Handles `[DONE]` completion signal
- Accumulates content chunks
- Graceful error handling with fallback to mock responses

### Cookie Management
- `withCredentials: true` for all API requests
- Automatic CSRF token extraction from cookies
- Session persistence across page reloads

### Responsive Design
- Desktop-first approach
- Fixed 264px sidebar
- Fluid main content area
- Gradient overlay (5% opacity) for subtle visual depth

### Animations
- Fade-up entrance for messages
- Pulsing logo dot and current lesson indicator
- Smooth transitions on hover/focus states
- Bouncing dots for loading state

## 🎨 Color System

```css
--deep-bg: #0d0d0d
--main-bg: #141414
--sidebar-bg: #111111
--elevated-bg: #1c1c1c
--accent-purple: #8885FF
--accent-orange: #FA9042
--success-green: #22c55e
--text-primary: #e5e5e5
--text-muted: #5a5a5a
--text-dim: #333333
--border: #222222
```

## 🔮 Next Steps for Backend Integration

1. **Replace Mock Data**: Once your backend is ready, the frontend will automatically use real API endpoints. Mock data serves as fallback only.

2. **Environment Variables**: Configure in `/app/frontend/.env`:
   ```
   REACT_APP_BACKEND_URL=https://your-domain.com
   REACT_APP_TELEGRAM_BOT_USERNAME=YourBotName
   ```

3. **Telegram OAuth**: Update the Telegram login flow in `LoginPage.js` with your bot's callback URL.

4. **CometAPI Provider**: The AI chat integration is ready for your CometAPI provider. Update streaming logic in `sse.js` and `MainPage.js` when you add the provider.

5. **Course Content**: Seed your database with course modules and lessons. Frontend expects:
   ```javascript
   {
     id: number,
     order: number,
     title: string,
     status: 'completed' | 'active' | 'locked',
     lessons: [{
       id: number,
       title: string,
       completed: boolean
     }]
   }
   ```

## 🎯 Testing

Demo mode allows full UI testing without backend:
- ✅ Authentication flow
- ✅ Module navigation
- ✅ Lesson selection
- ✅ Mode switching (Lecture/Exam/Consultant)
- ✅ Chat interactions
- ✅ Progress visualization
- ✅ User logout

## 📱 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+

## 🎓 User Flow

1. User visits `/login`
2. Enters credentials or clicks Telegram button
3. Redirected to `/` (main page)
4. Sidebar shows course structure with progress
5. First active lesson auto-loads
6. User switches between Lecture/Exam/Consultant modes
7. Interactive chat with AI for learning
8. Logout from sidebar footer

---

**Status**: ✅ Frontend Complete and Ready for Backend Integration

All endpoints are configured, CSRF handling is implemented, and the UI matches the design specification perfectly. The app gracefully handles backend unavailability with mock data for demonstration purposes.
