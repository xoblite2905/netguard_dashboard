// src/api/config.js


const API_HOST = window.location.hostname;

// Your docker-compose.yml runs the backend on port 8080 on the host network.
const API_PORT = 8080;

// Construct the full, correct base URLs.
export const API_BASE_URL = `http://${API_HOST}:${API_PORT}`;
export const WS_BASE_URL = `ws://${API_HOST}:${API_PORT}`;