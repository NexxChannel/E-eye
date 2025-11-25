import axios from 'axios'

// In development, default to localhost:8000 if VITE_API_BASE_URL is not set
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL,
})

export default api
