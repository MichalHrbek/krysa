import hashlib, os, base64, hmac, json

HASH_NAME = 'sha256'     # Hash algorithm to use (e.g., sha256)
ITERATIONS = 100000      # Number of iterations for PBKDF2
SALT_SIZE = 16           # Size of the salt in bytes
KEY_LENGTH = 32          # Length of the derived key in bytes

USERS_FILE = "data/users.json"

class Hasher:
	def hash_password(password: str) -> str:
		salt = os.urandom(SALT_SIZE)
		key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, ITERATIONS, dklen=KEY_LENGTH)
		salt_b64 = base64.b64encode(salt).decode('utf-8')
		key_b64 = base64.b64encode(key).decode('utf-8')
		return f"{salt_b64}${key_b64}"

	def verify_password(stored_hash: str, password: str) -> bool:
		try:
			salt_b64, key_b64 = stored_hash.split('$')
		except ValueError:
			return False

		salt = base64.b64decode(salt_b64)
		original_key = base64.b64decode(key_b64)
		
		new_key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, ITERATIONS, dklen=KEY_LENGTH)
		
		return hmac.compare_digest(new_key, original_key)

def _load_users() -> dict:
	if not os.path.exists(USERS_FILE):
		return {}
	with open(USERS_FILE, 'r') as f:
		return json.loads(f.read())

class Authenticator:
	def set_user(username, password):
		users = _load_users()
		users[username] = Hasher.hash_password(password)

		with open(USERS_FILE, 'w') as f:
			f.write(json.dumps(users))

	def verify_user(username, password) -> bool:
		users = _load_users()
		if username not in users:
			return False
		return Hasher.verify_password(users[username], password)

if __name__ == '__main__':
	os.makedirs("data/", exist_ok=True)
	username = input("Enter a username: ")
	password = input("Enter a password: ")
	password_attempt = input("Re-enter the password for verification: ")
	
	if password != password_attempt:
		print("Entered different password")
	
	Authenticator.set_user(username, password)

	if Authenticator.verify_user(username, password_attempt):
		print("Password verified successfully")
	else:
		print("Something went wrong")