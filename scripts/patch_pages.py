import os

pages_dir = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\frontend\src\pages"

def patch_page(filename, loading_msg):
    filepath = os.path.join(pages_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "NoDatasetState" not in content:
        content = 'import NoDatasetState from "../components/common/NoDatasetState";\n' + content

    old_effect = """  useEffect(() => {
    if (currentDataset?.id) {"""
    
    new_effect = """  useEffect(() => {
    if (currentDataset?.id) {"""

    # Ensure else { setLoading(false); } is in useEffect
    if "else {\n      setLoading(false);\n    }" not in content and "setLoading(false)" in content:
        content = content.replace(
            "if (currentDataset?.id) {\n",
            "if (currentDataset?.id) {\n"
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Page templates ready for state updates.")
