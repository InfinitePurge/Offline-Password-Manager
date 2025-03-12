# WyvernGuard Password Manager

WyvernGuard is a secure, feature-rich password manager built with Python, offering robust encryption and comprehensive password management capabilities. It provides a user-friendly interface with multi-language support (English and Lithuanian) and extensive security features.

## 🔑 Key Features

### Security
- Strong encryption using Fernet symmetric encryption
- Master password protection with PBKDF2 key derivation
- Two-Factor Authentication (2FA)
- Optional face recognition authentication
- Protection against brute-force attacks
- Automatic session timeout
- Secure clipboard handling
- End-to-end encryption for all sensitive data

### Password Management
- Store and manage passwords securely
- Generate strong passwords
- Password strength evaluation
- Password history tracking
- Import/Export passwords (CSV/Steganography format)
- Categorize passwords
- Search and filter capabilities
- Direct website URL integration

### Secure Notes
- Create and manage encrypted notes
- Import/Export functionality
- Full text encryption
- Organized viewing and management

### Additional Features
- Username generator with customizable settings
- Multi-language support (English/Lithuanian)
- Light/Dark theme switching
- Customizable auto-logout settings

## 🚀 Getting Started

### Prerequisites
- Python 3.12


# Installation Guide

## Required Software

### Visual Studio Code
1. Download from the official website - https://code.visualstudio.com/Download
2. Install using default parameters

### Python 3.12
1. Download from https://www.python.org/downloads/release/python-3120/
2. During installation, make sure to check "Add Python to PATH"
3. Complete the installation

### Python Extension for VS Code
1. Open VS Code
2. Go to Extensions section
3. Find and install the "Python" extension

### CMake
1. Download Windows x64 Installer from https://cmake.org/download/
2. During installation, ensure "Add CMake to the system PATH" is checked
3. Complete the installation

### Visual Studio Build Tools
1. Download Visual Studio Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. During installation, select "Desktop development with C++"
3. Wait for all components to be installed

### Git
1. Download 64-bit Git for Windows Setup from https://git-scm.com/downloads/win
2. During installation, keep default parameters
3. Complete the installation

## Application Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/InfinitePurge/Offline-Password-Manager.git
   ```

2. Navigate to the project directory:
   ```bash
   cd wyvernguard
   ```

3. Open terminal in VS Code and install face_recognition_models:
   ```bash
   pip install git+https://github.com/ageitgey/face_recognition_models
   ```

4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python WyvernGuard.py
   ```

## Important Notes
- It's recommended to restart VS Code after each component installation
- Make sure all packages are installed successfully
- Run the program through VS Code using the Python extension
- If you encounter any issues during installation, verify that all prerequisites are properly installed
- The application requires a camera for face recognition features (if you plan to use this functionality)

## System Requirements
- Windows 10 or later
- At least 4GB RAM
- Webcam (for face recognition features)
- Internet connection (for initial setup and package installation)

## 📖 Usage

### Initial Setup
1. Launch the application
2. Create a master password
3. Set up Two-Factor Authentication with any 2fa supporting apps (recommended: Google Authenticator)
4. Configure preferred language and theme

### Managing Passwords
- Add new passwords using the "+" button
- View and edit existing passwords in the password list
- Use the search function to find specific entries
- Generate secure passwords using the built-in generator
- Organize passwords using categories

### Secure Notes
- Create encrypted notes for sensitive information
- Import existing text files as secure notes
- View and edit notes in a secure environment
- Export notes when needed

### Settings (Optional)
- Adjust auto-logout duration
- Customize password generation rules
- Configure username generation preferences
- Add new categories if needed
- Enable/Disable face recognition
- Switch between languages
- Toggle dark/light theme

## 🔒 Security Features

### Encryption
- All sensitive data is encrypted using Fernet symmetric encryption
- Master password is never stored, only its hash
- Encryption key is derived from the master password using PBKDF2
- Automatic re-encryption after data access

### Protection Mechanisms
- Automatic clipboard clearing
- Session timeout after inactivity
- Limited login attempts
- Secure error handling
- Input validation against injection attacks

## 🛠️ Technical Details

- Built with Python and Tkinter
- Uses cryptography library for encryption
- JSON-based data storage
- Modular architecture for easy maintenance
- Comprehensive error handling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the (LICENSE) file for details.

Copyright (c) 2024 Edvinas Babilas

This means you can use this code for any purpose, including commercial applications, as long as you include the original copyright notice and license terms.

## 🔍 Support

For support, please open an issue in the GitHub repository or contact [edvinasbabilas@gmail.com].

## ⚠️ Security Notice

While WyvernGuard implements strong security measures, always ensure you:
- Keep your master password secure and unique
- Regularly update the application
- Back up your data securely
