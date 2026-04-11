import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function InputForm({ onSubmit, isLoading }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !isLoading) {
      onSubmit(text);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-3xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        <div className="relative glass rounded-xl p-6 shadow-2xl flex flex-col gap-4">
          <label htmlFor="historical-text" className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent" /> Extract Historical Events
          </label>
          <textarea
            id="historical-text"
            className="w-full h-40 bg-surface/50 border border-slate-700 rounded-lg p-4 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none transition-all"
            placeholder="Paste raw historical text here... (e.g., The Battle of Gettysburg was fought from July 1 to July 3, 1863...)"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isLoading || !text.trim()}
              className="bg-primary hover:bg-primary/90 text-white font-medium py-2.5 px-6 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing Narrative...</>
              ) : (
                'Generate Timeline'
              )}
            </button>
          </div>
        </div>
      </form>
    </motion.div>
  );
}
