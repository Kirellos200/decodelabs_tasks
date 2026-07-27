import argparse
import asyncio
import os
import json
from pydantic import BaseModel
from google import genai
from google.genai import types
from tenacity import retry, wait_random_exponential, stop_after_attempt


client = genai.Client()

# enforcing maximum concurrent network connections (Limit: 10)
semaphore = asyncio.Semaphore(10)

# 1. Define the Pydantic Models
class MarketingCopy(BaseModel):
    """Establishes the strict output schemas required for the final copy generation."""
    headline: str
    body_text: str
    call_to_action: str


# 2. Protection: Tenacity Retry Shield
# Recovers from transient network drops using randomized exponential backoff
@retry(wait=wait_random_exponential(min=1, max=8), stop=stop_after_attempt(5))
async def safe_api_call(prompt: str, temperature: float, model_name="gemini-3.5-flash"):
    """Executes the asynchronous API routing through the semaphore gate using Gemini."""
    async with semaphore:
        # Using the new genai async client and types
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=MarketingCopy,
            )
        )
        
        # Parse output directly into the Pydantic model
        data = json.loads(response.text)
        return MarketingCopy(**data)


# 3. Build the Master Template
def compile_prompt(product: str, tone: str, platform: str) -> tuple[str, float]:

    platform_constraints = ""

    if platform.lower() in ["twitter", "x"]:
        platform_constraints = "Strict constraint: The entire body text must be strictly under 280 characters."
    elif platform.lower() == "email":
        platform_constraints = "Format as a structured, professional email with appropriate spacing."

    master_template = f"""
    You are an expert copywriter. Generate marketing copy based on the following parameters:
    Product: {product}
    Target Tone: {tone}
    Target Platform: {platform}
    {platform_constraints}
    """

    if tone.lower() in ["witty", "engaging"]:
        temperature = 0.8  # Diverse phrasing for witty social media copy
    else:
        temperature = 0.2  # Structured and factual for professional emails
        
    return master_template, temperature

# 4. Implement the Dual-Pipeline Router
async def realtime_pipeline(product: str, tone: str, platform: str):

    print(f"[*] Routing to Real-Time Async Pipeline for {platform} via Gemini API...")
    prompt, temp = compile_prompt(product, tone, platform)
    
    try:
        result = await safe_api_call(prompt, temp)
        print("\n--- GENERATED COPY ---")
        print(f"Headline: {result.headline}")
        print(f"Body: {result.body_text}")
        print(f"CTA: {result.call_to_action}")
        print("----------------------\n")
    except Exception as e:
        print(f"[!] Real-time generation failed: {e}")

def bulk_processing_pipeline(product: str, tone: str, platform: str):

    print("[*] Routing to Bulk Processing Pipeline...")
    prompt, temp = compile_prompt(product, tone, platform)
    
    batch_request = {
        "custom_id": f"batch-{product.replace(' ', '')}",
        "prompt": prompt,
        "temperature": temp,
        "response_schema": MarketingCopy.model_json_schema()
    }
    
    with open("batch_payload.jsonl", "w") as f:
        f.write(json.dumps(batch_request) + "\n")
        
    print("[+] Batch payload successfully generated and saved to batch_payload.jsonl.")


def main():
    parser = argparse.ArgumentParser(description="Automated Copywriting & Tone Transformer (Gemini Edition)")
    
    parser.add_argument("--product", type=str, required=True, help="The product name or description.")
    parser.add_argument("--tone", type=str, required=True, help="The desired tone (e.g., witty, professional).")
    parser.add_argument("--platform", type=str, required=True, help="The target platform (e.g., Twitter, LinkedIn, Email).")
    parser.add_argument("--batch", action="store_true", help="Route to the Bulk Processing Pipeline instead of real-time.")
    
    args = parser.parse_args()

    if args.batch:
        bulk_processing_pipeline(args.product, args.tone, args.platform)
    else:
        asyncio.run(realtime_pipeline(args.product, args.tone, args.platform))


if __name__ == "__main__":
    main()