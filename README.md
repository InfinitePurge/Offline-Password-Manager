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


### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wyvernguard.git
   ```
2. Navigate to the project directory:
   ```bash
   cd wyvernguard
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python password_manager.py
   ```

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