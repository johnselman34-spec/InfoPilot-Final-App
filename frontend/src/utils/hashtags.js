// ==================== HASHTAG EXTRACTION ====================
// Extract 4-8 relevant hashtags from article content
// Now with category and protocol relevance

// Category-specific popular hashtags
const CATEGORY_HASHTAGS = {
  // Aviation/Flight
  'aviation': ['#Aviation', '#Flying', '#Pilot', '#Aircraft', '#FlightNews'],
  'pilot': ['#Pilot', '#Aviation', '#Cockpit', '#Flying', '#AviationLife'],
  'flight': ['#Flight', '#Aviation', '#Aircraft', '#Travel', '#AirTravel'],
  
  // Technology
  'technology': ['#Tech', '#Innovation', '#Digital', '#TechNews', '#Future'],
  'ai': ['#AI', '#ArtificialIntelligence', '#MachineLearning', '#TechTrends'],
  'software': ['#Software', '#Development', '#Tech', '#Coding', '#SoftwareEngineering'],
  
  // Science
  'science': ['#Science', '#Research', '#Discovery', '#Scientific', '#Innovation'],
  'space': ['#Space', '#NASA', '#SpaceExploration', '#Astronomy', '#Cosmos'],
  'health': ['#Health', '#Wellness', '#Medical', '#Healthcare', '#HealthNews'],
  
  // Business
  'business': ['#Business', '#Entrepreneurship', '#Finance', '#Investment', '#Economy'],
  'finance': ['#Finance', '#Investing', '#Markets', '#Economy', '#Money'],
  'startup': ['#Startup', '#Entrepreneur', '#Business', '#Innovation', '#Tech'],
  
  // News/Current Events
  'news': ['#Breaking', '#News', '#CurrentEvents', '#Headlines', '#TopNews'],
  'politics': ['#Politics', '#Government', '#Policy', '#Elections', '#Political'],
  'world': ['#WorldNews', '#Global', '#International', '#Breaking', '#World'],
  
  // Environment
  'environment': ['#Environment', '#Climate', '#Sustainability', '#Green', '#EcoFriendly'],
  'climate': ['#Climate', '#ClimateChange', '#Sustainability', '#Environment', '#GreenEnergy'],
  
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
