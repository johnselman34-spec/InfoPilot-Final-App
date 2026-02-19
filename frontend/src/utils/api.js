// API Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Trigger map refresh event - call this after any data changes
export const triggerMapRefresh = () => {
  window.dispatchEvent(new CustomEvent('infopilot-data-changed'));
};

// Prohibited content filter
const PROHIBITED_TOPICS = [
  'nuclear weapons', 'nuclear technology', 'uranium enrichment', 'plutonium',
  'terrorism', 'terrorist', 'bomb making', 'explosive devices', 'ied',
  'biological weapons', 'bioweapons', 'anthrax', 'smallpox weaponization',
  'chemical weapons', 'nerve agents', 'sarin', 'mustard gas', 'vx gas',
  'psychological warfare', 'mind control', 'brainwashing techniques',
  'mass destruction', 'wmd', 'radiological weapons', 'dirty bomb',
  'ricin', 'botulinum', 'weaponized', 'how to make a bomb'
];

// Check if a search query contains prohibited content
export const containsProhibitedContent = (query) => {
  if (!query) return false;
  const lowerQuery = query.toLowerCase();
  return PROHIBITED_TOPICS.some(topic => lowerQuery.includes(topic.toLowerCase()));
};

// Get blocked message for prohibited content
export const getProhibitedContentMessage = () => {
  return {
    title: '🚫 Search Blocked',
    message: 'Your search contains terms related to prohibited content (nuclear, terrorism, biological/chemical/psychological warfare). This type of research is not allowed on InfoPilot Explorer.',
    type: 'error'
  };
};

export default API;
