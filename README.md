# Channel Picks

Channel Picks is a lightweight web tool for collecting interpretations of channelised features on seismic sections from several interpreters. Each interpreter outlines the features they see. The interpretations are then combined into agreement heat maps, consensus labels and inter-interpreter agreement scores.

The tool was built to create reference labels for evaluating machine learning models that detect channelised features in field seismic data. Labels from a single interpreter carry that person's bias. Combining several independent interpretations gives a more reliable reference and a measure of how much interpreters agree.

**Live version:** https://ada-fb525.github.io/Channel-picks/

## How it works

- The website is a single static page hosted on GitHub Pages.
- Interpreters enter a name or code and their level of experience, read the labelling guide, and draw closed polygons around each channelised feature. Sections without channelised features can be marked as such.
- Each save is sent to a Google Apps Script web app, which appends it as a new row in a Google Sheet. Picks are also kept in the interpreter's browser, so unsent saves are retried automatically.
- An organiser view (`?organiser`), protected by a key, shows the results for each section:
  - a heat map of the fraction of interpreters who picked each pixel,
  - a consensus label based on a selectable rule (more than half of the interpreters, a fixed percentage, or all interpreters),
  - the mean pairwise Dice coefficient between interpreters,
  - filters by experience level and by interpreter.
- A Python script (`tools/fuse_picks.py`) produces the same outputs offline from the exported data.

## Repository structure

| Path | Contents |
|---|---|
| `index.html` | The web application. |
| `config.json` | Page title, introduction text and the address of the Apps Script web app (`scriptUrl`). |
| `guide.txt` | The labelling guide shown to interpreters, as plain text. |
| `sections/` | Section images and `list.json`, which sets the order in which they are shown. |
| `apps_script/Code.gs` | Google Apps Script that stores the picks in a Google Sheet. |
| `tools/fuse_picks.py` | Script that combines the picks into heat maps, labels and agreement tables. |

## Setting up your own copy

### 1. Google Sheet and Apps Script

1. Create a new Google Sheet.
2. Open **Extensions → Apps Script** and replace the default code with the contents of `apps_script/Code.gs`.
3. In the Apps Script editor, set `ORGANISER_KEY` to a private phrase. Do not commit the real key to a public repository.
4. Deploy it via **Deploy → New deployment → Web app**, with *Execute as: Me* and *Who has access: Anyone*.
5. Copy the web app URL (ending in `/exec`) into `scriptUrl` in `config.json`.

The script only accesses the Sheet it is attached to (`@OnlyCurrentDoc`). After changing the script, publish a new version under **Deploy → Manage deployments**. The URL stays the same.

### 2. Sections

1. Place the section images (PNG or JPG) in `sections/`.
2. List their file names in `sections/list.json`, in the order they should be shown:
   ```json
   ["inline_1234.png", "crossline_0567.png"]
   ```
3. Use only letters, numbers, `_`, `-` and `.` in file names.

Picks are stored in image pixels. Export the sections on a known grid, ideally one pixel per trace and per time sample, without axes or margins, and with the same amplitude clipping for all sections. Any display scaling, such as vertical exaggeration, should be an integer factor and should be recorded, so that labels can be mapped back to the survey grid. Do not change the images once interpretation has started.

### 3. GitHub Pages

Push the repository to GitHub. Under **Settings → Pages**, deploy from the `main` branch and the root folder. The site is published at `https://<username>.github.io/<repository>/`.

If `scriptUrl` is empty, the page runs in test mode and keeps picks only in the browser. To test locally, run `python -m http.server` in the repository folder and open `http://localhost:8000`.

## Data format

Each save is one row in the `picks` sheet:

| Column | Description |
|---|---|
| `received_at` | Time the save was received. |
| `code` | Interpreter name or code, in capitals, with spaces replaced by `_`. |
| `level` | Experience level. |
| `section` | Image file name. |
| `width`, `height` | Image size in pixels when the pick was made. |
| `no_channel` | `TRUE` if the interpreter marked the section as having no channelised feature. |
| `n_polygons` | Number of polygons. |
| `polygons` | Polygon vertices as JSON, `[[[x, y], ...], ...]`, in image pixels with the origin at the top-left corner. |
| `client_time` | Time of the save in the interpreter's browser. |

Rows are never edited or deleted, so the Sheet is a complete log. In the analysis, only the latest save per interpreter and section is used.

## Combining interpretations

Export the `picks` sheet as CSV (**File → Download → Comma-separated values**), or download all picks as JSON from the organiser view. Then run:

```bash
python tools/fuse_picks.py picks.csv sections results
python tools/fuse_picks.py picks.csv sections results_70 --rule 0.7
python tools/fuse_picks.py picks.csv sections results_phd --level "PhD student" --exclude ORG
```

For each section, the script writes:

- `<name>_heatmap.npy` and `<name>_heatmap.png`: the fraction of interpreters who picked each pixel,
- `<name>_label.png`: the consensus label (white = channelised feature),
- `agreement.csv`: the number of interpreters, the mean pairwise Dice coefficient and the label rule per section,
- `interpreters.csv`: the experience level and number of sections completed per interpreter.

By default, a pixel belongs to the label if more than half of the interpreters picked it (`--rule majority`). With `--rule 0.7`, at least 70% must have picked it. An interpreter counts for a section if they drew at least one polygon or marked it as having no channelised feature. Picks made on an image of a different size are left out.

Polygons are rasterised with Pillow. The preview in the organiser view can differ by a few pixels along polygon edges, so reported numbers should come from the script.

Requirements: Python 3, NumPy and Pillow.

## Limitations

- There is no login. Interpreters are identified by the name or code they type, so two people who enter the same name are treated as one interpreter.
- Anyone with the link can submit picks. Every row records its name or code, so unexpected rows can be removed from the Sheet.
- The Sheet stores the name or code, experience level and picks. It does not store email addresses.
- In a public repository, the page and the section images are publicly visible.

## Citation

If you use this tool, please cite the associated publication. The reference will be added here once it is available.
