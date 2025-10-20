#!/usr/bin/env python3

import csv
import os
import sys
import re
from html import unescape

CSV_PATH = \
    "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv"

OUT_DIR = \
    "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/diagnostics"


def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def extract_linkedin_job_urls(html_content: str):
    if not html_content:
        return []
    pattern = r'https?://[^\"]*linkedin\.com[^\"]*jobs/view/\d+[^\"]*'
    return re.findall(pattern, html_content)


def window_around(text: str, needle: str, window: int = 500) -> str:
    if not text or not needle:
        return ""
    idx = text.find(needle)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(needle) + window)
    snippet = text[start:end]
    return snippet


def main(limit: int = 2):
    ensure_dir(OUT_DIR)

    # Increase CSV field size limit for large HTML bodies
    import sys as _sys
    max_int = _sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 10)

    picked = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sender = row.get("EMAIL_SENDER", "")
            if "jobs-listings@linkedin.com" in (sender or "").lower():
                picked.append(row)
                if len(picked) >= limit:
                    break

    if not picked:
        print("No jobs-listings emails found.")
        return

    for i, row in enumerate(picked, start=1):
        subject = row.get("EMAIL_SUBJECT", "")
        body = row.get("EMAIL_BODY", "")
        date = row.get("EMAIL_DATE", "")

        # Write raw HTML body for full context
        html_out = os.path.join(OUT_DIR, f"jobs_listings_{i}_raw.html")
        with open(html_out, "w", encoding="utf-8") as hf:
            hf.write(body)

        # Extract all job urls and dump context windows
        urls = extract_linkedin_job_urls(body)
        txt_out = os.path.join(OUT_DIR, f"jobs_listings_{i}_windows.txt")
        with open(txt_out, "w", encoding="utf-8") as tf:
            tf.write(f"Subject: {subject}\n")
            tf.write(f"Date: {date}\n")
            tf.write(f"Total job URLs found: {len(urls)}\n\n")
            for j, u in enumerate(urls, start=1):
                w = window_around(body, u, window=700)
                tf.write(f"==== URL #{j} ====" + "\n")
                tf.write(u + "\n\n")
                tf.write("-- Surrounding HTML --\n")
                tf.write(w + "\n\n")
                # Also a plain-text version for readability
                plain = re.sub(r"<[^>]+>", " ", w)
                plain = unescape(re.sub(r"\s+", " ", plain)).strip()
                tf.write("-- Surrounding TEXT --\n")
                tf.write(plain + "\n\n\n")

        print(f"Wrote: {html_out}\nWrote: {txt_out}")


if __name__ == "__main__":
    # Optional arg: limit number of emails to dump
    try:
        lim = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    except ValueError:
        lim = 2
    main(limit=lim)


