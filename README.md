# 🛡️ وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)

مشروع متكامل ومستقل بلغة Python لرصد الأخبار واستخلاص الذكاء الإخباري تلقائياً في قطاعين محوريين:
1. **قطاع التقنية والذكاء الاصطناعي (AI & Tech Giants):**
   - متابعة سباق الذكاء الاصطناعي والنماذج التوليدية: Gemini, ChatGPT, Claude, OpenAI, Anthropic, DeepMind.
   - كبرى شركات التقنية: Google, Apple, Samsung, Microsoft, Nvidia.
   - أحدث أدوات ومكتبات البرمجة والأنظمة للمطورين (Python, Frameworks, Developer Ecosystem).
2. **قطاع الرياضة وكرة القدم الأوروبية (Sports & European Football):**
   - تغطية حصرية ومكثفة لنادي **برشلونة (FC Barcelona)**: الصفقات، التشكيلة، تصريحات هانسي فليك، لامين يامال، والأخبار الحصرية.
   - دوري أبطال أوروبا (UEFA Champions League) وأقوى الدوريات الأوروبية (الدوري الإسباني، الإنجليزي، الإيطالي).

---

## 🏗️ الهيكلية المعمارية للمشروع (Architecture)

```
z:\Antigravity project\
├── config.py             # مصادر الـ RSS، الكلمات المفتاحية، أوزان التقييم، والمتغيرات البيئية
├── fetcher.py            # محرك سحب الخلاصات (feedparser + requests) مع معالجة الأخطاء والتنظيف
├── database.py           # قاعدة بيانات SQLite لمنع التكرار (Deduplication) وتسجيل العمليات
├── processor.py          # فلترة الأخبار، قياس درجة الصلة (Relevance Scoring)، وتوليد الموجز التنفيذي
├── notifier.py           # إرسال تنبيهات Telegram Bot + توليد لوحة تحكم HTML داكنة وفائقة الأناقة
├── main.py               # وحدة التحكم الرئيسية (CLI) وإدارة خط سير العمليات مع سجلات ملونة
├── requirements.txt      # قائمة الاعتماديات والمكتبات المطلوبة بدقة
├── .env.example          # قالب الإعدادات السرية والمفاتيح الاختيارية
├── run_watchdog.bat      # سكريبت تشغيل فوري بنقرة واحدة لنظام Windows
└── README.md             # دليل التشغيل والتوثيق والجدولة التلقائية
```

---

## ⚡ البدء السريع والتشغيل الفوري (Quick Start)

### 1. تثبيت المتطلبات (مرة واحدة):
```bash
pip install -r requirements.txt
```

### 2. تشغيل الفحص المباشر:
```bash
python main.py
```
> **ملاحظة:** سيعمل النظام فوراً ويقوم بسحب مئات الأخبار الحقيقية، وإجراء الفلترة واستخلاص أفضل 5 أحداث في كل قطاع، ثم توليد لوحة التحكم الداكنة `reports/latest.html` وفتحها مباشرة في متصفحك!

### 3. خيارات سطر الأوامر المفيدة (CLI Options):
- **إعادة توليد التقرير متضمناً الأخبار السابقة (للتجربة أو التحديث):**
  ```bash
  python main.py --force
  ```
- **تشغيل الفحص دون فتح المتصفح تلقائياً:**
  ```bash
  python main.py --no-browser
  ```
- **تشغيل مسار واحد فقط (مثل الذكاء الاصطناعي فقط):**
  ```bash
  python main.py --track tech
  # أو للرياضة فقط:
  python main.py --track sports
  ```
- **تجربة وهمية دون الكتابة في قاعدة البيانات (Dry Run):**
  ```bash
  python main.py --dry-run
  ```
- **عرض إحصائيات قاعدة البيانات والأخبار المخزنة:**
  ```bash
  python main.py --stats
  ```

---

## ⚙️ الإعدادات المتقدمة وتفعيل Telegram Bot (اختياري)

إذا أردت وصول التقارير مباشرة إلى هاتفك عبر Telegram:
1. انسخ ملف `.env.example` إلى `.env`:
   ```bash
   copy .env.example .env
   ```
