/**
 * Fetches enrichment data for an event from Wikipedia REST API.
 * Used for per-card image and summary enrichment.
 */
const WIKI_API = 'https://en.wikipedia.org/api/rest_v1';

const cache = new Map();

export async function fetchEventDetails(title) {
  if (!title || title.length < 3) return null;
  
  // Check cache first
  const cacheKey = title.toLowerCase().trim();
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  // Clean title for Wikipedia search
  const searchTerm = title
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .split(' ')
    .slice(0, 4)
    .join(' ');

  try {
    const encoded = encodeURIComponent(searchTerm);
    const resp = await fetch(`${WIKI_API}/page/summary/${encoded}`, {
      headers: { 'User-Agent': 'ChronoMind/3.0' }
    });
    
    if (!resp.ok) return null;
    
    const data = await resp.json();
    
    const result = {
      summary: data.extract || null,
      thumbnail: data.thumbnail?.source || null,
      originalImage: data.originalimage?.source || null,
      pageUrl: data.content_urls?.desktop?.page || null,
    };
    
    cache.set(cacheKey, result);
    return result;
  } catch {
    return null;
  }
}
