# diff-brief

Terminal-native git diff → PR description & daily standup notes.

Powered by Gemini. No fluff, just Markdown you can paste into GitHub or Slack.

## Install

```bash
pip install -e .
```

## Setup

1. Copy `.env.example` to `.env`
2. Set your Gemini API key:

```bash
GEMINI_API_KEY=your_key_here
```

Or export it in your shell.

## Usage

Generate a PR description from staged / unstaged / recent diff:

```bash
diff-brief pr
diff-brief pr -c   # also copy to clipboard
```

Generate standup bullets from today's commits + working tree:

```bash
diff-brief standup
diff-brief standup -c
```

## How it picks the diff

1. Staged changes (`git diff --staged`)
2. Else unstaged working tree (`git diff`)
3. Else previous commit (`git diff HEAD~1`)

Lockfiles, minified JS, and SVGs are excluded automatically.

## Requirements

- Python 3.10+
- `git` on PATH
- `GEMINI_API_KEY`

## License

MIT
