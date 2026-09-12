def estimate_tokens(text: str) -> int:
    """
    Approximate token count.

    A rough estimate of 1 token per 4 characters
    is sufficient for approximate cost tracking.
    """
    return max(1, len(text) // 4)


MODEL_PRICING = {
    "gemini-3.6-flash": {
        "input": 0.30,
        "output": 2.50,
    },
}


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:

    pricing = MODEL_PRICING.get(
        model,
        MODEL_PRICING["gemini-3.6-flash"],
    )

    input_cost = (
        input_tokens / 1_000_000
    ) * pricing["input"]

    output_cost = (
        output_tokens / 1_000_000
    ) * pricing["output"]

    return round(
        input_cost + output_cost,
        6,
    )
