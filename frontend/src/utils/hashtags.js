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
  'digital': ['#Digital', '#Tech', '#Innovation', '#Digital Transformation'],
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
  'climate': ['#Climate', '#ClimateChange', '#Sustainability', '#Environment', '#Global Warming'],
  
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

export default extractHashtags;ustainability', '#Environment', '#GreenEnergy'],
  
  // Education
  'education': ['#Education', '#Learning', '#EdTech', '#School', '#Teaching'],
  'research': ['#Research', '#Academic', '#Study', '#Science', '#Findings'],
  
  // Sports
  'sports': ['#Sports', '#Athletic', '#Competition', '#Championship', '#SportsNews'],
  
  // Default/General
  'default': ['#Trending', '#MustRead', '#FYP', '#Viral', '#TopPicks']
};

// Protocol keyword to hashtag mapping
const PROTOCOL_KEYWORDS = {
  'breaking': '#BreakingNews',
  'urgent': '#Urgent',
  'exclusive': '#Exclusive',
  'trending': '#Trending',
  'latest': '#Latest',
  'update': '#Update',
  'official': '#Official',
  'revealed': '#Revealed',
  'announces': '#Announcement',
  'study': '#Research',
  'report': '#Report',
  'analysis': '#Analysis',
  'review': '#Review',
  'guide': '#Guide',
  'tips': '#Tips',
  'howto': '#HowTo',
  'tutorial': '#Tutorial',
  'opinion': '#Opinion',
  'editorial': '#Editorial'
};

/**
 * Extract relevant hashtags from content, category, and protocol
 * @param {string} title - Article title
 * @param {string} snippet - Article snippet/description
 * @param {string} articleType - Type of article (News, Blog, etc)
 * @param {string} categoryName - Name of the category (optional)
 * @param {string} protocol - Search protocol used (optional)
 * @returns {string[]} Array of formatted hashtags
 */
export const extractHashtags = (title, snippet, articleType, categoryName = '', protocol = '') => {
  const text = `${title || ''} ${snippet || ''}`.toLowerCase();
  const words = text.match(/\b[a-z]{4,15}\b/g) || [];
  
  // Common words to exclude
  const stopWords = new Set([
    'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they', 'their',
    'what', 'when', 'where', 'which', 'while', 'about', 'would', 'could',
    'should', 'there', 'these', 'those', 'being', 'other', 'some', 'such',
    'into', 'over', 'after', 'before', 'under', 'between', 'through', 'during',
    'without', 'again', 'further', 'then', 'once', 'here', 'there', 'more',
    'most', 'very', 'just', 'only', 'also', 'back', 'well', 'even', 'still',
    'will', 'each', 'make', 'like', 'time', 'take', 'come', 'made', 'find',
    'says', 'said', 'year', 'years', 'first', 'last', 'new', 'news', 'many'
  ]);
  
  const hashtags = new Set();
  
  // 1. Add category-relevant hashtags (1-2)
  if (categoryName) {
    const catLower = categoryName.toLowerCase();
    // Find matching category
    for (const [key, tags] of Object.entries(CATEGORY_HASHTAGS)) {
      if (catLower.includes(key)) {
        tags.slice(0, 2).forEach(tag => hashtags.add(tag));
        break;
      }
    }
  }
  
  // 2. Add protocol-relevant hashtags (1-2)
  if (protocol) {
    const protocolLower = protocol.toLowerCase();
    for (const [keyword, hashtag] of Object.entries(PROTOCOL_KEYWORDS)) {
      if (protocolLower.includes(keyword)) {
        hashtags.add(hashtag);
        if (hashtags.size >= 4) break;
      }
    }
  }
  
  // 3. Add article type hashtag
  const typeTag = articleType?.replace(/\s+/g, '') || 'Article';
  hashtags.add(`#${typeTag}`);
  
  // 4. Extract content-based hashtags
  const wordCount = {};
  words.forEach(word => {
    if (!stopWords.has(word) && word.length > 3) {
      wordCount[word] = (wordCount[word] || 0) + 1;
    }
  });
  
  // Sort by frequency and add top words
  const sortedWords = Object.entries(wordCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([word]) => `#${word.charAt(0).toUpperCase() + word.slice(1)}`);
  
  sortedWords.forEach(tag => {
    if (hashtags.size < 8) {
      hashtags.add(tag);
    }
  });
  
  // 5. If still under 4 hashtags, add defaults
  if (hashtags.size < 4) {
    CATEGORY_HASHTAGS.default.slice(0, 4 - hashtags.size).forEach(tag => hashtags.add(tag));
  }
  
  return Array.from(hashtags).slice(0, 8);
};

/**
 * Get popular hashtags for a specific category
 * @param {string} categoryName - Name of the category
 * @returns {string[]} Array of popular hashtags for that category
 */
export const getCategoryHashtags = (categoryName) => {
  if (!categoryName) return CATEGORY_HASHTAGS.default;
  
  const catLower = categoryName.toLowerCase();
  for (const [key, tags] of Object.entries(CATEGORY_HASHTAGS)) {
    if (catLower.includes(key)) {
      return tags;
    }
  }
  return CATEGORY_HASHTAGS.default;
};

/**
 * Extract hashtags from protocol string
 * @param {string} protocol - InfoJet 2.0 protocol string
 * @returns {string[]} Array of hashtags derived from protocol
 */
export const getProtocolHashtags = (protocol) => {
  if (!protocol) return [];
  
  const hashtags = [];
  const protocolLower = protocol.toLowerCase();
  
  // Extract terms from protocol syntax
  const terms = protocolLower.match(/\b[a-z]{3,15}\b/g) || [];
  const uniqueTerms = [...new Set(terms)].filter(t => t.length > 3);
  
  // Convert to hashtags
  uniqueTerms.slice(0, 5).forEach(term => {
    hashtags.push(`#${term.charAt(0).toUpperCase() + term.slice(1)}`);
  });
  
  return hashtags;
};

export default extractHashtags;
