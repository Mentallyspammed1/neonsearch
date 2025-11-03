import { create } from 'zustand';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const useVideoStore = create((set, get) => ({
  // State
  results: [],
  selectedVideo: null,
  isLoading: false,
  error: null,
  searchQuery: '',
  selectedSources: ['all'],
  availableSources: [],
  
  // Actions
  searchVideos: async (query, sources = ['all']) => {
    set({ isLoading: true, error: null, searchQuery: query });
    
    try {
      const response = await axios.post(`${API}/search`, {
        query,
        sources,
        page: 1,
        limit: 40
      });
      
      set({ 
        results: response.data.results || [], 
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Search failed', 
        isLoading: false,
        results: []
      });
    }
  },
  
  selectVideo: (video) => {
    set({ selectedVideo: video });
  },
  
  clearResults: () => {
    set({ 
      results: [], 
      selectedVideo: null, 
      error: null, 
      searchQuery: '' 
    });
  },
  
  setLoading: (loading) => {
    set({ isLoading: loading });
  },
  
  setError: (error) => {
    set({ error });
  },
  
  setSearchQuery: (query) => {
    set({ searchQuery: query });
  },
  
  setSelectedSources: (sources) => {
    set({ selectedSources: sources });
  },
  
  fetchSources: async () => {
    try {
      const response = await axios.get(`${API}/sources`);
      set({ availableSources: response.data.sources || [] });
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    }
  },
}));
