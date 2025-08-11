from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
import re
from openai import AsyncOpenAI
import tiktoken
from app.models import Exchange, Topic, Conversation, Entity
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class SummarizedContent:
    """Represents the output of a summarization operation.
    
    This class encapsulates the results of summarizing content, including the original ID,
    the generated summary, preserved entities, compression metrics, and additional metadata.
    It serves as a structured way to track and manage summarized content throughout the system.
    """
    original_id: str
    summary: str
    preserved_entities: List[Entity]
    compression_ratio: float
    metadata: Dict[str, Any]

@dataclass
class OptimizedContext:
    """Represents the optimized context after token reduction and summarization.
    
    This class holds the final optimized content along with token count information,
    preserved entities, and metadata about the optimization process. It's used to
    maintain the context window within token limits while preserving important information.
    """
    content: str
    token_count: int
    preserved_entities: List[Entity]
    metadata: Dict[str, Any]

class SummarizationStrategy(Protocol):
    """Protocol defining the interface for summarization strategies.
    
    This protocol ensures that any summarization implementation provides a consistent
    interface for summarizing content while preserving important entities.
    """
    def summarize(self, content: str, entities: List[Entity]) -> SummarizedContent:
        ...

class TokenOptimizationStrategy(Protocol):
    """Protocol defining the interface for token optimization strategies.
    
    This protocol ensures that any token optimization implementation provides a consistent
    interface for reducing token count while maintaining content quality.
    """
    def optimize(self, content: str, max_tokens: int) -> OptimizedContext:
        ...

class ProgressiveSummarization(SummarizationStrategy):
    """Implements progressive summarization using OpenAI's GPT models.
    
    This strategy uses GPT to create coherent summaries that preserve important entities
    and their relationships while eliminating redundancy. It's designed to handle multiple
    pieces of content and combine them into a single, cohesive narrative.
    """
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        logger.info("Initialized ProgressiveSummarization with OpenAI client")

    def _chunk_content(self, content: str, max_chunk_tokens: int = 4000) -> List[str]:
        """Split content into manageable chunks."""
        tokens = self.encoding.encode(content)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for token in tokens:
            if current_length + 1 > max_chunk_tokens:
                chunks.append(self.encoding.decode(current_chunk))
                current_chunk = [token]
                current_length = 1
            else:
                current_chunk.append(token)
                current_length += 1
        
        if current_chunk:
            chunks.append(self.encoding.decode(current_chunk))
        
        return chunks

    async def summarize(self, content: str, entities: List[Entity]) -> SummarizedContent:
        """Summarizes content while preserving important entities and relationships."""
        logger.info(f"Starting progressive summarization for content of length {len(content)}")
        
        # First, chunk the content if it's too large
        chunks = self._chunk_content(content)
        logger.info(f"Split content into {len(chunks)} chunks")
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                summary = await self._summarize_chunk(chunk, entities)
                chunk_summaries.append(summary)
                logger.info(f"Summarized chunk {i+1}/{len(chunks)}")
            except Exception as e:
                logger.error(f"Error summarizing chunk {i+1}: {e}")
                # If a chunk fails, use a basic summary
                chunk_summaries.append(chunk[:1000] + "...")
        
        # If we have multiple chunks, combine their summaries
        if len(chunk_summaries) > 1:
            try:
                combined_summary = await self._combine_summaries(chunk_summaries, entities)
                return SummarizedContent(
                    original_id="",
                    summary=combined_summary,
                    preserved_entities=entities,
                    compression_ratio=len(combined_summary.split()) / len(content.split()) if len(content.split()) > 0 else 1.0,
                    metadata={
                        "compression_level": 0.8,
                        "model": "gpt-4o-mini",
                        "temperature": 0.3,
                        "chunks_processed": len(chunks)
                    }
                )
            except Exception as e:
                logger.error(f"Error combining summaries: {e}")
                # Fallback to concatenating summaries
                return SummarizedContent(
                    original_id="",
                    summary="\n\n".join(chunk_summaries),
                    preserved_entities=entities,
                    compression_ratio=0.5,
                    metadata={"error": str(e)}
                )
        else:
            # If we only have one chunk, return its summary
            return SummarizedContent(
                original_id="",
                summary=chunk_summaries[0],
                preserved_entities=entities,
                compression_ratio=len(chunk_summaries[0].split()) / len(content.split()) if len(content.split()) > 0 else 1.0,
                metadata={
                    "compression_level": 0.8,
                    "model": "gpt-4o-mini",
                    "temperature": 0.3
                }
            )

    async def _summarize_chunk(self, chunk: str, entities: List[Entity]) -> str:
        """Summarize a single chunk of content."""
        system_prompt = """You are a summarization expert that helps combine and summarize content.
        Create a concise summary that:
        1. Preserves all important entities and their relationships
        2. Maintains chronological order and context
        3. Eliminates redundancy and unnecessary details
        4. Creates a cohesive narrative"""

        entity_names = [e.name for e in entities]
        user_prompt = f"""Content to summarize:
{chunk}

Important entities to preserve:
{', '.join(entity_names)}

Please create a coherent summary that preserves these entities and their relationships."""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()

    async def _combine_summaries(self, summaries: List[str], entities: List[Entity]) -> str:
        """Combine multiple chunk summaries into a single coherent summary."""
        system_prompt = """You are a summarization expert that helps combine multiple summaries into a single coherent narrative.
        Create a final summary that:
        1. Preserves all important entities and their relationships
        2. Maintains chronological order and context
        3. Eliminates redundancy between summaries
        4. Creates a cohesive narrative"""

        entity_names = [e.name for e in entities]
        summaries_text = "\n".join(f"Summary {i+1}:\n{summary}" for i, summary in enumerate(summaries))
        user_prompt = f"""Summaries to combine:
{summaries_text}

Important entities to preserve:
{', '.join(entity_names)}

Please create a coherent final summary that preserves these entities and their relationships."""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()