2. افتح `.env` وضع المفاتيح الخاصة بك:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
   TELEGRAM_CHAT_ID=987654321
   ```
*(إذا تركت هذه الحقول فارغة، سيعمل النظام بشكل طبيعي جداً ويعتمد على لوحة تحكم الـ HTML الحديثة).*

---

## ⏰ دليل الجدولة الدورية التلقائية داخل Antigravity (Scheduled Tasks)

تم تصميم هذا الوكيل ليعمل كوحدة ذاتية ومستقلة تدعم الجدولة الدورية التلقائية ليعمل كل 6 أو 12 ساعة داخل بيئة **Antigravity**.

### الطريقة الأولى: عبر واجهة Antigravity الرسومية (Left-hand Sidebar)
1. في القائمة الجانبية اليسرى لنافذة Antigravity (Left-hand Sidebar)، اضغط على **Scheduled Tasks**.
2. اضغط على زر **+ New Task** لإنشاء مهمة مجدولة جديدة.
3. قم بملء الحقول على النحو التالي:
   - **Task Name (اسم المهمة):** `AI & Sports Watchdog Monitor`
   - **Schedule Type:** اختر **Cron Expression**.
   - **Cron Expression:**
     - للتشغيل **كل 6 ساعات**: `0 */6 * * *`
     - للتشغيل **كل 12 ساعة**: `0 */12 * * *`
     - للتشغيل **يومياً الساعة 8:00 صباحاً**: `0 8 * * *`
   - **Prompt / Action (الأمر المطلوب تنفيذه):**
     ```text
     Run the command: python "z:/Antigravity project/main.py" --no-browser
     Review the latest extracted intelligence and summarize the top highlights for me.
     ```
4. اضغط **Save / Enable Task**. سيتولى Antigravity إيقاظ الوكيل وتشغيل المهمة بانتظام في الخلفية.

---

### الطريقة الثانية: عبر أمر الدردشة السريع (`/schedule`)
يمكنك تفعيل الجدولة مباشرة من نافذة المحادثة في Antigravity بكتابة الأمر:

**للتشغيل كل 6 ساعات:**
```
/schedule CronExpression="0 */6 * * *" Prompt="Execute python 'z:/Antigravity project/main.py' --no-browser and report any breaking news"
```

**للتشغيل كل 12 ساعة:**
```
/schedule CronExpression="0 */12 * * *" Prompt="Execute python 'z:/Antigravity project/main.py' --no-browser and send me the latest executive brief"
```

---

### الطريقة الثالثة: عبر مجدول مهام ويندوز (Windows Task Scheduler)
إذا أردت أن يعمل الوكيل كخادم خلفي دائم على مستوى نظام التشغيل:
1. افتح قائمة ابدأ واكتب `Task Scheduler` (مجدول المهام).
2. اختر **Create Basic Task** وسَمِّها `AI-Sports-Watchdog`.
3. اضبط التكرار على **Daily** مع تكرار كل 6 ساعات (**Repeat task every 6 hours**).
4. في شاشة **Action** اختر **Start a program**.
5. حدد مسار ملف التشغيل:
   - Program/script: `cmd.exe`
   - Add arguments: `/c "z:\Antigravity project\run_watchdog.bat"`
   - Start in: `z:\Antigravity project`
6. اضغط **Finish**.

---

## 📊 مميزات لوحة التحكم الداكنة (Modern Dark Dashboard)

- **تصميم زجاجي عصري (Glassmorphism Dark UI):** يدعم شاشات الحواسب والهواتف ومتوافق مع النمط الليلي.
- **تصفية وبحث لحظي (Live Search & Filter):** كتابة أي اسم (مثل `Yamal` أو `Gemini` أو `Apple`) يقوم بفلترة الأخبار فورياً.
- **مصفوفة الأهمية والدرجات:** كل خبر يحمل شارة تقييم من 0 إلى 100 بناءً على وزنه وأهميته.
- **أزرار المصدر المباشر:** إمكانية الانتقال للمقال الأصلي بضغطة زر واحدة.
- **تحديث دائم:** يتم حفظ آخر تقرير تم إنشاؤه تحت الرابط الثابت: `reports/latest.html`.

---
تم التطوير ليعمل بكفاءة عالية وبدون أي استهلاك لمفاتيح مدفوعة.
