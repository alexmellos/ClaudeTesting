# Phone Number Recovery Tool

Recover your forgotten phone number by checking WhatsApp profile pictures.

**Pattern:** `017X3251X60X` (German mobile)
**Combinations:** 1,000 possible numbers

## Quick Start

### Step 1: Generate the number list
```bash
python3 generate_numbers.py
```

This creates:
- `possible_numbers.txt` - All 1000 numbers, sorted by likelihood
- `numbers_international.txt` - Numbers formatted for WhatsApp checking

### Step 2: Check WhatsApp (automated)
```bash
npm install
npm run check
```

1. Scan the QR code with your WhatsApp
2. The script will check all 1000 numbers (~50 minutes with rate limiting)
3. Results saved to `whatsapp_results.txt`
4. Numbers with profile pictures saved to `MATCHES_WITH_PICTURES.txt`

## Manual Alternative

If you prefer not to use automation:
1. Open `possible_numbers.txt`
2. Start with the top 20 (most likely patterns)
3. Save each number as a contact and check WhatsApp

## Files

| File | Description |
|------|-------------|
| `generate_numbers.py` | Generates all possible combinations |
| `whatsapp_checker.js` | Automated WhatsApp profile checker |
| `possible_numbers.txt` | All numbers (generated) |
| `numbers_international.txt` | Numbers for WhatsApp (generated) |

## Warning

The WhatsApp checker uses an unofficial library. Use responsibly and only for recovering your own number.
