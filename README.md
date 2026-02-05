# Q Bot - Ultimate Discord Security & Monitoring System 🛡️

**نظام المراقبة والحماية الشامل لسيرفرات ديسكورد**

---

## 📋 المحتويات / Table of Contents

- [English Documentation](#english-documentation)
- [الوثائق العربية](#الوثائق-عربية)

---

# English Documentation

## 🎯 Overview

Q Bot is an **ultra-stealth** Discord security and monitoring bot designed to protect your server while remaining completely invisible to regular members. It provides comprehensive monitoring, instant alerts, and powerful moderation tools - all controlled via private DM commands.

### Key Features

✅ **Complete Stealth** - Looks like a normal utility bot
✅ **DM-Only Control** - All commands via private messages
✅ **Comprehensive Monitoring** - Tracks everything that matters
✅ **Quick Actions** - Rapid response to threats
✅ **Smart Filtering** - Control what you want to be notified about
✅ **Whitelist System** - Trust your admins
✅ **Encrypted Database** - Your data stays secure
✅ **Auto-Reply Mask** - Optional channel auto-responder

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the bot files
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Set these environment variables (required):

```bash
TOKEN=your_discord_bot_token
OWNER_ID=your_discord_user_id
GUILD_ID=your_server_id  # Recommended
```

Optional settings:
```bash
DB_KEY=your_encryption_key  # For database encryption
DM_ALERTS=true  # Enable/disable DM alerts
ENCRYPT_DB=true  # Enable database encryption
```

### 3. Run

```bash
python bot.py
```

---

## 📱 DM Commands

All commands start with `.` and work **only** in DMs with the bot owner.

### 📋 Monitoring Commands

| Command | Arabic | Description |
|---------|--------|-------------|
| `.watch <user_id>` | `.راقب <id>` | Start monitoring a user |
| `.unwatch <user_id>` | `.الغاء <id>` | Stop monitoring a user |
| `.list` | `.قائمة` | List all watched users |
| `.info <user_id>` | `.معلومات <id>` | Get detailed user info |
| `.logs <user_id>` | `.سجل <id>` | View user activity logs |

### ✅ Whitelist Commands

| Command | Description |
|---------|-------------|
| `.whitelist <user_id>` | Add trusted user (skip alerts) |
| `.unwhitelist <user_id>` | Remove from whitelist |
| `.listwhite` | Show whitelisted users |

### 🔧 Filter Commands

| Command | Description |
|---------|-------------|
| `.filter <name> on/off` | Toggle specific filter |
| `.filter all on/off` | Toggle all filters |
| `.filter reset` | Reset to defaults |
| `.filters` | Show all filter statuses |

**Available Filters:**
- `roles` - Role changes
- `channels` - Channel changes  
- `members` - Member joins/leaves
- `messages` - Message edits/deletes (watched users only)
- `moderation` - Bans/kicks/timeouts
- `server` - Server settings changes
- `bots` - Bot additions (always critical)
- `invites` - Invite tracking
- `voice` - Voice channel activity

### ⚔️ Moderation Commands

| Command | Arabic | Description |
|---------|--------|-------------|
| `.strip <user_id>` | `.سحب <id>` | Remove all roles from user |
| `.ban <user_id> [reason]` | `.حظر <id>` | Ban user |
| `.kick <user_id> [reason]` | `.طرد <id>` | Kick user |
| `.timeout <user_id> [minutes]` | `.كتم <id>` | Timeout user |

### 📊 Server Info Commands

| Command | Arabic | Description |
|---------|--------|-------------|
| `.channels` | `.قنوات` | List all channels |
| `.roles` | `.رتب` | List all roles with risk levels |
| `.members` | `.اعضاء` | Show member summary |
| `.stats` | `.احصائيات` | Bot statistics |

### ⚙️ Settings Commands

| Command | Description |
|---------|-------------|
| `.settings` | View current bot settings |
| `.mask set_channel <id>` | Set auto-reply channel |
| `.mask set_reply <text>` | Set auto-reply message |
| `.mask clear` | Clear auto-reply settings |

### ⚡ Quick Actions

When you receive an alert with quick actions, respond with:
- Just the number (e.g., `1`) - Acts on most recent alert
- Or `ACTION_ID NUMBER` (e.g., `ABC123 1`) - Acts on specific alert

**Quick Action Options (vary by event):**
1. Ban
2. Kick  
3. Strip Roles
4. Timeout
5. Get Info
6. Ignore

---

## 🎭 Fake Slash Commands (Public Cover)

These commands are visible to everyone and make the bot look normal:

- `/help` - Shows fake help message
- `/ping` - Shows bot latency
- `/serverinfo` - Server information
- `/avatar [user]` - Show user avatar
- `/set-auto-reply` - (Owner only) Set auto-reply channel

---

## 📊 What Gets Monitored?

### 🔴 Critical (Always Alerted)

- **Bot Additions** - Any bot added to server
  - Who added it
  - Bot permissions
  - Risk level
  - Quick actions available

- **Server Settings** - Major server changes
- **Mass Actions** - Multiple deletions/changes

### 🟡 Warning (Filterable)

- **Role Changes** - Create/delete/modify roles
- **Channel Changes** - Create/delete/modify channels
- **Member Updates** - Role/permission changes
- **Moderation Actions** - Bans/kicks/timeouts

### 🟢 Info (Filterable)

- **Member Joins** - New members (alerts for suspicious accounts)
- **Member Leaves** - Member departures  
- **Voice Activity** - Watched users only
- **Invite Tracking** - Invite creation/deletion
- **Message Changes** - Watched users only (edits/deletes)

---

## 🔐 Security Features

### Database Encryption
- All data encrypted at rest
- Uses PBKDF2 with SHA-256
- Configurable encryption key

### Stealth Mode
- Appears as normal utility bot
- No suspicious presence
- Fake public commands for cover
- All real control via DMs

### Access Control
- Owner-only commands
- Guild-locked (optional)
- Auto-leave unauthorized servers

---

## 📁 File Structure

```
q-bot/
├── bot.py              # Main bot file
├── commands.py         # DM command handlers
├── monitors.py         # Event monitoring system
├── config.py           # Configuration
├── db_manager.py       # Database with encryption
├── logger.py           # Logging system
├── mask.py             # Auto-reply system
├── filters.py          # Notification filtering
├── whitelist.py        # Whitelist management
├── quick_actions.py    # Quick action system
├── permissions.py      # Permission analysis
├── utils.py            # Utility functions
├── dm_notify.py        # DM alert system
├── requirements.txt    # Dependencies
├── README.md           # This file
└── db.json             # Database (auto-created)
```

---

## ⚠️ Important Notes

1. **No Server Channels** - Everything is via DM only for maximum stealth
2. **Encryption** - Change the default `DB_KEY` in production
3. **Permissions** - Bot needs these Discord permissions:
   - View Channels
   - Send Messages  
   - View Audit Log (for detailed monitoring)
   - Manage Roles (for strip command)
   - Ban Members (for ban command)
   - Kick Members (for kick command)
   - Moderate Members (for timeout)

4. **Rate Limiting** - Max 30 alerts per minute (configurable)
5. **Watched Users** - Get full message monitoring (edits/deletes)
6. **Whitelisted Users** - Skip non-critical alerts (e.g., trusted admins)

---

## 🆘 Support

For issues or questions, check the code comments or logs in `q_bot.log`.

---

# الوثائق العربية

## 🎯 نظرة عامة

بوت Q هو نظام **مراقبة وحماية خفي بالكامل** لسيرفرات ديسكورد. مصمم لحماية سيرفرك بينما يبقى غير مرئي تماماً للأعضاء العاديين.

### المميزات الرئيسية

✅ **إخفاء تام** - يبدو كبوت عادي
✅ **التحكم عبر DM فقط** - كل الأوامر عبر الرسائل الخاصة
✅ **مراقبة شاملة** - يتتبع كل شيء مهم
✅ **إجراءات سريعة** - رد فعل سريع للتهديدات
✅ **فلترة ذكية** - تحكم بما تريد معرفته
✅ **نظام الموثوقين** - ثق بمشرفيك
✅ **قاعدة بيانات مشفرة** - بياناتك آمنة
✅ **رد تلقائي** - رد آلي اختياري في قناة معينة

---

## 🚀 البدء السريع

### 1. التثبيت

```bash
# حمل ملفات البوت
# ثبت المتطلبات
pip install -r requirements.txt
```

### 2. الإعداد

ضع هذه المتغيرات (مطلوبة):

```bash
TOKEN=توكن_البوت
OWNER_ID=معرف_الديسكورد_حقك
GUILD_ID=معرف_السيرفر  # موصى به
```

اختياري:
```bash
DB_KEY=مفتاح_التشفير
DM_ALERTS=true
ENCRYPT_DB=true
```

### 3. التشغيل

```bash
python bot.py
```

---

## 📱 أوامر DM

كل الأوامر تبدأ بـ `.` وتعمل **فقط** في رسائلك الخاصة مع البوت.

### 📋 أوامر المراقبة

```
.راقب <معرف>        - بدء مراقبة شخص
.الغاء <معرف>       - إيقاف المراقبة
.قائمة              - عرض المراقبين
.معلومات <معرف>    - معلومات مفصلة
.سجل <معرف>        - سجل النشاط
```

### ⚔️ أوامر الإدارة

```
.سحب <معرف>        - سحب كل الرتب
.حظر <معرف>        - باند
.طرد <معرف>        - كيك
.كتم <معرف>        - كتم مؤقت
```

### 📊 معلومات السيرفر

```
.قنوات             - قائمة القنوات
.رتب               - قائمة الرتب
.اعضاء             - ملخص الأعضاء
.احصائيات         - إحصائيات البوت
```

---

## 🎭 الأوامر الوهمية (الغطاء)

هذه الأوامر مرئية للجميع تخلي البوت يبدو عادي:

- `/help` - مساعدة وهمية
- `/ping` - السرعة
- `/serverinfo` - معلومات السيرفر
- `/avatar` - الأفاتار

---

## 🔔 أنواع التنبيهات

### 🔴 حرجة (دائماً)
- إضافة بوتات
- تغييرات السيرفر الكبيرة

### 🟡 تحذيرية (قابلة للفلترة)
- تغييرات الرتب
- تغييرات القنوات
- إجراءات الإدارة

### 🟢 معلومات (قابلة للفلترة)
- دخول/خروج الأعضاء
- نشاط الصوت (للمراقبين)
- الدعوات

---

## ⚡ الإجراءات السريعة

لما يجيك تنبيه مع خيارات، رد بـ:
- رقم فقط (مثل `1`) للتنبيه الأخير
- أو `الكود الرقم` (مثل `ABC123 1`)

---

## 🔐 الأمان

- 🔒 قاعدة بيانات مشفرة
- 👻 وضع التخفي الكامل
- 🚫 DM فقط - ما فيه قنوات في السيرفر
- 🛡️ حماية من السيرفرات غير المصرح بها

---

## ⚠️ ملاحظات مهمة

1. **ممنوع القنوات** - كل شيء DM فقط للإخفاء الكامل
2. **غير المفتاح** - غير `DB_KEY` الافتراضي
3. **الصلاحيات** - البوت يحتاج:
   - قراءة القنوات
   - إرسال رسائل
   - قراءة سجل الأحداث
   - إدارة الأدوار
   - باند/كيك
   - كتم الأعضاء

4. **الحد الأقصى** - 30 تنبيه بالدقيقة
5. **المراقبون** - يحصلون على مراقبة الرسائل الكاملة
6. **الموثوقون** - ما تجيك تنبيهات غير مهمة عنهم

---

## 📞 الدعم

للمشاكل أو الأسئلة، شوف التعليقات في الكود أو السجل في `q_bot.log`.

---

## 📝 License

This bot is for personal use. Modify as needed for your server.

**Made with ❤️ for server security**

---

**حماية سيرفرك تبدأ هنا! 🛡️**
