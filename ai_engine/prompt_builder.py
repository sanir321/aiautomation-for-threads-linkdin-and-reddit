import database

def build_system_context():
    """Builds the comprehensive system prompt by combining the Persona and Knowledge Base."""
    config = database.get_config()
    base_persona = config.get('system_prompt', 'You are a helpful AI assistant.')
    
    knowledge_entries = database.get_all_knowledge()
    kb_context = ""
    
    # --- Mandatory Integrity Directive ---
    core_directive = """
### CORE OPERATING PRINCIPLE ###
You are NOT an AI assistant. You are the PERSONA defined below. 
1. Direct Adherence: Inhabit this role with 100% fidelity. 
2. Voice & Tone: Never use generic corporate AI language. Use the specific vocabulary, style, and tone of your Persona.
3. No Meta-Commentary: Never provide conversational filler (e.g. "Sure, I can do that", "Here is your post"). 
4. Output Format: Return ONLY the final content requested.
"""

    if knowledge_entries:
        MAX_KB_CHARS = 15000
        # Calculate budget per file to ensure fairness
        per_file_budget = MAX_KB_CHARS // len(knowledge_entries)
        
        kb_context = "\n\n--- KNOWLEDGE BASE ---\nUse the following context from my project documents for accuracy:\n"
        for doc in knowledge_entries:
            content_slice = doc['content'][:per_file_budget]
            kb_context += f"\n[Document: {doc['filename']}]\n{content_slice}\n"
            if len(doc['content']) > per_file_budget:
                kb_context += "[... truncated to fit context budget ...]\n"
            
    final_system_prompt = f"{core_directive}\n\n### YOUR PERSONA ###\n{base_persona}\n{kb_context}"
    return final_system_prompt.strip()

def build_post_prompt(platform: str, trends: list) -> str:
    """Builds the user prompt requesting a post for a specific platform based on trends."""
    config = database.get_config()
    
    platform_rules = {
        'reddit': config.get('reddit_rule') or "Create a value-heavy text post. Do not use hashtags. Use markdown formatting. Focus on sparking discussion.",
        'threads': config.get('threads_rule') or "Create a short, punchy hook. Max 500 characters. Conversational tone.",
        'linkedin': config.get('linkedin_rule') or "Create a professional story-telling post. Use paragraph breaks. End with a question to drive engagement."
    }
    
    rule = platform_rules.get(platform.lower(), "Write a standard social media post.")
    
    trends_text = "None found"
    if trends:
        trends_text = ", ".join(trends)
        
    prompt = f"""
I need you to generate a new post for {platform.capitalize()}.

Platform Rules: {rule}

Current Trending Topics in my niche: {trends_text}

Task: Write the post content. 
- Ensure it aligns with my Persona and Knowledge Base. 
- Use Paragraph breaks for readability. 
- MANDATORY: Only return the final post text. No introductory remarks, no quotes at the start/end, and no reasoning.
"""
    return prompt
