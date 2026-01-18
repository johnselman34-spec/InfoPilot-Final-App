/**
 * InfoPilot Explorer - API Configuration
 */
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
export const API = `${BACKEND_URL}/api`;
export { BACKEND_URL };

// PayPal Business Email
export const PAYPAL_BUSINESS_EMAIL = "JJspilot24@gmail.com";

// PayPal Payment Links (using PayPal.me which is more reliable)
export const PAYPAL_INFOPILOT_LINK = "https://www.paypal.com/paypalme/JJspilot24/1";
export const PAYPAL_BOOK_LINK = "https://www.paypal.com/paypalme/JJspilot24/9.98";
export const AMAZON_BOOK_LINK = "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J";

// Fallback: Direct PayPal checkout URL
export const createPayPalPaymentUrl = (amount, itemName) => {
  return `https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=${encodeURIComponent(PAYPAL_BUSINESS_EMAIL)}&item_name=${encodeURIComponent(itemName)}&amount=${amount}&currency_code=USD`;
};
