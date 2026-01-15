// API Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Trigger map refresh event - call this after any data changes
export const triggerMapRefresh = () => {
  window.dispatchEvent(new CustomEvent('infopilot-data-changed'));
};

export default API;
