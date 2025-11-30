def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate cost based on model and tokens.
    Pricing (approximate):
    GPT-4o: Input $5.00/1M, Output $15.00/1M
    """
    if not model:
        return 0.0
        
    if "gpt-4o" in model:
        input_cost = (prompt_tokens / 1_000_000) * 5.00
        output_cost = (completion_tokens / 1_000_000) * 15.00
        return input_cost + output_cost
    return 0.0
