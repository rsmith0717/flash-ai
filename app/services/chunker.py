import asyncio
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple


class AgenticChunker:
    """
    Intelligent text chunker optimized for speed with batch processing, caching, and async execution.
    """

    def __init__(self, model):
        self.model = model
        self.min_chunk_size = 50
        self.max_chunk_size = 1000
        self.batch_size = 8  # Process 8 segments at once
        self.skip_merge_threshold = 10  # Skip merge phase for small documents
        self.qa_cache = {}  # In-memory cache for QA pairs
        self.merge_cache = {}  # Cache merge decisions
        self.executor = ThreadPoolExecutor(max_workers=3)  # For parallel execution

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
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def extract_qa_pairs_batch(self, texts: List[str]) -> List[List[Dict[str, str]]]:
        """
        Extract QA pairs from multiple text segments in a single LLM call.
        """
        if not texts:
            return []

        # Check cache
        results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self.qa_cache:
                print(f"Cache hit for segment {i}")
                results.append(self.qa_cache[cache_key])
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        if not uncached_texts:
            return results

        # Build segments text
        segments_text = ""
        for i, text in enumerate(uncached_texts):
            segments_text += f"\n\n--- SEGMENT {i} ---\n{text}"

        # IMPROVED PROMPT with better examples and instructions
        prompt = f"""You are a study assistant creating flashcards from educational content.

        Extract question-answer pairs from each text segment below. Return ONLY valid JSON.

        CRITICAL RULES:
        1. NEVER create questions or answers that are empty or just whitespace
        2. Questions MUST end with a question mark (?)
        3. Answers MUST be complete sentences or phrases with actual content
        4. Each segment MUST have at least 1 QA pair (unless segment is meaningless)
        5. Keep answers clear and concise (under 200 characters)
        6. Questions should test understanding, not just repeat the text
        7. You MUST complete the entire JSON - include ALL {len(uncached_texts)} segments

        GOOD EXAMPLES:
        {{"question": "What is photosynthesis?", "answer": "The process by which plants convert light energy into chemical energy using chlorophyll."}}
        {{"question": "What organelle performs photosynthesis?", "answer": "Chloroplasts"}}

        BAD EXAMPLES (DO NOT DO THIS):
        {{"question": "", "answer": "Something"}}  ❌ Empty question
        {{"question": "What is X?", "answer": ""}}  ❌ Empty answer
        {{"question": "Tell me about it", "answer": "It"}}  ❌ Vague/incomplete

        Text Segments:
        {segments_text}

        Return this exact JSON structure (ensure ALL segments 0-{len(uncached_texts) - 1} are included):
        {{
        "segments": [
            {{"segment_id": 0, "qa_pairs": [{{"question": "What is X?", "answer": "X is a complete answer with actual content."}}]}},
            {{"segment_id": 1, "qa_pairs": [{{"question": "What is Y?", "answer": "Y is another complete answer."}}]}}
        ]
        }}

        JSON:"""

        try:
            print(f"Calling LLM for {len(uncached_texts)} segments...")
            response = self.model.invoke(prompt)

            # Extract content
            content = self._extract_content_from_response(response)

            if not content or len(content) < 10:
                print("Warning: Response too short or empty")
                for idx in uncached_indices:
                    results[idx] = []
                return results

            print(f"Response received, length: {len(content)} chars")

            # Clean response
            content = content.strip()

            # Remove markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].strip() in ["```json", "```"]:
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

            # Extract JSON object
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                print("ERROR: No JSON object found in response")
                for idx in uncached_indices:
                    results[idx] = []
                return results

            content = content[json_start:json_end]

            # Repair incomplete JSON
            content = self._repair_incomplete_json(content)

            print("Attempting to parse JSON...")

            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON PARSE ERROR: {e.msg} at position {e.pos}")

                # Try aggressive repair
                print("Attempting aggressive JSON repair...")
                content = self._aggressive_json_repair(content, len(uncached_texts))

                try:
                    result = json.loads(content)
                    print("✓ Successfully repaired and parsed JSON!")
                except json.JSONDecodeError as e2:
                    print(f"Repair failed: {e2.msg}")
                    for idx in uncached_indices:
                        results[idx] = []
                    return results

            # Validate structure
            if not isinstance(result, dict) or "segments" not in result:
                print("ERROR: Invalid result structure")
                for idx in uncached_indices:
                    results[idx] = []
                return results

            # Extract and VALIDATE QA pairs
            qa_pairs_by_segment = {}
            total_rejected = 0

            for seg in result["segments"]:
                if not isinstance(seg, dict):
                    continue

                segment_id = seg.get("segment_id")
                qa_pairs = seg.get("qa_pairs", [])

                if segment_id is None:
                    continue

                # STRICT VALIDATION: Reject empty/invalid QA pairs
                valid_qa_pairs = []
                for qa in qa_pairs:
                    if not isinstance(qa, dict):
                        print(f"  ❌ Segment {segment_id}: QA pair is not a dict")
                        total_rejected += 1
                        continue

                    question = qa.get("question", "").strip()
                    answer = qa.get("answer", "").strip()

                    # Validate question
                    if not question:
                        print(f"  ❌ Segment {segment_id}: Empty question")
                        total_rejected += 1
                        continue

                    if len(question) < 5:
                        print(
                            f"  ❌ Segment {segment_id}: Question too short: '{question}'"
                        )
                        total_rejected += 1
                        continue

                    # Validate answer
                    if not answer:
                        print(
                            f"  ❌ Segment {segment_id}: Empty answer for question: '{question}'"
                        )
                        total_rejected += 1
                        continue

                    if len(answer) < 3:
                        print(
                            f"  ❌ Segment {segment_id}: Answer too short: '{answer}'"
                        )
                        total_rejected += 1
                        continue

                    # Check for placeholder/generic answers
                    if answer.lower() in [
                        "it",
                        "this",
                        "that",
                        "something",
                        "unknown",
                        "n/a",
                    ]:
                        print(
                            f"  ❌ Segment {segment_id}: Generic/placeholder answer: '{answer}'"
                        )
                        total_rejected += 1
                        continue

                    # All validation passed
                    valid_qa_pairs.append({"question": question, "answer": answer})

                if valid_qa_pairs:
                    qa_pairs_by_segment[segment_id] = valid_qa_pairs
                    print(
                        f"  ✓ Segment {segment_id}: {len(valid_qa_pairs)} valid QA pairs"
                    )
                else:
                    print(
                        f"  ⚠ Segment {segment_id}: No valid QA pairs after validation"
                    )

            if total_rejected > 0:
                print(f"⚠ Total rejected QA pairs: {total_rejected}")

            # Fill results and cache
            total_pairs = 0
            for i, text_idx in enumerate(uncached_indices):
                qa_pairs = qa_pairs_by_segment.get(i, [])
                results[text_idx] = qa_pairs
                total_pairs += len(qa_pairs)

                cache_key = self._cache_key(uncached_texts[i])
                self.qa_cache[cache_key] = qa_pairs

            print(
                f"✓ Extracted {total_pairs} valid QA pairs from {len(uncached_texts)} segments"
            )

            return results

        except Exception as e:
            print(f"FATAL ERROR: {e}")
            import traceback

            traceback.print_exc()
            for idx in uncached_indices:
                results[idx] = []
            return results

    def _repair_incomplete_json(self, content: str) -> str:
        """
        Attempt to repair incomplete JSON by adding missing closing brackets.
        """
        # Count opening and closing brackets
        open_braces = content.count("{")
        close_braces = content.count("}")
        open_brackets = content.count("[")
        close_brackets = content.count("]")

        if open_braces == close_braces and open_brackets == close_brackets:
            # JSON appears complete
            return content

        print(
            f"Incomplete JSON detected: {{: {open_braces}/{close_braces}, [: {open_brackets}/{close_brackets}"
        )

        # Add missing closing brackets
        # Typical structure: {"segments": [...]}
        # So we need to close: array, then object

        # Remove any trailing commas first
        content = re.sub(r",\s*$", "", content.strip())

        # Add missing closing brackets in the right order
        while close_brackets < open_brackets:
            content += "\n  ]"
            close_brackets += 1
            print("Added missing ]")

        while close_braces < open_braces:
            content += "\n}"
            close_braces += 1
            print("Added missing }")

        return content

    def _aggressive_json_repair(self, content: str, expected_segments: int) -> str:
        """
        Aggressive JSON repair for severely truncated responses.
        """
        print(
            f"Attempting aggressive repair for {expected_segments} expected segments..."
        )

        # Find the last complete segment
        # Look for the last occurrence of complete segment structure
        last_complete = -1
        segment_pattern = r'\{"segment_id":\s*\d+,\s*"qa_pairs":\s*\[[^\]]*\]\}'

        matches = list(re.finditer(segment_pattern, content, re.DOTALL))
        if matches:
            last_match = matches[-1]
            last_complete = last_match.end()
            print(
                f"Found {len(matches)} complete segments, last ends at position {last_complete}"
            )

        if last_complete > 0:
            # Truncate to last complete segment
            content = content[:last_complete]

            # Close the array and object
            content = re.sub(r",\s*$", "", content)  # Remove trailing comma
            content += "\n  ]\n}"

            print("Repaired JSON by truncating to last complete segment")
        else:
            # No complete segments found, try to salvage what we can
            print("No complete segments found, attempting basic repair...")
            content = self._repair_incomplete_json(content)

        return content

    def _extract_content_from_response(self, response) -> str:
        """Extract text content from various response formats."""
        content = response.content

        if hasattr(content, "__iter__") and not isinstance(content, str):
            if len(content) > 0:
                first_block = content[0]
                if hasattr(first_block, "text"):
                    content = first_block.text
                else:
                    content = str(first_block)
            else:
                content = ""
        elif not isinstance(content, str):
            content = str(content)

        return content

    async def extract_qa_pairs_batch_async(
        self, texts: List[str]
    ) -> List[List[Dict[str, str]]]:
        """
        Async version of batch QA extraction.
        Runs the synchronous LLM call in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.extract_qa_pairs_batch, texts
        )

    def extract_qa_pairs(self, text: str) -> List[Dict[str, str]]:
        """
        Extract question-answer pairs from a single text segment.
        For compatibility - internally uses batch processing with caching.
        """
        results = self.extract_qa_pairs_batch([text])
        return results[0] if results else []

    def should_merge_chunks_batch(
        self, chunk_pairs: List[Tuple[Dict, Dict]]
    ) -> List[Tuple[bool, str]]:
        """
        Determine if multiple chunk pairs should be merged in a single LLM call.
        Includes caching for repeated comparisons.
        """
        if not chunk_pairs:
            return []

        # Check cache and prepare uncached pairs
        results = []
        uncached_pairs = []
        uncached_indices = []

        for i, (chunk1, chunk2) in enumerate(chunk_pairs):
            if not chunk1["qa_pairs"] or not chunk2["qa_pairs"]:
                results.append((False, "One or both chunks are empty"))
                continue

            # Don't merge if combined size is too large
            combined_size = len(chunk1["text"]) + len(chunk2["text"])
            if combined_size > self.max_chunk_size:
                results.append((False, "Combined size would be too large"))
                continue

            # Create cache key from questions
            questions_a = tuple(qa["question"] for qa in chunk1["qa_pairs"][:3])
            questions_b = tuple(qa["question"] for qa in chunk2["qa_pairs"][:3])
            cache_key = hashlib.md5(
                f"{questions_a}||{questions_b}".encode()
            ).hexdigest()

            if cache_key in self.merge_cache:
                print(f"Merge cache hit for pair {i}")
                results.append(self.merge_cache[cache_key])
            else:
                results.append(None)  # Placeholder
                uncached_pairs.append((chunk1, chunk2))
                uncached_indices.append((i, cache_key))

        # If all cached, return immediately
        if not uncached_pairs:
            return results

        # Build prompt for uncached pairs
        comparisons_text = ""
        for i, (chunk1, chunk2) in enumerate(uncached_pairs):
            questions_a = [qa["question"] for qa in chunk1["qa_pairs"][:3]]
            questions_b = [qa["question"] for qa in chunk2["qa_pairs"][:3]]

            comparisons_text += f"\n\n--- COMPARISON {i} ---"
            comparisons_text += f"\nGroup A: {questions_a}"
            comparisons_text += f"\nGroup B: {questions_b}"

        prompt = f"""Analyze these pairs of flashcard question groups and determine if each pair relates to the same topic.

        {comparisons_text}

        Return JSON with decisions for ALL comparisons: 
        {{"comparisons": [{{"comparison_id": 0, "should_merge": true, "reason": "Both about photosynthesis"}}, {{"comparison_id": 1, "should_merge": false, "reason": "Different topics"}}]}}

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

            if "comparisons" not in result:
                # Fill with defaults
                for idx, cache_key in uncached_indices:
                    decision = (False, "Parse error")
                    results[idx] = decision
                    self.merge_cache[cache_key] = decision
                return results

            # Map results back and cache them
            decisions_by_id = {}
            for comp in result["comparisons"]:
                comp_id = comp.get("comparison_id")
                should_merge = comp.get("should_merge", False)
                reason = comp.get("reason", "Unknown")
                if comp_id is not None:
                    decisions_by_id[comp_id] = (should_merge, reason)

            # Fill in uncached results and update cache
            for i, (result_idx, cache_key) in enumerate(uncached_indices):
                decision = decisions_by_id.get(i, (False, "Unknown"))
                results[result_idx] = decision
                self.merge_cache[cache_key] = decision

            return results

        except Exception as e:
            print(f"Error in batch merge decision: {e}")
            # Fill with defaults
            for idx, cache_key in uncached_indices:
                decision = (False, "Error analyzing chunks")
                results[idx] = decision
                self.merge_cache[cache_key] = decision
            return results

    async def should_merge_chunks_batch_async(
        self, chunk_pairs: List[Tuple[Dict, Dict]]
    ) -> List[Tuple[bool, str]]:
        """
        Async version of batch merge decision.
        Runs the synchronous LLM call in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.should_merge_chunks_batch, chunk_pairs
        )

    def should_merge_chunks(self, chunk1: Dict, chunk2: Dict) -> Tuple[bool, str]:
        """
        Determine if two chunks should be merged.
        For compatibility - internally uses batch processing with caching.
        """
        results = self.should_merge_chunks_batch([(chunk1, chunk2)])
        return results[0] if results else (False, "Error")

    def chunk_text_file(self, file_path: str) -> List[Dict]:
        """
        Main method: Read a .txt file and chunk it into flashcard-ready segments.
        """
        text = self.read_txt_file(file_path)
        segments = self.preprocess_text(text)
        return self.chunk_segments(segments)

    def chunk_text(self, text: str) -> List[Dict]:
        """
        Chunk raw text string into flashcard-ready segments.
        """
        segments = self.preprocess_text(text)
        return self.chunk_segments(segments)

    async def chunk_text_async(self, text: str) -> List[Dict]:
        """
        Async version of chunk_text for non-blocking operation.
        Processes multiple batches in parallel when possible.
        """
        segments = self.preprocess_text(text)
        return await self.chunk_segments_async(segments)

    def chunk_segments(self, segments: List[str]) -> List[Dict]:
        """
        Process segments into intelligent chunks with QA pairs.
        Uses batch processing and caching for maximum speed.
        Synchronous version.
        """
        if not segments:
            return []

        # Filter out very short segments
        valid_segments = [s for s in segments if len(s) >= self.min_chunk_size]

        if not valid_segments:
            return []

        print(
            f"Processing {len(valid_segments)} segments in batches of {self.batch_size}"
        )

        # OPTIMIZATION: Process QA extraction in batches
        all_qa_pairs = []
        for i in range(0, len(valid_segments), self.batch_size):
            batch = valid_segments[i : i + self.batch_size]
            batch_qa_pairs = self.extract_qa_pairs_batch(batch)
            all_qa_pairs.extend(batch_qa_pairs)
            print(
                f"Processed QA batch {i // self.batch_size + 1}/{(len(valid_segments) + self.batch_size - 1) // self.batch_size}"
            )

        # Create segment chunks with QA pairs
        segment_chunks = []
        for segment, qa_pairs in zip(valid_segments, all_qa_pairs):
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

        # OPTIMIZATION: Skip merge phase for small documents
        if len(segment_chunks) < self.skip_merge_threshold:
            print(
                f"Small document detected ({len(segment_chunks)} chunks), skipping merge phase for speed"
            )
            return segment_chunks

        print(
            f"Large document detected ({len(segment_chunks)} chunks), performing merge analysis"
        )

        # OPTIMIZATION: Merge related chunks using batch processing
        final_chunks = [segment_chunks[0]]

        # Prepare merge candidates in batches
        merge_candidates = []

        for current_chunk in segment_chunks[1:]:
            merge_candidates.append((final_chunks[-1], current_chunk))

            # Process merge decisions in batches
            if len(merge_candidates) >= self.batch_size:
                merge_decisions = self.should_merge_chunks_batch(merge_candidates)

                for (last_chunk, curr_chunk), (should_merge, reason) in zip(
                    merge_candidates, merge_decisions
                ):
                    # Check if we're still looking at the same last chunk
                    if should_merge and final_chunks[-1] == last_chunk:
                        # Merge chunks
                        final_chunks[-1]["text"] = (
                            final_chunks[-1]["text"] + "\n\n" + curr_chunk["text"]
                        )
                        final_chunks[-1]["qa_pairs"].extend(curr_chunk["qa_pairs"])
                        final_chunks[-1]["char_count"] = len(final_chunks[-1]["text"])
                        final_chunks[-1]["merge_reason"] = reason
                    else:
                        # Keep as separate chunk
                        curr_chunk["split_reason"] = reason
                        final_chunks.append(curr_chunk)

                print(
                    f"Processed merge batch, current chunk count: {len(final_chunks)}"
                )
                merge_candidates = []

        # Process remaining merge candidates
        if merge_candidates:
            merge_decisions = self.should_merge_chunks_batch(merge_candidates)

            for (last_chunk, curr_chunk), (should_merge, reason) in zip(
                merge_candidates, merge_decisions
            ):
                if should_merge and final_chunks[-1] == last_chunk:
                    # Merge chunks
                    final_chunks[-1]["text"] = (
                        final_chunks[-1]["text"] + "\n\n" + curr_chunk["text"]
                    )
                    final_chunks[-1]["qa_pairs"].extend(curr_chunk["qa_pairs"])
                    final_chunks[-1]["char_count"] = len(final_chunks[-1]["text"])
                    final_chunks[-1]["merge_reason"] = reason
                else:
                    # Keep as separate chunk
                    curr_chunk["split_reason"] = reason
                    final_chunks.append(curr_chunk)

        print(f"Merge phase complete, final chunk count: {len(final_chunks)}")
        return final_chunks

    async def chunk_segments_async(self, segments: List[str]) -> List[Dict]:
        """
        Async version of chunk_segments.
        Processes multiple batches in parallel for better performance.
        """
        if not segments:
            return []

        # Filter out very short segments
        valid_segments = [s for s in segments if len(s) >= self.min_chunk_size]

        if not valid_segments:
            return []

        print(
            f"Processing {len(valid_segments)} segments ASYNC in batches of {self.batch_size}"
        )

        # PARALLEL: Process all QA extraction batches in parallel
        batch_tasks = []
        for i in range(0, len(valid_segments), self.batch_size):
            batch = valid_segments[i : i + self.batch_size]
            task = self.extract_qa_pairs_batch_async(batch)
            batch_tasks.append(task)

        # Wait for all batches to complete in parallel
        batch_results = await asyncio.gather(*batch_tasks)

        # Flatten results
        all_qa_pairs = []
        for batch_result in batch_results:
            all_qa_pairs.extend(batch_result)

        print(f"Completed {len(batch_tasks)} QA batches in parallel")

        # Create segment chunks with QA pairs
        segment_chunks = []
        for segment, qa_pairs in zip(valid_segments, all_qa_pairs):
            if qa_pairs:
                segment_chunks.append(
                    {
                        "text": segment,
                        "qa_pairs": qa_pairs,
                        "char_count": len(segment),
                    }
                )

        if not segment_chunks:
            return []

        # Skip merge phase for small documents
        if len(segment_chunks) < self.skip_merge_threshold:
            print(
                f"Small document detected ({len(segment_chunks)} chunks), skipping merge phase"
            )
            return segment_chunks

        print(
            f"Large document detected ({len(segment_chunks)} chunks), performing ASYNC merge analysis"
        )

        # PARALLEL: Process merge decisions in parallel
        final_chunks = [segment_chunks[0]]
        merge_batch_tasks = []
        merge_batch_chunks = []

        current_batch = []
        for current_chunk in segment_chunks[1:]:
            current_batch.append((final_chunks[-1], current_chunk))

            if len(current_batch) >= self.batch_size:
                task = self.should_merge_chunks_batch_async(current_batch)
                merge_batch_tasks.append(task)
                merge_batch_chunks.append(current_batch.copy())
                current_batch = []

        # Process remaining
        if current_batch:
            task = self.should_merge_chunks_batch_async(current_batch)
            merge_batch_tasks.append(task)
            merge_batch_chunks.append(current_batch)

        # Wait for all merge decisions in parallel
        if merge_batch_tasks:
            all_merge_decisions = await asyncio.gather(*merge_batch_tasks)

            # Apply merge decisions
            batch_idx = 0
            for merge_decisions, chunk_pairs in zip(
                all_merge_decisions, merge_batch_chunks
            ):
                for (last_chunk, curr_chunk), (should_merge, reason) in zip(
                    chunk_pairs, merge_decisions
                ):
                    if should_merge and final_chunks[-1] == last_chunk:
                        final_chunks[-1]["text"] = (
                            final_chunks[-1]["text"] + "\n\n" + curr_chunk["text"]
                        )
                        final_chunks[-1]["qa_pairs"].extend(curr_chunk["qa_pairs"])
                        final_chunks[-1]["char_count"] = len(final_chunks[-1]["text"])
                        final_chunks[-1]["merge_reason"] = reason
                    else:
                        curr_chunk["split_reason"] = reason
                        final_chunks.append(curr_chunk)
                batch_idx += 1

        print(f"Async merge phase complete, final chunk count: {len(final_chunks)}")
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

    def clear_cache(self):
        """Clear all caches. Useful for testing or memory management."""
        self.qa_cache.clear()
        self.merge_cache.clear()
        print("Caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cache usage."""
        return {
            "qa_cache_size": len(self.qa_cache),
            "merge_cache_size": len(self.merge_cache),
            "total_cached_items": len(self.qa_cache) + len(self.merge_cache),
        }
