# XML Product Feed Comparator

This is a small Python utility that compares two XML product feeds (e.g. live vs staging/server) and reports differences in common products.

It:

- Downloads two XML feeds from given URLs.
- Indexes products by `id` (or `mpn` as a fallback).
- Finds:
  - Products common to both feeds.
  - Products only in the live feed.
  - Products only in the server feed.
- Randomly samples products from the **top**, **middle**, and **bottom** of the common key list.
- Compares the sampled products field-by-field, with optional normalization and ignored fields.

The goal is to quickly spot discrepancies between two feeds without having to compare everything manually.

---

## Features

- **HTTP fetching with timeout**  
  Fetches feeds using `urllib.request` with a custom `User-Agent` and a 120-second timeout.

- **Product indexing**
  - Each `<product>` element is flattened into a Python dictionary.
  - Products are identified by:
    - `id` (preferred), or
    - `mpn` (fallback).
  - Products that have neither `id` nor `mpn` are ignored.

- **Smart comparison**
  - Some fields are **ignored completely** during comparison (configurable via `IGNORE_TAGS`).
  - URL fields are compared ignoring the **scheme and domain** (configurable via `URL_TAGS`).
  - Nested elements (other than the ignored ones) are kept as XML strings so structural differences can still be detected.

- **Sampling strategy**
  - The script does not compare all products (which could be heavy on large feeds).
  - Instead it:
    - Sorts common product keys.
    - Splits them into three ranges:
      - First ~20% (start)
      - Middle ~20% (middle)
      - Last ~20% (end)
    - Randomly picks up to `take_per_section` keys from each range (default: 5).
  - This gives a spread of samples from the beginning, middle, and end of the feed.

- **Detailed diff output**
  - For each sampled product:
    - If no differences are found (after normalization), it prints a `MATCH` line.
    - Otherwise, it prints:
      - The product key.
      - The `id` values from both feeds.
      - All fields that differ, with both values.

---

## Normalization Rules

### Ignored fields

Some tags are completely ignored when building the product dictionaries:


## Author

**harrisstef**

This project is part of my personal portfolio.
