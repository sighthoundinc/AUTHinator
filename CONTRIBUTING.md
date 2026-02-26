# Contributing to Authinator

Thank you for your interest in contributing to Authinator! This document provides guidelines for contributing.

## Development Setup

1. **Fork and clone** the repository
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```
4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
5. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Development Workflow

1. **Create a branch** for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Test your changes**:
   ```bash
   python manage.py test
   cd frontend && npm test
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push and create a pull request**

## Code Style

### Python (Backend)
- Follow PEP 8
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Type hints where appropriate
- Docstrings for public methods/classes

### TypeScript/React (Frontend)
- Use Prettier for formatting
- Follow React best practices
- Functional components with hooks
- TypeScript strict mode enabled

## Testing

- Write tests for new features
- Maintain or improve code coverage
- Test both backend (pytest/Django tests) and frontend (Jest)
- Test SSO flows manually before submitting

## Pull Request Guidelines

- **Clear description** of what the PR does
- **Reference any related issues** (e.g., "Fixes #123")
- **Keep PRs focused** - one feature/fix per PR
- **Update documentation** if adding new features
- **Add tests** for new functionality
- **Ensure all tests pass** before submitting

## Reporting Issues

When reporting issues, please include:
- **Clear description** of the problem
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages/logs** if applicable

## Security Issues

**DO NOT** open public issues for security vulnerabilities.
Please report security issues privately to the maintainers.

## Questions?

Feel free to open a discussion or issue for any questions about contributing!
