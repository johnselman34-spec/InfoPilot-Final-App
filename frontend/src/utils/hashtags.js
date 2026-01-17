// ==================== HASHTAG EXTRACTION ====================
// Extract 4-8 relevant hashtags from article content
// PRIORITY: Protocol-based hashtags for maximum revenue and relevance

// Protocol keyword to popular hashtag mapping (for revenue maximization)
const PROTOCOL_HASHTAGS = {
  // Aviation/Flight keywords
  'aviation': ['#Aviation', '#Flying', '#Pilot', '#Aircraft', '#AviationNews', '#Aerospace'],
  'pilot': ['#Pilot', '#Aviation', '#Cockpit', '#Flying', '#PilotLife', '#FlightCrew'],
  'flight': ['#Flight', '#Aviation', '#Aircraft', '#AirTravel', '#FlightNews'],
  'airplane': ['#Airplane', '#Aviation', '#Aircraft', '#Flying', '#Travel'],
  'aircraft': ['#Aircraft', '#Aviation', '#Aerospace', '#Flying', '#AviationPhotography'],
  
  // Technology keywords
  'technology': ['#Tech', '#Innovation', '#Digital', '#TechNews', '#FutureTech'],
  'ai': ['#AI', '#ArtificialIntelligence', '#MachineLearning', '#DeepLearning', '#TechTrends'],
  'software': ['#Software', '#Development', '#Tech', '#Programming', '#SoftwareDev'],
  'computer': ['#Computer', '#Tech', '#Technology', '#Computing', '#IT'],
  'digital': ['#Digital', '#Tech', '#Innovation', '#DigitalTransformation'],
  'programming': ['#Programming', '#Coding', '#Developer', '#Tech', '#Code'],
  'machine learning': ['#MachineLearning', '#AI', '#DataScience', '#ML', '#TechTrends'],
  
  // History keywords
  'history': ['#History', '#Historical', '#Heritage', '#HistoryMatters', '#HistoryBuff'],
  'civil war': ['#CivilWar', '#History', '#AmericanHistory', '#HistoricalEvents', '#WarHistory'],
  'world war': ['#WorldWar', '#WWII', '#WWI', '#History', '#MilitaryHistory'],
  'ancient': ['#AncientHistory', '#Archaeology', '#History', '#Ancient', '#Historical'],
  'medieval': ['#Medieval', '#MedievalHistory', '#History', '#MiddleAges'],
  
  // Science keywords
  'science': ['#Science', '#Research', '#Discovery', '#Scientific', '#ScienceNews'],
  'space': ['#Space', '#NASA', '#SpaceExploration', '#Astronomy', '#Cosmos'],
  'health': ['#Health', '#Wellness', '#Medical', '#Healthcare', '#HealthNews'],
  'medicine': ['#Medicine', '#Medical', '#Healthcare', '#Health', '#MedicalNews'],
  'physics': ['#Physics', '#Science', '#Quantum', '#PhysicsNews', '#Scientific'],
  'biology': ['#Biology', '#Science', '#LifeScience', '#BioScience', '#Research'],
  
  // Business keywords
  'business': ['#Business', '#Entrepreneurship', '#Finance', '#Investment', '#Economy'],
  'finance': ['#Finance', '#Investing', '#Markets', '#Economy', '#FinancialNews'],
  'startup': ['#Startup', '#Entrepreneur', '#Business', '#Innovation', '#StartupLife'],
  'investment': ['#Investment', '#Investing', '#Finance', '#Money', '#Wealth'],
  'stock': ['#StockMarket', '#Stocks', '#Investing', '#Finance', '#Trading'],
  
  // News/Current Events keywords
  'news': ['#Breaking', '#News', '#CurrentEvents', '#Headlines', '#TopNews'],
  'politics': ['#Politics', '#Government', '#Policy', '#Elections', '#Political'],
  'world': ['#WorldNews', '#Global', '#International', '#Breaking', '#GlobalNews'],
  
  // Environment keywords
  'environment': ['#Environment', '#Climate', '#Sustainability', '#Green', '#EcoFriendly'],
  'climate': ['#Climate', '#ClimateChange', '#Sustainability', '#Environment', '#GlobalWarming'],
  
  // Sports keywords
  'sports': ['#Sports', '#Athletics', '#Fitness', '#SportsNews', '#GameDay'],
  'football': ['#Football', '#NFL', '#Sports', '#GameDay', '#Touchdown'],
  'basketball': ['#Basketball', '#NBA', '#Sports', '#Hoops', '#BallIsLife'],
  
  // Entertainment keywords
  'entertainment': ['#Entertainment', '#Movies', '#Music', '#Celebrity', '#PopCulture'],
  'movie': ['#Movies', '#Film', '#Cinema', '#MovieNight', '#FilmTwitter'],
  'music': ['#Music', '#NewMusic', '#MusicNews', '#Spotify', '#MusicLovers'],
  
  // Default
  'default': ['#Trending', '#News', '#Discover', '#Information', '#Knowledge']
};

