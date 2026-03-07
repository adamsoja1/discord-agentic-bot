"""Tools for AITIS swarm — plain functions, no CrewAI dependency."""

import re
import html
import unicodedata
import requests
from typing import List, Tuple
from bs4 import BeautifulSoup
from ddgs import DDGS
from agentic_framework.tools.base import tool


# ---------------------------------------------------------------------------
# Web / Research
# ---------------------------------------------------------------------------
@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo. Returns a summary of the top results. Use links for more detailed info or for tool usage.
    Just use simple string query argument to search, no need for complex structured input. Always provide sources for the information you return, even if you know the answer without tools. This is very important for the user to verify the information."""
    try:
        max_results: int = 10
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"No results found for: {query}"

            # Deduplicate by URL
            seen_urls = set()
            unique_results = []
            for r in results:
                url = r.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(r)

            out = f"Web search results for '{query}':\n\n"
            for i, r in enumerate(unique_results, 1):
                title = r.get("title", "N/A")
                body = r.get("body", "").strip()
                link = r.get("href", "N/A")
                # Include full body snippet — don't truncate individual results
                out += f"{i}. {title}\n"
                out += f"   {body[:1200]}\n"
                out += f"   Source: {link}\n\n"

            # Truncate total output cleanly at a newline boundary rather than mid-sentence
            limit = 10000
            if len(out) > limit:
                truncated = out[:limit]
                last_newline = truncated.rfind("\n")
                out = truncated[:last_newline] + "\n\n[Results truncated]"

            return out
    except Exception as e:
        return f"Error during web search: {e}"

@tool
def league_of_legends_search(query: str) -> str:
    """Search League of Legends info — champions, items, patch notes, meta."""
    try:
        with DDGS() as ddgs:
            lol_query = f"league of legends {query}"
            results = list(ddgs.text(lol_query, max_results=8))
            if not results:
                return f"No LoL information found for: {query}"
            out = f"League of Legends search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                out += f"{i}. {r.get('title', 'N/A')}\n"
                out += f"   {r.get('body', '')[:1200]}\n"
                out += f"   Source: {r.get('href', 'N/A')}\n\n"

            limit = 10000
            if len(out) > limit:
                truncated = out[:limit]
                out = truncated[:truncated.rfind("\n")] + "\n\n[Results truncated]"

            return out
    except Exception as e:
        return f"Error searching LoL info: {e}"

@tool
def gaming_search(query: str) -> str:
    """Search general gaming news, guides, and game info."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return f"No gaming information found for: {query}"
            out = f"Gaming search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                out += f"{i}. {r.get('title', 'N/A')}\n"
                out += f"   {r.get('body', '')[:1200]}\n"
                out += f"   Source: {r.get('href', 'N/A')}\n\n"
            return out[:8000]
    except Exception as e:
        return f"Error during gaming search: {e}"

@tool
def technical_search(query: str) -> str:
    """Search programming documentation, Stack Overflow, GitHub, and developer resources."""
    try:
        with DDGS() as ddgs:
            # NOTE: DuckDuckGo's API does not reliably support site: operators.
            # Use plain query enriched with technical keywords instead.
            tech_query = f"{query} documentation tutorial example"
            results = list(ddgs.text(tech_query, max_results=8))
            if not results:
                results = list(ddgs.text(query, max_results=8))
            if not results:
                return f"No technical information found for: {query}"
            out = f"Technical search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                out += f"{i}. {r.get('title', 'N/A')}\n"
                out += f"   {r.get('body', '')[:1200]}\n"
                out += f"   Source: {r.get('href', 'N/A')}\n\n"

            limit = 10000
            if len(out) > limit:
                truncated = out[:limit]
                out = truncated[:truncated.rfind("\n")] + "\n\n[Results truncated]"

            return out
    except Exception as e:
        return f"Error during technical search: {e}"


# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------

# Tags that never contain readable content
_NOISE_TAGS = [
    "script", "style", "noscript", "header", "footer", "nav", "aside",
    "form", "button", "input", "select", "textarea", "iframe", "svg",
    "figure", "figcaption", "picture", "video", "audio",
]

# CSS class/id substrings that indicate noise blocks
_NOISE_PATTERNS = re.compile(
    r"(cookie|consent|gdpr|popup|modal|banner|advert|sidebar|breadcrumb|"
    r"share|social|comment|related|recommend|newsletter|subscribe|promo|"
    r"widget|footer|header|nav|menu|masthead|pagination)",
    re.IGNORECASE,
)


def _is_noisy_element(tag) -> bool:
    """Return True if a BeautifulSoup tag looks like UI noise rather than content."""
    for attr in ("class", "id"):
        values = tag.get(attr, [])
        if isinstance(values, str):
            values = [values]
        for v in values:
            if _NOISE_PATTERNS.search(v):
                return True
    return False


