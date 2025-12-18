import logging
from typing import Dict, Any, List
from openai import OpenAI
from cohere import Client as CohereClient
from config.settings import settings
import json

logger = logging.getLogger(__name__)

class GenerationService:
    def __init__(self):
        self.language_model_provider = settings.LANGUAGE_MODEL_PROVIDER

        if self.language_model_provider.lower() == 'cohere':
            self.client = CohereClient(api_key=settings.COHERE_API_KEY)
        else:  # Default to OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE

    def generate_answer(self, query: str, context: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
        """
        Generate an answer based on the query and retrieved context
        """
        try:
            if not context:
                # No relevant context found, return a generic response
                return {
                    'answer': "I couldn't find relevant information in the book to answer your question. Please try rephrasing or ask about a different topic.",
                    'citations': []
                }

            # Construct the prompt with context
            context_str = "\n\n".join([f"Source: {chunk['source']}\nContent: {chunk['text']}" for chunk in context])

            system_prompt = f"""You are an AI assistant helping users understand content from textbooks.
            Answer questions based strictly on the provided context from the book.
            If the information isn't available in the context, say so directly.
            Always be concise, accurate, and helpful."""

            user_prompt = f"""Context: {context_str}\n\nQuestion: {query}\n\nAnswer:"""

            if self.language_model_provider.lower() == 'cohere':
                # Use Cohere API
                response = self.client.generate(
                    model=self.model,
                    prompt=user_prompt,
                    max_tokens=1000,
                    temperature=self.temperature
                )
                answer = response.generations[0].text
            else:  # Default to OpenAI
                # Call the OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=1000
                )

                answer = response.choices[0].message.content

            # Extract citations from context (sources of information)
            citations = []
            for chunk in context:
                citation_info = {
                    'source': chunk.get('source', 'unknown'),
                    'content_snippet': chunk.get('text', '')[:200] + "..." if len(chunk.get('text', '')) > 200 else chunk.get('text', '')
                }
                if citation_info not in citations:  # Avoid duplicate citations
                    citations.append(citation_info)

            logger.info(f"Generated answer for query: {query[:50]}...")
            return {
                'answer': answer,
                'citations': citations
            }

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': "Sorry, I encountered an error while generating a response. Please try again later.",
                'citations': []
            }