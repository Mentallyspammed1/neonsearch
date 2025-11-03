import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Search, Video as VideoIcon, Grid3x3, X, Loader2, ArrowLeft, Play, Eye, Clock } from 'lucide-react';
import ReactPlayer from 'react-player';
import { useVideoStore } from './store/videoStore';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// SearchBar Component
const SearchBar = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const { selectedSources, setSelectedSources, availableSources } = useVideoStore();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, selectedSources);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for videos..."
            className="w-full px-6 py-4 pr-32 text-lg rounded-2xl bg-gray-800 text-white border-2 border-gray-700 focus:border-purple-500 focus:outline-none transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            Search
          </button>
        </div>
        
        {/* Source Filters */}
        <div className="flex flex-wrap gap-2 justify-center">
          <button
            type="button"
            onClick={() => setSelectedSources(['all'])}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedSources.includes('all')
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            All Sources
          </button>
          {availableSources.map((source) => (
            <button
              key={source.name}
              type="button"
              onClick={() => {
                if (selectedSources.includes('all')) {
                  setSelectedSources([source.name]);
                } else {
                  const newSources = selectedSources.includes(source.name)
                    ? selectedSources.filter((s) => s !== source.name)
                    : [...selectedSources, source.name];
                  setSelectedSources(newSources.length ? newSources : ['all']);
                }
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedSources.includes(source.name) && !selectedSources.includes('all')
                  ? 'bg-pink-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              disabled={!source.enabled}
            >
              {source.driver_name || source.name}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
};

// VideoCard Component
const VideoCard = ({ video, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="group cursor-pointer bg-gray-800 rounded-xl overflow-hidden hover:ring-2 hover:ring-purple-500 transition-all transform hover:scale-105"
    >
      <div className="relative aspect-video bg-gray-900">
        <img
          src={video.thumbnail}
          alt={video.title}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={(e) => {
            e.target.src = 'https://via.placeholder.com/320x180/374151/9CA3AF?text=No+Image';
          }}
        />
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
          <div className="bg-purple-600 rounded-full p-3 opacity-0 group-hover:opacity-100 transition-all transform scale-75 group-hover:scale-100">
            <Play className="w-6 h-6 text-white" fill="white" />
          </div>
        </div>
        {video.duration && (
          <div className="absolute bottom-2 right-2 px-2 py-1 bg-black bg-opacity-80 text-white text-xs rounded">
            {video.duration}
          </div>
        )}
        <div className="absolute top-2 left-2 px-2 py-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs rounded font-medium">
          {video.source}
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-white text-sm line-clamp-2 group-hover:text-purple-400 transition-colors">
          {video.title}
        </h3>
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
          {video.views && (
            <div className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              <span>{video.views}</span>
            </div>
          )}
          {video.duration && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{video.duration}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// VideoGrid Component
const VideoGrid = ({ videos, onVideoSelect, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 px-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="bg-gray-800 rounded-xl overflow-hidden animate-pulse">
            <div className="aspect-video bg-gray-700" />
            <div className="p-4 space-y-2">
              <div className="h-4 bg-gray-700 rounded" />
              <div className="h-4 bg-gray-700 rounded w-3/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!videos.length) {
    return (
      <div className="text-center py-20">
        <VideoIcon className="w-20 h-20 mx-auto text-gray-600 mb-4" />
        <p className="text-gray-400 text-lg">No videos found. Try a different search.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 px-4">
      {videos.map((video) => (
        <VideoCard key={video.id} video={video} onClick={() => onVideoSelect(video)} />
      ))}
    </div>
  );
};

// VideoPlayer Component
const VideoPlayer = ({ video, onBack }) => {
  return (
    <div className="max-w-6xl mx-auto px-4">
      <button
        onClick={onBack}
        className="mb-6 flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-all"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Results
      </button>

      <div className="bg-gray-800 rounded-2xl overflow-hidden shadow-2xl">
        {/* Video Player */}
        <div className="aspect-video bg-black">
          <ReactPlayer
            url={video.url}
            width="100%"
            height="100%"
            controls
            playing
            config={{
              file: {
                attributes: {
                  crossOrigin: 'anonymous',
                },
              },
            }}
            onError={(e) => {
              console.error('Video player error:', e);
            }}
          />
        </div>

        {/* Video Info */}
        <div className="p-6">
          <h1 className="text-2xl font-bold text-white mb-4">{video.title}</h1>
          <div className="flex flex-wrap items-center gap-4 text-gray-400">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 rounded-lg">
              <span className="text-sm font-medium">Source:</span>
              <span className="text-white font-semibold">{video.source}</span>
            </div>
            {video.views && (
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                <span>{video.views}</span>
              </div>
            )}
            {video.duration && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{video.duration}</span>
              </div>
            )}
          </div>
          <a
            href={video.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-block px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
          >
            Watch on {video.source}
          </a>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const {
    results,
    selectedVideo,
    isLoading,
    error,
    searchVideos,
    selectVideo,
    clearResults,
    fetchSources,
    availableSources,
  } = useVideoStore();

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const handleSearch = (query, sources) => {
    searchVideos(query, sources);
  };

  const handleVideoSelect = (video) => {
    selectVideo(video);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBack = () => {
    selectVideo(null);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white">
        {/* Header */}
        <header className="py-8 border-b border-gray-800">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-center gap-3 mb-2">
              <div className="p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl">
                <VideoIcon className="w-8 h-8" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Video Search Engine
              </h1>
            </div>
            <p className="text-center text-gray-400">Search across multiple video platforms</p>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto py-8">
          {!selectedVideo && (
            <div className="mb-8">
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </div>
          )}

          {error && (
            <div className="max-w-2xl mx-auto mb-8 px-4">
              <div className="bg-red-900 bg-opacity-50 border border-red-700 text-red-200 px-6 py-4 rounded-lg">
                <p className="font-semibold">Error:</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {selectedVideo ? (
            <VideoPlayer video={selectedVideo} onBack={handleBack} />
          ) : (
            <>
              {results.length > 0 && (
                <div className="mb-6 px-4 flex justify-between items-center">
                  <h2 className="text-2xl font-semibold">Found {results.length} videos</h2>
                  <button
                    onClick={clearResults}
                    className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-all flex items-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Clear
                  </button>
                </div>
              )}
              <VideoGrid
                videos={results}
                onVideoSelect={handleVideoSelect}
                isLoading={isLoading}
              />
            </>
          )}
        </main>

        {/* Footer */}
        <footer className="py-8 mt-20 border-t border-gray-800">
          <div className="container mx-auto px-4 text-center text-gray-500">
            <p>Multi-source video search platform</p>
            <p className="text-sm mt-2">
              {availableSources.length} sources available: {availableSources.map(s => s.driver_name || s.name).join(', ')}
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
