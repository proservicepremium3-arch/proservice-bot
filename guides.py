from telegram import InlineKeyboardMarkup, InlineKeyboardButton

GUIDES = {
    "policy": {
        "name": "⚠️ Login & Warranty Policy",
        "text": """⚠️ Important Login & Warranty Policy

Once you log in, you cannot log out or switch to another device. Please choose your device carefully before logging in. If you delete the app or sign out and log in again, there is a $2.9 fee"""
    },

    "netflix_household": {
        "name": "🍿 Netflix Household 24h Guide",
        "text": """🍿 Bot automatically Fix Verify Code Netflix Household ដោយខ្លួនឯង បាន 24ម៉ោង

📱 សម្រាប់ Phone

1. ចុច Watch Temporarily → Send Email
2. ចូល Telegram Bot: @Proserviceautomaticbot រួចចុច Start
3. យក Code 4 ខ្ទង់ដែល Bot ផ្ញើមក បញ្ចូលលើ Phone ជាការស្រេច!

📺 សម្រាប់ TV

1. ចុច Update Netflix Household លើ TV
2. ចូល Bot @Proserviceautomaticbot រួចចុច Start
3. ចុចប៊ូតុង ✅ Update Household Here ជាការស្រេច!

⏳ ចំណាំ៖ Code និង Link មានសុពលភាពតែ 15 នាទី។ បើមិនទាន់បាន សូមចុច Resend រួចចូល Bot ចុច 🔄 Check for New Messages ម្ដងទៀត។"""
    },

    "netflix_policy": {
        "name": "⚠️ Netflix Login & Warranty Policy",
        "text": """⚠️Netflix : Important Login & Warranty Policy
We can provide you with a login code a maximum of two times, allowing you to log in on up to two devices only. Once logged in, you cannot log out or switch to another device. Please make sure you choose your device carefully before logging in.

If we detect repeated suspicious or irregular login activity, we reserve the right to refuse future sales to you. Please follow our login policy carefully to ensure your warranty remains valid.
One person’s misuse can affect everyone’s access. Please use responsibly.

Thank you for your understanding and cooperation! 🙏"""
    }
}

def get_guides_keyboard(customer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚠️ Login & Warranty Policy", callback_data=f"guide:{customer_id}:policy"),
        ],
        [
            InlineKeyboardButton("🍿 Netflix Household 24h", callback_data=f"guide:{customer_id}:netflix_household"),
        ],
        [
            InlineKeyboardButton("⚠️ Netflix Login Policy", callback_data=f"guide:{customer_id}:netflix_policy"),
        ],
        [
            InlineKeyboardButton("🔙 Quick Replies", callback_data=f"qmenu:{customer_id}"),
            InlineKeyboardButton("📦 Products", callback_data=f"pmenu:{customer_id}"),
        ]
    ])

