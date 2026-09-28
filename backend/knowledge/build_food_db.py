"""把 extract_pdf.py 的原始逐页结果合并成结构化食物数据库。

输入：data/food_raw.json（{页码: {side, rows:[{...}]}}）
输出：
    data/food_composition.json   按「食物编码」合并左右页后的完整食物成分记录
    data/food_seeds.json         供向量库使用的自然语言种子句（每食物一条）

合并规则：
    - 同名食物编码在左右页各出现一次（左页=宏量营养素，右页=维生素/矿物质），
      按 food_code 合并字段。
    - 仅保留有有效编码与名称、且至少有能量/蛋白质/脂肪任一数值的记录。
"""
import json
import os
import re

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")

CODE_RE = re.compile(r"^\d{5,8}[a-z]?$")  # 如 081101x / 081102 / 132101

# 字段中文名（用于生成种子句）
FIELD_LABELS = {
    "edible_pct": "可食部{}%",
    "energy_kcal": "能量{}千卡",
    "protein_g": "蛋白质{}克",
    "fat_g": "脂肪{}克",
    "carbo_g": "碳水化合物{}克",
    "fiber_g": "膳食纤维{}克",
    "cholesterol_mg": "胆固醇{}毫克",
    "water_g": "水分{}克",
    "ash_g": "灰分{}克",
    "vit_a_ug": "维生素A{}微克",
    "carotene_ug": "胡萝卜素{}微克",
    "retinol_ug": "视黄醇{}微克",
    "thiamin_mg": "硫胺素{}毫克",
    "riboflavin_mg": "核黄素{}毫克",
    "niacin_mg": "烟酸{}毫克",
    "vit_c_mg": "维生素C{}毫克",
    "vit_d_ug": "维生素D{}微克",
    "vit_e_total_mg": "维生素E{}毫克",
    "calcium_mg": "钙{}毫克",
    "phosphorus_mg": "磷{}毫克",
    "potassium_mg": "钾{}毫克",
    "sodium_mg": "钠{}毫克",
    "magnesium_mg": "镁{}毫克",
    "iron_mg": "铁{}毫克",
    "zinc_mg": "锌{}毫克",
    "selenium_ug": "硒{}微克",
    "copper_mg": "铜{}毫克",
    "manganese_mg": "锰{}毫克",
}


def _clean_value(v):
    """'Tr' 表示微量，保留字符串；数字转 float；其余 None。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s in ("", "—", "-", "Tr", "Tr.", "trace"):
            return "Tr" if s.startswith(("T", "t")) else None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def merge(raw: dict) -> list[dict]:
    """按 food_code 合并，返回规范化后的食物记录列表。"""
    merged: dict[str, dict] = {}
    order: list[str] = []

    for page in raw.values():
        for row in page.get("rows", []):
            if not isinstance(row, dict):
                continue
            code = str(row.get("food_code", "")).strip()
            name = str(row.get("food_name", "")).strip()
            if not CODE_RE.match(code) or not name:
                continue
            if code not in merged:
                merged[code] = {"food_code": code, "food_name": name}
                order.append(code)
            rec = merged[code]
            # 名称以信息更完整的为准（左右页名称基本一致）
            if len(name) > len(rec["food_name"]):
                rec["food_name"] = name
            for field in FIELD_LABELS:
                if field in row and row[field] is not None:
                    cleaned = _clean_value(row[field])
                    # 已有值的字段不覆盖（左页/右页字段天然不重叠，重叠时保留首次）
                    if cleaned is not None and field not in rec:
                        rec[field] = cleaned

    foods = []
    for code in order:
        rec = merged[code]
        # 至少要有能量或蛋白质，否则视为非数据行（如引言页误识别）
        if rec.get("energy_kcal") is None and rec.get("protein_g") is None:
            continue
        foods.append(rec)
    return foods


def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else str(v)
    return str(v)


def to_seed(rec: dict) -> str:
    """把一条食物记录转成自然语言种子句，用于向量检索。"""
    name = rec["food_name"]
    parts = []
    # 核心宏量营养素优先
    for field in (
        "energy_kcal", "protein_g", "fat_g", "carbo_g", "fiber_g",
        "cholesterol_mg", "calcium_mg", "iron_mg", "zinc_mg", "sodium_mg",
        "potassium_mg", "vit_c_mg", "vit_a_ug", "vit_e_total_mg",
    ):
        if field in rec and rec[field] is not None and rec[field] != "Tr":
            parts.append(FIELD_LABELS[field].format(_fmt(rec[field])))
    if not parts:
        return ""
    return f"每100克{name}（可食部）：" + "，".join(parts) + "。"


def main() -> None:
    raw_path = os.path.join(DATA_DIR, "food_raw.json")
    if not os.path.exists(raw_path):
        raise SystemExit(f"未找到原始数据：{raw_path}，请先运行 extract_pdf.py")

    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    foods = merge(raw)
    comp_path = os.path.join(DATA_DIR, "food_composition.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(foods, f, ensure_ascii=False, indent=1)

    seeds = [s for rec in foods if (s := to_seed(rec))]
    seed_path = os.path.join(DATA_DIR, "food_seeds.json")
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=1)

    print(f"食物记录：{len(foods)} 条")
    print(f"种子句：{len(seeds)} 条")
    print(f"已写入：{comp_path}")
    print(f"已写入：{seed_path}")
    # 打印 2 条样例
    for s in seeds[:2]:
        print("样例：", s)


if __name__ == "__main__":
    main()
