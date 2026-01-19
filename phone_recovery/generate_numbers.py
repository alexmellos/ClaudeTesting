#!/usr/bin/env python3
"""
Phone Number Recovery Tool
Generates all possible combinations for: 017X3251X60X
Total combinations: 10 × 10 × 10 = 1000
"""

import itertools

def generate_phone_numbers():
    """Generate all possible phone number combinations."""

    # Pattern: 017X3251X60X
    # Unknown positions: X at index 3, 8, 11 (0-indexed)

    base_pattern = "017{0}3251{1}60{2}"

    numbers = []
    for d1, d2, d3 in itertools.product(range(10), repeat=3):
        number = base_pattern.format(d1, d2, d3)
        numbers.append(number)

    return numbers

def prioritize_by_likelihood(numbers):
    """
    Sort numbers by likelihood based on common patterns.
    Optimized for numbers from 2011-2013 era (12-14 years old).
    """

    def score(num):
        score = 0

        # German mobile prefixes - prioritized for 2011-2013 era
        # During that time, O2/E-Plus (0176-0179) and T-Mobile (0175) were very active
        prefix = num[:4]
        prefix_scores = {
            '0176': 15,  # O2 - VERY common in 2011-2013, most new contracts
            '0177': 14,  # E-Plus - very common in that era
            '0178': 13,  # E-Plus - common for prepaid
            '0175': 12,  # T-Mobile - popular in that period
            '0179': 11,  # O2 - common
            '0170': 8,   # Telekom - older prefix, less common for new numbers
            '0171': 8,   # Telekom - older prefix
            '0173': 7,   # Vodafone
            '0174': 7,   # Vodafone
            '0172': 6,   # Telekom - less common in that era
        }
        score += prefix_scores.get(prefix, 0)

        # Check for repeating digits (memorable)
        if num[8] == num[11]:  # The two unknown middle/end digits match
            score += 3

        # Check for sequential patterns
        digits = [int(d) for d in num]
        for i in range(len(digits) - 2):
            if digits[i+1] == digits[i] + 1 and digits[i+2] == digits[i] + 2:
                score += 2

        # Round numbers (0s and 5s are common)
        unknown_digits = [num[3], num[8], num[11]]
        for d in unknown_digits:
            if d in '05':
                score += 1

        return score

    return sorted(numbers, key=score, reverse=True)

def save_numbers(numbers, filename="possible_numbers.txt"):
    """Save numbers to a file."""
    with open(filename, 'w') as f:
        for i, num in enumerate(numbers, 1):
            # Format: local and international
            international = f"+49{num[1:]}"  # Remove leading 0, add +49
            f.write(f"{i:4d}. {num} ({international})\n")
    print(f"Saved {len(numbers)} numbers to {filename}")

def save_for_whatsapp_check(numbers, filename="numbers_international.txt"):
    """Save numbers in international format for WhatsApp checking."""
    with open(filename, 'w') as f:
        for num in numbers:
            international = f"49{num[1:]}"  # WhatsApp format without +
            f.write(f"{international}\n")
    print(f"Saved {len(numbers)} numbers in WhatsApp format to {filename}")

if __name__ == "__main__":
    print("=" * 50)
    print("Phone Number Recovery Tool")
    print("Pattern: 017X3251X60X")
    print("=" * 50)

    # Generate all combinations
    numbers = generate_phone_numbers()
    print(f"\nGenerated {len(numbers)} possible combinations")

    # Prioritize by likelihood
    prioritized = prioritize_by_likelihood(numbers)

    # Save files
    save_numbers(prioritized, "possible_numbers.txt")
    save_for_whatsapp_check(prioritized, "numbers_international.txt")

    # Show top 20 most likely
    print("\n" + "=" * 50)
    print("TOP 20 MOST LIKELY NUMBERS:")
    print("=" * 50)
    for i, num in enumerate(prioritized[:20], 1):
        international = f"+49 {num[1:4]} {num[4:8]} {num[8:]}"
        print(f"{i:2d}. {num}  →  {international}")

    print("\n" + "=" * 50)
    print("Files created:")
    print("  - possible_numbers.txt (all 1000 numbers, prioritized)")
    print("  - numbers_international.txt (for WhatsApp checking)")
    print("=" * 50)
