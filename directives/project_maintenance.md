# Directive: Project Maintenance

## .gitignore Management
- **Proactive Updates**: Antigravity should automatically detect and add new temporary, local-only, or security-sensitive files to `.gitignore`.
- **Standard Exclusions**:
    - `.tmp/`: All processing intermediates.
    - `.vscode/` & `.idea/`: IDE-specific settings.
    - `.env`, `credentials.json`, `token.json`: Secrets and local configurations.
    - `__pycache__/`, `node_modules/`: Build and dependency artifacts.
- **Index Cleanup**: If a file that should be ignored is already being tracked, use `git rm --cached <file>` to stop tracking it without deleting the local copy.
