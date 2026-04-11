import { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, AlertTriangle } from 'lucide-react';
import TimelineView from './components/TimelineView';

function App() {
  const [query, setQuery] = useState('');
  const [events, setEvents] = useState([]);
  const [meta, setMeta] = useState({ topic: '', summary: '', thumbnail: '', images: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchTimeline = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    
    setIsLoading(true);
    setError('');
    setEvents([]);
    setMeta({ topic: '', summary: '', thumbnail: '', images: [] });
    
    try {
      const response = await axios.post('https://chronomind-backend.onrender.com/api/v1/query', {
        query: query.trim()
      }, { timeout: 30000 });
      
      const data = response.data;
      setEvents(data.events || []);
      setMeta({
        topic: data.topic || query,
        summary: data.summary || '',
        thumbnail: data.thumbnail || '',
        images: data.images || []
      });
      
      if (!data.events || data.events.length === 0) {
        setError('No historical events found for this query. Try a more specific topic.');
      }
    } catch (err) {
      console.error('Query failed:', err);
      setError('Could not fetch timeline. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden bg-slate-50">
      
      {/* Background Glows (dark mode only) */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/5 dark:bg-primary/10 blur-[150px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent/3 dark:bg-accent/5 blur-[120px] pointer-events-none" />

      <div className="relative z-10 pt-20 px-4 md:px-8 pb-32">
        {/* Header */}
        <header className="text-center mb-12 w-full max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 tracking-tight text-slate-900 dark:text-white">
            ChronoMind
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg leading-relaxed max-w-2xl mx-auto font-light">
            Enter any historical topic, person, or event. The system will retrieve knowledge and generate an interactive timeline.
          </p>
        </header>

        {/* Search Input */}
        <form onSubmit={fetchTimeline} className="w-full max-w-2xl mx-auto mb-12">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300" />
            <div className="relative flex items-center glass dark:glass rounded-2xl px-5 py-3 shadow-xl">
              <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-3 flex-shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Try "World War 1", "Mahatma Gandhi", or "French Revolution"...'
                className="flex-1 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none text-base"
              />
              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className="ml-3 bg-primary hover:bg-primary/90 text-white font-medium py-2 px-5 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed text-sm flex-shrink-0"
              >
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                ) : 'Generate'}
              </button>
            </div>
          </div>
        </form>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-2xl mx-auto mb-8 p-4 bg-amber-50 dark:bg-accent/10 border border-amber-200 dark:border-accent/20 rounded-xl text-amber-700 dark:text-accent text-center text-sm font-medium flex items-center justify-center gap-2"
            >
              <AlertTriangle className="w-4 h-4" /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Topic Summary */}
        <AnimatePresence>
          {meta.summary && (
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="max-w-3xl mx-auto mb-12"
            >
              <div className="glass dark:glass rounded-2xl p-6 shadow-lg flex gap-5 items-start">
                {meta.thumbnail && (
                  <img src={meta.thumbnail} alt={meta.topic} className="w-24 h-24 rounded-xl object-cover flex-shrink-0 shadow-md" />
                )}
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{meta.topic}</h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed line-clamp-4">{meta.summary}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Timeline */}
        {events.length > 0 && <TimelineView events={events} images={meta.images} />}
      </div>
    </div>
  );
}

export default App;
