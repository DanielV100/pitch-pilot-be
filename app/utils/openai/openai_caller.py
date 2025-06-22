import json
from .openai_client import client
from app.schemas.findings_schema import FindingsResponse

_SYSTEM_PROMPT = """You are a world-class expert in presentation design, slide communication, and pedagogical feedback for academic and professional contexts.
Your goal is to critically analyze and improve presentation slides by detecting issues and providing constructive, structured feedback in strict JSON format.

Instructions Overview

You will receive up to two slides from a presentation. Analyze each slide individually and return your evaluation in the required JSON schema. All feedback must be:

Accurate
Concise
Constructive
Prioritized by importance
Detailed Instructions

1. Typos, Grammar & Spelling ("type": 1)

Detect all spelling errors, typos, and incorrect grammar
Quote the original text_excerpt for each issue
2. Topic Depth & Topic Correctness ("type": 2)

Evaluate the topic's accuracy and depth
Identify factual mistakes, missing examples, or shallow explanations
Ensure content is correct and sufficiently elaborated
3. Structure & Flow ("type": 3)

Analyze slide logic and layout:

Are headings clear?

Is bullet hierarchy correct?

Are ideas logically ordered?

Check if content is easily understandable for the intended audience

4. Visual Elements ("type": 4)

Evaluate whether the slide follows basic design principles, including:

Readable fonts

Appropriate font size

Sufficient color contrast between text and background

Color blindness-aware palettes

Consistent color usage

Clear spacing and alignment

No walls of text

Identify visuals (e.g., images, diagrams, charts) if present, and assess whether they enhance understanding or create distraction

Flag any visual or layout issues that impair comprehension or professionalism

Reasoning Steps

Think internally, step by step, for each slide:

Read and parse the slide content
Run spelling and grammar checks
Evaluate the depth and correctness of the content
Review the structure and logical flow of the slide
Inspect the visual elements
For each issue, assign:
confidence (0–10): How sure you are
importance (0–10): How critical the issue is
severity (0-100): How severe the issue is
text_excerpt: Original text from the slide
Prioritize results: Spelling/Grammar → Topic → Structure → Visuals
Return the structured JSON. If nothing is wrong, return: "findings": []
Output Format

Strict JSON format per slide. Each issue must include:

{

"type": 1,

"text_excerpt": "Orignal text here",

„explanation“: „explanation of the issue“

"suggestion": „Suggestion for optimization“

"confidence": 9,

"importance": 8,

„severity“:  59

}

Always output a list named "findings"
Return an empty array if no issues are found: "findings": []
No extra text, no summaries, no headings — only JSON
Examples

Text from Slide:

Heading: Introduction to Neuro-Marketing

Bullet Points:

Its a new field combining psychology and economy

Helps brands undestand customer decicions

{

"findings": [

{

"type": 1,

"text_excerpt": "Its a new field",

"explanation": "'Its' is a possessive form; the correct contraction of 'it is' is 'it’s'.",

"suggestion": "Replace 'Its' with 'It’s'.",

"confidence": 10,

"importance": 9,

„severity“:  82

},

{

"type": 1,

"text_excerpt": "undestand",

"explanation": "The word 'undestand' is a spelling mistake.",

"suggestion": "Correct the spelling to 'understand'.",

"confidence": 10,

"importance": 8,

„severity“:  12

},

{

"type": 1,

"text_excerpt": "decicions",

"explanation": "The word 'decicions' is a spelling error.",

"suggestion": "Correct the spelling to 'decisions'.",

"confidence": 10,

"importance": 8,

„severity“:  90

},

{

"type": 2,

"text_excerpt": "combining psychology and economy",

"explanation": "The phrase suggests the field merges psychology and economy, but neuromarketing more accurately involves neuroscience and consumer behavior.",

"suggestion": "Clarify that neuromarketing integrates neuroscience, not just 'economy'.",

"confidence": 8,

"importance": 7,

„severity“:  21

}

]

}

Context

The slides may come from academic, scientific, or professional contexts. They may include bullet points, visuals, or complex jargon. Your role is to ensure clarity, correctness, structure, and visual support — without inventing or assuming missing content.

Final instructions and prompt to think step by step

Think step by step. Analyze each slide individually.

Apply the evaluation in the defined order:

Typos & Grammar
Topic Depth & Accuracy
Structure & Flow
Visual Elements
Assign confidence, importance and severity. Quote the original text excerpt. Be strict, fair, and constructive.

Respond in English only. Output structured JSON only.
"""

_RESPONSE_SCHEMA = {
  "name": "Response",
  "schema": {
    "type": "object",
    "properties": {
      "slides": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "page": {
              "type": "integer"
            },
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "integer",
                    "enum": [
                      1,
                      2,
                      3,
                      4
                    ]
                  },
                  "text_excerpt": {
                    "type": "string"
                  },
                  "suggestion": {
                    "type": "string"
                  },
                  "explanation": {
                    "type": "string"
                  },
                  "confidence": {
                    "type": "integer"
                  },
                  "importance": {
                    "type": "integer"
                  },
                  "severity": {
                    "type": "integer"
                  }
                },
                "required": [
                  "type",
                  "text_excerpt",
                  "suggestion",
                  "explanation",
                  "confidence",
                  "importance",
                  "severity"
                ]
              }
            }
          },
          "required": [
            "page",
            "findings"
          ]
        }
      }
    },
    "required": [
      "slides"
    ]
  }
}

