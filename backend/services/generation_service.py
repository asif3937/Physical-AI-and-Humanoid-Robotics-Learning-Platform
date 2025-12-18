from typing import List, Dict, Any, Optional
import cohere
from config.settings import settings
from utils import logger
import json


class GenerationService:
    def __init__(self):
        if not settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY environment variable is required")

        self.client = cohere.Client(settings.COHERE_API_KEY)
        # Use the command model which is typically available in most Cohere tiers
        # If your specific Cohere plan doesn't have access to "command", you may need
        # to upgrade your plan or use a different model that's available to your account
        self.model = "command"  # Standard model that is typically available to most users
        print(f"Using Cohere model: {self.model}")
    
    def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        mode: str = "full_book",
        temperature: float = 0.1  # Lower temperature for more factual responses
    ) -> Dict[str, Any]:
        """
        Generate an answer based on the query and context

        Args:
            query: The user's question
            context: List of relevant context chunks
            mode: Either "full_book" or "selected_text_only"
            temperature: Controls randomness in the response (0.0 to 1.0)

        Returns:
            Dictionary with answer and citations
        """
        try:
            # Build the context text from the retrieved chunks
            context_texts = []
            citations = []

            for i, chunk in enumerate(context):
                text = chunk['text']
                context_texts.append(f"Context {i+1}: {text}")

                # Add citation info
                citation = {
                    "text": text,
                    "chapter": chunk.get('metadata', {}).get('chapter', 'Unknown'),
                    "page": chunk.get('metadata', {}).get('page', 'Unknown'),
                    "paragraph": chunk.get('metadata', {}).get('paragraph', 'Unknown'),
                    "relevance_score": chunk.get('relevance_score', 0.0)
                }
                citations.append(citation)

            context_str = "\n\n".join(context_texts)

            # Create the system prompt based on the mode
            if mode == "selected_text_only":
                preamble = (
                    "You are a helpful assistant that answers questions based ONLY on the provided selected text. "
                    "Do not use any external knowledge or make assumptions beyond what is explicitly stated in the selected text. "
                    "If the answer is not available in the provided selected text, respond with: "
                    "\"The answer is not available in the provided text.\""
                )
            else:  # full_book mode
                preamble = (
                    "You are a helpful assistant that answers questions based ONLY on the provided book content. "
                    "Do not use any external knowledge or make assumptions beyond what is explicitly stated in the provided content. "
                    "Always cite the specific passages you use to answer the question."
                )

            # Create the full message for Cohere
            if context_str:
                message = f"Context:\n{context_str}\n\nQuestion: {query}"
            else:
                message = f"Question: {query}"

            # Make the API call to Cohere
            response = self.client.chat(
                message=message,
                preamble=preamble,
                model=self.model,
                temperature=temperature,
                max_tokens=500,  # Adjust based on expected answer length
            )

            # Extract the answer
            answer = response.text.strip()

            # Check if the answer indicates insufficient context
            if "answer is not available in the provided text" in answer.lower():
                logger.info("Response indicates insufficient context")

            # Validate citations to ensure accuracy
            validated_citations = self._validate_citations(answer, citations)

            # Prepare the result
            result = {
                "answer": answer,
                "citations": validated_citations,
                "context_used": len(context),
                "model": self.model
            }

            logger.info(f"Generated answer with model {self.model}")
            return result
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            # Return a default response when model is unavailable
            if "model" in str(e) and "not found" in str(e):
                return {
                    "answer": "Model not available with your current Cohere plan. Please check your Cohere dashboard for available models.",
                    "citations": [],
                    "context_used": 0,
                    "model": self.model
                }
            raise
    
    def validate_answer_based_on_context(
        self,
        answer: str,
        context: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the answer is based on the provided context
        
        Args:
            answer: The generated answer
            context: List of context chunks that should support the answer
        
        Returns:
            True if the answer is consistent with the context
        """
        try:
            # This is a simple validation - in a more sophisticated implementation,
            # we might use semantic similarity, NLI models, or other techniques
            
            answer_lower = answer.lower()
            
            # Check if key terms from context appear in the answer
            context_terms = set()
            for chunk in context:
                text = chunk['text'].lower()
                # Extract some key terms (simplified approach)
                words = text.split()
                # Take some significant words (not stop words)
                for word in words[:20]:  # Check first 20 words for relevant terms
                    if len(word) > 4:  # Only consider words with more than 4 characters
                        context_terms.add(word)
            
            # Check if any of the context terms appear in the answer
            term_found = any(term in answer_lower for term in list(context_terms)[:5])  # Check first 5 terms

            logger.info(f"Answer validation result: {term_found}")
            return term_found
        except Exception as e:
            logger.error(f"Error validating answer: {str(e)}")
            return False

    def _validate_citations(self, answer: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate that citations accurately reflect the information in the answer

        Args:
            answer: The generated answer
            citations: List of citations to validate

        Returns:
            List of validated citations
        """
        try:
            validated_citations = []
            answer_lower = answer.lower()

            for citation in citations:
                citation_text = citation["text"].lower()

                # Check if the content of the citation appears in the answer
                # This is a simplified validation - in practice, you'd want more sophisticated NLP
                citation_content_in_answer = any(
                    sentence.strip() in answer_lower
                    for sentence in citation_text.split('. ')
                    if len(sentence.strip()) > 10  # Only check sentences with meaning
                )

                # Add validation flag to the citation
                validated_citation = citation.copy()
                validated_citation["validated"] = citation_content_in_answer
                validated_citations.append(validated_citation)

            logger.info(f"Validated {len(validated_citations)} citations")
            return validated_citations
        except Exception as e:
            logger.error(f"Error validating citations: {str(e)}")
            # Return original citations with validation flag if validation fails
            for citation in citations:
                citation["validated"] = False
            return citations