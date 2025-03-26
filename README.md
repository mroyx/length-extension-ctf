### Overview
This project is a Capture The Flag (CTF) challenge designed to demonstrate the mechanics and real-world impact of Length Extension attacks — a cryptographic vulnerability affecting hash functions like MD5 and SHA-1.

In this challenge, users can browse a store and attempt to purchase an item. Although their account balance isn't sufficient to complete the transaction, a flaw in the way requests are signed allows them to exploit a length extension attack to manipulate the payment data — ultimately enabling them to purchase items without spending any money.

Perfect for CTF participants, security researchers, or anyone curious about cryptographic flaws in practice.

📖 Blog Post: <url>
🎥 Video Demo: <url>

Suggestions, feedback, or improvements are always welcome!

### Setup Instructions
##### 1. Install the Requirements 
pip install -r requirements.txt

##### 2. Create the MySQL Database
sudo mysql -u root
CREATE DATABASE ctf;
CREATE USER 'flaskuser'@'localhost' IDENTIFIED BY 'flaskpassword';
GRANT ALL PRIVILEGES ON ctf.* TO 'flaskuser'@'localhost';
FLUSH PRIVILEGES;

##### 3. Run the Setup Script to Create the Tables
python3 setup.py

##### 4. Launch the Application
python3 app/routes.py
