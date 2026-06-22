"""
arXiv 工具 — 解析 arXiv 论文信息

通过 arXiv API 获取真实论文元信息。
"""

import re
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from app.core.logger import logger

# arXiv API 常量
ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
REQUEST_TIMEOUT = 10


def extract_arxiv_id(paper_url: str) -> Optional[str]:
    """从 arXiv URL 或 ID 字符串中提取 arXiv ID，支持版本号"""
    if not paper_url or not paper_url.strip():
        return None

    paper_url = paper_url.strip()

    # 匹配 arXiv URL 格式
    patterns = [
        r"arxiv\.org/abs/([\w.\-]+)",
        r"arxiv\.org/pdf/([\w.\-]+?)(?:\.pdf)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, paper_url)
        if match:
            return match.group(1)

    # 直接匹配纯 ID 格式，如 2501.12345 或 2501.12345v2
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", paper_url):
        return paper_url

    return None


def normalize_text(text: Optional[str]) -> str:
    """清洗文本：压缩空白、去首尾空格"""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _parse_arxiv_response(xml_text: str, arxiv_id: str) -> dict:
    """解析 arXiv API 返回的 Atom XML"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse arXiv API response: {e}")

    ns = {"atom": ATOM_NS}

    # 查找第一个 entry
    entries = root.findall("atom:entry", ns)
    if not entries:
        raise ValueError(f"Paper not found on arXiv: {arxiv_id}")

    entry = entries[0]

    # 提取各字段
    title_el = entry.find("atom:title", ns)
    title = normalize_text(title_el.text if title_el is not None else "")

    # 作者列表
    authors = []
    for author_el in entry.findall("atom:author", ns):
        name_el = author_el.find("atom:name", ns)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())
    authors_str = ", ".join(authors)

    # 摘要
    summary_el = entry.find("atom:summary", ns)
    abstract = normalize_text(summary_el.text if summary_el is not None else "")

    # 发布日期
    published_el = entry.find("atom:published", ns)
    published_at = ""
    if published_el is not None and published_el.text:
        # 取日期部分 YYYY-MM-DD
        published_at = published_el.text.strip()[:10]

    return {
        "arxivId": arxiv_id,
        "title": title,
        "authors": authors_str,
        "abstractText": abstract,
        "publishedAt": published_at,
    }


def fetch_paper_info(paper_url: str) -> dict:
    """
    获取论文信息

    通过 arXiv API 获取真实论文元信息。

    Args:
        paper_url: arXiv URL 或 ID

    Returns:
        dict: 论文信息，结构与系统约定一致

    Raises:
        ValueError: 无法解析 arXiv ID 或未找到论文
        RuntimeError: 网络请求或 XML 解析失败
    """
    # 1. 提取 arXiv ID
    arxiv_id = extract_arxiv_id(paper_url)
    if arxiv_id is None:
        raise ValueError(f"Invalid arXiv URL or ID: {paper_url}")

    logger.info(f"Extracted arXiv ID: {arxiv_id}")

    # 2. 请求 arXiv API
    params = {"id_list": arxiv_id, "max_results": 1}
    logger.info(f"Requesting arXiv API for {arxiv_id}")

    try:
        response = requests.get(ARXIV_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.Timeout:
        raise RuntimeError(f"Failed to request arXiv API: timeout after {REQUEST_TIMEOUT}s")
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to request arXiv API: {e}")

    # 3. 解析 XML
    paper_info = _parse_arxiv_response(response.text, arxiv_id)

    # 4. 补充 paperUrl
    paper_info["paperUrl"] = paper_url

    logger.info(f"Successfully parsed paper: {paper_info['title'][:80]}...")
    return paper_info