def _clean_text(raw: str) -> str:
    """Normalise raw scraped text into clean, model-friendly prose."""
    # Decode HTML entities (&amp; &nbsp; etc.)
    text = html.unescape(raw)
    # Normalise unicode (e.g. fancy quotes → ASCII equivalents)
    text = unicodedata.normalize("NFKC", text)
    # Replace non-breaking and other exotic spaces with regular space
    text = re.sub(r"[\xa0\u200b\u200c\u200d\ufeff]+", " ", text)
    # Collapse runs of whitespace within a line
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse more than two consecutive newlines into a paragraph break
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove lines that are clearly garbage:
    # - pure whitespace
    # - consist entirely of non-alphanumeric symbols (e.g. "---", "***")
    # NOTE: Keep short lines like "v2", "$5", "OK" — only drop if NO alphanumeric chars at all.
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and re.search(r"[a-zA-Z0-9]", ln)]
    return "\n".join(lines).strip()


def _split_sentences(text: str) -> List[str]:
    """Split text into individual sentences on sentence-ending punctuation."""
    sentence_end = re.compile(r"(?<=[.!?])\s+")
    return [s.strip() for s in sentence_end.split(text) if s.strip()]


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 2) -> List[str]:
    """
    Split text into chunks that respect sentence boundaries.

    `chunk_size`  – approximate max characters per chunk. Raised from 600 to 1200
                    so each chunk contains enough context for coherent reasoning.
    `overlap`     – number of sentences carried over into the next chunk
                    to preserve local context across chunk boundaries.
    """
    sentences = _split_sentences(text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > chunk_size and current:
            chunks.append(" ".join(current))
            # Keep the last `overlap` sentences as context for the next chunk
            current = current[-overlap:] if overlap else []
            current_len = sum(len(s) for s in current)
        current.append(sentence)
        current_len += len(sentence)

    if current:
        chunks.append(" ".join(current))

    return chunks


def _keyword_score(chunk: str, keywords: List[str]) -> int:
    lower = chunk.lower()
    return sum(lower.count(kw.lower()) for kw in keywords)


# ---------------------------------------------------------------------------
# Public tools
# ---------------------------------------------------------------------------

@tool
def scrape_website(url: str) -> str:
    """Scrape a website and return its cleaned text content. Useful for reading documentation or longer articles."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Remove obvious noise tags
        for tag in soup(_NOISE_TAGS):
            tag.decompose()

        # 2. Remove elements whose class/id looks like UI chrome
        for tag in soup.find_all(True):
            if _is_noisy_element(tag):
                tag.decompose()

        # 3. Prefer the main content area when available
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"(content|main|body|article)", re.I))
            or soup.find(class_=re.compile(r"(content|main|body|article)", re.I))
        )
        target = main if main else soup

        # 4. Extract text with block separators so sentences don't run together
        text = target.get_text(separator="\n")
        text = _clean_text(text)

        if not text:
            return f"Failed to retrieve content from {url} or page is empty."

        # Truncate cleanly at a paragraph boundary to avoid mid-sentence cuts
        limit = 12000
        if len(text) > limit:
            truncated = text[:limit]
            last_para = truncated.rfind("\n\n")
            text = truncated[:last_para] if last_para > 0 else truncated
            text += "\n\n[Content truncated — use search_scraped_website for targeted lookup]"

        return f"Content of {url}:\n\n{text}"
    except Exception as e:
        return f"Error scraping {url}: {e}"


@tool
def search_scraped_website(url: str, keywords: List[str], top_k: int = 5) -> str:
    """
    Scrape a URL and return the most relevant text chunks for the given keywords.
    Chunks respect sentence boundaries so the model receives coherent passages.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(_NOISE_TAGS):
            tag.decompose()
        for tag in soup.find_all(True):
            if _is_noisy_element(tag):
                tag.decompose()
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"(content|main|body|article)", re.I))
            or soup.find(class_=re.compile(r"(content|main|body|article)", re.I))
        )
        target = main if main else soup
        text = _clean_text(target.get_text(separator="\n"))

        if not text:
            return f"Failed to retrieve content from {url} or page is empty."

        chunks = _chunk_text(text)
        scored: List[Tuple[str, int]] = sorted(
            [(c, _keyword_score(c, keywords)) for c in chunks],
            key=lambda x: x[1],
            reverse=True,
        )

        # Only keep chunks that actually matched at least one keyword
        matched = [(c, s) for c, s in scored if s > 0]

        if not matched:
            # Fallback: return opening content with a clear disclaimer
            preview = text[:3000]
            return (
                f"No passages matching keywords {keywords} were found on {url}.\n\n"
                f"The page may not contain this information. "
                f"Here is the beginning of the page content for reference:\n\n{preview}"
            )

        top_chunks = matched[:top_k]
        header = (
            f"Found {len(matched)} relevant passage(s) on {url} "
            f"(keywords: {keywords}). Showing top {len(top_chunks)}:\n\n"
        )
        body = "\n\n---\n\n".join(chunk for chunk, _ in top_chunks)
        return header + body

    except Exception as e:
        return f"Error scraping {url}: {e}"