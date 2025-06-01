import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from config import Config
from models import Message, Task
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import spacy
from textblob import TextBlob
from gensim.summarization import summarize
from functools import lru_cache

logger = logging.getLogger(__name__)

class AIServices:
    def __init__(self):
        self._initialize_nlp()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        
    def _initialize_nlp(self) -> None:
        """Initialize NLP components with error handling"""
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            logger.info("Downloading spaCy model...")
            spacy.cli.download('en_core_web_sm')
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            logger.error(f"Failed to initialize spaCy: {e}")
            raise RuntimeError("Failed to initialize NLP components")
    
    @lru_cache(maxsize=1000)
    def _process_text(self, text: str) -> spacy.tokens.Doc:
        """Process text with spaCy with caching"""
        return self.nlp(text.lower())
    
    def analyze_message_priority(self, content: str) -> Tuple[str, float]:
        """Analyze message content to determine priority"""
        try:
            if not content.strip():
                return 'Low', 0.0
                
            doc = self._process_text(content)
            blob = TextBlob(content)
            sentiment_score = blob.sentiment.polarity
            
            # Get settings from config
            settings = Config.AI_SETTINGS['priority']
            
            # Priority indicators with weights from config
            urgent_terms = {'urgent', 'asap', 'emergency', 'immediate', 'critical', 'important', 'priority'}
            deadline_terms = {'deadline', 'due', 'by', 'before', 'tomorrow', 'today', 'tonight'}
            action_terms = {'need', 'must', 'required', 'necessary', 'mandatory'}
            
            # Calculate weighted scores
            scores = {
                'urgent': settings['urgent_terms_weight'] if any(token.text in urgent_terms for token in doc) else 0,
                'deadline': settings['deadline_terms_weight'] if any(token.text in deadline_terms for token in doc) else 0,
                'action': settings['action_terms_weight'] if any(token.text in action_terms for token in doc) else 0,
                'date': settings['date_weight'] if any(ent.label_ in {'DATE', 'TIME'} for ent in doc.ents) else 0,
                'sentiment': settings['sentiment_weight'] * abs(sentiment_score) if sentiment_score < 0 else 0
            }
            
            priority_score = sum(scores.values())
            
            # Determine priority level using thresholds from config
            if priority_score > settings['high_threshold']:
                return 'High', priority_score
            elif priority_score > settings['medium_threshold']:
                return 'Medium', priority_score
            return 'Low', priority_score
                
        except Exception as e:
            logger.error(f"Error in priority analysis: {e}")
            return 'Medium', 0.5
    
    def suggest_actions(self, content: str) -> List[Dict]:
        """Analyze content and suggest relevant actions"""
        try:
            if not content.strip():
                return []
                
            doc = self._process_text(content)
            actions = []
            
            # Extract action items using dependency parsing
            for sent in doc.sents:
                roots = [token for token in sent if token.dep_ == 'ROOT']
                if not roots:
                    continue
                    
                root = roots[0]
                if root.pos_ == 'VERB':
                    # Calculate confidence based on verb type and context
                    confidence = 0.8 if root.tag_ == 'VB' else 0.6
                    if any(child.dep_ in {'dobj', 'pobj'} for child in root.children):
                        confidence += 0.1
                    
                    action = {
                        'type': 'task',
                        'description': sent.text,
                        'confidence': min(confidence, 1.0)
                    }
                    
                    # Extract dates and add to action
                    dates = [ent.text for ent in sent.ents if ent.label_ in {'DATE', 'TIME'}]
                    if dates:
                        action['dates'] = dates
                        action['confidence'] += 0.1
                    
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error suggesting actions: {e}")
            return []
    
    def find_similar_messages(self, content: str, limit: int = 5) -> List[Message]:
        """Find similar messages using TF-IDF and cosine similarity"""
        try:
            if not content.strip():
                return []
                
            settings = Config.AI_SETTINGS['similarity']
            recent_messages = Message.query.order_by(Message.created_at.desc()).limit(settings['max_messages']).all()
            
            if not recent_messages:
                return []
            
            # Create document corpus with preprocessing
            corpus = [msg.content for msg in recent_messages]
            corpus.append(content)
            
            # Calculate TF-IDF vectors
            try:
                tfidf_matrix = self.vectorizer.fit_transform(corpus)
            except Exception as e:
                logger.error(f"TF-IDF calculation failed: {e}")
                return []
            
            # Calculate similarities
            try:
                new_vector = tfidf_matrix[-1]
                similarities = np.dot(tfidf_matrix[:-1], new_vector.T).toarray().flatten()
            except Exception as e:
                logger.error(f"Similarity calculation failed: {e}")
                return []
            
            # Get top similar messages above threshold
            similar_indices = (-similarities).argsort()[:limit]
            return [
                recent_messages[i] for i in similar_indices 
                if similarities[i] > settings['min_similarity_score']
            ]
            
        except Exception as e:
            logger.error(f"Error finding similar messages: {e}")
            return []
    
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary of the content"""
        try:
            if not content.strip():
                return ""
                
            settings = Config.AI_SETTINGS['summarization']
            max_length = settings['max_length']
            
            # Return as is if content is short enough
            if len(content) <= max_length:
                return content
            
            # Try gensim summarization first
            try:
                summary = summarize(content, word_count=30)
                if summary:
                    return summary[:max_length] + ("..." if len(summary) > max_length else "")
            except:
                pass
            
            # Fall back to extractive summarization
            doc = self._process_text(content)
            sentences = [sent.text.strip() for sent in doc.sents]
            
            if len(sentences) < settings['min_sentences']:
                return sentences[0][:max_length] + ("..." if len(sentences[0]) > max_length else "")
            
            # Calculate sentence vectors
            sentence_vectors = []
            for sent in sentences:
                sent_doc = self._process_text(sent)
                if sent_doc.vector_norm:  # Check if vector exists
                    sentence_vectors.append(sent_doc.vector)
                else:
                    sentence_vectors.append(np.zeros(sent_doc.vector.shape))
            
            # Cluster sentences
            n_clusters = min(settings['max_clusters'], len(sentences))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            
            try:
                kmeans.fit(sentence_vectors)
                # Get sentences closest to cluster centers
                closest_sentences = []
                for center in kmeans.cluster_centers_:
                    distances = [np.linalg.norm(center - vec) for vec in sentence_vectors]
                    closest_idx = np.argmin(distances)
                    closest_sentences.append(sentences[closest_idx])
                
                summary = ' '.join(closest_sentences)
                return summary[:max_length] + ("..." if len(summary) > max_length else "")
            except:
                # Fallback to first sentence if clustering fails
                return sentences[0][:max_length] + "..."
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return content[:max_length] + "..."
    
    def analyze_task_dependencies(self, tasks: List[Task]) -> Dict:
        """Analyze task descriptions to identify potential dependencies"""
        try:
            if not tasks:
                return {}
                
            settings = Config.AI_SETTINGS['task_dependencies']
            dependencies = {}
            task_docs = {}
            
            # Process all task texts first
            for task in tasks:
                if task.description:
                    task_docs[f"desc_{task.id}"] = self._process_text(task.description)
                task_docs[f"title_{task.id}"] = self._process_text(task.title)
            
            # Analyze dependencies
            for task in tasks:
                task_deps = set()
                
                # Get task documents
                task_desc_doc = task_docs.get(f"desc_{task.id}")
                task_title_doc = task_docs[f"title_{task.id}"]
                
                for other_task in tasks:
                    if other_task.id == task.id:
                        continue
                    
                    other_title_doc = task_docs[f"title_{other_task.id}"]
                    
                    # Check title similarity
                    if task_desc_doc:
                        title_sim = task_desc_doc.similarity(other_title_doc)
                        if title_sim > settings['similarity_threshold']:
                            task_deps.add(other_task.id)
                    
                    # Check semantic similarity
                    sem_sim = task_title_doc.similarity(other_title_doc)
                    if sem_sim > settings['similarity_threshold']:
                        task_deps.add(other_task.id)
                
                if task_deps:
                    dependencies[task.id] = list(task_deps)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing task dependencies: {e}")
            return {}

# Initialize AI services as a singleton
ai_services = AIServices() 