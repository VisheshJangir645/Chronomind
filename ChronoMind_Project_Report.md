# AI Project 
## INT428 (ARTIFICIAL INTELLIGENCE ESSENTIALS)
## COMPUTER SCIENCE AND ENGINEERING

**Submitted by:**  
Registration Number: [Insert Registration Number]  
Roll No.: [Insert Roll Number]  
Section: [Insert Section]  

**Submitted to:**  
[Insert Faculty Name]  

**Student Name:** Vishesh Jangir  
**Branch & Semester:** B. Tech CSE / [Insert Semester]  
**Project Title:** ChronoMind — AI-Powered Historical Timeline Generator  
**Guide/Faculty Name:** [Insert Faculty Name]  

---

## Student Declaration
To whom so ever it may concern

I hereby declare that the project work entitled "ChronoMind — AI-Powered Historical Timeline Generator" is an authentic record of my own work carried out as requirements of AI Project for the award of B. Tech degree in Computer Science and Engineering from Lovely Professional University, Phagwara. All the information furnished in this AI project report is based on my own intensive work and is genuine.

**Name of the student:** Vishesh Jangir  
**Registration Number:** [Insert Registration Number]  
**Dated:** 4th May 2026  

---

## ACKNOWLEDGEMENT
I express my sincere gratitude to my project mentor for providing invaluable guidance, continuous support, and motivation throughout the development of this project. Their insightful suggestions and expert advice have been instrumental in shaping this work.

I extend my heartfelt thanks to the School of Computer Science and Engineering, Lovely Professional University, for providing the necessary infrastructure and resources that facilitated the successful completion of this project.

I am also grateful to my fellow students and peers who provided constructive feedback and encouragement throughout the development process. Finally, I would like to thank my family for their unwavering support and encouragement.

---

## TABLE OF CONTENTS
1. Front page
2. Declaration
3. Acknowledgement
4. Table of Contents
5. **Section A:** Project Overview
6. **Section B:** Model & API Details
7. **Section C:** Context & Data Handling
8. **Section D:** Model Configuration & Behavior
9. **Section E:** Technology Stack
10. **Section F:** Implementation Evidence (Code Snippets & Description)
11. **Section G:** GitHub Repository Link
12. System Prompt (Appendix)

---

## Section A: Project Overview

### Q1. Type of AI System Developed
☐ Rule-based  
☑ Retrieval-based (Uses FAISS Vector Search and MediaWiki API)  
☑ Generative (LLM-based) (Uses FLAN-T5 for semantic event extraction)  
☑ Hybrid (Combines Retrieval-Augmented Generation, Graph DB, and NLP Extraction)  

**Explanation:** ChronoMind implements a highly advanced Hybrid AI system. It combines a 5-Stage Intelligence Pipeline utilizing the MediaWiki API for data retrieval, HuggingFace transformers (FLAN-T5) for semantic information extraction, dense vector search (Bi-Encoders with FAISS) for broad retrieval, and Cross-Encoders for precision re-ranking. It also constructs a Semantic Knowledge Graph using Neo4j.

### Q2. Platform Used for Deployment
☑ Web Application (React/Vite frontend with a FastAPI backend)  
☐ Mobile Application  
☐ Desktop Application  
☐ Messaging Platform  
☐ Cloud API only (no UI)  

**Explanation:** The application consists of a decoupled architecture: a robust Python FastAPI backend and a visually rich Single Page Application (SPA) frontend built with React and Vite. The backend is containerized for cloud deployment.

### Q3. Deployment Link / Access Details

**Deployment URL:** https://chronomind-backend.onrender.com/api/v1/query (Backend API)  
**GitHub Repository:** [Insert GitHub Link]

---

## Section B: Model & API Details

### Q4. Type of API Used
☐ OpenAI API  
☐ Google Gemini API  
☐ Azure OpenAI API  
☑ Custom REST API (Hosted FastAPI backend + Wikipedia API)  
☑ Local Model API (HuggingFace Transformers run locally/in-container)  

**Explanation:** ChronoMind relies on the MediaWiki REST API to dynamically fetch historical data based on user queries. Simultaneously, it serves its own intelligent endpoints using a FastAPI backend which runs local open-source HuggingFace models for NLP processing.

### Q5. Model Name Used
**Model Names:** 
1. `google/flan-t5-base` (For semantic extraction)
2. `all-MiniLM-L6-v2` (Bi-Encoder for FAISS Vector Embeddings)
3. `cross-encoder/ms-marco-MiniLM-L-6-v2` (Cross-Encoder for precision Re-ranking)

**Explanation:** The system uses `google/flan-t5-base` to intelligently extract structured event JSON (date, actor, location) from unstructured text. It then uses SentenceTransformers (`MiniLM` variants) to handle a two-stage Retrieval-Augmented Generation (RAG) pipeline for scoring and ranking historical relevancy.

### Q6. Model Version
**Model Version:** Latest stable variants pulled from HuggingFace Hub.

**Explanation:** The HuggingFace `AutoModelForSeq2SeqLM` and `SentenceTransformer` libraries automatically download and cache the latest stable weights for the specified models.

---

## Section C: Context & Data Handling

### Q7. Contextual Memory Usage
☑ No memory (Stateless Query-Driven system)  
☐ Session-based memory  
☑ Long-term memory (Database/Vector Store) (Uses FAISS & Neo4j)  
☐ Hybrid memory approach  

**Explanation:** 
*   **Stateless Execution:** Each user query to the FastAPI backend is stateless and independent.
*   **Long-term Memory Storage:** Extracted events are permanently embedded into a FAISS Vector Database for O(log N) similarity search, and causally linked inside a Neo4j Knowledge Graph.

