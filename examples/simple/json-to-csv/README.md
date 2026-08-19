# json-to-csv

## Purpose
Serialize name, age, and birth-year records into safe CSV text.

## Key points
- It outputs the `name`, `age`, and `birthyear` fields of `CsvRecord` in the same order as the fixed header.
- Fields containing a comma, double quote, CR, or LF are double-quoted, and embedded double quotes are doubled to preserve CSV boundaries.
- The Python implementation returns exactly `name,age,birthyear\r\n` for empty input and appends CRLF to every record.
