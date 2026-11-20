"""All Gemini calls live here, each guarded by the daily quota counter."""
import json, re
from google import genai
from google.genai import types
import store
from config import *


class QuotaExceeded(Exception):
    pass


def _parse(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _call_json(api_key, prompt):
    if store.calls_left() <= 0:
        raise QuotaExceeded("Daily Gemini call budget used up.")
    client = genai.Client(api_key=api_key)
    res = client.models.generate_content(
        model=LLM_MODEL, contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1))
    store.record_call()          # only counted when the call succeeded
    return _parse(res.text)


def extract_criteria_batch(api_key, schemes):
    """ONE call extracts structured criteria for several schemes."""
    blocks = "\n\n".join(f'### scheme_id: {s["scheme_id"]}\nname: {s["name"]}\n{s["elig_text"]}' for s in schemes)
    prompt = f"""Extract structured eligibility criteria for each government scheme below.
Use ONLY the given text. Use null when a criterion is not stated. Convert income to rupees per year
(1 lakh = 100000, 1 crore = 10000000).

Allowed values:
- states: ["ALL"] or a list from {STATES}
- occupations: ["any"] or a list from {OCCUPATIONS}
- gender: "any" | "Male" | "Female"
- categories: ["any"] or a list from {CATEGORIES}

Return a JSON list; one object per scheme with keys:
scheme_id, min_age (number|null), max_age (number|null), max_income (number|null),
states, occupations, gender, categories, requires_disability (bool), requires_bpl (bool),
special_conditions (list of short strings for conditions the form cannot check, e.g. "owns cultivable land").

SCHEMES:
{blocks}"""
    return _call_json(api_key, prompt)


def explain(api_key, profile, items):
    """ONE call explains all shortlisted schemes. Status is already decided by the rule engine."""
    blocks = []
    for it in items:
        ex = "\n".join(f"- {c[:CHUNK_CHARS_IN_PROMPT]}" for c in it["excerpts"])
        blocks.append(f'### scheme_id: {it["scheme_id"]}\nname: {it["name"]}\n'
                      f'rule verdict: {it["status"]}\nmatched: {it["matched"]}\n'
                      f'to confirm: {it["to_confirm"]}\nexcerpts:\n{ex}')
    prompt = f"""You help citizens understand government schemes.
Citizen profile: {json.dumps(profile)}

For each scheme, the eligibility verdict was already computed by code. Do NOT change it.
Using ONLY the excerpts, write a short plain-language explanation. Never invent facts.
If the excerpts do not contain something, use an empty string/list.

Return a JSON list; one object per scheme with keys:
scheme_id, reason (1-2 sentences: why this person qualifies or what to confirm),
benefits (string), documents_required (list of strings), how_to_apply (string).

SCHEMES:
{chr(10).join(blocks)}"""
    return _call_json(api_key, prompt)
