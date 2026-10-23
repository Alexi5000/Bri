import json

with open("eval_report_75befeed.json") as report:
    data = json.load(report)
failed = [t for t in data["detailed_results"] if not t["passed"]]

print(f"Failed tests: {len(failed)}/50\n")
print("=" * 80)

for t in failed:
    print(f"\nTest {t['test_id']}: {t['question']}")
    print(f"  Category: {t['category']} | Difficulty: {t['difficulty']}")
    print(f"  Score: {t['score']:.2f}")
    print(f"  Keywords found: {t['keywords_found']}")
    print(f"  Keywords missing: {t['keywords_missing']}")
    print(f"  Response preview: {t['response'][:150]}...")
