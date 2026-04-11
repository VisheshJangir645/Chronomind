import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, MapPin, User, ExternalLink, Link2, BarChart3 } from 'lucide-react';
import { fetchEventDetails } from '../utils/fetchEventDetails';

export default function EventCard({ event, images = [] }) {
  const [wikiData, setWikiData] = useState(null);
  const [loadingWiki, setLoadingWiki] = useState(false);

  const date = event.date_normalized || event.date || 'Unknown';
  const title = event.title || '';
  const description = event.description || '';
  const actors = event.people?.length > 0 ? event.people : [];
  const locations = event.locations?.length > 0 ? event.locations : [];
  const relevance = event.relevance_score;
  const relatedTo = event.related_to;

  // Fetch Wikipedia enrichment on mount
  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      setLoadingWiki(true);
      const data = await fetchEventDetails(title);
      if (!cancelled) {
        setWikiData(data);
        setLoadingWiki(false);
      }
    };
    fetchData();
    return () => { cancelled = true; };
  }, [title]);

  const displayImage = wikiData?.thumbnail || (images.length > 0 ? images[0] : null);

  return (
    <div className="glass dark:glass rounded-2xl shadow-xl overflow-hidden max-h-[520px] overflow-y-auto">
      {/* Image Header */}
      {displayImage && (
        <div className="relative h-36 overflow-hidden">
          <img src={displayImage} alt={title} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
          <div className="absolute bottom-3 left-4 right-4">
            <time className="text-accent text-xs font-bold">{date}</time>
            <h3 className="text-white font-bold text-sm leading-snug line-clamp-2">{title}</h3>
          </div>
        </div>
      )}

      <div className="p-5">
        {/* Title + Date (if no image) */}
        {!displayImage && (
          <div className="mb-3">
            <div className="flex items-center gap-2 text-accent font-semibold text-sm mb-1">
              <Calendar className="w-4 h-4" />
              <time>{date}</time>
            </div>
            <h3 className="text-slate-900 dark:text-white font-bold text-base leading-snug">{title}</h3>
          </div>
        )}

        {/* Causal Link — "Follows: Previous Event" */}
        {relatedTo && (
          <div className="flex items-center gap-1.5 text-xs text-primary/80 dark:text-primary/70 mb-3 bg-primary/5 dark:bg-primary/10 rounded-lg px-3 py-1.5">
            <Link2 className="w-3 h-3 flex-shrink-0" />
            <span>Follows: <strong>{relatedTo}</strong></span>
          </div>
        )}

        {/* Multi-sentence Description */}
        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed mb-3">
          {description}
        </p>

        {/* Wikipedia Summary (if different from description) */}
        {loadingWiki && (
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
            <div className="w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            Enriching with Wikipedia...
          </div>
        )}
        {wikiData?.summary && (
          (() => {
            const descWords = new Set(description.toLowerCase().split(/\s+/).slice(0, 20));
            const summWords = new Set(wikiData.summary.toLowerCase().split(/\s+/).slice(0, 20));
            const overlap = [...descWords].filter(w => summWords.has(w)).length;
            const isUnique = overlap < descWords.size * 0.5;
            
            return isUnique ? (
              <div className="mb-3 border-l-2 border-primary/30 pl-3">
                <p className="text-xs font-semibold text-primary mb-1 uppercase tracking-wider">Additional Context</p>
                <p className="text-slate-500 dark:text-slate-400 text-xs leading-relaxed line-clamp-3">{wikiData.summary}</p>
              </div>
            ) : null;
          })()
        )}

        {/* Entity Chips */}
        {(actors.length > 0 || locations.length > 0) && (
          <div className="flex flex-wrap gap-2 mb-3">
            {actors.map((a, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary/10 dark:bg-primary/15 text-primary border border-primary/20">
                <User className="w-3 h-3" /> {a}
              </span>
            ))}
            {locations.map((l, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-accent/10 dark:bg-accent/15 text-accent border border-accent/20">
                <MapPin className="w-3 h-3" /> {l}
              </span>
            ))}
          </div>
        )}

        {/* Footer: Relevance Score + Wiki Link */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-700/50">
          {relevance && (
            <div className="flex items-center gap-1.5 text-xs">
              <BarChart3 className="w-3 h-3 text-green-500" />
              <span className="text-green-600 dark:text-green-400 font-medium">
                {(relevance * 100).toFixed(0)}% relevant
              </span>
            </div>
          )}
          {wikiData?.pageUrl && (
            <a href={wikiData.pageUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
              <ExternalLink className="w-3 h-3" /> Wikipedia
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
