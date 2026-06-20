# HW7 Submission Template

Use this file when the public repository or shared-drive link is ready.

## Required TXT File

Filename:

```text
<StudentID>_HW7.txt
```

Content:

```text
GitHub repository: <PUBLIC_REPOSITORY_LINK>
Demo material: <VIDEO_OR_SCREENSHOT_FILENAME_OR_LINK>
Project title: Agentic Generative AI Experiment Orchestrator
```

If using Google Drive instead of GitHub, replace the repository line with:

```text
Google Drive folder: <ANYONE_WITH_LINK_URL>
```

Generator command:

```powershell
python create_submission_txt.py --student-id <StudentID> --link <PUBLIC_REPOSITORY_LINK> --link-kind github --demo <StudentID>_HW7.mp4
```

For Google Drive:

```powershell
python create_submission_txt.py --student-id <StudentID> --link <ANYONE_WITH_LINK_URL> --link-kind drive --demo <StudentID>_HW7.png
```

## Required Demo File

Filename:

```text
<StudentID>_HW7.mp4
```

or:

```text
<StudentID>_HW7.png
```

## Final Manual Inputs Needed

- Student ID.
- Public GitHub repository link or Google Drive sharing link.
- Final demo video/screenshot filename.
