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
  isLoadingSources: false, // New state for loading sources
  
  // Actions
  searchVideos: async (query, sources = ['all']) => {
    console.log(`[Store] Initiating search: query='${query}', sources=${JSON.stringify(sources)}`);
    set({ isLoading: true, error: null, searchQuery: query });
    console.log(`[Store] State updated: isLoading=true, error=null, searchQuery='${query}'`);
    
    try {
      const response = await axios.post(`${API}/search`, {
        query,
        sources,
        page: 1,
        limit: 40
      });
      
      const fetchedResults = response.data.results || [];
      console.log(`[Store] Search successful for query='${query}'. Received ${fetchedResults.length} results.`);
      set({ 
        results: fetchedResults, 
        isLoading: false 
      });
      console.log(`[Store] State updated: results=${fetchedResults.length}, isLoading=false`);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Search failed'; // More robust error message
      console.error(`[Store] Search failed for query='${query}': ${errorMessage}`, error);
      set({ 
        error: errorMessage, 
        isLoading: false,
        results: []
      });
      console.log(`[Store] State updated: error='${errorMessage}', isLoading=false, results=[]`);
    }
  },
  
  selectVideo: (video) => {
    console.log(`[Store] Video selected: ${video ? video.title : 'None'}`);
    set({ selectedVideo: video });
  },
  
  clearResults: () => {
    console.log('[Store] Clearing results.');
    set({ 
      results: [], 
      selectedVideo: null, 
      error: null, 
      searchQuery: '' 
    });
    console.log('[Store] State reset: results=[], selectedVideo=null, error=null, searchQuery=""');
  },
  
  setLoading: (loading) => {
    console.log(`[Store] Setting isLoading to: ${loading}`);
    set({ isLoading: loading });
  },
  
  setError: (error) => {
    console.log(`[Store] Setting error: ${error}`);
    set({ error });
  },
  
  setSearchQuery: (query) => {
    console.log(`[Store] Setting searchQuery to: '${query}'`);
    set({ searchQuery: query });
  },
  
  setSelectedSources: (sources) => {
    console.log(`[Store] Setting selectedSources to: ${JSON.stringify(sources)}`);
    set({ selectedSources: sources });
  },
  
  fetchSources: async () => {
    console.log('[Store] Initiating fetch for available sources...');
    set({ isLoadingSources: true, error: null }); // Set loading and clear previous error
    try {
      const response = await axios.get(`${API}/sources`);
      const fetchedSources = response.data.sources || [];
      console.log(`[Store] Successfully fetched ${fetchedSources.length} sources.`);
      set({ availableSources: fetchedSources, isLoadingSources: false });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch sources'; // More robust error message
      console.error('[Store] Failed to fetch sources:', error);
      set({ 
        error: errorMessage, // Use the general error state for now, or a dedicated sourcesError state
        isLoadingSources: false 
      });
    }
  },
}));