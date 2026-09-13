import json
from pathlib import Path

# Assumed mock pricing for 2026 Hackathon (USD per 1M tokens)
PRICING = {
    "qwen/qwen3.8-27b": {"input": 0.05, "output": 0.05},
    "gemini-3.6-flash": {"input": 0.075, "output": 0.30}
}

def generate_usage_report(tracker, output_path: str, total_requests: int = 0):
    """
    Generates the required evaluation/usage_report.md from the UsageTracker.
    """
    out_file = Path(output_path)
    
    # 1. Aggregate per-model stats
    models_stats = {}
    total_calls = 0
    total_input = 0
    total_output = 0
    
    for call in tracker.calls:
        m = call["model"]
        if m not in models_stats:
            models_stats[m] = {"calls": 0, "input": 0, "output": 0}
        
        models_stats[m]["calls"] += 1
        models_stats[m]["input"] += call["input_tokens"]
        models_stats[m]["output"] += call["output_tokens"]
        
        total_calls += 1
        total_input += call["input_tokens"]
        total_output += call["output_tokens"]
        
    total_tokens = total_input + total_output
    
    # Cost calculations
    def calc_cost(model_name, inp, out):
        rates = PRICING.get(model_name, {"input": 0.0, "output": 0.0})
        return (inp / 1_000_000) * rates["input"] + (out / 1_000_000) * rates["output"]

    model_costs = {m: calc_cost(m, s["input"], s["output"]) for m, s in models_stats.items()}
    total_cost = sum(model_costs.values())
    
    # Avoid div by zero
    req_count = total_requests if total_requests > 0 else max(1, total_calls)
    avg_tokens_per_req = total_tokens / req_count
    avg_cost_per_req = total_cost / req_count
    
    # 2. Build Markdown
    lines = []
    lines.append("# Hackathon Evaluation: Token Usage & Cost Report")
    lines.append("")
    lines.append(f"**Total Requests Evaluated:** {total_requests}")
    lines.append("")
    
    lines.append("## Overall Totals")
    lines.append(f"- **Total Model Calls:** {total_calls}")
    lines.append(f"- **Total Input Tokens:** {total_input:,}")
    lines.append(f"- **Total Output Tokens:** {total_output:,}")
    lines.append(f"- **Total Tokens:** {total_tokens:,}")
    lines.append(f"- **Average Tokens / Request:** {avg_tokens_per_req:,.1f}")
    lines.append(f"- **Estimated Total Cost:** ${total_cost:.5f}")
    lines.append(f"- **Estimated Cost / Request:** ${avg_cost_per_req:.5f}")
    lines.append("")
    
    lines.append("## Per-Model Breakdown")
    for m, s in models_stats.items():
        lines.append(f"### Model: `{m}`")
        lines.append(f"- **Calls:** {s['calls']}")
        lines.append(f"- **Input Tokens:** {s['input']:,}")
        lines.append(f"- **Output Tokens:** {s['output']:,}")
        lines.append(f"- **Estimated Cost:** ${model_costs[m]:.5f}")
        lines.append("")
        
    # Write out
    out_file.parent.mkdir(exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Usage report generated at {out_file}")

