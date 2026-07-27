import argparse
import sys
import os
from PIL import Image
from google import genai
from google.genai import types

client = genai.Client()


# 1. Aspect Ratio Mapper
def map_aspect_ratio(ratio: str) -> str:
    """Translates user intent to exact strict resolution variables."""
    mapping = {
        "1:1": "1:1",     
        "16:9": "16:9",    
        "9:16": "9:16"     
    }
    
    if ratio not in mapping:
        print("[!] Error: Unsupported aspect ratio requested.")
        sys.exit(1)
        
    return mapping[ratio]

# 2. Network Gateway & Resilience
def generate_and_save_image(prompt: str, ratio: str, filepath: str):
    print(f"[*] Capturing structural parameters and serializing the multimodal payload...")
    
    try:
        # Using the correct free-tier image model for the current API
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=prompt,
        )
        
        # Extracting the raw image bytes from the response structure
        print(f"[*] Executing Binary Write to Local Storage...")
        image_bytes = response.candidates[0].content.parts[0].inline_data.data
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
            
        print(f"[+] Asset written successfully to {filepath}")
        
    except Exception as e:
        print(f"\n[!] API REJECTION: The Google API blocked this request (ClientError).")
        print(f"[!] EXACT ERROR DETAILS: {e}")
        sys.exit(1)

# 3. Integrity Verification
def verify_image_integrity(filepath: str):
    print("[*] Forcing a Rigorous Pixel-Level Decode...")
    
    try:
        with Image.open(filepath) as img:
            img.load() 
        print("[+] Image integrity verified. No truncated data streams detected.")
        
    except OSError:
        print("[!] ERROR: OSError: broken data stream. The file cut off prematurely.")
        if os.path.exists(filepath):
            os.remove(filepath)
        print("[-] Corrupted asset discarded.")
        sys.exit(1)

# CLI Configuration

def main():
    parser = argparse.ArgumentParser(description="Multimodal Image Generation Studio (Gemini Edition)")
    parser.add_argument("--prompt", type=str, required=True, help="The natural language text description.")
    parser.add_argument("--ratio", type=str, choices=["1:1", "16:9", "9:16"], default="1:1", help="Target aspect ratio.")
    parser.add_argument("--output", type=str, default="generated_asset.jpg", help="Output filename.")
    args = parser.parse_args()

    resolution = map_aspect_ratio(args.ratio)
    
    # Execute the Pipeline
    generate_and_save_image(args.prompt, resolution, args.output)
    verify_image_integrity(args.output)
    print("\n[SUCCESS] Visual Orchestration complete. Asset is ready for deployment.")

if __name__ == "__main__":
    main()