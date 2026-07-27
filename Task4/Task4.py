import argparse
import sys
import os
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown

client = genai.Client()

console = Console()


# Input Ingestion Triage

def read_code_file(filepath: str) -> str:
    """
    Safely streams the raw file into a string buffer.
    Source code is bound by formal grammars; all whitespace and indentation must be preserved.
    """
    print(f"[*] Ingesting raw file payload: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_code = f.read()
        return raw_code
    
    except FileNotFoundError:
        print("\n[!] FileNotFoundError: The specified path does not point to a valid file.")
        sys.exit(1)
    except PermissionError:
        print("\n[!] PermissionError: The file has restricted read permissions.")
        sys.exit(1)
    except UnicodeDecodeError:
        print("\n[!] UnicodeDecodeError: Unexpected encoding characters. Cannot process binary assets.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Unexpected Error during ingestion: {e}")
        sys.exit(1)


#  Context Orchestration & Validation

def analyze_and_refactor(code_payload: str, filename: str) -> str:
    """Merges the payload with Persona Constraints and enters the Google GenAI payload."""
    
    print("[*] Compiling analysis payload and routing to Gemini API...")
    
    # Hardcoding behavioral rules into the execution environment.
    SYSTEM_INSTRUCTION = """You are a cold, analytical Senior Code Quality Assurance Engineer.
You only output valid code blocks and direct bullet points.
Do not write friendly greetings.
Your output MUST contain EXACTLY these two section headers:
## BUG_REPORT
- Direct, concise bullet points detailing syntax anomalies, logical vulnerabilities, and performance bugs.
## REFACTORED_CODE
- A single, valid Markdown-fenced code block containing the corrected, compilable code."""

    prompt = f"Analyze and refactor the following code from '{filename}':\n\n```{code_payload}```"

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1, 
            )
        )
        
        output = response.text
        
        # Validation: Script verifies the exact presence of bug report and refactored code sections
        if "## BUG_REPORT" not in output or "## REFACTORED_CODE" not in output:
            print("\n[!] VALIDATION FAILED: The model failed to return both explicit section headers.")
            print("[-] Rejecting response to ensure malformed reports are never pushed to the pipeline.")
            sys.exit(1)
            
        return output

    except Exception as e:
        print(f"\n[!] INFERENCE FAILURE: API Error. Details: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Intelligent Code Reviewer (Gemini Edition)")
    parser.add_argument("--file", type=str, required=True, help="Path to the raw code file (.py, .js, .java) to analyze.")
    args = parser.parse_args()

    # 1. Ingest Payload
    raw_code = read_code_file(args.file)
    
    # 2. Context Orchestration
    analysis_result = analyze_and_refactor(raw_code, args.file)
    
    # 3. Deterministic Markdown Terminal Output
    print("\n" + "="*60)
    print(" VERIFIED OUTPUT - CODE REVIEW REPORT")
    print("="*60 + "\n")
    
    # Rich engine compiles the markdown and prints color-coded syntax to standard output
    console.print(Markdown(analysis_result))
    
    print("\n[SUCCESS] Code Analysis Pipeline complete.")

if __name__ == "__main__":
    main()