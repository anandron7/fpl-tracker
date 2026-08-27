# FPL Tracker

Tracks Fantasy Premier League entry **2521217** and publishes a machine-readable snapshot to GitHub Pages.

## Setup

1. Create a GitHub repository named `fpl-tracker`.
2. Upload the contents of this folder to the repository root.
3. In GitHub: **Settings → Pages → Build and deployment → GitHub Actions**.
4. In **Actions**, run **Update FPL Data** once.
5. Your JSON should then be available at:
   `https://YOUR-GITHUB-USERNAME.github.io/fpl-tracker/fpl.json`

The workflow refreshes every 3 hours.
