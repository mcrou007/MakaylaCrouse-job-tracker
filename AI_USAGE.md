# AI Usage Documentation

## Tools Used

- **Claude (Anthropic)**, used through the Claude app, for:
  - Outlining course assignments and directing to first steps
  - Assistance in designing files, tables, foreign keys, indexes, JSON columns, etc. 
  - Setting up GitHub, VS Code, the Python packages and the `.env` password file
  - Debugging setup and runtime errors
  - Assistance with the Flask app: `database.py`, `app.py`, the HTML templates and `style.css`
  - Assistance with the job algorithm 
  - Testing setup with MYSQL

Claude assisted in writing the code and setup steps for me to input. I set up everything on my computer with MySQL, Python, VS Code, and Guthub. I fixed the setup issues, reviewed and tested the app, organized the commits, and listed changes.

## Key Prompts

1. *"Read these MySQL files and outline what the database would look like"* (with Assignments 2–5 attached). Ran everything assignment on a MySQL server to show the final tables. 
2. *"Assist me with setting up the schema and the Flask portion."* This produced `schema.sql` and a step-by-step plan.
3. *"Show me how to edit the stylization of the app."* This helped me change the style of the app with different colors and aspects to make it more interesting.

## What Worked Well

- **Setting up the SQL.** Claude helped fix every error I ran into with MySQL, which helped with errors:
  - The Assignment 4 `'text' + CURDATE()` line fails in MySQL (you need `CONCAT`).
  - MySQL silently drops the automatic foreign key index on `jobs` when you add the composite index.
  **Setting up files** It assisted in outlining files I needed and creating things such as:
  - database.py
  - style.css
  - schema.sql
- **Explaining errors.** It explained each error in plain language and gave the exact fix:
  - `python -m pip` instead of `pip`
  - the wrong password in `.env`
  - running `schema.sql` before the app
  - an old copy of `database.py` that hadn't been replaced
- **Security advice.** It told me to keep my MySQL password out of GitHub with a `.env` file and `.gitignore`.

## What I Changed / Did Myself

- **`.env`:** replaced the placeholder with my real MySQL password after the first attempt gave "Access denied".
- **`.gitignore`:** created it myself and checked that `.env` never showed up in my commits.
- **pip:** used `python -m pip` because `pip` wasn't on my PATH.
- **Database:**
  - Drafted and ran `schema.sql` in MySQL Workbench to check for errors and make sure it worked before launching the app.
  - Troubleshot errors with connecting to the MySQL database.
- **Testing and commits:**
  - Tested every page in the browser: adding, editing and deleting records, plus Job Match.
  - Added different stylization options and made sure everything went through before committing to the changes.

## Lessons Learned

- AI is great at explaining error messages. Pasting the exact error got a fix much faster than guessing.
- Always test AI output. Several things in the course handouts looked fine but failed when actually run, so I can't assume code is right just because it looks right.
- Make sure to input a commit message before pushing it through. I wasted some time confused why my changes weren't being pushed until I remember to input a message with the changes.
- Never put passwords in code that goes to GitHub. Use environment variables or a `.env` file.
- AI is a great tool that still must be tested and double checked for its work. It is great at outlining and helping set up projects but it still needs guidance.