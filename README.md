# Channel Picks

A small website where several interpreters pick channelised features on the same seismic sections. Each save goes to a Google Sheet that you own. The picks are then combined into a heat map, a majority label and agreement numbers per section.

The site is static, so it runs on GitHub Pages. The Google Sheet acts as its database.

## What is in this folder

| Path | What it is |
|---|---|
| `index.html` | The website. |
| `config.json` | Title, intro text, labelling guide and the Google Sheet address (`scriptUrl`). |
| `sections/` | The section images and `list.json`, which lists them in the order they are shown. |
| `apps_script/Code.gs` | The script that connects the Google Sheet to the website. |
| `tools/fuse_picks.py` | Builds heat maps, majority labels and agreement tables from the picks. |

## 1. Connect a Google Sheet (about 15 minutes)

1. Create a new Google Sheet. A personal Google account is safest, because some university accounts block the "Anyone" option below.
2. In the Sheet, open **Extensions → Apps Script**. Delete the code you see and paste in everything from `apps_script/Code.gs`.
3. In the Apps Script editor only, change `ORGANISER_KEY` to a long phrase that only you know. Do not put your real key in the copy of `Code.gs` that goes to GitHub, because that copy is public.
4. Click **Save**, then **Deploy → New deployment**. Click the gear icon and choose **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Click **Deploy** and allow access. Google will say it hasn't verified the app. This is normal for your own script: click **Advanced**, then **Go to … (unsafe)**.
6. Copy the **Web app URL**. It ends with `/exec`.
7. Paste it into `config.json` as the value of `scriptUrl`.

If you change `Code.gs` later, open **Deploy → Manage deployments**, click the pencil, choose **New version** and click **Deploy**. The URL stays the same.

## 2. Put the site on GitHub Pages (about 10 minutes)

1. On GitHub, create a new **public** repository, for example `channel-picks`.
2. Click **Add file → Upload files** and drag in everything from this folder, keeping the `sections`, `apps_script` and `tools` folders.
3. Go to **Settings → Pages**. Under **Build and deployment**, set **Source** to **Deploy from a branch**, choose the **main** branch and the **/(root)** folder, then click **Save**.
4. After a minute or two, the site is live at `https://YOUR-USERNAME.github.io/channel-picks/`.

To change something later, edit or upload the file on GitHub. The site updates within a minute or two.

## 3. Test it with one person

1. Open the site, enter a code such as `T01`, choose an experience level and pick one or two test sections.
2. Check that new rows appear in the **picks** tab of your Google Sheet.
3. Open the organiser view (below), enter your key and click **Load picks**.
4. When you are happy, delete the test rows from the Sheet. Keep the header row.

## 4. Add your final sections

1. Delete the `test_*.png` files from `sections/` and upload your own PNG or JPG files.
2. Edit `sections/list.json` so it lists your file names, in the order you want them shown:
   ```json
   ["crossline_035.png", "crossline_120.png", "inline_0480.png"]
   ```
3. Rules that matter for the analysis:
   - Export the sections on the **same pixel grid as your U-Net predictions**. Picks are stored in image pixels.
   - Put the line number in each file name, so every pick can be traced back to the survey.
   - **Freeze the sections before anyone starts.** Picks are tied to each file's name and size. `fuse_picks.py` leaves out picks made on an image of a different size.

## 5. Send it to the interpreters

Send each person the link and their own code (`S01`, `S02`, …). Codes must contain at least one letter. Keep any list of who has which code separate from the data.

Picks are also kept in each person's browser. If they come back on the same computer and browser, they can continue where they stopped. If a save does not reach the Sheet, the page says so and tries again on the next save. As a last resort, there is a **Download a copy of my picks** link at the bottom of the page.

## Organiser view

Open `https://YOUR-USERNAME.github.io/channel-picks/?organiser` and go to the **Results** tab. Enter your key and click **Load picks**. You can:

- view the heat map or the majority label (at least 50%) for each section,
- see how many interpreters picked each section and their mean pairwise Dice,
- filter by experience level, or leave out codes (for example your own),
- download the heat map or label as PNG, and all picks as JSON.

The organiser link is not secret, but nobody can load picks without the key.

## Analysis for the paper

Download the Sheet (**File → Download → Comma-separated values**, with the **picks** tab open), then run:

```bash
python tools/fuse_picks.py picks.csv sections results
python tools/fuse_picks.py picks.csv sections results_phd --level "PhD student"
python tools/fuse_picks.py picks.csv sections results_no_org --exclude ORG
```

Only the latest save per interpreter and section counts. The script writes, per section, a heat map (`.npy` and `.png`) and a majority label (`.png`), plus `agreement.csv` and `interpreters.csv`. Use these files for numbers in the paper. The website preview fills shapes slightly differently at their edges.

## Things to know

- The repository is public, so the page and the section images are public. Check that the data licence allows you to share the images.
- The Sheet stores code, experience level, section name, image size, polygons and save times. It stores no names or email addresses.
- Anyone with the site link can submit picks. Each row records its code, so you can delete unexpected rows.
- Test mode: if `scriptUrl` in `config.json` is empty, the page shows a banner and keeps picks only in the browser. You can try it on your own computer by running `python -m http.server` in this folder and opening `http://localhost:8000`.
