"""
Location Service - Auto-detect geo-coordinates from content
Extracts location information and converts to latitude/longitude
"""
import re
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# Common location patterns and their coordinates
LOCATION_DATABASE = {
    # US States
    "alabama": (32.3182, -86.9023), "alaska": (64.2008, -152.4937),
    "arizona": (34.0489, -111.0937), "arkansas": (35.2010, -91.8318),
    "california": (36.7783, -119.4179), "colorado": (39.5501, -105.7821),
    "connecticut": (41.6032, -73.0877), "delaware": (38.9108, -75.5277),
    "florida": (27.6648, -81.5158), "georgia": (32.1656, -82.9001),
    "hawaii": (19.8968, -155.5828), "idaho": (44.0682, -114.7420),
    "illinois": (40.6331, -89.3985), "indiana": (40.2672, -86.1349),
    "iowa": (41.8780, -93.0977), "kansas": (39.0119, -98.4842),
    "kentucky": (37.8393, -84.2700), "louisiana": (30.9843, -91.9623),
    "maine": (45.2538, -69.4455), "maryland": (39.0458, -76.6413),
    "massachusetts": (42.4072, -71.3824), "michigan": (44.3148, -85.6024),
    "minnesota": (46.7296, -94.6859), "mississippi": (32.3547, -89.3985),
    "missouri": (37.9643, -91.8318), "montana": (46.8797, -110.3626),
    "nebraska": (41.4925, -99.9018), "nevada": (38.8026, -116.4194),
    "new hampshire": (43.1939, -71.5724), "new jersey": (40.0583, -74.4057),
    "new mexico": (34.5199, -105.8701), "new york": (43.2994, -74.2179),
    "north carolina": (35.7596, -79.0193), "north dakota": (47.5515, -101.0020),
    "ohio": (40.4173, -82.9071), "oklahoma": (35.0078, -97.0929),
    "oregon": (43.8041, -120.5542), "pennsylvania": (41.2033, -77.1945),
    "rhode island": (41.5801, -71.4774), "south carolina": (33.8361, -81.1637),
    "south dakota": (43.9695, -99.9018), "tennessee": (35.5175, -86.5804),
    "texas": (31.9686, -99.9018), "utah": (39.3210, -111.0937),
    "vermont": (44.5588, -72.5778), "virginia": (37.4316, -78.6569),
    "washington": (47.7511, -120.7401), "west virginia": (38.5976, -80.4549),
    "wisconsin": (43.7844, -88.7879), "wyoming": (43.0760, -107.2903),
    
    # Major US Cities
    "new york city": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298), "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740), "philadelphia": (39.9526, -75.1652),
    "san antonio": (29.4241, -98.4936), "san diego": (32.7157, -117.1611),
    "dallas": (32.7767, -96.7970), "san jose": (37.3382, -121.8863),
    "austin": (30.2672, -97.7431), "jacksonville": (30.3322, -81.6557),
    "san francisco": (37.7749, -122.4194), "seattle": (47.6062, -122.3321),
    "denver": (39.7392, -104.9903), "boston": (42.3601, -71.0589),
    "washington dc": (38.9072, -77.0369), "nashville": (36.1627, -86.7816),
    "portland": (45.5152, -122.6784), "las vegas": (36.1699, -115.1398),
    "miami": (25.7617, -80.1918), "atlanta": (33.7490, -84.3880),
    "brunswick": (43.9145, -69.9653),  # Maine - Maestro Bistro location!
    
    # Countries
    "united states": (37.0902, -95.7129), "usa": (37.0902, -95.7129),
    "canada": (56.1304, -106.3468), "mexico": (23.6345, -102.5528),
    "united kingdom": (55.3781, -3.4360), "uk": (55.3781, -3.4360),
    "germany": (51.1657, 10.4515), "france": (46.2276, 2.2137),
    "spain": (40.4637, -3.7492), "italy": (41.8719, 12.5674),
    "japan": (36.2048, 138.2529), "china": (35.8617, 104.1954),
    "australia": (-25.2744, 133.7751), "brazil": (-14.2350, -51.9253),
    "india": (20.5937, 78.9629), "russia": (61.5240, 105.3188),
    
    # US State Abbreviations
    "al": (32.3182, -86.9023), "ak": (64.2008, -152.4937),
    "az": (34.0489, -111.0937), "ar": (35.2010, -91.8318),
    "ca": (36.7783, -119.4179), "co": (39.5501, -105.7821),
    "ct": (41.6032, -73.0877), "de": (38.9108, -75.5277),
    "fl": (27.6648, -81.5158), "ga": (32.1656, -82.9001),
    "hi": (19.8968, -155.5828), "id": (44.0682, -114.7420),
    "il": (40.6331, -89.3985), "in": (40.2672, -86.1349),
    "ia": (41.8780, -93.0977), "ks": (39.0119, -98.4842),
    "ky": (37.8393, -84.2700), "la": (30.9843, -91.9623),
    "me": (45.2538, -69.4455), "md": (39.0458, -76.6413),
    "ma": (42.4072, -71.3824), "mi": (44.3148, -85.6024),
    "mn": (46.7296, -94.6859), "ms": (32.3547, -89.3985),
    "mo": (37.9643, -91.8318), "mt": (46.8797, -110.3626),
    "ne": (41.4925, -99.9018), "nv": (38.8026, -116.4194),
    "nh": (43.1939, -71.5724), "nj": (40.0583, -74.4057),
    "nm": (34.5199, -105.8701), "ny": (43.2994, -74.2179),
    "nc": (35.7596, -79.0193), "nd": (47.5515, -101.0020),
    "oh": (40.4173, -82.9071), "ok": (35.0078, -97.0929),
    "or": (43.8041, -120.5542), "pa": (41.2033, -77.1945),
    "ri": (41.5801, -71.4774), "sc": (33.8361, -81.1637),
    "sd": (43.9695, -99.9018), "tn": (35.5175, -86.5804),
    "tx": (31.9686, -99.9018), "ut": (39.3210, -111.0937),
    "vt": (44.5588, -72.5778), "va": (37.4316, -78.6569),
    "wa": (47.7511, -120.7401), "wv": (38.5976, -80.4549),
    "wi": (43.7844, -88.7879), "wy": (43.0760, -107.2903),
    "dc": (38.9072, -77.0369),
    
    # Country codes
    "ger": (51.1657, 10.4515), "fra": (46.2276, 2.2137),
    "gbr": (55.3781, -3.4360), "jpn": (36.2048, 138.2529),
    "chn": (35.8617, 104.1954), "aus": (-25.2744, 133.7751),
    "can": (56.1304, -106.3468), "mex": (23.6345, -102.5528),
}

