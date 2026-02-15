import os
import subprocess
import json
from datetime import datetime

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    result = subprocess.run(["python3", script_name], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors in {script_name}: {result.stderr}")
    return result.returncode == 0

def generate_markdown_report(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    report = f"# 🍱 Japan Local Restaurant Discovery Report ({date_str})\n\n"
    report += "SNS와 Tabelog 데이터를 결합하여 현지인들이 선호하는 식당을 선정했습니다.\n\n"
    
    if not data:
        report += "이번 주에는 조건에 맞는 식당을 찾지 못했습니다.\n"
        return report
        
    report += "| 식당명 | Tabelog 점수 | 가격대 (저녁/점심) | 링크 |\n"
    report += "| :--- | :---: | :--- | :--- |\n"
    
    for item in data:
        name = item.get('name', 'N/A')
        score = item.get('score', 0.0)
        budget = f"{item.get('night_price', '-')} / {item.get('day_price', '-')}"
        url = item.get('url', '#')
        report += f"| **{name}** | ⭐ {score} | {budget} | [Tabelog 확인]({url}) |\n"
    
    report += "\n---\n*이 리포트는 Antigravity에 의해 자동으로 생성되었습니다.*"
    return report

def main():
    base_dir = os.getcwd()
    execution_dir = os.path.join(base_dir, "execution")
    tmp_dir = os.path.join(base_dir, ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 1. SNS Scanner
    if not run_script(os.path.join(execution_dir, "sns_scanner.py")):
        print("SNS scanning failed.")
        return
        
    # 2. Tabelog Lookup
    if not run_script(os.path.join(execution_dir, "tabelog_lookup.py")):
        print("Tabelog lookup failed.")
        return
        
    # 3. Load Results and Generate Report
    report_data_path = os.path.join(tmp_dir, "tabelog_report.json")
    if os.path.exists(report_data_path):
        with open(report_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        md_report = generate_markdown_report(data)
        
        report_output_path = os.path.join(tmp_dir, f"discovery_report_{datetime.now().strftime('%Y%m%d')}.md")
        with open(report_output_path, "w", encoding="utf-8") as f:
            f.write(md_report)
            
        print(f"Final report generated at: {report_output_path}")
    else:
        print("No report data found.")

if __name__ == "__main__":
    main()
