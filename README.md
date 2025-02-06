# Blockchain-Based AI-Driven Secure Voting System 🗳️

A cutting-edge electronic voting system that combines blockchain security, facial recognition authentication, and smart contract technology to ensure transparent and tamper-proof elections.

## Legal Notice ⚖️
This project is patent-pending. All rights reserved. Unauthorized access, reproduction, or distribution of the source code is strictly prohibited.

## Contact for Access 📧
For licensing, collaboration, or access requests:

**Karthik K R**
- 📧 Email: karthik94833@gmail.com
- 💼 LinkedIn: [Karthik K R](https://www.linkedin.com/in/karthik-k-r-37bb52244/)
- 🔒 Patent Status: Pending


## Core Features 🔐
- Blockchain-powered vote recording and verification
- AI-based facial recognition for voter authentication
- Two-factor authentication with SMS verification
- Smart contract-based vote validation
- Real-time vote tracking and monitoring

## Technical Stack 🛠️

### Backend Infrastructure
- **Django**: Web framework for robust backend development
- **Python 3.11**: Core programming language
- **MongoDB**: NoSQL database for user management and data storage
- **Web3.py**: Ethereum blockchain interaction

### Blockchain Components
- **Ethereum**: Blockchain platform
- **Ganache**: Local blockchain development
- **Truffle**: Smart contract development framework
- **Solidity**: Smart contract programming

### AI & Security
- **DeepFace**: Facial recognition and verification
- **OpenCV**: Image processing
- **Twilio**: SMS verification service

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript**: Interactive features
- **Bootstrap**: Responsive design framework

## Installation Guide 📝

### Prerequisites
- Python 3.11+
- Node.js & npm
- MongoDB
- Ganache
- Truffle Suite
- Web3.py

## Technical Stack 🛠️

### Backend Infrastructure
- **Django**: Web framework for robust backend development
- **Python 3.11**: Core programming language
- **MongoDB**: NoSQL database for user management and data storage
- **Web3.py**: Ethereum blockchain interaction

### Blockchain Components
- **Ethereum**: Blockchain platform
- **Ganache**: Local blockchain development
- **Truffle**: Smart contract development framework
- **Solidity**: Smart contract programming

### AI & Security
- **DeepFace**: Facial recognition and verification
- **OpenCV**: Image processing
- **Twilio**: SMS verification service

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript**: Interactive features
- **Bootstrap**: Responsive design framework

## Installation Guide 📝

### Prerequisites
- Python 3.11+
- Node.js & npm
- MongoDB
- Ganache
- Truffle Suite

Setup Steps

1. Clone the repository:
    `bash  git clone https://github.com/Karthik0704/Block-chain-based-AI-driven-secure-votting-system.git`
    `cd Block-chain-based-AI-driven-secure-votting-system`

2. Create and activate virtual environment:
    `python -m venv venv`
# For Windows
    `venv\Scripts\activate`
# For Linux/Mac
    `source venv/bin/activate`

3. Install dependencies:
    `bash pip install -r requirements.txt`

4. Configure environment variables:
# Create .env file in root directory
    TWILIO_ACCOUNT_SID=your_sid
    TWILIO_AUTH_TOKEN=your_token
    TWILIO_PHONE_NUMBER=your_phone
    MONGODB_URI=mongodb://localhost:27017/
    BLOCKCHAIN_PRIVATE_KEY=your_private_key

5. Start MongoDB:
    `mongod`

6. Launch Ganache:
        Open Ganache UI
        Create new workspace
        Configure port to 7545
        Save workspace settings

7. Deploy smart contracts:
    `cd blockchain`
    `truffle compile`
    `truffle migrate`

8. Run the application:
    `cd voting_system_backend`
    `python manage.py runserver`

## Usage Guide 🔍

### Voter Registration
1. Access the registration portal
2. Enter required credentials
3. Complete facial recognition setup
4. Receive SMS verification
5. Store login credentials securely

### Casting Vote
1. Login with credentials
2. Complete face verification
3. Select preferred candidate
4. Confirm vote
5. Receive blockchain transaction confirmation




