# Contributing to SwipeGen HR Automation

Thank you for your interest in contributing to the SwipeGen HR Automation project!

## 📋 Code of Conduct

Please maintain professional and respectful communication. This project is confidential and proprietary.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- Virtual environment setup
- All dependencies from `requirements.txt` installed

### Setup Development Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/NamanSinha786/SwipeGen_Automations.git
   cd SwipeGen-Automation
   ```
2. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install development dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## 📝 Contribution Guidelines

### Before Making Changes

- Check existing issues and pull requests
- Discuss major changes in an issue first
- Follow the existing code style and structure
- Ensure all tests pass before submitting

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and modular

### Commit Messages

Use clear, descriptive commit messages:

```
feature: Add new capability X
fix: Resolve issue with Y
docs: Update documentation for Z
refactor: Improve code structure for feature X
```

### Testing

- Test your changes thoroughly before submitting
- Test with sample data to ensure functionality
- Document any new test scenarios

## 🔄 Pull Request Process

1. **Update your branch with latest main**

   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. **Push your changes**

   ```bash
   git push origin feature/your-feature-name
   ```
3. **Create a Pull Request**

   - Provide a clear description of changes
   - Reference related issues
   - Include testing details
   - List any breaking changes
4. **Address feedback**

   - Respond to code review comments
   - Make requested changes
   - Push updates to the same branch

## 🐛 Reporting Issues

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS
- Relevant error messages or logs

## 📚 Documentation

### Updating Documentation

- Keep README.md updated with new features
- Document configuration changes
- Add examples for new functionality
- Update SETUP.md if setup changes

### Code Documentation

- Add docstrings to functions and classes
- Include parameter descriptions
- Document return values
- Explain complex logic with comments

## 🔐 Security

### Security Considerations

- Never commit sensitive credentials
- Use environment variables for secrets
- Validate all user inputs
- Be cautious with file operations
- Keep dependencies updated

### Reporting Security Issues

- Do NOT create public issues for security vulnerabilities
- Email security concerns directly to the maintainers
- Include proof of concept if applicable

## 📋 Project Structure

```
scripts/           # Main application scripts
templates/         # Email and document templates
output/            # Generated files (certificates, offers)
config.json        # Configuration file
requirements.txt   # Python dependencies
```

### Adding New Features

1. Create new script in `scripts/` directory
2. Follow naming convention: `optionX_description.py`
3. Integrate with `main_menu.py`
4. Create templates if needed in `templates/`
5. Update documentation

## ✅ Checklist Before Submitting PR

- [ ] Code follows PEP 8 style guidelines
- [ ] All comments and docstrings are updated
- [ ] Tests pass locally
- [ ] No sensitive data committed
- [ ] README/documentation updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] No unnecessary files or dependencies added
- [ ] Code is tested with sample data

## 🎓 Learning Resources

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Python Documentation](https://docs.python.org/3/)

## 💬 Questions?

Feel free to:

- Open an issue with your question
- Check existing issues for similar questions
- Review the documentation in each script

## 📄 License

By contributing to this project, you agree that your contributions are licensed under the project's license. This project is proprietary and confidential.

---

Thank you for contributing to SwipeGen HR Automation! 🎉
