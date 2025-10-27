# Contributing to Gulf Coast Hurricane Visualization Dashboard

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## 🌟 Ways to Contribute

- **Bug Reports**: Report bugs via GitHub Issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests with enhancements
- **Documentation**: Improve documentation and examples
- **Testing**: Help test new features and report issues

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/gulfCoastHurricaneVis.git
cd gulfCoastHurricaneVis
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install black isort flake8 pylint pytest
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/bug-description
```

## 💻 Development Guidelines

### Code Style

- **Python Style**: Follow PEP 8 guidelines
- **Formatting**: Use `black` for code formatting
- **Imports**: Use `isort` for import sorting
- **Line Length**: Maximum 127 characters
- **Docstrings**: Use Google-style docstrings

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

### Code Organization

- **Modular Design**: Keep functions focused and single-purpose
- **Clear Naming**: Use descriptive variable and function names
- **Comments**: Add comments for complex logic
- **Type Hints**: Use type hints for function parameters and returns

### Testing

```bash
# Run existing tests (if available)
pytest

# Test your changes manually
python launch_with_loading.py
```

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(timeline): add interactive year range slider"
git commit -m "fix(map): correct filter application for categories"
git commit -m "docs(readme): update Docker installation instructions"
```

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] Documentation is updated (if needed)
- [ ] Commits are meaningful and well-organized
- [ ] Branch is up to date with master

```bash
# Update your branch with latest master
git checkout master
git pull upstream master
git checkout your-branch
git rebase master
```

### 2. Submit Pull Request

1. Push your branch to your fork
2. Go to the original repository on GitHub
3. Click "New Pull Request"
4. Select your branch
5. Fill out the PR template

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
How has this been tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

### 4. Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, your PR will be merged

## 🐛 Bug Reports

### Good Bug Report Includes:

1. **Clear Title**: Descriptive summary of the issue
2. **Environment**: OS, Python version, dependencies
3. **Steps to Reproduce**: Detailed steps to reproduce the bug
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Screenshots/Logs**: Visual evidence or error messages
7. **Additional Context**: Any other relevant information

**Example:**

```markdown
**Title:** Map filter not applying category selection

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12.3
- CustomTkinter: 5.2.0

**Steps to Reproduce:**
1. Launch dashboard
2. Navigate to Map tab
3. Select "Category 3+" from filter
4. Click Apply
5. All categories still visible

**Expected:** Only Category 3+ storms shown
**Actual:** All storms still displayed

**Error Log:**
```
[error message here]
```

**Screenshots:** [attach screenshot]
```

## 💡 Feature Requests

### Good Feature Request Includes:

1. **Problem Statement**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other solutions considered
4. **Use Case**: Real-world scenario
5. **Priority**: How important is this feature?

## 📊 Project Areas

### Areas Needing Contribution:

1. **Data Processing**
   - `csv_data_processor.py`
   - `data_processor_db.py`

2. **Visualizations**
   - `native_visualizations.py`
   - New chart types

3. **UI/UX**
   - `tabbed_native_dashboard.py`
   - `aesthetic_theme.py`
   - Accessibility improvements

4. **Performance**
   - Caching optimizations
   - Database query optimization

5. **Testing**
   - Unit tests
   - Integration tests
   - Performance benchmarks

6. **Documentation**
   - Code documentation
   - User guides
   - API documentation

## 🎯 Development Priorities

### High Priority
- Bug fixes
- Performance improvements
- Security updates
- Critical features

### Medium Priority
- New visualizations
- UI enhancements
- Additional filters
- Export capabilities

### Low Priority
- Nice-to-have features
- Cosmetic improvements
- Optional integrations

## 🤝 Code Review Guidelines

### For Contributors
- Be open to feedback
- Respond to comments promptly
- Make requested changes
- Ask questions if unclear

### For Reviewers
- Be respectful and constructive
- Explain the "why" behind suggestions
- Approve when ready
- Provide clear action items

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create a GitHub Issue
- **Chat**: [Add Discord/Slack if available]
- **Email**: [Add contact email if available]

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

---

**Happy Contributing! 🎉**