class TokenOptimizer(TokenOptimizationStrategy):
    """Implements token optimization using OpenAI's GPT models.
    
    This strategy ensures content fits within token limits while preserving key information.
    It uses tiktoken for token counting and GPT for content optimization when needed.
    """
    def __init__(self, openai_client: AsyncOpenAI, max_tokens: int = 4096):
        self.openai_client = openai_client
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    async def optimize(self, content: str, max_tokens: int) -> OptimizedContext:
        """Optimizes content to fit within token limits while preserving key information.
        
        This method first checks if the content is already within token limits. If not,
        it uses GPT to create a more concise version while maintaining the essential
        information and meaning of the original content.
        
        Args:
            content: The text content to be optimized
            max_tokens: Maximum number of tokens allowed in the optimized content
            
        Returns:
            OptimizedContext object containing the optimized content and token metrics
        """
        # Count tokens using tiktoken
        current_tokens = len(self.encoding.encode(content))
        
        if current_tokens <= max_tokens:
            return OptimizedContext(
                content=content,
                token_count=current_tokens,
                preserved_entities=[],  # This should be populated by the caller
                metadata={"optimization_level": 1.0}
            )
        
        # If we need to reduce tokens, use OpenAI to create a more concise version
        prompt = f"""Please create a more concise version of the following text while preserving its key information. The target length should be approximately {max_tokens} tokens.

Text to optimize:
{content}"""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise versions of text while preserving key information."},
                {"role": "user", "content": prompt}
            ],
        )
        
        optimized_content = response.choices[0].message.content
        optimized_tokens = len(self.encoding.encode(optimized_content))
        
        return OptimizedContext(
            content=optimized_content,
            token_count=optimized_tokens,
            preserved_entities=[],  # This should be populated by the caller
            metadata={
                "optimization_level": optimized_tokens / current_tokens,
                "model": "gpt-4o-mini",
            }
        )

class ContextWindowOptimizer:
    """Manages the optimization of context windows for large language models.
    
    This class coordinates between summarization and token optimization strategies
    to ensure content fits within model context windows while preserving important
    information and entities.
    """
    def __init__(
        self,
        summarization_strategy: SummarizationStrategy,
        token_optimization_strategy: TokenOptimizationStrategy
    ):
        self.summarization_strategy = summarization_strategy
        self.token_optimization_strategy = token_optimization_strategy

    async def optimize_context(
        self,
        content: str,
        entities: List[Entity],
        max_tokens: int
    ) -> OptimizedContext:
        """Optimizes context by applying summarization and token optimization in sequence.
        
        This method first summarizes the content to preserve important entities and
        relationships, then optimizes the token count if needed. The result is a
        context that fits within token limits while maintaining key information.
        
        Args:
            content: The text content to be optimized
            entities: List of entities that must be preserved
            max_tokens: Maximum number of tokens allowed in the final context
            
        Returns:
            OptimizedContext object containing the final optimized content
        """
        # First, try to summarize the content
        summarized = await self.summarization_strategy.summarize(content, entities)
        
        # Then, optimize the token count if needed
        optimized = await self.token_optimization_strategy.optimize(
            summarized.summary,
            max_tokens
        )
        
        # Update the preserved entities
        optimized.preserved_entities = summarized.preserved_entities
        
        return optimized

    def create_prompt_template(
        self,
        context: OptimizedContext,
        template_type: str = "default"
    ) -> str:
        """Creates a formatted prompt template using the optimized context.
        
        This method generates a structured prompt that incorporates the optimized
        context and preserved entities. It supports different template types for
        various use cases, such as default conversation or summary-based prompts.
        
        Args:
            context: The optimized context to include in the prompt
            template_type: Type of template to use (default or summary)
            
        Returns:
            Formatted prompt string ready for use with language models
        """
        # Create a prompt template based on the optimized context
        templates = {
            "default": """
Context: {context}

Please use the above context to inform your response. Pay special attention to the following entities:
{entities}

Response:
""",
            "summary": """
Summary of previous conversation:
{context}

Key points to consider:
{entities}

Please continue the conversation:
"""
        }
        
        template = templates.get(template_type, templates["default"])
        return template.format(
            context=context.content,
            entities="\n".join(f"- {entity.name}" for entity in context.preserved_entities)
        ) 