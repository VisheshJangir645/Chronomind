import re
import json
import logging
from typing import List, Dict

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
except ImportError:
    AutoTokenizer, AutoModelForSeq2SeqLM = None, None

logger = logging.getLogger(__name__)

# Knowledge base of historical context to enrich extracted events
CONTEXT_DB = {
    "1776": "The American Revolution was in full swing. The Continental Congress had declared independence on July 4th. British forces occupied New York City. Washington's army was demoralized after a string of defeats. The crossing of the Delaware on December 25th was a desperate gamble that revived the revolutionary cause.",
    "1789": "France was in severe economic crisis. King Louis XVI had called the Estates-General for the first time since 1614. The Third Estate declared itself the National Assembly. On July 14th, Parisians stormed the Bastille. The Declaration of the Rights of Man was adopted in August.",
    "1914": "Tensions between European imperial powers had been escalating for decades. The assassination of Archduke Franz Ferdinand in Sarajevo triggered a chain of alliance obligations. Within weeks, most of Europe was at war. The conflict would claim over 17 million lives.",
    "1939": "Nazi Germany invaded Poland on September 1st, triggering declarations of war from Britain and France. The Soviet Union invaded Poland from the east under the Molotov-Ribbentrop Pact. The Blitzkrieg tactics stunned the world with their speed and devastation.",
    "1945": "Germany surrendered unconditionally on May 8th (V-E Day). The United States dropped atomic bombs on Hiroshima and Nagasaki in August. Japan surrendered on September 2nd, ending World War II. The United Nations was formally established in October.",
    "1947": "India and Pakistan gained independence from British rule on August 15th and 14th respectively. The partition led to massive displacement and communal violence affecting millions. The Cold War between the US and Soviet Union began intensifying.",
    "1969": "The Apollo 11 mission landed humans on the Moon for the first time on July 20th. Neil Armstrong and Buzz Aldrin walked on the lunar surface while Michael Collins orbited above. The Vietnam War continued to escalate with widespread anti-war protests.",
    "1989": "The Berlin Wall fell on November 9th, symbolizing the end of the Cold War. Democratic movements swept across Eastern Europe. The Tiananmen Square protests in Beijing were violently suppressed in June.",
    "2001": "The September 11th attacks killed nearly 3,000 people and fundamentally altered global security policies. The US launched the War on Terror, invading Afghanistan in October. The world economy faced significant disruption.",
    "1453": "The Ottoman Empire, led by Sultan Mehmed II, captured Constantinople after a 53-day siege. This marked the definitive end of the Byzantine Empire and the Eastern Roman legacy spanning over a millennium. It shifted Mediterranean trade routes dramatically.",
    "1492": "Christopher Columbus reached the Americas on October 12th, opening an era of European exploration and colonization. Spain expelled Jews under the Alhambra Decree the same year. The Treaty of Granada ended the Reconquista.",
    "1857": "The Indian Rebellion of 1857 erupted against the British East India Company. Sepoys in Meerut mutinied and marched on Delhi. The revolt spread across northern India before being suppressed. It led to the dissolution of the Company and direct British Crown rule.",
    "1917": "The Russian Revolution overthrew the Tsarist autocracy. The Bolsheviks, led by Lenin, seized power in October. The US entered World War I. The Balfour Declaration supported a Jewish homeland in Palestine.",
    "1865": "The American Civil War ended with Lee's surrender at Appomattox. President Abraham Lincoln was assassinated at Ford's Theatre. The 13th Amendment abolished slavery throughout the United States.",
    "1066": "William the Conqueror defeated King Harold at the Battle of Hastings on October 14th. The Norman Conquest fundamentally transformed English law, language, and culture. The Domesday Book survey would follow in 1086.",
}


class TimelineExtractor:
    """
    Semantic Event Extractor with contextual enrichment.
    Uses FLAN-T5 when available, otherwise falls back to regex + context DB.
    """
    def __init__(self, model_name='google/flan-t5-base'):
        self.tokenizer = None
        self.model = None
        self.model_name = model_name
        self.ner_pipeline = False

    def load_models(self):
        if AutoTokenizer and AutoModelForSeq2SeqLM:
            try:
                logger.info(f"Loading Semantic T5 Model: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                self.ner_pipeline = True
            except Exception as e:
                logger.warning(f"Could not load T5: {e}. Using regex fallback.")
                self.ner_pipeline = True
        else:
            logger.warning("Transformers not installed. Using regex fallback.")
            self.ner_pipeline = True

    def process_text(self, text_chunk: str) -> List[Dict]:
        if self.model and self.tokenizer:
            return self._extract_with_t5(text_chunk)
        return self._extract_with_regex(text_chunk)

    def _extract_with_t5(self, text_chunk: str) -> List[Dict]:
        prompt = (
            "Extract the most significant historical event from the following text. "
            "Do not just copy a sentence. Summarize the core semantic action. "
            "Output strictly as JSON with keys: 'date', 'description', 'actor', 'location', 'significance_score' (1-10). "
            f"Text: {text_chunk}"
        )
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.model.generate(**inputs, max_length=256, temperature=0.1, num_beams=3)
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        try:
            cleaned_json = generated_text.strip("`").removeprefix("json").strip()
            event_dict = json.loads(cleaned_json)
            self._enrich_context(event_dict)
            return [event_dict]
        except json.JSONDecodeError:
            logger.error(f"T5 failed to output valid JSON. Falling back to regex.")
            return self._extract_with_regex(text_chunk)

    def _extract_with_regex(self, text_chunk: str) -> List[Dict]:
        events = []
        sentences = re.split(r'(?<=[.!?])\s+', text_chunk.strip())
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
                
            year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', sentence)
            extracted_date = f"{year_match.group(1)}-01-01" if year_match else "Unknown"
            
            # Extract proper nouns as actors
            words = sentence.split()
            actors = []
            for i, word in enumerate(words):
                clean = re.sub(r'[^a-zA-Z]', '', word)
                if i > 0 and clean and clean[0].isupper() and len(clean) > 2:
                    actors.append(clean)
            
            actor_name = " ".join(actors[:3]) if actors else None
            
            # Detect locations using common patterns
            loc_match = re.search(r'(?:in|at|near|across)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sentence)
            location = loc_match.group(1) if loc_match else None
            
            event = {
                'date': extracted_date,
                'description': sentence,
                'actor': actor_name,
                'location': location,
                'significance_score': 7.0
            }
            
            # Enrich with historical context
            self._enrich_context(event)
            events.append(event)
        
        if not events:
            year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', text_chunk)
            event = {
                'date': f"{year_match.group(1)}-01-01" if year_match else "Unknown",
                'description': text_chunk[:300],
                'actor': None,
                'location': None,
                'significance_score': 5.0
            }
            self._enrich_context(event)
            events.append(event)
            
        return events

    def _enrich_context(self, event: Dict):
        """Attach related historical context from the knowledge base."""
        date_str = event.get('date', '')
        year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', date_str)
        if year_match:
            year = year_match.group(1)
            if year in CONTEXT_DB:
                event['related_context'] = CONTEXT_DB[year]
