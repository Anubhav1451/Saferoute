import random
import math
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel

# Connaught Place, Delhi coordinates (central area)
CENTER_LAT = 28.6315
CENTER_LON = 77.2167
# Spread radius in degrees (approx 1-2 km area)
LAT_SPREAD = 0.015
LON_SPREAD = 0.015

# Database configuration (SQLite for now)
DATABASE_URL = "sqlite:///./saferoute.db"


def generate_random_coordinate():
    """Generate a random coordinate near Connaught Place, Delhi"""
    lat = CENTER_LAT + random.uniform(-LAT_SPREAD, LAT_SPREAD)
    lon = CENTER_LON + random.uniform(-LON_SPREAD, LON_SPREAD)
    return lat, lon


def generate_safety_nodes(count=80):
    """Generate mock safety nodes"""
    nodes = []
    for _ in range(count):
        lat, lon = generate_random_coordinate()
        safety_score = random.uniform(0.3, 0.95)  # Higher is safer
        lighting_level = random.choice(list(LightingLevel))
        crowd_density = random.choice(list(CrowdDensity))
        
        node = SafetyNode(
            latitude=lat,
            longitude=lon,
            safety_score=safety_score,
            lighting_level=lighting_level,
            crowd_density=crowd_density,
            updated_at=datetime.utcnow()
        )
        nodes.append(node)
    return nodes


def generate_safe_detour_nodes(hotspots, detour_radius=0.003, nodes_per_hotspot=5):
    """Generate safe detour nodes around crime hotspots for alternate routing"""
    detour_nodes = []
    
    for hotspot in hotspots:
        if hotspot.severity == SeverityLevel.HIGH:
            # Generate safe detour nodes around high-severity hotspots
            for i in range(nodes_per_hotspot):
                angle = (2 * math.pi * i) / nodes_per_hotspot
                # Place nodes at detour_radius distance from hotspot center
                detour_lat = hotspot.latitude + detour_radius * math.cos(angle)
                detour_lon = hotspot.longitude + detour_radius * math.sin(angle)
                
                # Ensure detour nodes have high safety scores
                node = SafetyNode(
                    latitude=detour_lat,
                    longitude=detour_lon,
                    safety_score=random.uniform(0.85, 0.98),  # Very safe
                    lighting_level=LightingLevel.HIGH,  # Well-lit
                    crowd_density=CrowdDensity.HIGH,  # Well-populated
                    updated_at=datetime.utcnow()
                )
                detour_nodes.append(node)
    
    return detour_nodes


def generate_crime_hotspots(count=15):
    """Generate mock crime hotspots"""
    hotspots = []
    descriptions = [
        "Theft incidents reported",
        "Assault cases in area",
        "Vandalism reported",
        "Robbery hotspot",
        "Harassment complaints",
        "Pickpocketing area",
        "Suspicious activity zone",
        "Vehicle theft reported"
    ]
    
    for _ in range(count):
        lat, lon = generate_random_coordinate()
        radius = random.uniform(50, 300)  # 50-300 meters
        severity = random.choice(list(SeverityLevel))
        description = random.choice(descriptions)
        
        hotspot = CrimeHotspot(
            latitude=lat,
            longitude=lon,
            radius=radius,
            severity=severity,
            description=description
        )
        hotspots.append(hotspot)
    return hotspots


def generate_user_reports(count=50):
    """Generate mock user reports"""
    report_types = [
        "SUSPICIOUS_ACTIVITY",
        "NO_STREETLIGHTS",
        "POOR_ROAD_CONDITION",
        "OVERGROWN_VEGETATION",
        "BROKEN_STREETLIGHT",
        "DARK_AREA",
        "UNSAFE_PATH",
        "LACK_OF_SECURITY"
    ]
    
    reports = []
    for _ in range(count):
        lat, lon = generate_random_coordinate()
        report_type = random.choice(report_types)
        # Random timestamp within last 30 days
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        is_active = random.choice([True, True, True, False])  # 75% active
        
        report = UserReport(
            latitude=lat,
            longitude=lon,
            report_type=report_type,
            timestamp=timestamp,
            is_active=is_active
        )
        reports.append(report)
    return reports


def generate_mock_data():
    """Generate and insert all mock data into the database"""
    print("Creating database engine...")
    engine = create_engine(DATABASE_URL, echo=True)
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Creating session...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("Generating safety nodes...")
        safety_nodes = generate_safety_nodes(80)
        session.add_all(safety_nodes)
        print(f"Added {len(safety_nodes)} safety nodes")
        
        print("Generating crime hotspots...")
        crime_hotspots = generate_crime_hotspots(15)
        session.add_all(crime_hotspots)
        print(f"Added {len(crime_hotspots)} crime hotspots")
        
        print("Generating safe detour nodes around high-severity hotspots...")
        detour_nodes = generate_safe_detour_nodes(crime_hotspots)
        session.add_all(detour_nodes)
        print(f"Added {len(detour_nodes)} safe detour nodes")
        
        print("Generating user reports...")
        user_reports = generate_user_reports(50)
        session.add_all(user_reports)
        print(f"Added {len(user_reports)} user reports")
        
        print("Committing changes...")
        session.commit()
        print("Mock data generation completed successfully!")
        
        print("\nSummary:")
        print(f"- Safety Nodes: {len(safety_nodes)}")
        print(f"- Crime Hotspots: {len(crime_hotspots)}")
        print(f"- Safe Detour Nodes: {len(detour_nodes)}")
        print(f"- User Reports: {len(user_reports)}")
        print(f"- Total Records: {len(safety_nodes) + len(crime_hotspots) + len(detour_nodes) + len(user_reports)}")
        
    except Exception as e:
        print(f"Error generating mock data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    generate_mock_data()
