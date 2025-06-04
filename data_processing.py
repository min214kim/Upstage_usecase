import os
import json
from pathlib import Path
from typing import Dict, Any

def process_single_file(filepath: Path) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_info = data.get("info", {})
    conversation_text = ""
    문항별정보 = []

    for section in data.get("list", []):
        topic = section.get("문항", "")
        for item in section.get("list", []):
            sub_topic = item.get("항목", "")
            audio = item.get("audio", [])
            dialogue = []
            for qa in audio:
                prefix = "상담사" if qa["type"] == "Q" else "내담자"
                dialogue.append(f"{prefix}: {qa['text']}")
            if dialogue:
                conversation_text += f"\n[{topic} - {sub_topic}]\n" + "\n".join(dialogue) + "\n"

            judgment = {
                "문항": topic,
                "항목": sub_topic,
                "점수": item.get("점수"),
                "임상가코멘트": item.get("임상가코멘트", {}).get("val", "")
            }
            for k, v in item.items():
                if isinstance(v, dict) and k not in ["임상가코멘트"]:
                    judgment[k] = v.get("val", "")
            문항별정보.append(judgment)

    result = {
        "id": base_info.get("ID", ""),
        "text": conversation_text.strip(),
        "info": base_info,
        "문항별정보": 문항별정보
    }

    return result

def process_all_files(origin_dir: str, output_dir: str):
    origin_path = Path(origin_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i in range(10000):
        file_name = f"{i:04d}.json"
        input_path = origin_path / file_name
        if not input_path.exists():
            continue

        try:
            unified_json = process_single_file(input_path)
            with open(output_path / file_name, "w", encoding="utf-8") as f:
                json.dump(unified_json, f, ensure_ascii=False, indent=2)
            print(f"[✓] Processed {file_name}")
        except Exception as e:
            print(f"[✗] Failed {file_name}: {e}")

process_all_files("origin", "processed")
