// ==================== HASHTAG EXTRACTION ====================
// Extract 4-6 relevant hashtags from article content
export const extractHashtags = (title, snippet, articleType) => {
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
    'will', 'each', 'make', 'like', 'time', 'take', 'come', 'made', 'find'
  ]);
  
  // Count word frequency
  const wordCount = {};
  words.forEach(word => {
    if (!stopWords.has(word) && word.length > 3) {
      wordCount[word] = (wordCount[word] || 0) + 1;
    }
  });
  
  // Sort by frequency and take top words
  const sortedWords = Object.entries(wordCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);
  
  // Add article type as a hashtag
  const typeTag = articleType?.toLowerCase().replace(/\s+/g, '') || 'article';
  
  // Combine and format as hashtags (4-6 total)
  const hashtags = [typeTag, ...sortedWords].slice(0, 6);
  return hashtags.map(tag => `#${tag.charAt(0).toUpperCase() + tag.slice(1)}`);
};

export default extractHashtags;
