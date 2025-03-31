# Djin: Your Magical Terminal Assistant

![Djin Banner](./cover.jpg)

[![GitHub stars](https://img.shields.io/github/stars/patrickkalkman/djin)](https://github.com/PatrickKalkman/djin/stargazers)
[![GitHub contributors](https://img.shields.io/github/contributors/patrickkalkman/djin)](https://github.com/PatrickKalkman/djin/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/patrickkalkman/djin)](https://github.com/PatrickKalkman/djin)
[![open issues](https://img.shields.io/github/issues/patrickkalkman/djin)](https://github.com/PatrickKalkman/djin/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

Djin is your magical terminal companion that banishes tedious dev tasks by managing Jira tickets, tracking time, taking context-aware notes, and automating MoneyMonk entries so you can stay in your coding flow.

## ✨ Features

- **Jira Integration**: Access, view, and update your Jira tickets without leaving the terminal
- **Time Tracking**: Easily track time spent on tasks with simple commands
- **Smart Notes**: Take context-aware notes that are automatically linked to your current task
- **MoneyMonk Automation**: Automatically register hours in MoneyMonk with AI-generated descriptions
- **AI-Powered Summaries**: Generate concise work summaries for reporting and daily standups
- **Command-Line Focused**: Do everything from your terminal without switching context
- **Fast & Lightweight**: Built for performance with minimal resource usage

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- A Jira account with API access
- MoneyMonk account (for time registration features)

### Installation

```bash
# Clone the repository
git clone https://github.com/patrickkalkman/djin.git
cd djin

# Install dependencies with uv
uv sync
```

### First-time Setup

Run the setup command to configure your credentials:

```bash
djin --setup
```

This will guide you through setting up your Jira and MoneyMonk credentials.

## 🔧 Usage

Djin works with simple, intuitive commands:

```bash
# See all available commands
djin
> Type /help for available commands.

# View your Jira tasks
> /tasks todo
> /tasks active

# Add a note
> /note add This is an important observation about the current task

# Register time with an AI-generated summary
> /register-time 2023-05-15 7.5

# Get an AI-generated work summary
> /work-summary

# Register hours in MoneyMonk
> /accounting register-hours 2023-05-15 7.5 "Implemented new API endpoints"
```

## 💡 Command Examples

### Jira Tasks

```bash
# View to-do tasks
> /tasks todo

# View active tasks
> /tasks active

# View tasks worked on today
> /tasks worked-on

# View tasks worked on a specific date
> /tasks worked-on 2023-05-15
```

### Notes

```bash
# Add a note
> /note add Found a bug in the authentication flow

# List all notes
> /note list

# View a specific note
> /note view 123
```

### MoneyMonk Time Registration

```bash
# Register hours manually
> /accounting register-hours 2023-05-15 7.5 "Implemented new API endpoints"

# Register hours with AI-generated description
> /register-time 2023-05-15 7.5
```

## 🔌 Architecture

Djin uses LangGraph to create intelligent agent workflows that coordinate between different features:

- **CLI**: Simple command interface built with prompt-toolkit
- **Task Agent**: Handles Jira integration and task management
- **Note Agent**: Manages contextual note-taking
- **Accounting Agent**: Automates MoneyMonk time registration
- **Text Synthesis**: AI-powered work summary generation
- **Orchestrator**: Coordinates between agents for complex tasks

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent workflows
- Uses [Groq](https://groq.com/) for AI-powered summaries
- [Playwright](https://playwright.dev/) for browser automation with MoneyMonk
- [Prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the interactive CLI
- [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting

---

Built with ❤️ by Patrick Kalkman. Star the repo if you find it useful!
