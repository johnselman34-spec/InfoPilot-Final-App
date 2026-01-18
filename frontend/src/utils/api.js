/**
 * InfoPilot Explorer - API Configuration
 */
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
export const API = `${BACKEND_URL}/api`;
export { BACKEND_URL };

// PayPal Links
export const PAYPAL_INFOPILOT_LINK = "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ";
export const PAYPAL_BOOK_LINK = "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU";
export const AMAZON_BOOK_LINK = "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J";
