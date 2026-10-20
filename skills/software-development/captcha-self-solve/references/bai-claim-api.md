# b.ai Claim API Flow (June 2025)

## Endpoints
- Check claimed: `GET /trpc/lambda/user.hasClaimedSignupBonus?batch=1&input={"0":{"json":null}}`
- Claim: `POST /trpc/lambda/user.claimSignupBonus?batch=1`

## Claim Payload
```json
{"0":{"json":{"turnstileToken":"<solved_token>","type":"oauth:google","encryptedToken":"<encrypted>"}}}
```

## Encrypted Token Generation (CryptoJS AES compatible)
```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64, os, hashlib, time

ENCRYPT_KEY = "claimSignupBonus"

def make_encrypted_token(display_name):
    """Replicate CryptoJS.AES.encrypt(plaintext, passphrase).toString()"""
    timestamp = int(time.time() * 1000)
    plaintext = f"{display_name} welcome gift-claim|{timestamp}"
    
    # CryptoJS EVP_BytesToKey derivation (MD5-based)
    key_bytes = ENCRYPT_KEY.encode('utf-8')
    salt = os.urandom(8)
    key_iv = b''
    prev = b''
    while len(key_iv) < 48:
        prev = hashlib.md5(prev + key_bytes + salt).digest()
        key_iv += prev
    
    aes_key = key_iv[:32]
    iv = key_iv[32:48]
    
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode('utf-8'), 16)
    encrypted = cipher.encrypt(padded)
    
    # CryptoJS format: base64("Salted__" + salt + ciphertext)
    return base64.b64encode(b"Salted__" + salt + encrypted).decode('utf-8')
```

## Turnstile
- Sitekey: `0x4AAAAAADKhTSXIozuHjOoF`
- Page URL: `https://chat.b.ai/chat`
- Self-solve requires residential IP
- Paid solver (sctg.xyz) works from any IP

## Session Cookie
- Framework: AuthJS (NextAuth successor)
- Cookie domain: chat.b.ai / chat.ainft.com
- Verify via: `/api/auth/session` → `response.user.name`

## Architecture Decision
- Login phase: MUST use browser (Google OAuth popup uses postMessage)
- Claim phase: pure API (solver + requests) — no browser needed
- Split into 2 phases for efficiency: login parallel headless → claim parallel API
