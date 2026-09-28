"""从《中国食物成分表》扫描版 PDF 提取食物营养成分数据。

背景：
    PDF 为纯扫描件（无文本层），逐页渲染成图片后调用视觉大模型（阿里云百炼
    MaaS，OpenAI 兼容协议）做表格 OCR，输出结构化 JSON。

    表一「能量和食物一般营养成分」= 书页 49~182（对应 PDF 页 74~204）。
    部分章节为跨页对开（左页=宏量营养素/维生素A/B，右页=维生素E/矿物质），
    婴幼儿食品等章节为单页完整表格。故采用「统一字段」方案：每页让模型只输出
    图中实际存在的列，最后按「食物编码」合并同名食物的左右页数据。

用法：
    cd backend
    python -m knowledge.extract_pdf --start 74 --end 204 --out data/food_raw.json
"""
import argparse
import base64
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF
from openai import OpenAI

import config

PDF_PATH = os.getenv(
    "FOOD_PDF_PATH",
    r"D:\夸克\中国食物成分表 标准版 第二册 第6版 杨月欣 北大医 2019 中 扫描 ※ 9787565919787(1).pdf",
)

# 统一字段（全表可能出现的所有列）。模型只输出图中实际存在的列。
UNIFIED_FIELDS = {
    "food_code": "食物编码",
    "food_name": "食物名称",
    "edible_pct": "可食部(%)",
    "water_g": "水分(g)",
    "energy_kcal": "能量(kcal)",
    "protein_g": "蛋白质(g)",
    "fat_g": "脂肪(g)",
    "carbo_g": "碳水化合物(g)",
    "fiber_g": "不溶性膳食纤维(g)",
    "cholesterol_mg": "胆固醇(mg)",
    "ash_g": "灰分(g)",
    "vit_a_ug": "维生素A(μgRAE)",
    "carotene_ug": "胡萝卜素(μg)",
    "retinol_ug": "视黄醇(μg)",
    "thiamin_mg": "硫胺素(mg)",
    "riboflavin_mg": "核黄素(mg)",
    "niacin_mg": "烟酸(mg)",
    "vit_c_mg": "维生素C(mg)",
    "vit_d_ug": "维生素D(μg)",
    "vit_e_total_mg": "维生素E总(mg)",
    "calcium_mg": "钙(mg)",
    "phosphorus_mg": "磷(mg)",
    "potassium_mg": "钾(mg)",
    "sodium_mg": "钠(mg)",
    "magnesium_mg": "镁(mg)",
    "iron_mg": "铁(mg)",
    "zinc_mg": "锌(mg)",
    "selenium_ug": "硒(μg)",
    "copper_mg": "铜(mg)",
    "manganese_mg": "锰(mg)",
    "note": "备注",
}


def _field_desc() -> str:
    return "\n".join(f'- "{k}": {v}' for k, v in UNIFIED_FIELDS.items())


def _prompt() -> str:
    return f"""你是严谨的数据录入员。这是《中国食物成分表》的扫描页。请把表格中【每一行食物】的数据提取成 JSON 数组。

每个元素是一个对象，可能的字段及含义如下（只输出图中【实际存在】的列，未出现的列不要输出）：
{_field_desc()}

规则：
1. 只输出 JSON 数组，不要任何解释、注释或 markdown 代码块。
2. 数值字段输出为数字；"Tr" 表示微量，输出字符串 "Tr"；"—" 表示无数据/未检测，输出 null。
3. food_code 中的 "x" 是"代表值"标记，必须保留（如 "081101x"）。
4. food_name 保留完整名称、括号和备注。
5. 看不清的字段输出 null，不要凭空编造。
6. 只提取真实数据行，跳过表头、分类标题行、引言和页脚。

输出示例：
[{{"food_code":"081101x","food_name":"猪肉（代表值）","energy_kcal":331,"protein_g":15.1}}]"""


def _render_page_b64(page_index: int, zoom: float = 2.2, jpeg_quality: int = 85) -> str:
    doc = fitz.open(PDF_PATH)
    try:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = pix.tobytes("jpeg", jpeg_quality)
    finally:
        doc.close()
    return base64.b64encode(img).decode("ascii")


def _parse_json(content: str) -> list[dict]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"未找到 JSON 数组: {content[:200]}")
    return json.loads(content[start:end + 1])


def _extract_page(page_index: int, client: OpenAI) -> list[dict]:
    b64 = _render_page_b64(page_index)
    resp = client.chat.completions.create(
        model=config.VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": _prompt()},
            ],
        }],
        max_tokens=config.VISION_MAX_TOKENS,
    )
    return _parse_json(resp.choices[0].message.content or "")


class _Checkpoint:
    """线程安全的增量写盘。"""

    def __init__(self, out_path: str):
        self.out_path = out_path
        self.lock = threading.Lock()
        self.data: dict[str, dict] = {}
        if os.path.exists(out_path):
            try:
                with open(out_path, encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.data = {}

    def has(self, page: int) -> bool:
        return str(page) in self.data

    def set(self, page: int, side: str, rows: list[dict]) -> None:
        with self.lock:
            self.data[str(page)] = {"side": side, "rows": rows}
            tmp = self.out_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.out_path)


def _worker(page: int, cp: _Checkpoint, delay: float) -> tuple[int, int]:
    if cp.has(page):
        return page, -1  # skip
    client = OpenAI(api_key=config.VISION_API_KEY, base_url=config.VISION_BASE_URL)
    for attempt in range(3):
        try:
            rows = _extract_page(page, client)
            cp.set(page, "any", rows)
            return page, len(rows)
        except Exception as e:  # noqa: BLE001
            print(f"[retry {attempt + 1}] page {page}: {e}", flush=True)
            time.sleep(3 * (attempt + 1))
    return page, 0


def extract_range(start: int, end: int, out_path: str, workers: int = 4, delay: float = 1.0) -> None:
    pages = list(range(start, end + 1))
    cp = _Checkpoint(out_path)
    pending = [p for p in pages if not cp.has(p)]
    print(f"总页数 {len(pages)}，待提取 {len(pending)}，workers={workers}", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker, p, cp, delay): p for p in pending}
        for fut in as_completed(futs):
            page, n = fut.result()
            done += 1
            if n >= 0:
                print(f"[{done}/{len(pending)}] page {page}: {n} rows", flush=True)
            time.sleep(delay)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    out = args.out or os.path.join(os.path.dirname(__file__), "data", "food_raw.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    extract_range(args.start, args.end, out, workers=args.workers)


if __name__ == "__main__":
    main()
