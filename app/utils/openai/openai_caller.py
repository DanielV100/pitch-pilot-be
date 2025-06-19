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
