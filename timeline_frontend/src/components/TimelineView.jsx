import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import EventCard from './EventCard';

export default function TimelineView({ events, images = [] }) {
  const [openEvents, setOpenEvents] = useState(new Set());
  const cardRefs = useRef({});

  if (!events || events.length === 0) return null;

  const sorted = [...events].sort((a, b) => {
    const da = a.date_normalized || a.date || '';
    const db = b.date_normalized || b.date || '';
    return da.localeCompare(db);
  });

  const handleDotClick = useCallback((idx) => {
    setOpenEvents(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
        // Scroll into view after render
        requestAnimationFrame(() => {
          cardRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
      }
      return next;
    });
  }, []);

  return (
    <div className="w-full max-w-5xl mx-auto relative pb-20">
      {/* Central Axis */}
      <div className="absolute top-0 bottom-0 left-8 md:left-1/2 md:-translate-x-1/2 w-0.5 bg-gradient-to-b from-primary/40 via-slate-300 dark:via-slate-700 to-transparent" />

      <div className="flex flex-col">
        {sorted.map((event, idx) => {
          const isOpen = openEvents.has(idx);
          const isEven = idx % 2 === 0;
          const date = event.date_normalized || event.date || '';

          return (
            <div key={`${date}-${idx}`} className="relative mb-4">
              {/* Dot Row */}
              <div className="flex items-center mb-2">
                {/* Left date label (desktop even) */}
                <div className="hidden md:block w-[calc(50%-24px)] text-right pr-6">
                  {isEven && (
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 transition-colors duration-300">{date}</span>
                  )}
                </div>

                {/* Clickable Dot */}
                <div className="absolute left-8 md:left-1/2 md:-translate-x-1/2 z-20">
                  <motion.button
                    onClick={() => handleDotClick(idx)}
                    className={`w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                      isOpen
                        ? 'bg-primary border-primary shadow-lg shadow-primary/30 scale-125'
                        : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 hover:border-primary hover:scale-110'
                    }`}
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                    title={event.title}
                  >
                    <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${isOpen ? 'bg-white' : 'bg-primary/60'}`} />
                  </motion.button>
                </div>

                {/* Right date label (desktop odd) */}
                <div className="hidden md:block w-[calc(50%-24px)] ml-auto pl-6">
                  {!isEven && (
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 transition-colors duration-300">{date}</span>
                  )}
                </div>

                {/* Mobile label */}
                <div className="md:hidden ml-16">
                  <button
                    onClick={() => handleDotClick(idx)}
                    className="text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-primary transition-colors duration-200"
                  >
                    {date} — {event.title?.slice(0, 40)}
                  </button>
                </div>
              </div>

              {/* Event Card — persists until explicitly closed */}
              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    ref={(el) => { cardRefs.current[idx] = el; }}
                    initial={{ opacity: 0, y: 20, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.96 }}
                    transition={{ type: 'spring', stiffness: 260, damping: 24 }}
                    className={`relative pl-16 md:pl-0 ${isEven ? 'md:pr-[calc(50%+32px)]' : 'md:pl-[calc(50%+32px)]'}`}
                  >
                    <EventCard event={event} images={images} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}
