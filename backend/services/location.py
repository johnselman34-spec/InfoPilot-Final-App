"""
Location extraction service for InfoPilot Explorer
"""
import re
from typing import List, Dict


class LocationExtractor:
    """Extract location information from text with enhanced geolocation support"""
    
    US_STATES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming"
    ]
    
    # State abbreviations
    STATE_ABBREV = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
    }
    
    COUNTRIES = [
        "United States", "USA", "UK", "United Kingdom", "Canada", "Australia",
        "Germany", "France", "Italy", "Spain", "Japan", "China", "India",
        "Brazil", "Mexico", "Russia", "South Korea", "Netherlands", "Sweden",
        "Switzerland", "Nicaragua", "Costa Rica", "Panama", "Ireland", "Scotland",
        "Norway", "Denmark", "Finland", "Belgium", "Austria", "Portugal",
        "Greece", "Poland", "Czech Republic", "Hungary", "Romania", "Ukraine",
        "Turkey", "Israel", "Egypt", "South Africa", "Argentina", "Chile",
        "Colombia", "Peru", "Venezuela", "Cuba", "Puerto Rico", "Philippines",
        "Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore", "New Zealand",
        "Honduras", "Guatemala", "El Salvador", "Belize", "Ecuador", "Bolivia",
        "Paraguay", "Uruguay", "Jamaica", "Haiti", "Dominican Republic",
        "Kenya", "Nigeria", "Ghana", "Tanzania", "Ethiopia", "Morocco", "Algeria",
        "Tunisia", "Libya", "Sudan", "Congo", "Cameroon", "Zimbabwe", "Zambia"
    ]
    
    # Major US cities
    MAJOR_US_CITIES = [
        "New York City", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
        "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City",
        "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore",
        "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Mesa",
        "Sacramento", "Atlanta", "Kansas City", "Colorado Springs", "Miami",
        "Raleigh", "Omaha", "Long Beach", "Virginia Beach", "Oakland",
        "Minneapolis", "Tulsa", "Tampa", "Arlington", "New Orleans",
        "Brunswick", "Bath", "Bangor", "Augusta", "Lewiston",  # Maine cities
        "Honolulu", "Anchorage", "Salt Lake City", "Boise", "Richmond",
        "Newark", "Jersey City", "Trenton", "Camden", "Hartford", "New Haven",
        "Providence", "Worcester", "Springfield", "Buffalo", "Rochester",
        "Syracuse", "Albany", "Yonkers", "Pittsburgh", "Erie", "Scranton"
    ]
    
    # International cities by country
    INTERNATIONAL_CITIES = {
        "Nicaragua": ["Managua", "León", "Granada", "Masaya", "Chinandega", "Matagalpa", 
                      "Estelí", "Tipitapa", "Virgin Bay", "San Juan del Sur", "Bluefields",
                      "Puerto Cabezas", "Jinotega", "Rivas", "Corinto"],
        "Costa Rica": ["San José", "Limón", "Alajuela", "Heredia", "Cartago", "Puntarenas"],
        "Panama": ["Panama City", "Colón", "David", "Santiago", "Chitré"],
        "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Tijuana", "Cancún", "Puebla",
                   "León", "Juárez", "Mérida", "Acapulco", "Veracruz", "Oaxaca"],
        "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton",
                   "Winnipeg", "Quebec City", "Halifax", "Victoria", "Saskatoon"],
        "UK": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Edinburgh",
               "Bristol", "Leeds", "Sheffield", "Newcastle", "Belfast", "Cardiff"],
        "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart",
                    "Düsseldorf", "Leipzig", "Dresden", "Hanover"],
        "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Bordeaux"],
        "Italy": ["Rome", "Milan", "Naples", "Turin", "Florence", "Venice", "Bologna"],
        "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Málaga"],
        "Japan": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya", "Sapporo", "Fukuoka"],
        "China": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hong Kong", "Chengdu"],
        "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata"],
        "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"],
        "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra"],
        "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata"],
        "South Africa": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth"]
    }
    
    # Regional descriptors
    REGIONAL_PREFIXES = ["Northern", "Southern", "Eastern", "Western", "Central",
                         "North", "South", "East", "West", "Upper", "Lower",
                         "Greater", "Metro", "Downtown", "Uptown", "Suburban"]
    
    @staticmethod
    def extract_locations(text: str) -> List[Dict]:
        """Extract all locations found in text with enhanced detection for city+state and city+country"""
        locations = []
        text_lower = text.lower()
        
        # PATTERN 1: City, Country format (e.g., "Virgin Bay, Nicaragua")
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            for city in cities:
                # Pattern: "City, Country" or "City in Country" or "City (Country)"
                patterns = [
                    rf'\b{re.escape(city)}\s*,\s*{re.escape(country)}\b',
                    rf'\b{re.escape(city)}\s+in\s+{re.escape(country)}\b',
                    rf'\b{re.escape(city)}\s*\({re.escape(country)}\)',
                    rf'\b{re.escape(city)}\b.*\b{re.escape(country)}\b'
                ]
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        locations.append({
                            "type": "city_country",
                            "city": city,
                            "country": country
                        })
                        break
        
        # PATTERN 2: City, State format (e.g., "Portland, Maine")
        for city in LocationExtractor.MAJOR_US_CITIES:
            for state in LocationExtractor.US_STATES:
                patterns = [
                    rf'\b{re.escape(city)}\s*,\s*{re.escape(state)}\b',
                    rf'\b{re.escape(city)}\s+in\s+{re.escape(state)}\b',
                    rf'\b{re.escape(city)}\s*\({re.escape(state)}\)'
                ]
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        locations.append({
                            "type": "city_state",
                            "city": city,
                            "state": state,
                            "country": "United States"
                        })
                        break
        
        # PATTERN 3: City, State Abbreviation (e.g., "Portland, ME")
        for city in LocationExtractor.MAJOR_US_CITIES:
            for abbrev, state in LocationExtractor.STATE_ABBREV.items():
                pattern = rf'\b{re.escape(city)}\s*,\s*{abbrev}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    locations.append({
                        "type": "city_state",
                        "city": city,
                        "state": state,
                        "country": "United States"
                    })
        
        # PATTERN 4: International cities mentioned alone (check if country is also in text)
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            country_lower = country.lower()
            if country_lower in text_lower:
                for city in cities:
                    if city.lower() in text_lower:
                        # Check we haven't already added this city+country
                        exists = any(
                            loc.get("city") == city and loc.get("country") == country
                            for loc in locations
                        )
                        if not exists:
                            locations.append({
                                "type": "city_country",
                                "city": city,
                                "country": country
                            })
        
        # PATTERN 4B: International cities mentioned WITHOUT country in text
        # This catches cases like "Virgin Bay" appearing in an article about Nicaragua
        # where the country may not be explicitly mentioned near the city name
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            for city in cities:
                # Use word boundary to avoid partial matches
                city_pattern = rf'\b{re.escape(city)}\b'
                if re.search(city_pattern, text, re.IGNORECASE):
                    # Check we haven't already added this city
                    exists = any(
                        loc.get("city") == city and loc.get("country") == country
                        for loc in locations
                    )
                    if not exists:
                        locations.append({
                            "type": "city_country",
                            "city": city,
                            "country": country
                        })
        
        # PATTERN 5: US States alone
        for state in LocationExtractor.US_STATES:
            if state.lower() in text_lower:
                exists = any(loc.get("state") == state for loc in locations)
                if not exists:
                    locations.append({
                        "type": "state",
                        "state": state,
                        "country": "United States"
                    })
        
        # PATTERN 6: State abbreviations with context
        for abbrev, state in LocationExtractor.STATE_ABBREV.items():
            patterns = [
                rf',\s*{abbrev}\b',
                rf'\b{abbrev},',
                rf'\b{abbrev}\s+\d{{5}}',
                rf'\({abbrev}\)'
            ]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    exists = any(loc.get("state") == state for loc in locations)
                    if not exists:
                        locations.append({
                            "type": "state",
                            "state": state,
                            "country": "United States"
                        })
                    break
        
        # PATTERN 7: Countries alone
        for country in LocationExtractor.COUNTRIES:
            if country.lower() in text_lower:
                exists = any(loc.get("country") == country and loc.get("type") == "country" for loc in locations)
                if not exists:
                    locations.append({
                        "type": "country",
                        "country": country
                    })
        
        # PATTERN 8: US cities mentioned with state context
        for city in LocationExtractor.MAJOR_US_CITIES:
            if city.lower() in text_lower:
                exists = any(loc.get("city") == city for loc in locations)
                if not exists:
                    locations.append({
                        "type": "city",
                        "city": city,
                        "country": "United States"
                    })
        
        # PATTERN 9: Regional prefixes (Northern Virginia, Greater Boston)
        for prefix in LocationExtractor.REGIONAL_PREFIXES:
            pattern = rf'\b{prefix}\s+(\w+(?:\s+\w+)?)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_title = match.title()
                if match_title in LocationExtractor.US_STATES:
                    locations.append({
                        "type": "region",
                        "region": f"{prefix} {match_title}",
                        "state": match_title,
                        "country": "United States"
                    })
                elif match_title in LocationExtractor.MAJOR_US_CITIES:
                    locations.append({
                        "type": "metro_area",
                        "region": f"{prefix} {match_title}",
                        "city": match_title,
                        "country": "United States"
                    })
        
        # PATTERN 10: Street addresses (multiple per article)
        street_types = r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Highway|Hwy|Route|Rt|Pike|Parkway|Pkwy)'
        address_pattern = rf'\b(\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+({street_types})\b'
        address_matches = re.findall(address_pattern, text)
        for number, street_name, street_type in address_matches:
            locations.append({
                "type": "street_address",
                "address": f"{number} {street_name} {street_type.title()}",
                "country": "United States"
            })
        
        # PATTERN 11: Full addresses with city, state, ZIP
        full_address_pattern = rf'(\d+)\s+([A-Za-z\s]+?)\s+({street_types})\s*,?\s*([A-Za-z\s]+?)\s*,?\s*([A-Z]{{2}})\s*(\d{{5}}(?:-\d{{4}})?)?'
        full_matches = re.findall(full_address_pattern, text)
        for match in full_matches:
            number, street, st_type, city, state_abbrev, zipcode = match
            state = LocationExtractor.STATE_ABBREV.get(state_abbrev, state_abbrev)
            locations.append({
                "type": "full_address",
                "address": f"{number} {street.strip()} {st_type}",
                "city": city.strip(),
                "state": state,
                "zip": zipcode if zipcode else None,
                "country": "United States"
            })
        
        # PATTERN 12: ZIP codes
        zip_pattern = r'\b(\d{5})(?:-\d{4})?\b'
        zip_matches = re.findall(zip_pattern, text)
        for zip_code in zip_matches:
            zip_regions = {
                '0': 'Northeast', '1': 'Northeast', '2': 'Mid-Atlantic',
                '3': 'Southeast', '4': 'Midwest', '5': 'Midwest',
                '6': 'Central', '7': 'South', '8': 'West', '9': 'West'
            }
            if zip_code[0] in zip_regions:
                locations.append({
                    "type": "zip_code",
                    "zip": zip_code,
                    "region": zip_regions[zip_code[0]],
                    "country": "United States"
                })
        
        return locations