### Q8. Flow of Data in the System
**Data Flow Explanation:**
*   **Step 1:** User inputs a historical query in the React frontend and clicks "Generate".
*   **Step 2:** Frontend sends an Axios POST request to `/api/v1/query` on the FastAPI backend.
*   **Step 3:** `WikiRetriever` searches Wikipedia for the topic, cleans the raw text of academic noise, and performs candidate extraction.
*   **Step 4:** The `MasterPipeline` kicks in. Text chunks are passed to the `TimelineExtractor` which uses the `FLAN-T5` model (or a robust regex fallback) to extract structured events.
*   **Step 5:** `TemporalReasoner` resolves colloquial dates (e.g., "late 19th century") into strict ISO-8601 bounds.
*   **Step 6:** The `RAGService` indexes these events. A Bi-Encoder fetches the top 100 relevant candidates, and a Cross-Encoder trims this to the top 10 most historically pertinent events.
*   **Step 7:** Events are optionally inserted into the Neo4j Knowledge Graph.
*   **Step 8:** The structured timeline JSON is returned to the frontend where Framer Motion animates the interactive timeline layout.

---

## Section D: Model Configuration & Behavior

### Q9. Model Parameters Used

| Parameter | Value | Justification |
| :--- | :--- | :--- |
| **Temperature (T5)** | `0.1` | Ensures highly deterministic, factual JSON extraction without hallucinations. |
| **Num Beams (T5)** | `3` | Uses beam search to find the most probable sequence during semantic extraction. |
| **Max Length (T5)** | `256` | Limits the extraction length to ensure concise historical facts. |
| **Top K (Bi-Encoder)** | `100` | Pulls a broad pool of candidates rapidly from FAISS. |
| **Top N (Cross-Encoder)**| `10` | Narrows down to the top 10 most relevant historical events for UI display. |

### Q10. Thinking Level & Role Assignment
**Thinking Level:**
☐ Basic (direct answers)  
☐ Intermediate (context-aware reasoning)  
☑ Advanced (multi-step reasoning) (Graph linking and Semantic RAG)  

**Role Assigned to System:**
☑ Domain Expert — Historical Intelligence Engine

**Thinking Level:** Advanced Reasoning — ChronoMind does not just fetch text; it utilizes Temporal Reasoning to map ambiguous periods ("Victorian Era") to exact dates, computes Relevancy Scores using four dimensions (Semantic Overlap, Action Presence, Causal Language, Entity Richness), and ranks them using multi-stage ML pipelines.

---

## Section E: Technology Stack

### Q11. Technology Stack Used
| Layer | Technology / Tool |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, React 18, Vite |
| **UI/UX Frameworks** | Tailwind CSS, Framer Motion, Lucide React icons |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Machine Learning** | HuggingFace Transformers, SentenceTransformers, PyTorch |
| **Vector Search** | FAISS (Facebook AI Similarity Search) |
| **Database** | Neo4j (Graph Database) |
| **Data Parsing** | Pydantic (Schema Validation) |
| **Cloud / Hosting** | Backend hosted on Render (Containerized via Docker) |

---

## Section F: Implementation Evidence (Code Snippets & Description)

### Q12. API Call Code Snippet
The following code from `App.jsx` shows how the frontend queries the ChronoMind backend:
```javascript
const fetchTimeline = async (e) => {
  e.preventDefault();
  if (!query.trim() || isLoading) return;
  
  setIsLoading(true);
  try {
    const response = await axios.post('https://chronomind-backend.onrender.com/api/v1/query', {
      query: query.trim()
    }, { timeout: 60000 });
    
    setEvents(response.data.events || []);
    setMeta({
      topic: response.data.topic,
      summary: response.data.summary,
      thumbnail: response.data.thumbnail
    });
  } catch (err) {
    setError('Could not fetch timeline. Please check your connection and try again.');
  }
};
```

### Q13. Domain Logic / Extraction Code Snippet
The Semantic Extraction using FLAN-T5 from `extractor.py`:
```python
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
        return self._extract_with_regex(text_chunk)
```

### Q14. Application Working Interface Description
The ChronoMind web interface consists of:
*   **Dynamic Backgrounds:** Ambient glowing orbs utilizing Tailwind blur classes that adapt to dark/light mode.
*   **Search Interface:** A premium, glassmorphism input bar with an animated search button and loading states (`framer-motion` loaders).
*   **Topic Summary Card:** Displays the Wikipedia extracted summary and thumbnail of the queried topic.
*   **Interactive Timeline Axis:** A vertical timeline layout. Events are marked with interactive dots that user can click to expand the `EventCard`.
*   **Animated Event Cards:** When triggered, cards gracefully animate into view, displaying the event date, headline, description, actors involved, and relevant Wikipedia images.

---

## Section G: GitHub Repository Link
**Repository URL:** [Insert GitHub Link]

The repository is structured into `timeline_frontend/` and `timeline_backend/`. Both folders include their respective dependencies (`package.json`, `requirements.txt`) and instructions for local execution.

---

## System Prompt (Appendix)
While ChronoMind is primarily an extraction engine and not a conversational chatbot, the FLAN-T5 zero-shot prompt acts as the system logic director:

```text
Extract the most significant historical event from the following text.
Do not just copy a sentence. Summarize the core semantic action.
Output strictly as JSON with keys: 
'date', 'description', 'actor', 'location', 'significance_score' (1-10).
Text: {text_chunk}
```

---

## Declaration
I confirm that the information provided above is accurate to the best of my knowledge.

**Student Signature:** Vishesh Jangir  
**Date:** 04.05.2026
