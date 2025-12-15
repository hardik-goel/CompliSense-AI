from agent.agent_runner import run_agent

result = run_agent(
    model_root="artefacts",
    out_dir="out_headless",
    rulepack_path="rulepacks/euai_core_v1.yaml"
)

print(result)