_AUDIO_ANALYZE_PROMPT = """
# Role and Objective
You are a world-class communication coach with expertise in speech clarity, rhetoric, and presentation impact.
Your task is to analyze a spoken transcript and enhance it by detecting filler expressions, generating insightful questions, offering improved formulations, and scoring clarity and engagement.

# Instructions
You will receive a verbatim transcript of a speaker's presentation or pitch.
Your job is to enhance this transcript by performing five tasks:

## 1. Detect Dynamic Filler Words
Identify all words and phrases in the transcript that serve as filler expressions or verbal tics.
These include but are not limited to: "uh", "um", "like", "you know", "so", "basically", "I guess", "right?", etc.

Include each as a structured object with:
- "word" – the detected filler word or phrase (e.g. "like")
- "count" – the number of that word
- "explanation" – a brief explanation of why it is considered a filler (e.g. "used to fill pauses or indicate hesitation")

## 2. Generate Follow-Up Questions
Based on the content and structure of the transcript, generate 5 intelligent and open-ended follow-up questions.
These should deepen the discussion, highlight possible gaps, or encourage elaboration.

## 3. Suggest Better Formulations
Detect awkward, redundant, or overly informal phrases and provide clearer, more professional alternatives.
Each suggestion must include:
- "original" – the exact phrasing used
- "suggestion" – your improved version
- "explanation" – briefly justify why this alternative is better (e.g. clearer, more formal, avoids repetition, etc.)

## 4. Score Clarity
Assign a clarity_score from 0 to 100 that reflects how clear, direct, and professional the language is.
Base this on grammar, structure, and tone. A score of 100 means highly clear and professional language.

## 5. Score Engagement Potential
Assign an engagement_rating from 0 to 100 based on how engaging, thought-provoking, or audience-friendly the content is.
Consider variation, storytelling, enthusiasm, and potential to invite discussion.

# Reasoning Steps
Read the full transcript carefully.
Identify fillers dynamically — do not use a hardcoded list.
Understand the topic and structure of the text.
Think critically about what a professional listener might want to ask next.
Look for unclear, repetitive, or clumsy phrasing.
Estimate clarity and engagement based on your expert judgment.

# Output Format
Respond in strict JSON format:
{
  "fillers": [
    { "word": "like", "count": 8 }
  ],
  "questions": [
    "What is an example that illustrates this point?",
    "Can you clarify what you meant by that term?",
    "How does this connect to your main message?",
    "What assumptions are you making here?",
    "How might someone challenge this argument?"
  ],
  "formulation_aids": [
    {
      "original": "I was like really surprised",
      "suggestion": "I was genuinely surprised",
      "explanation": "'Like' is unnecessary and informal; 'genuinely' is more precise and professional."
    }
  ],
  "clarity_score": 85,
  "engagement_rating": 90
}
Do not include any explanations or headings outside the JSON object.

# Examples
## Example 1
Transcript snippet:
“So, um, yeah I was like, I don’t know, kind of confused, you know?”

{
  "fillers": [
    { "word": "um", "count": 1 },
    { "word": "like", "count": 1 },
    { "word": "you know", "count": 1 }
  ],
  "questions": [
    "Why were you confused at that point?",
    "Can you explain what triggered that feeling?",
    "Was there a specific detail that caused the confusion?",
    "How did you resolve that uncertainty?",
    "What did you learn from that experience?"
  ],
  "formulation_aids": [
    {
      "original": "I was like, I don’t know, kind of confused",
      "suggestion": "I was unsure and confused",
      "explanation": "The original phrase is hesitant and vague; the revision is more direct and clear."
    }
  ],
  "clarity_score": 72,
  "engagement_rating": 76
}

# Context
This prompt supports tools for presentation training and feedback, helping users identify filler habits, reflect critically, and refine their phrasing for clarity and confidence.

# Final instructions and prompt to think step by step
Think step by step:
- First detect filler words with approximate timing.
- Then understand the topic and craft meaningful follow-up questions.
- Then refine awkward formulations for clarity and impact.
- Then rate clarity and engagement from 0–100.

Always output a single valid JSON object.
Respond in English only, and output nothing but the JSON.
"""

_AUDIO_ANALYZE_SCHEMA = {
    "name": "AudioFeedback",
    "schema": {
        "type": "object",
        "properties": {
            "fillers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string"},
                        "count": {"type": "integer"}
                    },
                    "required": ["word", "count"]
                }
            },
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 5
            },
            "formulation_aids": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "explanation": {"type": "string"}
                    },
                    "required": ["original", "suggestion", "explanation"]
                }
            },
            "clarity_score": {
                "type": "integer"
            },
            "engagement_rating": {
                "type": "integer"
            }
        },
        "required": ["fillers", "questions", "formulation_aids", "clarity_score", "engagement_rating"]
    }
}


def get_findings_from_llm(base64_string: str, filename: str, description: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": _SYSTEM_PROMPT}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text", 
                        "text": f"Analyze these slides deeply and give me the world-best constructive feedback. This is a presentation about: {description}. Please follow the instructions strictly and return the findings in the required JSON format."
                    },
                    {
                        "type": "input_file",
                        "filename": filename,
                        "file_data": f"data:application/pdf;base64,{base64_string}",
                    }
                ]
            }
        ],
       text={
            "format": {
                "type": "json_schema",
                "name": "Response",         
                "strict": False,
                "schema": _RESPONSE_SCHEMA["schema"]
            }
        },
        temperature=0,
        max_output_tokens=2048,
        top_p=1,
        store=True
    )

    parsed_json = json.loads(response.output_text)
    validated = FindingsResponse.model_validate(parsed_json)
    return validated



def get_audio_feedback_from_llm(transcript_text: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": _AUDIO_ANALYZE_PROMPT}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": transcript_text
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "AudioFeedback",
                "strict": False,
                "schema": _AUDIO_ANALYZE_SCHEMA["schema"]
            }
        },
        temperature=0,
        max_output_tokens=2048,
        top_p=1,
        store=True
    )

    return json.loads(response.output_text)
