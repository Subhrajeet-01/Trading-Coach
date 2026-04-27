# eval/run_eval.py
import json, sys, os, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sklearn.metrics import classification_report

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SEED_PATH = os.path.join(os.path.dirname(__file__), "../data/nevup_seed_dataset.json")

ALL_PATHOLOGIES = [
    "revenge_trading", "overtrading", "fomo_entries",
    "plan_non_adherence", "premature_exit", "loss_running",
    "session_tilt", "time_of_day_bias", "position_sizing_inconsistency"
]

with open(SEED_PATH) as f:
    dataset = json.load(f)

y_true, y_pred, trader_results = [], [], []

for trader in dataset["traders"]:
    uid  = trader["userId"]
    name = trader["name"]

    token_resp = requests.post(f"{BASE_URL}/auth/login",
        json={"userId": uid, "name": name})
    token = token_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    all_trades = [t for s in trader["sessions"] for t in s["trades"]]
    profile_resp = requests.post(f"{BASE_URL}/profile/{uid}",
        json={"trades": all_trades}, headers=headers)
    predicted = profile_resp.json().get("detectedPathologies", [])

    gt = dataset["groundTruthLabels"]
    true_labels = next(g["pathologies"] for g in gt if g["userId"] == uid)

    trader_results.append({
        "name": name, "true": true_labels, "predicted": predicted,
        "correct": set(true_labels) == set(predicted)
    })

    trader_true = []
    trader_pred = []
    for p in ALL_PATHOLOGIES:
        trader_true.append(1 if p in true_labels else 0)
        trader_pred.append(1 if p in predicted else 0)
    y_true.append(trader_true)
    y_pred.append(trader_pred)

    status = "CORRECT" if set(true_labels)==set(predicted) else "WRONG"
    print(f"{status} | {name:15s} | true={true_labels} | pred={predicted}")

report = classification_report(
    y_true, y_pred,
    target_names=ALL_PATHOLOGIES,
    output_dict=True, zero_division=0
)

print("\n" + classification_report(
    y_true, y_pred, target_names=ALL_PATHOLOGIES, zero_division=0))

accuracy = sum(1 for r in trader_results if r["correct"]) / len(trader_results)
print(f"Exact-match accuracy (trader level): {accuracy:.0%}")

report["trader_results"] = trader_results
report["exact_match_accuracy"] = accuracy

report_path = os.path.join(os.path.dirname(__file__), "report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\nreport.json written to {report_path}")