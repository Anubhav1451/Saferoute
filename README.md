# SafeRoute AI 🛡️

A cutting-edge 3D intelligent navigation system that prioritizes user safety through AI-powered route analysis, crime data integration, and real-time emergency response features.

## 🌟 Features

### Core Navigation
- **AI Safety Routing Engine**: Custom A* algorithm with dynamic cost calculation
- **Dual Route Modes**: Safest route (weighted for safety) vs Fastest route (shortest distance)
- **Real-time Safety Metrics**: Live safety scores, lighting levels, crowd density analysis

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

### Technology Stack

#### Backend
- **FastAPI**: High-performance Python web framework
- **SQLAlchemy**: Advanced ORM with GeoAlchemy2 for spatial data
- **Custom A* Algorithm**: Dynamic cost calculation with safety penalties
- **SQLite/PostgreSQL**: Flexible database support with PostGIS for geospatial queries

#### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first CSS with custom cyberpunk theme
- **Mapbox GL**: 3D mapping and visualization
- **Framer Motion**: Smooth cinematic animations
- **Lucide React**: Modern icon library

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
│   │   │   └── routes.py          # API endpoints (route calculation, SOS)
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   └── session.py         # Database session management
│   │   ├── services/
│   │   │   └── routing.py         # AI safety routing algorithm
│   │   ├── schemas/
│   │   │   └── routing.py         # Pydantic schemas
│   │   ├── utils/
│   │   │   └── generate_mock_data.py  # Mock data generator
│   │   └── main.py                # FastAPI application
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
└── README.md
```

## 🔧 API Endpoints

### Route Calculation
```http
POST /api/v1/route/calculate
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

### SOS Emergency Alert
```http
POST /api/v1/route/sos/trigger
Content-Type: application/json

{
  "latitude": 28.6315,
  "longitude": 77.2167,
  "timestamp": "2026-06-04T01:00:00Z"
}
```

## 🧠 Routing Algorithm

The custom safety routing algorithm calculates dynamic cost for each path segment:

```
Cost = Distance + Penalty

Penalties:
- Crime Hotspots: HIGH (500), MEDIUM (250), LOW (100)
- Low Lighting: 50
- Sparse Crowd: 30
- Recent User Reports: Dynamic (decays over time)
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

## 📊 Mock Data

The system generates realistic mock data for Connaught Place, Delhi:
- 80 Safety Nodes with safety scores, lighting levels, and crowd density
- 15 Crime Hotspots with severity levels and radius
- 50 User Reports with various types and timestamps

## 🚧 Future Enhancements

- Real-time GPS tracking
- User authentication and profiles
- Historical route analysis
- Machine learning model for predictive safety scoring
- Integration with real emergency services APIs
- Mobile application (React Native)
- Multi-city support

## 📝 License

This project is proprietary and confidential.

## 👥 Team

SafeRoute AI Development Team

## 📞 Support

For support and inquiries, contact the development team.

---

**Built with ❤️ for safer navigation**
