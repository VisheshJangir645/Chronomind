import re
import logging
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ============================================================
# NOISE PATTERNS — sentences matching these are REJECTED
# ============================================================
NOISE_PATTERNS = [
    # Academic / editorial content
    r'(?i)\bfurther\s+reading\b', r'(?i)\bsee\s+also\b', r'(?i)\breferences\b',
    r'(?i)\bbibliography\b', r'(?i)\bexternal\s+links\b', r'(?i)\bnotes\s+and\b',
    r'(?i)\badvanced\s+stud', r'(?i)\bresearch\s+area', r'(?i)\bhistoriograph',
    r'(?i)\bfor\s+more\s+information\b', r'(?i)\baccording\s+to\s+some\s+scholars\b',
    r'(?i)\bhas\s+been\s+(widely\s+)?debated\b', r'(?i)\bscholarship\s+on\b',
    # Category / classification noise
    r'(?i)\bis\s+a\s+(sub)?field\b', r'(?i)\bis\s+a\s+branch\s+of\b',
    r'(?i)\brefers\s+to\s+the\s+study\b', r'(?i)\bis\s+defined\s+as\b',
    r'(?i)\bthe\s+term\s+.+\s+refers\b', r'(?i)\bis\s+an?\s+(academic|literary)\b',
    # Page structure noise
    r'^=+', r'^\d+\.\s', r'^\^', r'^\[edit\]',
]

# ============================================================
# ACTION VERBS — sentences containing these are MORE LIKELY real events
# ============================================================
ACTION_VERBS = [
    'invaded', 'declared', 'signed', 'defeated', 'captured', 'conquered',
    'assassinated', 'founded', 'established', 'abolished', 'surrendered',
    'launched', 'overthrew', 'annexed', 'bombed', 'massacred', 'revolted',
    'marched', 'blockaded', 'ratified', 'proclaimed', 'occupied', 'liberated',
    'negotiated', 'mobilized', 'attacked', 'retreated', 'collapsed', 'erupted',
    'enacted', 'outlawed', 'crowned', 'deposed', 'exiled', 'unified',
    'partitioned', 'intervened', 'broke out', 'began', 'ended', 'fell',
    'elected', 'appointed', 'resigned', 'died', 'born', 'discovered',
    'published', 'arrived', 'sailed', 'led', 'fought', 'won', 'lost',
    'withdrew', 'expelled', 'formed', 'dissolved', 'adopted', 'rejected',
    'succeeded', 'triggered', 'sparked', 'caused', 'resulted', 'killed',
]

# ============================================================
# CAUSAL CONNECTORS — used to score causal relevance
# ============================================================
CAUSAL_KEYWORDS = [
    'led to', 'resulted in', 'triggered', 'caused', 'sparked',
    'in response to', 'as a result', 'consequently', 'therefore',
    'following', 'due to', 'because of', 'paved the way',
    'contributed to', 'culminated in', 'preceded', 'provoked',
    'in retaliation', 'after the', 'which led', 'this led',
]


