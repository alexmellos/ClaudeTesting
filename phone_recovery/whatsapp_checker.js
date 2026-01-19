/**
 * WhatsApp Profile Picture Checker
 *
 * WARNING: This uses an unofficial WhatsApp Web library.
 * - Violates WhatsApp Terms of Service
 * - Could result in account ban if abused
 * - Use at your own risk, only for recovering YOUR OWN number
 *
 * Requirements:
 *   npm install whatsapp-web.js qrcode-terminal
 *
 * Usage:
 *   node whatsapp_checker.js
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const readline = require('readline');

// Configuration
const NUMBERS_FILE = 'numbers_international.txt';
const RESULTS_FILE = 'whatsapp_results.txt';
const DELAY_MS = 3000; // 3 seconds between checks to avoid rate limiting

// Read numbers from file
function loadNumbers() {
    const content = fs.readFileSync(NUMBERS_FILE, 'utf-8');
    return content.trim().split('\n').filter(n => n.length > 0);
}

// Sleep helper
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
    console.log('=' .repeat(50));
    console.log('WhatsApp Profile Picture Checker');
    console.log('=' .repeat(50));
    console.log('\nInitializing WhatsApp Web client...');
    console.log('You will need to scan a QR code with your phone.\n');

    const client = new Client({
        authStrategy: new LocalAuth(),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
    });

    client.on('qr', (qr) => {
        console.log('Scan this QR code with WhatsApp on your phone:');
        qrcode.generate(qr, { small: true });
    });

    client.on('ready', async () => {
        console.log('\n✓ WhatsApp client is ready!\n');

        const numbers = loadNumbers();
        console.log(`Loaded ${numbers.length} numbers to check.\n`);

        const results = [];
        let foundWithPicture = [];

        for (let i = 0; i < numbers.length; i++) {
            const number = numbers[i];
            const numberId = `${number}@c.us`;

            process.stdout.write(`[${i + 1}/${numbers.length}] Checking +${number}... `);

            try {
                // Check if number is registered on WhatsApp
                const isRegistered = await client.isRegisteredUser(numberId);

                if (isRegistered) {
                    // Try to get profile picture
                    try {
                        const profilePicUrl = await client.getProfilePicUrl(numberId);

                        if (profilePicUrl) {
                            console.log('✓ REGISTERED + HAS PROFILE PICTURE!');
                            results.push(`${number} - REGISTERED - HAS PICTURE: ${profilePicUrl}`);
                            foundWithPicture.push({
                                number: number,
                                formatted: `+49 ${number.slice(2, 5)} ${number.slice(5, 9)} ${number.slice(9)}`,
                                pictureUrl: profilePicUrl
                            });
                        } else {
                            console.log('✓ Registered (no profile picture)');
                            results.push(`${number} - REGISTERED - NO PICTURE`);
                        }
                    } catch (picError) {
                        console.log('✓ Registered (picture private/unavailable)');
                        results.push(`${number} - REGISTERED - PICTURE PRIVATE`);
                    }
                } else {
                    console.log('✗ Not on WhatsApp');
                    results.push(`${number} - NOT REGISTERED`);
                }
            } catch (error) {
                console.log(`✗ Error: ${error.message}`);
                results.push(`${number} - ERROR: ${error.message}`);
            }

            // Save progress periodically
            if (i % 10 === 0) {
                fs.writeFileSync(RESULTS_FILE, results.join('\n'));
            }

            // Rate limiting delay
            await sleep(DELAY_MS);
        }

        // Save final results
        fs.writeFileSync(RESULTS_FILE, results.join('\n'));

        console.log('\n' + '=' .repeat(50));
        console.log('SCAN COMPLETE!');
        console.log('=' .repeat(50));

        if (foundWithPicture.length > 0) {
            console.log(`\n🎉 Found ${foundWithPicture.length} number(s) WITH PROFILE PICTURES:\n`);
            foundWithPicture.forEach((item, idx) => {
                console.log(`${idx + 1}. ${item.formatted}`);
                console.log(`   Picture: ${item.pictureUrl}\n`);
            });

            // Save matches to separate file
            const matchesContent = foundWithPicture.map(item =>
                `${item.formatted}\n${item.pictureUrl}\n`
            ).join('\n');
            fs.writeFileSync('MATCHES_WITH_PICTURES.txt', matchesContent);
            console.log('Matches saved to: MATCHES_WITH_PICTURES.txt');
        } else {
            console.log('\nNo numbers with visible profile pictures found.');
            console.log('Note: The picture might be set to "contacts only" privacy.');
        }

        console.log(`\nFull results saved to: ${RESULTS_FILE}`);

        await client.destroy();
        process.exit(0);
    });

    client.on('auth_failure', (msg) => {
        console.error('Authentication failed:', msg);
        process.exit(1);
    });

    client.initialize();
}

main().catch(console.error);
