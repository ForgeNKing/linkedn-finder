#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn search link generator.
Reads an input file with one email per line and produces a CSV (and optional XLSX)
containing Google/Bing/Yandex search links to find the person's LinkedIn profile.
Heuristics: uses the last part of the local email (after ., -, or _ ) as a surname hint
and adds organization keywords to narrow results.

Usage:
  python3 linkedin_search_tool.py -i emails.txt -o sk_linkedin_searches.csv
  python3 linkedin_search_tool.py -i emails.txt -o sk.csv --xlsx sk.xlsx
  python3 linkedin_search_tool.py -i emails.txt -o out.csv --org "sk.kz;Samruk-Kazyna;Самрук-Қазына"

By default, organization keywords are set for Samruk-Kazyna.
"""
import argparse
import csv
import re
from urllib.parse import quote_plus
from typing import List, Dict, Iterable

DEFAULT_ORG_KEYWORDS = ["sk.kz", "Samruk-Kazyna", "Самрук-Казына"]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def iter_emails(lines: Iterable[str]) -> Iterable[str]:
    seen = set()
    for raw in lines:
        line = raw.strip()
        if not line or " " in line or "@" not in line:
            continue
        if EMAIL_RE.match(line) and line not in seen:
            seen.add(line)
            yield line

def extract_surname_hint(local: str) -> str:
    # try dot, hyphen, underscore splits; take the last chunk with letters
    for sep in (".", "-", "_"):
        if sep in local:
            parts = [p for p in local.split(sep) if p]
            if len(parts) >= 2:
                return parts[-1]
    # fallback to local part itself
    return local

def build_query(surname: str, org_keywords: List[str]) -> str:
    # Quote surname to avoid tokenization issues
    org_block = " OR ".join([f'"{kw}"' if " " in kw else kw for kw in org_keywords])
    return f'site:linkedin.com/in "{surname}" ({org_block})'

def build_search_links(query: str) -> Dict[str, str]:
    return {
        "Google": "https://www.google.com/search?q=" + quote_plus(query),
        "Bing": "https://www.bing.com/search?q=" + quote_plus(query),
        "Yandex": "https://yandex.com/search/?text=" + quote_plus(query),
    }

def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        # still write header for convenience
        rows = [{"email": "", "surname_hint": "", "Google": "", "Bing": "", "Yandex": ""}]
    fieldnames = ["email", "surname_hint", "Google", "Bing", "Yandex"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

def try_write_xlsx(rows: List[Dict[str, str]], path: str) -> bool:
    try:
        from openpyxl import Workbook  # optional dependency
    except Exception:
        return False
    fieldnames = ["email", "surname_hint", "Google", "Bing", "Yandex"]
    wb = Workbook()
    ws = wb.active
    ws.append(fieldnames)
    for r in rows:
        ws.append([r.get(k, "") for k in fieldnames])
    wb.save(path)
    return True

def main():
    ap = argparse.ArgumentParser(description="Generate LinkedIn search links from emails.")
    ap.add_argument("-i", "--input", default="emails.txt", help="Path to input file with one email per line (default: emails.txt)")
    ap.add_argument("-o", "--output", default="linkedin_searches.csv", help="Path to output CSV file (default: linkedin_searches.csv)")
    ap.add_argument("--xlsx", help="Optional path to output XLSX (requires openpyxl)")
    ap.add_argument("--org", help="Organization keywords separated by ';' (default targets Samruk-Kazyna)")
    args = ap.parse_args()

    org_keywords = DEFAULT_ORG_KEYWORDS.copy()
    if args.org:
        # split by ; and strip
        org_keywords = [kw.strip() for kw in args.org.split(";") if kw.strip()] or org_keywords

    # read emails
    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        emails = list(iter_emails(f))

    rows = []
    for e in emails:
        local, _domain = e.split("@", 1)
        surname = extract_surname_hint(local)
        query = build_query(surname, org_keywords)
        links = build_search_links(query)
        row = {"email": e, "surname_hint": surname, **links}
        rows.append(row)

    write_csv(rows, args.output)

    if args.xlsx:
        ok = try_write_xlsx(rows, args.xlsx)
        if not ok:
            print("[!] Не удалось записать XLSX: модуль openpyxl не установлен. Установите: pip install openpyxl")
        else:
            print(f"[+] XLSX: {args.xlsx}")

    print(f"[+] Обработано адресов: {len(rows)}")
    print(f"[+] CSV: {args.output}")

if __name__ == "__main__":
    main()
