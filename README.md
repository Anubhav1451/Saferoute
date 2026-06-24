# SafeRoute AI 🛡️

A cutting-edge AI-powered navigation system that prioritizes user safety through machine learning route analysis, crime data integration, and real-time emergency response features.

## 🌟 Features

### Core Navigation
- **AI Safety Routing Engine**: Custom A* algorithm with dynamic cost calculation
- **Dual Route Modes**: Safest route (weighted for safety) vs Fastest route (shortest distance)
- **Real-time Safety Metrics**: Live safety scores, lighting levels, crowd density analysis
- **AI Safety Prediction**: Machine learning model for location-based safety scoring

### 3D Visualization
- **Mapbox GL Integration**: Stunning 3D map with dark cyberpunk theme
- **3D Building Extrusion**: Immersive skyscraper visualization on zoom
- **Crime Heatmap Layer**: Glowing neon red/orange danger zones
- **Neon Route Display**: Dynamic green (safest) and cyan (fastest) route lines with glow effects

### Safety Features
- **Crime Hotspot Analysis**: High/Medium/Low severity zones with radius-based penalties
- **Safety Node Network**: Lighting level and crowd density tracking
- **User Report System**: Dynamic penalty calculation based on recent suspicious activity
- **SOS Emergency System**: One-click emergency alert with full-screen red overlay
- **AI Explainability**: Detailed risk factor breakdown and confidence scores

