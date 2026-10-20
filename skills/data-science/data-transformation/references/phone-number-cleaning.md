# Phone Number Cleaning — Indonesian Mobile Numbers

## Operator's Format
- INPUT: Raw dumps with numbering prefix (`1 085xxx`, `2 085xxx`), timestamps, emoji markers
- OUTPUT: Clean numbers, one per line, grouped per 20 with blank line separator

## Cleaning Rules
1. Strip line numbering prefix (`1 `, `10 `, `1  `, etc.)
2. Strip timestamps (`[7/22/2026 11:55 AM] the user: `)
3. Drop entries marked ❌ / 🔴 / 🔁 (invalid, flagged, duplicate)
4. Drop non-phone junk (text, headers, empty lines)
5. Valid prefixes: 08x, 8x, 9x (Indonesian mobile)
6. No spaces within numbers

## Output Format
```
[20 numbers, one per line]

[blank line]
[20 numbers, one per line]

[blank line]
[remaining numbers]
```

## Example
```
# Input:
1 085706036693
2 085805257014 ❌
3 08984302711
[7/22/2026 11:55 AM] the user: 085137211887

# Output:
085706036693
08984302711
085137211887
```
