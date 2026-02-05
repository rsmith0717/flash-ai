import json
from typing import List, Tuple


class AgenticChunker:
    def __init__(self, model):
        self.model = model

    def extract_propositions(self, text: str) -> List[str]:
        prompt = f"""Extract atomic propositions from the following text.
        You are helping a student study for an exam so each proposition should be a single factual question and answer.
        Return as a JSON array of questions and answers.

        Text: {text}

        Return format: {"propositions": [{"question": 'What is this?','answer'': 'This is it.'},{"question": 'What time is it?','answer': 'It is five pm eastern.'}]}
        """

        response = self.model.invoke(prompt)

        result = json.loads(response.content[0].text)
        return result["propositions"]

    def should_split(
        self, props_before: List[str], props_after: List[str]
    ) -> Tuple[bool, str]:
        """Ask LLM if there should be a boundary between proposition groups."""

        prompt = f"""Analyze these two groups of propositions and determine if they
        should be in separate chunks based on topic coherence.

        Group A: {props_before}
        Group B: {props_after}

        Return JSON: {{"should_split": true/false, "reason": "explanation"}}
        """

        response = self.model.invoke(prompt)

        result = json.loads(response.content[0].text)
        return result["should_split"], result["reason"]

    def chunk_text(self, sentences: List[str]) -> List[dict]:
        """Main chunking algorithm using agentic decisions."""

        sentence_to_props = {}

        # Extract propositions for each sentence
        for sentence in sentences:
            sentence_to_props[sentence] = self.extract_propositions(sentence)

        # Build chunks by analyzing proposition groups
        chunks = []
        current_chunk = []
        current_props = []

        for sentence in sentences:
            props = sentence_to_props[sentence]

            if not current_chunk:
                current_chunk.append(sentence)
                current_props.extend(props)
                continue

            # Ask LLM if we should create a boundary
            should_split, reason = self.should_split(current_props, props)

            if should_split:
                chunks.append(
                    {
                        "text": " ".join(current_chunk),
                        "propositions": current_props.copy(),
                        "boundary_reason": reason,
                    }
                )
                current_chunk = [sentence]
                current_props = props.copy()
            else:
                current_chunk.append(sentence)
                current_props.extend(props)

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(
                {
                    "text": " ".join(current_chunk),
                    "propositions": current_props,
                    "boundary_reason": "End of document",
                }
            )

        return chunks
