from compliance.registry import get_rulepack
from agent.agent_runner import run_agent

default_rulepack = get_rulepack()
result = run_agent(
    model_root=default_rulepack.sample_artifact_root,
    out_dir="out_headless",
    rulepack_path=default_rulepack.pack_id + ".yaml"
)

print(result)