class WikiRetriever:
    """
    Intelligent Wikipedia retriever with 5-stage pipeline:
    FETCH → CLEAN → EXTRACT → SCORE & VALIDATE → ENRICH
    """
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"

    def fetch_historical_data(self, query: str) -> Dict:
        logger.info(f"WikiRetriever: Processing query '{query}'")

        title = self._search_title(query)
        if not title:
            return {"events": [], "summary": "", "thumbnail": None}

        summary_data = self._fetch_summary(title)
        full_text = self._fetch_full_text(title)
        images = self._fetch_images(title)

        # === 5-STAGE INTELLIGENCE PIPELINE ===
        # Stage 1: Clean noise from raw text
        clean_paragraphs = self._stage_clean(full_text)
        # Stage 2: Extract candidate events
        candidates = self._stage_extract(clean_paragraphs, title)
        # Stage 3: Score each candidate for relevance to query
        scored = self._stage_score(candidates, query, title)
        # Stage 4: Validate & filter — keep only real events above threshold
        validated = self._stage_validate(scored)
        # Stage 5: Enrich descriptions with context from surrounding text
        enriched = self._stage_enrich(validated, clean_paragraphs, query)

        logger.info(f"Pipeline: {len(candidates)} candidates → {len(validated)} validated → {len(enriched)} enriched")

        return {
            "topic": title,
            "summary": summary_data.get("extract", ""),
            "thumbnail": summary_data.get("thumbnail", {}).get("source"),
            "events": enriched,
            "images": images
        }

    # =================================================================
    # STAGE 1: NOISE CLEANING
    # =================================================================
    def _stage_clean(self, text: str) -> List[str]:
        """Remove academic noise, section headers, and non-event content."""
        if not text:
            return []

        clean = []
        for para in text.split('\n'):
            para = para.strip()
            if len(para) < 40:
                continue
            # Reject if matches any noise pattern
            if any(re.search(pat, para) for pat in NOISE_PATTERNS):
                continue
            # Reject pure section headers (== Header ==)
            if para.startswith('=='):
                continue
            clean.append(para)
        return clean

    # =================================================================
    # STAGE 2: CANDIDATE EXTRACTION
    # =================================================================
    def _stage_extract(self, paragraphs: List[str], topic: str) -> List[Dict]:
        """Extract candidate events: sentences with dates + action verbs."""
        candidates = []
        seen_descriptions = set()

        for para in paragraphs:
            sentences = re.split(r'(?<=[.!?])\s+', para)

            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 40 or len(sentence) > 600:
                    continue

                # Must contain a year
                year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', sentence)
                if not year_match:
                    continue

                year = year_match.group(1)
                year_int = int(year)
                if year_int < 800 or year_int > 2030:
                    continue

                # Dedup by normalized description
                norm = re.sub(r'\s+', ' ', sentence.lower().strip())
                if norm in seen_descriptions:
                    continue
                seen_descriptions.add(norm)

                full_date = self._extract_full_date(sentence, year)
                actors = self._extract_proper_nouns(sentence)
                location = self._extract_location(sentence)

                candidates.append({
                    "date": full_date,
                    "year": year,
                    "raw_sentence": sentence,
                    "actors": actors,
                    "location": location,
                    "source_para": re.sub(r'\s+', ' ', sentence),
                })

        return candidates

    # =================================================================
    # STAGE 3: RELEVANCE SCORING
    # =================================================================
    def _stage_score(self, candidates: List[Dict], query: str, topic: str) -> List[Dict]:
        """Score each candidate on 4 dimensions, producing a 0.0–1.0 relevance score."""
        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z]{3,}\b', query_lower))
        topic_words = set(re.findall(r'\b[a-z]{3,}\b', topic.lower()))
        key_terms = query_words | topic_words

        for cand in candidates:
            sentence = cand["raw_sentence"]
            sent_lower = sentence.lower()
            sent_words = set(re.findall(r'\b[a-z]{3,}\b', sent_lower))

            # Dimension 1: Semantic overlap with query (0.0–1.0)
            if key_terms:
                overlap = len(sent_words & key_terms) / len(key_terms)
            else:
                overlap = 0.0
            sem_score = min(overlap, 1.0)

            # Dimension 2: Action verb presence (0.0 or 0.25)
            has_action = any(v in sent_lower for v in ACTION_VERBS)
            action_score = 0.25 if has_action else 0.0

            # Dimension 3: Causal language (0.0 or 0.20)
            has_causal = any(k in sent_lower for k in CAUSAL_KEYWORDS)
            causal_score = 0.20 if has_causal else 0.0

            # Dimension 4: Entity richness — proper nouns count (0.0–0.20)
            entity_count = len(cand["actors"])
            entity_score = min(entity_count * 0.07, 0.20)

            # Penalty: too short sentences are likely fragments
            length_penalty = 0.0
            if len(sentence) < 60:
                length_penalty = -0.15

            total = sem_score + action_score + causal_score + entity_score + length_penalty
            cand["relevance_score"] = round(max(0.0, min(total, 1.0)), 3)

        # Sort by relevance descending
        candidates.sort(key=lambda c: c["relevance_score"], reverse=True)
        return candidates

    # =================================================================
    # STAGE 4: VALIDATION & FILTERING
    # =================================================================
    def _stage_validate(self, scored: List[Dict]) -> List[Dict]:
        """
        Keep only concrete historical events.
        Enforces minimum relevance threshold and action-verb requirement.
        """
        RELEVANCE_THRESHOLD = 0.15
        validated = []
        seen_years = set()

        for cand in scored:
            # Hard filter: below relevance threshold
            if cand["relevance_score"] < RELEVANCE_THRESHOLD:
                continue

            # Hard filter: must contain at least one action verb
            sent_lower = cand["raw_sentence"].lower()
            has_action = any(v in sent_lower for v in ACTION_VERBS)
            if not has_action:
                continue

            # Soft dedup: max 2 events per year to allow multiple important events
            year = cand["year"]
            year_count = sum(1 for v in validated if v["year"] == year)
            if year_count >= 2:
                continue

            validated.append(cand)

        # Sort chronologically
        validated.sort(key=lambda e: e["date"])

        # Cap at 10 high-quality events
        return validated[:10]

    # =================================================================
    # STAGE 5: ENRICHMENT
    # =================================================================
    def _stage_enrich(self, validated: List[Dict], paragraphs: List[str], query: str) -> List[Dict]:
        """
        Expand each event from a headline into a 3–5 sentence description.
        Gathers surrounding context from the source paragraphs.
        Adds causal links between consecutive events.
        """
        enriched = []
        full_text_joined = '\n'.join(paragraphs)

        for i, event in enumerate(validated):
            raw = event["raw_sentence"]
            year = event["year"]

            # Gather context: find sentences near this event's sentence in the source
            context_sentences = self._gather_context(raw, paragraphs, year)

            # Build enriched description
            description = self._build_rich_description(raw, context_sentences, query)

            # Generate a meaningful title (not just trimmed sentence)
            title = self._generate_smart_title(raw, event["actors"], event.get("location"))

            # Build causal links
            related_to = None
            if i > 0:
                prev = enriched[-1]
                related_to = prev["title"]

            enriched.append({
                "date": event["date"],
                "title": title,
                "description": description,
                "people": event["actors"],
                "location": event.get("location"),
                "relevance_score": event["relevance_score"],
                "related_to": related_to,
            })

        return enriched

    def _gather_context(self, raw_sentence: str, paragraphs: List[str], year: str) -> List[str]:
        """Find sentences near the raw event sentence in the source text for enrichment."""
        context = []
        raw_norm = raw_sentence[:50].lower()

        for para in paragraphs:
            if raw_norm in para.lower():
                # Found the paragraph containing this event — grab neighboring sentences
                all_sents = re.split(r'(?<=[.!?])\s+', para)
                for j, s in enumerate(all_sents):
                    if raw_norm[:30] in s.lower():
                        # Grab up to 2 sentences before and 2 after
                        start = max(0, j - 2)
                        end = min(len(all_sents), j + 3)
                        context = [s.strip() for s in all_sents[start:end] if s.strip() != raw_sentence.strip()]
                        break
                break

        # Also grab any sentence in other paragraphs mentioning the same year
        if len(context) < 2:
            for para in paragraphs:
                if year in para and raw_norm[:30] not in para.lower():
                    sents = re.split(r'(?<=[.!?])\s+', para)
                    for s in sents:
                        if year in s and len(s) > 40:
                            context.append(s.strip())
                            if len(context) >= 3:
                                break
                    if len(context) >= 3:
                        break

        return context[:4]

    def _build_rich_description(self, raw_sentence: str, context: List[str], query: str) -> str:
        """
        Synthesize a 3–5 sentence description from the raw event + context.
        Structure: What happened → Context/Why → Consequence.
        """
        parts = [raw_sentence.strip()]

        for ctx in context:
            ctx = ctx.strip()
            if not ctx or len(ctx) < 30:
                continue
            # Avoid near-duplicates
            if SequenceMatcher(None, raw_sentence.lower(), ctx.lower()).ratio() > 0.7:
                continue
            parts.append(ctx)
            if len(parts) >= 4:
                break

        return ' '.join(parts)

    def _generate_smart_title(self, sentence: str, actors: List[str], location: Optional[str]) -> str:
        """
        Generate a meaningful title from the sentence.
        Prefers: Actor + Action patterns, or known event names.
        """
        # Check for named events (Battle of X, Treaty of X, Siege of X)
        named_event = re.search(
            r'((?:Battle|Treaty|Siege|Fall|Declaration|Invasion|Conquest|Revolt|Revolution|'
            r'Assassination|Execution|Coronation|Abdication|Annexation|Partition|Armistice|'
            r'Massacre|Liberation|Occupation|Bombing|Conference)\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            sentence
        )
        if named_event:
            return named_event.group(1)

        # Check for "The X War/Revolution/Movement"
        named_movement = re.search(
            r'((?:The\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:War|Revolution|Rebellion|Uprising|Movement|Crisis|Pact|Act|Reform))',
            sentence
        )
        if named_movement:
            return named_movement.group(1)

        # Fallback: Actor + first verb
        if actors:
            # Find first action verb after actor
            for verb in ACTION_VERBS:
                if verb in sentence.lower():
                    idx = sentence.lower().index(verb)
                    end = min(idx + len(verb) + 30, len(sentence))
                    title_candidate = sentence[max(0, idx-20):end].strip()
                    # Clean up
                    title_candidate = re.sub(r'^[^A-Z]*', '', title_candidate)
                    if title_candidate and len(title_candidate) > 10:
                        return title_candidate[:60].rsplit(' ', 1)[0] if len(title_candidate) > 60 else title_candidate

        # Last fallback: first clause
        clause = sentence.split(',')[0].split(';')[0]
        if len(clause) > 65:
            clause = clause[:62] + '...'
        return clause

    # =================================================================
    # WIKIPEDIA API METHODS (unchanged from v3)
    # =================================================================
    def _search_title(self, query: str) -> Optional[str]:
        params = urllib.parse.urlencode({
            "action": "query", "list": "search",
            "srsearch": query, "srlimit": 1, "format": "json"
        })
        try:
            url = f"{self.SEARCH_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "ChronoMind/3.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("query", {}).get("search", [])
                return results[0]["title"] if results else None
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None

    def _fetch_summary(self, title: str) -> Dict:
        encoded = urllib.parse.quote(title, safe='')
        url = f"{self.BASE_URL}/page/summary/{encoded}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ChronoMind/3.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Summary fetch failed: {e}")
            return {}

    def _fetch_full_text(self, title: str) -> str:
        params = urllib.parse.urlencode({
            "action": "query", "titles": title,
            "prop": "extracts", "explaintext": True,
            "exlimit": 1, "format": "json"
        })
        try:
            url = f"{self.SEARCH_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "ChronoMind/3.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    return pdata.get("extract", "")
        except Exception as e:
            logger.error(f"Full text fetch failed: {e}")
        return ""

    def _fetch_images(self, title: str) -> List[str]:
        params = urllib.parse.urlencode({
            "action": "query", "titles": title,
            "prop": "images", "imlimit": 10, "format": "json"
        })
        image_urls = []
        try:
            url = f"{self.SEARCH_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "ChronoMind/3.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    for img in pdata.get("images", []):
                        img_title = img.get("title", "")
                        if any(x in img_title.lower() for x in ['.svg', 'icon', 'logo', 'commons-logo']):
                            continue
                        if any(x in img_title.lower() for x in ['.jpg', '.jpeg', '.png']):
                            img_url = self._get_image_url(img_title)
                            if img_url:
                                image_urls.append(img_url)
                            if len(image_urls) >= 3:
                                break
        except Exception as e:
            logger.error(f"Image fetch failed: {e}")
        return image_urls

    def _get_image_url(self, image_title: str) -> Optional[str]:
        params = urllib.parse.urlencode({
            "action": "query", "titles": image_title,
            "prop": "imageinfo", "iiprop": "url", "format": "json"
        })
        try:
            url = f"{self.SEARCH_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "ChronoMind/3.1"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    info = pdata.get("imageinfo", [{}])
                    if info:
                        return info[0].get("url")
        except Exception:
            pass
        return None

    def _extract_full_date(self, sentence: str, year: str) -> str:
        months = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        for mname, mnum in months.items():
            m1 = re.search(rf'{mname}\s+(\d{{1,2}}),?\s+{year}', sentence)
            if m1:
                return f"{year}-{mnum}-{m1.group(1).zfill(2)}"
            m2 = re.search(rf'(\d{{1,2}})\s+{mname}\s+{year}', sentence)
            if m2:
                return f"{year}-{mnum}-{m2.group(1).zfill(2)}"
        return f"{year}-01-01"

    def _extract_proper_nouns(self, sentence: str) -> List[str]:
        actors = []
        matches = re.findall(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b', sentence)
        skip = {'the', 'this', 'that', 'these', 'those', 'after', 'before', 'during',
                'however', 'although', 'meanwhile', 'furthermore', 'moreover'}
        for m in matches:
            if m.lower() not in skip:
                actors.append(m)
        return actors[:4]

    def _extract_location(self, sentence: str) -> Optional[str]:
        m = re.search(r'(?:in|at|near|from|to)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sentence)
        return m.group(1) if m else None


# Singleton
wiki_retriever = WikiRetriever()
