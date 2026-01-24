import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// API helper with auth
export const api = axios.create({
  baseURL: API,
  withCredentials: true
});
