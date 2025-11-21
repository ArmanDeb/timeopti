# TimeOpti - AI-Powered Agenda Optimizer

TimeOpti is an AI-first SaaS application that helps users optimize their daily schedules by intelligently matching tasks to available calendar gaps.

## Features

- 🤖 **AI-Powered Optimization**: Uses GPT-4 for intelligent task prioritization and scheduling
- 📅 **Google Calendar Integration**: Automatically fetches your calendar events and finds available time slots
- 🎯 **Smart Matching Algorithm**: Priority-based task-to-gap matching with efficiency scoring
- 📊 **Admin Dashboard**: Real-time monitoring of system usage, API calls, and user activity
- 🔐 **Secure Authentication**: Clerk-based user management with OAuth support
- 💾 **Database Logging**: Complete audit trail of all AI interactions

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Production database (SQLite for local dev)
- **SQLAlchemy + Alembic**: ORM and migrations
- **OpenAI/OpenRouter**: AI service integration
- **Google Calendar API**: Calendar integration
- **Clerk**: Authentication and user management

### Frontend
- **Angular 18**: Standalone components architecture
- **Clerk Angular SDK**: Client-side authentication
- **TypeScript**: Type-safe development
- **RxJS**: Reactive programming

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (for production) or SQLite (auto-configured for local dev)
- Google Cloud Project with Calendar API enabled
- Clerk account
- OpenAI or OpenRouter API key

### Backend Setup

1. **Clone the repository**
   ```bash
   cd timeopti/backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create `.env` file in `backend/` directory:
   ```env
   # AI Service (choose one)
   OPENAI_API_KEY=your_openai_key
   # OR
   OPENROUTER_API_KEY=your_openrouter_key
   
   # Database (optional - defaults to SQLite)
   DATABASE_URL=postgresql://user:password@host:port/dbname
   
   # Clerk Authentication
   CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
   ```

5. **Set up Google Calendar API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials (Desktop app type)
   - Download credentials and save as `google_credentials.json` in `backend/` directory

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd timeopti/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   Create `src/environments/environment.ts`:
   ```typescript
   export const environment = {
     production: false,
     apiUrl: 'http://localhost:8000',
     clerkPublishableKey: 'your_clerk_publishable_key'
   };
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Open the app**
   Navigate to `http://localhost:4200`

## Usage

### For End Users

1. **Sign In**: Click "Sign In" and authenticate with Clerk (Google, email, etc.)

2. **Connect Google Calendar**:
   - Go to settings or calendar integration page
   - Click "Connect Google Calendar"
   - Authorize calendar access

3. **Add Tasks**:
   - Enter your tasks with:
     - Title
     - Duration (in minutes)
     - Priority (high/medium/low)
     - Optional deadline

4. **Optimize Schedule**:
   - Click "Smart Optimize"
   - View your optimized schedule
   - See which tasks fit in which calendar gaps
   - Get AI-powered explanations for scheduling decisions

5. **Export Schedule**:
   - Export to Google Calendar
   - Download as iCal
   - Copy as text

### For Admins

Access the admin dashboard at `/admin` to view:
- System statistics (total users, API calls, recommendations)
- Recent API logs with timing and error tracking
- User list with usage metrics
- AI-generated recommendations history

## API Endpoints

### AI Optimization
- `POST /optimize` - Basic AI agenda optimization
- `POST /smart-optimize` - Smart optimization with calendar integration
- `POST /analyze/gaps` - Analyze calendar gaps
- `POST /analyze/priorities` - Get priority recommendations

### Google Calendar
- `POST /calendar/auth-url` - Get OAuth authorization URL
- `POST /calendar/exchange-token` - Exchange auth code for tokens
- `POST /calendar/events` - Fetch calendar events

### Admin (requires admin role)
- `GET /admin/stats` - System statistics
- `GET /admin/logs` - Recent API logs
- `GET /admin/users` - User list with metrics
- `GET /admin/recommendations` - Recent AI recommendations

## Architecture

### Smart Matching Algorithm

The core matching algorithm uses a hybrid approach:

1. **Gap Detection**: Analyzes calendar events to find free time slots
2. **Task Prioritization**: Sorts tasks by priority and deadline
3. **Fit Scoring**: Calculates how well each task fits each gap based on:
   - Efficiency (minimize wasted time)
   - Priority weight
   - Time of day preferences
4. **Greedy Assignment**: Assigns high-priority tasks to optimal gaps first
5. **AI Explanation**: Generates human-readable reasoning

### Database Models

- **User**: Clerk ID, email, admin status, calendar tokens
- **AILog**: Request/response tracking, duration, errors
- **Recommendation**: AI-generated schedule suggestions

## Development

### Running Tests
```bash
# Backend
cd backend
python test_matching.py  # Test matching algorithm

# Frontend
cd frontend
npm test
```

### Making Changes

1. Create a feature branch
2. Make your changes
3. Run tests
4. Create pull request

## Deployment

### Backend (Render)
1. Push to GitHub
2. Connect repository to Render
3. Set environment variables
4. Deploy

### Frontend (Netlify)  
1. Build: `npm run build`
2. Deploy `dist/` folder
3. Set environment variables
4. Configure redirects for Angular routing

## License

MIT

## Contributing

Contributions welcome! Please read our contributing guidelines first.

## Support

For issues or questions, please open a GitHub issue or contact support@timeopti.com
