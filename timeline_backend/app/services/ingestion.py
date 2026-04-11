import re
import logging
from typing import List

logger = logging.getLogger(__name__)

try:
    import spacy
except ImportError:
    spacy = None

class IngestionLayer:
    """
    The primary defensive boundary of the ChronoMind pipeline.
    Sanitizes filthy, heterogeneous data sources (Wikipedia scrapes, PDF OCR, Textbooks)
    into pristine, mathematically reliable chunks strictly optimized for the Transformer limits (512 tokens).
    """
    def __init__(self, target_chunk_words: int = 350):
        self.target_chunk_words = target_chunk_words
        
        # Load a deterministic NLP model for exact Sentence Boundary Disambiguation
        if spacy:
            try:
                # Disabling heavy pipelines (NER/Parsers) because we just need lightning-fast sentence bounding
                self.nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger", "lemmatizer"])
            except OSError:
                logger.warning("Spacy model 'en_core_web_sm' missing. Using Regex fallback.")
                self.nlp = None
        else:
            self.nlp = None

    def process_document(self, document_text: str) -> List[str]:
        """
        Transforms an entire 50-page raw text document into an array of BERT-ready contextual paragraphs.
        """
        if not document_text or not isinstance(document_text, str):
            return []

        logger.info("Ingestion Stage 1: Absolute Noise Purge")
        clean_text = self._clean_noise(document_text)

        logger.info("Ingestion Stage 2: Linguistic Sentence Segmentation")
        sentences = self._segment_sentences(clean_text)

        logger.info("Ingestion Stage 3: Contextual Slide-Chunking")
        chunks = self._chunk_for_transformers(sentences)

        return chunks

    def _clean_noise(self, text: str) -> str:
        # 1. Purge Wikipedia/Academic citation block redundancy (e.g. [14], [citation needed], (Smith, 2014))
        text = re.sub(r'\[\d+\]|\[citation needed\]', '', text)
        text = re.sub(r'\([A-Za-z]+,\s\d{4}\)', '', text)
        
        # 2. Markdown Link Anchor flattening. Turns "[French Revolution](http...)" into "French Revolution"
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 3. OCR Artifact purge (strips lonely bullet points, dashed lines, page numbers)
        text = re.sub(r'^\s*[-•]\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE) # Page numbers isolated on a newline
        
        # 4. Global whitespace/tab/newline compression
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _segment_sentences(self, text: str) -> List[str]:
        """
        Naive Regex like `text.split('.')` destroys historical abbreviations like "Lt. Gen. Washington".
        Spacy dependencies build syntactic dependency trees to avoid splitting mid-sentence.
        """
        if self.nlp:
            # Bypasses Python GIL limits for C-level parsing speeds
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        else:
            # Fallback regex capturing End-of-sentence punctuation followed by a capital letter
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
            
        # Drop fragmented noise. A single word like "Conclusion." is not a valid historical payload.
        return [s for s in sentences if len(s.split()) >= 4]

    def _chunk_for_transformers(self, sentences: List[str]) -> List[str]:
        """
        SpanBERT and RoBERTa mathematically crash (IndexOutOfBoundsException) if Token count > 512.
        This algorithm aggregates sentences functionally until the limit is physically reached.
        """
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            word_count = len(sentence.split())
            
            # If the current sentence exceeds the chunk bounds, we flush the buffer
            if current_word_count + word_count > self.target_chunk_words:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_word_count = word_count
            else:
                current_chunk.append(sentence)
                current_word_count += word_count
                
        # Flush the final remainder
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
