# alphabetical-file-groups

## Purpose
Determine the folder to move a file to from the first Unicode character of its filename.

## Key points
- `FileMove` returns the calculated folder name while retaining the original filename unchanged.
- An empty filename produces `EmptyFilename`, and a filename whose leading character is not a letter selects the `misc` folder.
- The Python implementation uses the leading letter's full Unicode casefold result as the folder, and for multiple files processes input order while propagating the first empty-filename error.
