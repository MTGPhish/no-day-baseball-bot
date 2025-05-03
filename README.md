# No Day Baseball Bot 🤠⚾️

**No Day Baseball** is an automated Twitter bot that gently reminds the MLB schedule team to bring us daytime baseball—every time they slip up.  Hosted via GitHub Actions, it runs daily at 8 AM ET and:

1. Queries ESPN’s public MLB scoreboard  
2. Detects if **there are games scheduled today** but **none start before 4 PM ET**  
3. Uploads and tweets a meme image (Bernie asking for day baseball) when that happens  
4. Silently skips posting on days with any early games—or when there are no games at all (off‑season, All‑Star break, etc.)

## Features

- **Zero maintenance**: fully cloud‑hosted, no local machine required  
- **Duplicate‑safe**: gracefully handles Twitter’s duplicate-content rules  
- **Off‑season aware**: won’t post during breaks when no games are scheduled  

---

🛠️ **Setup & Configuration**

1. Fork & clone the repo  
2. Create a Twitter developer app with Read & Write permissions  
3. Populate a `.env` with your API keys & tokens  
4. Push your changes and configure the four GitHub Secrets  
5. Watch it run (and tweet) every morning at 8 AM ET!

Pull requests, contributions, and meme‑upgrades welcome! 🎉