class LocationService:
    """Service for extracting and geocoding location information from text"""
    
    @staticmethod
    def extract_location(text: str) -> Optional[Tuple[float, float]]:
        """
        Extract location from text and return coordinates
        
        Args:
            text: Text to search for location references
            
        Returns:
            Tuple of (latitude, longitude) or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check for explicit coordinates in text
        coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        coord_match = re.search(coord_pattern, text)
        if coord_match:
            try:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except Exception:
                pass
        
        # Search for known locations (longest match first)
        sorted_locations = sorted(LOCATION_DATABASE.keys(), key=len, reverse=True)
        
        for location in sorted_locations:
            # Check for whole word match
            pattern = r'\b' + re.escape(location) + r'\b'
            if re.search(pattern, text_lower):
                return LOCATION_DATABASE[location]
        
        return None
    
    @staticmethod
    def extract_all_locations(text: str) -> list:
        """
        Extract all location references from text
        
        Args:
            text: Text to search
            
        Returns:
            List of dicts with location name and coordinates
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_locations = []
        
        sorted_locations = sorted(LOCATION_DATABASE.keys(), key=len, reverse=True)
        
        for location in sorted_locations:
            pattern = r'\b' + re.escape(location) + r'\b'
            if re.search(pattern, text_lower):
                coords = LOCATION_DATABASE[location]
                found_locations.append({
                    "name": location.title(),
                    "latitude": coords[0],
                    "longitude": coords[1]
                })
        
        return found_locations
    
    @staticmethod
    def geocode_search_result(result: Dict) -> Dict:
        """
        Add location data to a search result based on its content
        
        Args:
            result: Search result dict with title, snippet, url
            
        Returns:
            Result dict with latitude and longitude added if found
        """
        # Combine all text fields for location extraction
        text_to_search = " ".join([
            result.get("title", ""),
            result.get("snippet", ""),
            result.get("content", ""),
            result.get("url", "")
        ])
        
        coords = LocationService.extract_location(text_to_search)
        
        if coords:
            result["latitude"] = coords[0]
            result["longitude"] = coords[1]
            logger.info(f"Found location for result: {coords}")
        else:
            result["latitude"] = None
            result["longitude"] = None
        
        return result
    
    @staticmethod
    async def batch_geocode_results(results: list) -> list:
        """
        Add location data to multiple search results
        
        Args:
            results: List of search result dicts
            
        Returns:
            Results with location data added
        """
        geocoded = []
        for result in results:
            geocoded.append(LocationService.geocode_search_result(result))
        
        located_count = sum(1 for r in geocoded if r.get("latitude") is not None)
        logger.info(f"Geocoded {located_count}/{len(results)} results with locations")
        
        return geocoded