### Hackathon-Ready Demo
- **Quick Demo Mode**: Instant AI value demonstration for judges
- **30-Second Demo Flow**: Perfect judge presentation script
- **Demo Scenarios**: High Risk Area, Safe Corridor, and Quick Demo modes
- **Presentation Guide**: Complete talking points and Q&A preparation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Sidebar    │  │     Map      │  │   SOS Panel  │     │
│  │  (React/TS)  │  │  (Mapbox GL) │  │  (Emergency) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routing    │  │  AI/ML Model │  │     SOS      │     │
│  │   Service    │  │  (Scikit-learn)│  │   Service   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Database (SQLite)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Safety Nodes │  │Crime Hotspots│  │ User Reports │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Mapbox Access Token (get one at [mapbox.com](https://mapbox.com))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with mock data
python -m app.utils.generate_mock_data

# Start the server
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
# Edit .env.local and add your Mapbox token:
# NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
saferoute-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routing.py      # Route calculation endpoint
│   │   │       ├── sos.py          # SOS emergency endpoint
│   │   │       └── ai.py           # AI safety score endpoint
│   │   ├── db/
│   │   │   ├── models.py           # SQLAlchemy models
│   │   │   └── session.py          # Database session management
│   │   ├── services/
│   │   │   └── routing.py         # AI safety routing algorithm
│   │   ├── schemas/
│   │   │   ├── routing.py         # Pydantic schemas
│   │   │   └── sos.py             # SOS request schemas
│   │   ├── utils/
│   │   │   └── generate_mock_data.py  # Mock data generator
│   │   ├── core/
│   │   │   └── config.py          # Configuration management
│   │   └── main.py                # FastAPI application
│   ├── ml/
│   │   ├── safety_model.py        # ML model implementation
│   │   ├── feature_engineering.py # Feature extraction
│   │   └── train_model.py         # Model training
│   ├── requirements.txt
│   └── init_db.py                 # Database initialization
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Main application page
│   │   │   ├── layout.tsx         # Root layout
│   │   │   └── globals.css        # Global styles
│   │   └── components/
│   │       ├── Sidebar.tsx        # Glassmorphic sidebar with SOS
│   │       └── Map.tsx            # 3D Mapbox component
│   ├── package.json
│   ├── tailwind.config.ts
│   └── .env.local                 # Environment variables
├── HACKATHON_PRESENTATION.md      # Demo guide for judges
├── DEPLOYMENT.md                  # Deployment documentation
├── API_DOCUMENTATION.md           # API reference
└── README.md
```

## 🔧 API Endpoints

### Route Calculation
```http
POST /api/v1/calculate
Content-Type: application/json

{
  "source": {
    "latitude": 28.6315,
    "longitude": 77.2167
  },
  "destination": {
    "latitude": 28.6350,
    "longitude": 77.2200
  },
  "safety_weight": 0.7
}
```

### AI Safety Score
```http
GET /api/v1/ai/safety-score?latitude=28.6315&longitude=77.2167&radius=1000
```

### SOS Emergency Alert
```http
POST /api/v1/sos/trigger
Content-Type: application/json

{
  "latitude": 28.6315,
  "longitude": 77.2167,
  "timestamp": "2026-06-04T01:00:00Z"
}
```

### Health Check
```http
GET /health
```

## 🧠 AI/ML Pipeline

### Feature Engineering
- **Lighting Level Analysis**: Street light density and coverage
- **Crime Hotspot Detection**: Proximity to reported crime locations
- **Crowd Density Assessment**: Real-time crowd estimation
- **Historical Incident Data**: Past safety incidents in area
- **Time-based Factors**: Safety varies by time of day

### Model Architecture
- **Algorithm**: Random Forest Regressor
- **Features**: 15+ engineered safety features
- **Output**: Safety score between 0.0 (unsafe) and 1.0 (safe)
- **Confidence**: Model reliability metrics (87% average)
- **Fallback**: Rule-based system when AI unavailable

### Routing Algorithm
```
Cost = Distance + Safety Penalty

Safety Penalties:
- Crime Hotspots: HIGH (2500), MEDIUM (500), LOW (100)
- Low Lighting: 50
- Sparse Crowd: 30
- Recent User Reports: Dynamic (decays over time)
- AI Safety Score: Integrated into cost calculation
```

## 🎨 Design Philosophy

- **Cyberpunk Aesthetic**: Dark theme with neon accents
- **Glassmorphism**: Frosted glass UI elements
- **Smooth Animations**: Cinematic transitions with Framer Motion
- **3D Immersion**: Building extrusion and spatial visualization
- **Accessibility**: High contrast and clear visual hierarchy

## 🔐 Security Features

- CORS configuration for frontend-backend communication
- Environment variable management for sensitive data
- Input validation with Pydantic schemas
- SQL injection prevention with SQLAlchemy ORM
- Auto-generated SECRET_KEY for JWT tokens
- Health check endpoint for monitoring

## 📊 Mock Data

The system generates realistic mock data for Connaught Place, Delhi:
- 80 Safety Nodes with safety scores, lighting levels, and crowd density
- 15 Crime Hotspots with severity levels and radius
- 50 User Reports with various types and timestamps
- 50 Detour Nodes for alternative routing

## 🎯 Demo Instructions

### Quick Demo Mode (30-Second Judge Demo)
1. Click "Quick Demo Mode" button in the sidebar
2. Watch AI calculate optimal safe route
3. View safety score comparison (safest vs fastest)
4. See AI explainability panel with risk factors

### Demo Scenarios
- **High Risk Area**: Shows AI avoiding crime hotspots
- **Safe Corridor**: Demonstrates optimal safe routing
- **Quick Demo**: Instant AI value demonstration

See `HACKATHON_PRESENTATION.md` for complete demo script and talking points.

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Individual Docker Builds
```bash
# Backend
cd backend
docker build -t saferoute-backend .
docker run -p 8000:8000 saferoute-backend

# Frontend
cd frontend
docker build -t saferoute-frontend .
docker run -p 3000:3000 saferoute-frontend
```

See `DEPLOYMENT.md` for detailed deployment instructions.

## 📚 Documentation

- **API Documentation**: See `API_DOCUMENTATION.md` for complete API reference
- **Deployment Guide**: See `DEPLOYMENT.md` for production deployment
- **Hackathon Guide**: See `HACKATHON_PRESENTATION.md` for demo instructions
- **Interactive API Docs**: Available at `http://localhost:8000/docs` when backend is running

## 🚧 Future Enhancements

- Real-time GPS tracking
- User authentication and profiles
- Historical route analysis
- Integration with real emergency services APIs
- Mobile application (React Native)
- Multi-city support
- Real-time crowd-sourced safety reports
- Advanced ML model training with real data

## 🐛 Troubleshooting

### Common Issues

**Mapbox Token Error**
- Ensure `NEXT_PUBLIC_MAPBOX_TOKEN` is set in `frontend/.env.local`
- Get a free token at [mapbox.com](https://mapbox.com)

**Backend Connection Error**
- Verify backend is running on `http://localhost:8000`
- Check CORS configuration in `backend/app/main.py`
- Ensure database is initialized with mock data

**Port Conflicts**
- Frontend auto-selects available ports (3000-3006)
- Backend runs on port 8000 by default
- Modify ports in respective configuration files if needed

## 📝 License

This project is proprietary and confidential.

## 👥 Team

SafeRoute AI Development Team

## 📞 Support

For support and inquiries, contact the development team.

---

**Built with ❤️ for safer navigation**
