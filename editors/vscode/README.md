# Cott VS Code Extension

Syntax highlighting and language configuration for Cott (`.cott`).

## Installation

### Method 1: Symlink or copy to VS Code extensions directory
```bash
ln -s "$(pwd)/editors/vscode" ~/.vscode/extensions/cott
```

### Method 2: Package with vsce
```bash
npx vsce package
code --install-extension cott-syntax-0.1.0.vsix
```

## Features
- Full TextMate grammar syntax highlighting for `.cott` files
- Keywords: `module`, `use`, `alias`, `newtype`, `struct`, `enum`, `trait`, `rule`, `const`, `fn`, `override`, `delete`, `remove`
- Contract clauses: `requires`, `ensures`, `error`, `when`, `effects`, `where`, `doc`
- Built-in primitive types, container types, and nominal types
- Comment and auto-closing bracket configuration
