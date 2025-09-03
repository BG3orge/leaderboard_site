# GPA Leaderboard

Features:
- Overall + per-class leaderboards
- History (last 10 uploads)
- Rank-change arrows and trend colors
- One-click bookmarklet to upload grades from eSchool print page
- Optional HTML upload

## Quick start (local)
1. Install Python 3.x
2. Create virtualenv (optional) and install:
3. Run:
4. Open `http://127.0.0.1:5000/`

## Deploy (Render)
1. Push repo to GitHub.
2. On Render: New → Web Service → Connect GitHub → select repo.
3. Build command:
5. After deploy, open the site URL.

## Bookmarklet
- Once the site is live, there is a link “Install Bookmarklet” in the UI. Drag it to your bookmarks bar OR:
- Manually create a bookmark whose URL is the JavaScript shown in the page (uses your deployed origin).
- Open your eSchool print page, click the bookmark, confirm upload alert.

## Security / Notes
- Bookmarklet sends grade rows in JSON to `/update`. The server allows CORS so the bookmarklet can POST from eSchool.
- Only install and use this on accounts you are authorized to access. Respect your school’s Terms of Service.