/**
 * Extract hashtags primarily from PROTOCOL content for maximum relevance and revenue
 * @param {string} title - Article title  
 * @param {string} snippet - Article snippet
 * @param {string} articleType - Document type
 * @param {string} protocol - Category protocol string (PRIORITY SOURCE)
 * @param {string[]} categories - Array of category names result belongs to
 * @returns {string[]} Array of 4-8 relevant hashtags
 */
export const extractHashtags = (title = '', snippet = '', articleType = '', protocol = '', categories = []) => {
  const hashtags = new Set();
  
  // 1. PRIORITY: Extract hashtags from protocol terms (for revenue maximization)
  if (protocol) {
    const protocolLower = protocol.toLowerCase();
    
    // Check each protocol keyword mapping
    for (const [keyword, tags] of Object.entries(PROTOCOL_HASHTAGS)) {
      if (keyword !== 'default' && protocolLower.includes(keyword)) {
        // Add first 2-3 relevant hashtags from the matched keyword
        tags.slice(0, 3).forEach(tag => hashtags.add(tag));
      }
    }
    
    // Extract significant words from protocol syntax (within parentheses)
    const protocolTerms = protocolLower.match(/\(([^)]+)\)/g) || [];
    protocolTerms.forEach(term => {
      const cleanTerm = term.replace(/[()]/g, '').trim();
      const words = cleanTerm.split(/[\s&|+^]+/).filter(w => w.length > 3);
      words.slice(0, 2).forEach(word => {
        const formattedWord = word.charAt(0).toUpperCase() + word.slice(1);
        hashtags.add(`#${formattedWord}`);
      });
    });
  }
  
  // 2. Add category-based hashtags if provided
  if (categories && categories.length > 0) {
    categories.forEach(cat => {
      if (cat) {
        const catLower = cat.toLowerCase();
        for (const [keyword, tags] of Object.entries(PROTOCOL_HASHTAGS)) {
          if (keyword !== 'default' && catLower.includes(keyword)) {
            tags.slice(0, 2).forEach(tag => hashtags.add(tag));
            break;
          }
        }
      }
    });
  }
  
  // 3. Add article type hashtag
  if (articleType && articleType !== 'Unknown') {
    hashtags.add(`#${articleType.replace(/\s+/g, '')}`);
  }
  
  // 4. Extract important words from title (secondary source)
  const titleWords = (title || '').toLowerCase().match(/\b[a-z]{4,15}\b/g) || [];
  const significantTitleWords = titleWords.filter(w => 
    !['with', 'that', 'this', 'from', 'have', 'been', 'were', 'more', 'about', 'what', 'when', 'where', 'which', 'their', 'there', 'would', 'could', 'should', 'after', 'before', 'other', 'some', 'most', 'only', 'just', 'even', 'also', 'back', 'into', 'over', 'such', 'your', 'than'].includes(w)
  );
  
  significantTitleWords.slice(0, 3).forEach(word => {
    const formattedWord = word.charAt(0).toUpperCase() + word.slice(1);
    hashtags.add(`#${formattedWord}`);
  });
  
  // 5. If still under 4 hashtags, add defaults
  if (hashtags.size < 4) {
    PROTOCOL_HASHTAGS.default.slice(0, 4 - hashtags.size).forEach(tag => hashtags.add(tag));
  }
  
  return Array.from(hashtags).slice(0, 8);
};

/**
 * Get popular hashtags based on protocol string (PRIMARY for revenue)
 * @param {string} protocol - InfoJet 2.0 protocol string
 * @returns {string[]} Array of popular hashtags for that protocol
 */
export const getProtocolHashtags = (protocol) => {
  if (!protocol) return PROTOCOL_HASHTAGS.default;
  
  const protocolLower = protocol.toLowerCase();
  const hashtags = new Set();
  
  // Match protocol keywords to hashtag sets
  for (const [keyword, tags] of Object.entries(PROTOCOL_HASHTAGS)) {
    if (keyword !== 'default' && protocolLower.includes(keyword)) {
      tags.forEach(tag => hashtags.add(tag));
    }
  }
  
  if (hashtags.size === 0) {
    return PROTOCOL_HASHTAGS.default;
  }
  
  return Array.from(hashtags).slice(0, 8);
};

/**
 * Get popular hashtags for a specific category name
 * @param {string} categoryName - Name of the category
 * @returns {string[]} Array of popular hashtags for that category
 */
export const getCategoryHashtags = (categoryName) => {
  if (!categoryName) return PROTOCOL_HASHTAGS.default;
  
  const catLower = categoryName.toLowerCase();
  for (const [key, tags] of Object.entries(PROTOCOL_HASHTAGS)) {
    if (key !== 'default' && catLower.includes(key)) {
      return tags;
    }
  }
  return PROTOCOL_HASHTAGS.default;
};

export default extractHashtags;
