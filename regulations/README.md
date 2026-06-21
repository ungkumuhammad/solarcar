# Regulations Folder

## Files

| File | Description |
|---|---|
| `bwsc-2027-regulations.md` | BWSC 2027 event regulations (assembled from official announcements) |
| `key-rules-summary.md` | Quick-reference table of race-critical rules |

## Updating from the Official PDF

The official 2027 regulations PDF is at:  
**https://worldsolarchallenge.org/2027-event/regulations**

Once you have the PDF, convert it to Markdown using [markitdown](https://github.com/microsoft/markitdown):

```bash
# Install markitdown
pip install 'markitdown[all]'

# Convert the regulations PDF
markitdown bwsc-2027-regulations.pdf -o regulations/bwsc-2027-regulations.md

# Convert the Team Manager's Guide
markitdown 2027-BWSC-Team-Managers-Guide.pdf -o regulations/bwsc-2027-team-managers-guide.md
```

The converted Markdown will preserve headings, tables, and lists from the PDF, making it easy to search and reference in code or planning tools.
