# ChatGPT → Open-WebUI Chat Converter

Convert a ChatGPT export into an Open-WebUI importable JSON.

## Features
- Maps ChatGPT conversations to Open-WebUI format
- Preserves timestamps, hierarchy, and metadata
- Skips malformed conversations and tries to import each chat only once using `~/chatgpt/imported.json`

## Quick Start

### 1) Download
```bash
git clone git@github.com:scubanarc/chatgpt-to-open-webui.git
cd chatgpt-to-open-webui
```

### 2) Export your data from ChatGPT
1. Open ChatGPT
2. Settings → Data controls → Export data → Request export
3. When you receive the email, download and extract the export
4. Copy the conversations.json file to `~/chatgpt/conversations.json`

### 3) Run the converter
```bash
python convert.py
```
- Input: `~/chatgpt/conversations.json`
- Output: `~/chatgpt/converted-for-open-webui.json`

### 4) Backup your Open-WebUI database (important)
Before importing anything, back up your Open-WebUI database file:
- Stop Open-WebUI
- Make a copy of your `webui.db` (path varies by install; for Docker volumes or local data dirs)

### 5) Import into Open-WebUI
1. Open-WebUI → Settings → Chats → Import
2. Select `~/chatgpt/converted-for-open-webui.json`
3. Start import

Notes:
- Open-WebUI currently shows no progress or feedback during import — be patient.
- Large imports can take several minutes.

## De-duplication and Best Practices
- The converter saves already-imported chat IDs in `~/chatgpt/imported.json` to avoid re-importing the same chats on subsequent runs.
- Still, to minimize duplicates, delete all chats from ChatGPT between export→import cycles. That way, the next export only contains new chats.

## Requirements
- Python 3.8+

## Troubleshooting
- If the output file is empty or missing chats, confirm your ChatGPT export is complete and unmodified.
- Ensure the input path and output path exist: `~/chatgpt/` must be present and writable.
- Review terminal output for skipped or malformed conversations.

## License
Unlicense