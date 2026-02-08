import json
import re
from typing import Dict, List, Tuple


class AgenticChunker:
    """
    Intelligent text chunker that processes documents to extract
    question-answer pairs for flashcard generation.
    """

    def __init__(self, model):
        self.model = model
        self.min_chunk_size = 50  # Minimum characters per chunk
        self.max_chunk_size = 1000  # Maximum characters per chunk

    def read_txt_file(self, file_path: str) -> str:
        """Read and return content from a .txt file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text into logical segments.
        Handles paragraphs, bullet points, and numbered lists.
        """
        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        # Split into paragraphs
        paragraphs = text.split("\n\n")

        segments = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Handle bullet points and numbered lists
            if re.match(r"^[\•\-\*\d+\.]\s", para):
                # Split list items
                items = re.split(r"\n(?=[\•\-\*\d+\.])", para)
                segments.extend([item.strip() for item in items if item.strip()])
            else:
                # Keep paragraph as-is if it's short enough
                if len(para) <= self.max_chunk_size:
                    segments.append(para)
                else:
                    # Split long paragraphs by sentences
                    sentences = self._split_into_sentences(para)
                    segments.extend(sentences)

        return segments

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Simple sentence splitter
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_qa_pairs(self, text: str) -> List[Dict[str, str]]:
        """
        Extract question-answer pairs from text.
        The LLM identifies facts and generates appropriate questions.
        """
        prompt = f"""You are a study assistant creating flashcards from educational content.

        Analyze the following text and extract individual facts. For each fact, create a clear question-answer pair.

        Guidelines:
        1. Each fact should be atomic (one concept per flashcard)
        2. Questions should be clear and specific
        3. Answers should be concise but complete
        4. If the text contains an explicit question, use it directly
        5. For statements, generate an appropriate question that tests understanding

        Text:
        {text}

        Return ONLY valid JSON in this exact format:
        {{"qa_pairs": [{{"question": "What is photosynthesis?", "answer": "The process by which plants convert light energy into chemical energy"}}, {{"question": "What organelle performs photosynthesis?", "answer": "Chloroplasts"}}]}}

        Return JSON:"""

        try:
            print("The model is: ", self.model)
            response = self.model.invoke(prompt)

            # Extract JSON from response
            content = response.content
            if hasattr(content, "__iter__") and not isinstance(content, str):
                # Handle list of content blocks
                content = (
                    content[0].text if hasattr(content[0], "text") else str(content[0])
                )
            elif not isinstance(content, str):
                content = str(content)

            # Clean up the response to extract JSON
            content = content.strip()

            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                content = json_match.group()

            result = json.loads(content)

            if "qa_pairs" not in result:
                print(f"Warning: Invalid response format. Got: {content}")
                return []

            return result["qa_pairs"]

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response was: {content}")
            return []
        except Exception as e:
            # print(e)
            print(f"Error extracting QA pairs: {e}")
            raise e
            # return []

    def should_merge_chunks(self, chunk1: Dict, chunk2: Dict) -> Tuple[bool, str]:
        """
        Determine if two chunks should be merged based on topic coherence.
        """
        if not chunk1["qa_pairs"] or not chunk2["qa_pairs"]:
            return False, "One or both chunks are empty"

        # Don't merge if combined size is too large
        combined_size = len(chunk1["text"]) + len(chunk2["text"])
        if combined_size > self.max_chunk_size:
            return False, "Combined size would be too large"

        prompt = f"""Analyze these two groups of flashcard questions and determine if they relate to the same topic.

        Group A Questions:
        {[qa["question"] for qa in chunk1["qa_pairs"][:3]]}

        Group B Questions:
        {[qa["question"] for qa in chunk2["qa_pairs"][:3]]}

        Return JSON: {{"should_merge": true/false, "reason": "brief explanation"}}

        Return ONLY valid JSON:"""

        try:
            response = self.model.invoke(prompt)

            content = response.content
            if hasattr(content, "__iter__") and not isinstance(content, str):
                content = (
                    content[0].text if hasattr(content[0], "text") else str(content[0])
                )
            elif not isinstance(content, str):
                content = str(content)

            # Extract JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                content = json_match.group()

            result = json.loads(content)
            return result.get("should_merge", False), result.get("reason", "Unknown")

        except Exception as e:
            print(f"Error in should_merge_chunks: {e}")
            return False, "Error analyzing chunks"

    def chunk_text_file(self, file_path: str) -> List[Dict]:
        """
        Main method: Read a .txt file and chunk it into flashcard-ready segments.

        Args:
            file_path: Path to the .txt file

        Returns:
            List of chunks, each containing text and QA pairs
        """
        # Read file
        text = self.read_txt_file(file_path)

        # Preprocess into segments
        segments = self.preprocess_text(text)

        return self.chunk_segments(segments)

    def chunk_text(self, text: str) -> List[Dict]:
        """
        Chunk raw text string into flashcard-ready segments.

        Args:
            text: Raw text string

        Returns:
            List of chunks, each containing text and QA pairs
        """
        segments = self.preprocess_text(text)
        return self.chunk_segments(segments)

    def chunk_segments(self, segments: List[str]) -> List[Dict]:
        """
        Process segments into intelligent chunks with QA pairs.
        """
        if not segments:
            return []

        # Extract QA pairs for each segment
        segment_chunks = []
        for segment in segments:
            if len(segment) < self.min_chunk_size:
                # Skip very short segments
                continue

            qa_pairs = self.extract_qa_pairs(segment)

            if qa_pairs:  # Only include chunks with valid QA pairs
                segment_chunks.append(
                    {
                        "text": segment,
                        "qa_pairs": qa_pairs,
                        "char_count": len(segment),
                    }
                )

        if not segment_chunks:
            return []

        # Merge related chunks
        final_chunks = [segment_chunks[0]]

        for current_chunk in segment_chunks[1:]:
            last_chunk = final_chunks[-1]

            # Try to merge with previous chunk
            should_merge, reason = self.should_merge_chunks(last_chunk, current_chunk)

            if should_merge:
                # Merge chunks
                last_chunk["text"] = last_chunk["text"] + "\n\n" + current_chunk["text"]
                last_chunk["qa_pairs"].extend(current_chunk["qa_pairs"])
                last_chunk["char_count"] = len(last_chunk["text"])
                last_chunk["merge_reason"] = reason
            else:
                # Keep as separate chunk
                current_chunk["split_reason"] = reason
                final_chunks.append(current_chunk)

        return final_chunks

    def get_all_qa_pairs(self, chunks: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract all QA pairs from chunks into a flat list.
        Useful for directly creating flashcards.
        """
        all_pairs = []
        for chunk in chunks:
            all_pairs.extend(chunk.get("qa_pairs", []))
        return all_pairs
