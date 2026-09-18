import streamlit as st

st.set_page_config(
    page_title="The QC Analyst Decision Gap™",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# BRAND + COPY
# -----------------------------
TITLE = "THE QC ANALYST DECISION GAP™"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."

DIMENSIONS = {
    "science": {
        "name": "الفهم الكروماتوجرافي",
        "en": "Chromatography Understanding",
        "short": "الفهم العلمي",
    },
    "investigation": {
        "name": "منطق التحقيق",
        "en": "Investigation Logic",
        "short": "التحقيق",
    },
    "evidence": {
        "name": "الانضباط مع الأدلة",
        "en": "Evidence Discipline",
        "short": "الأدلة",
    },
    "gmp": {
        "name": "GMP وسلامة البيانات",
        "en": "GMP & Data Integrity",
        "short": "GMP",
    },
    "instrument": {
        "name": "فهم الجهاز والنظام",
        "en": "Instrument & System Thinking",
        "short": "الجهاز",
    },
    "decision": {
        "name": "القرار والتوثيق",
        "en": "Decision & Documentation",
        "short": "القرار",
    },
}

QUESTIONS = [
    # 1 — SCIENCE
    {
        "id": 1,
        "dim": "science",
        "q": "لو زمن الاحتجاز (RT) لكل القمم انخفض فجأة إلى النصف تقريبًا، أول تفسير علمي يخطر ببالك هو:",
        "options": [
            ("العمود انتهى ويجب تغييره فورًا.", 1),
            ("قد يكون تغيرًا في معدل التدفق أو تركيب الطور المتحرك، ويجب التحقق قبل الحكم.", 4),
            ("أعيد الحقن مرة أخرى وأرى إن كانت النتيجة ستتحسن.", 2),
            ("أغير نسبة الطور المتحرك مباشرة لتعويض RT.", 1),
        ],
    },
    {
        "id": 2,
        "dim": "science",
        "q": "قمة واحدة فقط أصبحت عريضة بينما باقي القمم طبيعية. أفضل قراءة أولية هي:",
        "options": [
            ("المشكلة غالبًا تخص هذا المركب أو تفاعله مع النظام، وليست بالضرورة عطلًا عامًا.", 4),
            ("العمود كله تالف.", 1),
            ("المضخة بها مشكلة مؤكدة.", 1),
            ("لا فرق؛ أي Peak Shape issue تعني نفس السبب.", 1),
        ],
    },
    {
        "id": 3,
        "dim": "science",
        "q": "لو الضغط ارتفع بينما RT وشكل القمم ما زالا قريبين من الطبيعي، أنسب تفكير هو:",
        "options": [
            ("أفصل أولًا هل المقاومة زادت في العمود أم في جزء آخر من مسار السريان.", 4),
            ("أخفض التدفق حتى ينجح SST.", 1),
            ("أرفع حرارة العمود مباشرة.", 1),
            ("أغير العمود بدون اختبار.", 1),
        ],
    },
    {
        "id": 4,
        "dim": "science",
        "q": "الـResolution انخفضت، لكن RT للقمتين لم يتغير كثيرًا. هذا يعني أن:",
        "options": [
            ("لا يمكن ربط المشكلة بالاحتجاز فقط؛ يجب تقييم selectivity وPeak Width أيضًا.", 4),
            ("الـflow بالتأكيد خطأ.", 1),
            ("المشكلة في detector فقط.", 1),
            ("لا يهم شكل القمم طالما RT ثابت.", 1),
        ],
    },
    {
        "id": 5,
        "dim": "science",
        "q": "أفضل وصف للعلاقة بين العرض الظاهر للمشكلة والسبب الجذري هو:",
        "options": [
            ("مكان ظهور العرض هو غالبًا مكان السبب.", 1),
            ("الأعراض قد تتشابه والسبب قد يكون في جزء آخر من النظام.", 4),
            ("لكل عرض سبب واحد معروف.", 1),
            ("خبرة المحلل تكفي بدون اختبارات تمييزية.", 2),
        ],
    },

    # 2 — INVESTIGATION
    {
        "id": 6,
        "dim": "investigation",
        "q": "أول مرة ترى فيها مشكلة جديدة، ما أفضل بداية؟",
        "options": [
            ("أكتب كل الأسباب المحتملة وأبدأ أغيّر واحدًا وراء الآخر.", 2),
            ("أثبت الملاحظة كما هي، أحدد ما تغير، ثم أختار سؤالًا أو اختبارًا يضيّق الاحتمالات.", 4),
            ("أسأل أكثر شخص خبرة عن الحل مباشرة.", 2),
            ("أكرر الحقن للتأكد فقط.", 1),
        ],
    },
    {
        "id": 7,
        "dim": "investigation",
        "q": "طريقة كانت ناجحة الأسبوع الماضي واليوم فشلت. السؤال الأعلى قيمة مبكرًا هو:",
        "options": [
            ("هل يمكن تغيير العمود؟", 1),
            ("ما الذي تغير بين آخر تشغيل ناجح والتشغيل الحالي؟", 4),
            ("هل نزيد عدد الحقن؟", 1),
            ("هل المشكلة حدثت لزميل آخر من قبل؟", 2),
        ],
    },
    {
        "id": 8,
        "dim": "investigation",
        "q": "لديك ثلاث فرضيات محتملة. أفضل اختبار هو الذي:",
        "options": [
            ("يغير أكبر عدد من المتغيرات بسرعة.", 1),
            ("يفصل بوضوح بين فرضيتين أو أكثر بنتيجة قابلة للتفسير.", 4),
            ("هو الأسهل في التنفيذ فقط.", 2),
            ("يعطي أكبر فرصة للحصول على نتيجة Passing.", 1),
        ],
    },
    {
        "id": 9,
        "dim": "investigation",
        "q": "غيرت الطور المتحرك والعمود ودرجة الحرارة في نفس الوقت وتحسنت النتيجة. ماذا عرفت؟",
        "options": [
            ("عرفت السبب الجذري.", 1),
            ("عرفت أن واحدًا أو أكثر من التغييرات أثّر، لكن لا أعرف أيها تحديدًا.", 4),
            ("أثبت أن العمود كان السبب.", 1),
            ("يكفي طالما النتيجة نجحت.", 1),
        ],
    },
    {
        "id": 10,
        "dim": "investigation",
        "q": "متى تقول إن Root Cause تم تأكيده؟",
        "options": [
            ("عندما يكون السبب شائعًا في خبرتي.", 1),
            ("عندما ينجح تدخل مستهدف كما توقعت وتصبح البدائل المعقولة أقل احتمالًا بوضوح.", 4),
            ("عندما يوافق شخصان في الفريق على نفس الرأي.", 2),
            ("عندما تعود SST للنجاح مرة واحدة.", 2),
        ],
    },

    # 3 — EVIDENCE
    {
        "id": 11,
        "dim": "evidence",
        "q": "الضغط أصبح 310 bar بعد 25 حقنة. ما الذي يمكنك قوله بثقة؟",
        "options": [
            ("الضغط زاد تدريجيًا مع كل حقنة.", 1),
            ("نعرف قيمة الضغط بعد 25 حقنة، لكن لا نعرف اتجاهه أثناء السلسلة بدون trend data.", 4),
            ("العمود انسد تدريجيًا.", 1),
            ("العينات لوثت العمود.", 1),
        ],
    },
    {
        "id": 12,
        "dim": "evidence",
        "q": "إذا كان سبب ما شائعًا في HPLC لكنه لا يملك دليلًا خاصًا بالحالة، كيف تصفه؟",
        "options": [
            ("High likelihood لأنه شائع.", 1),
            ("فرضية ممكنة فقط حتى يظهر دليل خاص بالحالة.", 4),
            ("Root Cause probable.", 1),
            ("أبدأ بعلاجه لأنه الأسرع.", 1),
        ],
    },
    {
        "id": 13,
        "dim": "evidence",
        "q": "نتيجة اختبار واحد دعمت فرضيتك. ماذا تفعل؟",
        "options": [
            ("أغلق التحقيق فورًا.", 1),
            ("أقيّم هل الاختبار فعلاً يستبعد البدائل أم يحتاج Confirmatory evidence إضافي.", 4),
            ("أكرر نفس الاختبار حتى أحصل على نفس النتيجة.", 2),
            ("أكتب أن السبب Confirmed طالما النتيجة منطقية.", 1),
        ],
    },
    {
        "id": 14,
        "dim": "evidence",
        "q": "كيف تتعامل مع معلومة لم يذكرها المستخدم أو السجل لكنها تبدو منطقية؟",
        "options": [
            ("أستخدمها كحقيقة لأنها منطقية.", 1),
            ("أصنفها كاستنتاج أو Unknown ولا أضعها داخل الحقائق المثبتة.", 4),
            ("أتجاهلها دائمًا.", 2),
            ("أبني عليها القرار لو كانت شائعة.", 1),
        ],
    },
    {
        "id": 15,
        "dim": "evidence",
        "q": "ما أفضل استخدام للكروماتوجرام القديم المقبول؟",
        "options": [
            ("مرجع للمقارنة المنضبطة: RT، Peak Shape، areas، pressure وسياق التشغيل.", 4),
            ("إثبات أن العمود الحالي هو السبب.", 1),
            ("مجرد صورة شكلية لا تضيف كثيرًا.", 1),
            ("يستخدم فقط لو فشل SST.", 2),
        ],
    },

    # 4 — GMP
    {
        "id": 16,
        "dim": "gmp",
        "q": "نتيجة OOS ظهرت ويُعتقد أن هناك خطأ تحليلي. أول مبدأ يجب الحفاظ عليه هو:",
        "options": [
            ("إعادة التحليل فورًا للحصول على نتيجة أوضح.", 1),
            ("حفظ البيانات الأصلية واتباع SOP/QA في التحقيق قبل أي إعادة اختبار.", 4),
            ("حذف الحقن المشكوك فيها.", 1),
            ("تعديل Integration إذا كان Peak Shape غير جيد.", 1),
        ],
    },
    {
        "id": 17,
        "dim": "gmp",
        "q": "أي سلوك أقرب إلى Testing into compliance؟",
        "options": [
            ("اختبار فرضية محددة وفق SOP.", 1),
            ("تكرار الحقن حتى تظهر نتيجة مقبولة ثم اعتمادها.", 4),
            ("مقارنة النظام بجهاز آخر كاختبار عزل.", 1),
            ("مراجعة Audit Trail.", 1),
        ],
        "reverse": True,
    },
    {
        "id": 18,
        "dim": "gmp",
        "q": "أثناء التحقيق جربت اختبارًا تشخيصيًا غير جزء من التحليل الروتيني. كيف تتعامل معه؟",
        "options": [
            ("أخفيه لأنه ليس جزءًا من النتيجة النهائية.", 1),
            ("أوثقه حسب الإجراء المعتمد وأوضح غرضه التشخيصي وعدم استخدامه لاستبدال النتيجة الأصلية.", 4),
            ("أستخدمه بدل النتيجة الأصلية لو نجح.", 1),
            ("لا مشكلة طالما لم يره QA.", 1),
        ],
    },
    {
        "id": 19,
        "dim": "gmp",
        "q": "متى يكون تغيير Integration مقبولًا؟",
        "options": [
            ("عندما يحسن النتيجة.", 1),
            ("وفق طريقة/إجراء معتمد ومبرر علميًا وقابل للتتبع، وليس للحصول على Passing result.", 4),
            ("عندما تكون النتيجة قريبة من المواصفة.", 1),
            ("عندما يطلب المحلل الأقدم ذلك.", 1),
        ],
    },
    {
        "id": 20,
        "dim": "gmp",
        "q": "ما القيمة الأساسية لـAudit Trail أثناء التحقيق؟",
        "options": [
            ("معرفة من فتح البرنامج فقط.", 1),
            ("تتبع التغييرات والإجراءات والوقت والمستخدم بما يساعد في إعادة بناء ما حدث فعليًا.", 4),
            ("استخدامه فقط وقت التفتيش.", 1),
            ("لا يفيد في مشاكل chromatography.", 1),
        ],
    },

    # 5 — INSTRUMENT
    {
        "id": 21,
        "dim": "instrument",
        "q": "عند High Pressure، أفضل طريقة لتحديد مكان المقاومة هي:",
        "options": [
            ("تغيير العمود أولًا.", 1),
            ("عزل أجزاء مسار السريان تدريجيًا وفق SOP ومقارنة الضغط بعد كل نقطة عزل.", 4),
            ("خفض التدفق فقط.", 2),
            ("زيادة حرارة العمود.", 1),
        ],
    },
    {
        "id": 22,
        "dim": "instrument",
        "q": "لو نفس الطريقة تفشل على جهاز وتنجح على جهاز آخر بنفس المواد والعمود، ماذا يعني ذلك؟",
        "options": [
            ("الجهاز الأول تالف بالكامل.", 1),
            ("هذا دليل قوي يوجه التحقيق نحو اختلاف في النظام/المسار، لكنه لا يحدد الجزء المسؤول بعد.", 4),
            ("الطريقة غير Robust.", 1),
            ("يجب استخدام الجهاز الذي ينجح فقط.", 1),
        ],
    },
    {
        "id": 23,
        "dim": "instrument",
        "q": "الـSet Flow = 1.0 mL/min. ما الذي يثبت أن التدفق الفعلي مطابق؟",
        "options": [
            ("ظهور 1.0 على الشاشة.", 1),
            ("قياس/تحقق مناسب لمعدل التدفق وفق الإجراء المعتمد ومقارنته بالقيمة المطلوبة.", 4),
            ("ضغط النظام طبيعي.", 2),
            ("RT قريب من المتوقع فقط.", 2),
        ],
    },
    {
        "id": 24,
        "dim": "instrument",
        "q": "Carryover ظهر بعد حقنة عالية التركيز. أول تمييز مفيد هو:",
        "options": [
            ("أغير العمود.", 1),
            ("أحدد هل الإشارة تقل في blanks المتتالية وأربطها بمسار الحقن/الغسل قبل اتهام العمود.", 4),
            ("أزيد زمن التشغيل.", 2),
            ("أقلل تركيز العينة.", 1),
        ],
    },
    {
        "id": 25,
        "dim": "instrument",
        "q": "Peak Area أصبحت غير دقيقة مع RT ثابت وPressure ثابت. أي منطقة تستحق فحصًا مبكرًا؟",
        "options": [
            ("حقن العينة/Autosampler ومسار القياس والاستجابة، مع الحفاظ على فرضيات أخرى مفتوحة.", 4),
            ("العمود فقط.", 1),
            ("تركيب الطور المتحرك فقط.", 1),
            ("لا يوجد عطل لأن RT ثابت.", 1),
        ],
    },

    # 6 — DECISION
    {
        "id": 26,
        "dim": "decision",
        "q": "أفضل Investigation note هي التي تفصل بوضوح بين:",
        "options": [
            ("الرأي والقرار فقط.", 1),
            ("Observation → Hypothesis → Test → Evidence → Conclusion.", 4),
            ("المشكلة والحل النهائي فقط.", 2),
            ("كل الاحتمالات الممكنة بدون ترتيب.", 1),
        ],
    },
    {
        "id": 27,
        "dim": "decision",
        "q": "إذا لم تصل للسبب الجذري بعد، أفضل صياغة هي:",
        "options": [
            ("Root Cause غير معروف حتى الآن، والدليل التالي المطلوب هو…", 4),
            ("السبب غالبًا العمود لأن ده الأكثر شيوعًا.", 1),
            ("لا توجد مشكلة واضحة.", 1),
            ("نجرب حلولًا إضافية.", 2),
        ],
    },
    {
        "id": 28,
        "dim": "decision",
        "q": "مديرك يسألك: ما الخطوة التالية؟ أفضل إجابة هي:",
        "options": [
            ("قائمة من 8 احتمالات.", 1),
            ("اختبار واحد محدد، لماذا اخترناه، وماذا ستعني كل نتيجة.", 4),
            ("نغير العمود ونشوف.", 1),
            ("نكرر التحليل.", 1),
        ],
    },
    {
        "id": 29,
        "dim": "decision",
        "q": "متى يكون القرار المهني قويًا؟",
        "options": [
            ("عندما يكون سريعًا.", 2),
            ("عندما يكون قابلًا للدفاع عنه بالأدلة ويمكن لشخص آخر تتبع منطقه.", 4),
            ("عندما يصدر من أكثر شخص خبرة.", 2),
            ("عندما يوفر تكلفة فورية.", 1),
        ],
    },
    {
        "id": 30,
        "dim": "decision",
        "q": "ما الهدف الحقيقي من Troubleshooting احترافي؟",
        "options": [
            ("إرجاع الجهاز للعمل بأسرع وقت بأي طريقة.", 1),
            ("الوصول لقرار صحيح قابل للتفسير والتكرار، مع حماية البيانات والتحقيق.", 4),
            ("الوصول إلى Passing chromatogram.", 1),
            ("إثبات خبرة المحلل.", 1),
        ],
    },
]

# -----------------------------
# STYLES
# -----------------------------
st.markdown(
    """
    <style>
      .block-container {max-width: 860px; padding-top: 3.3rem; padding-bottom: 5rem;}
      html, body, [class*="css"] {font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}
      .gap-hero {
        direction: rtl; text-align: right; position: relative; overflow: hidden;
        border-radius: 28px; padding: 2rem 1.6rem; margin-bottom: 1.2rem;
        background: linear-gradient(145deg,#07101f 0%,#101b2d 58%,#151922 100%);
        border: 1px solid rgba(202,167,80,.48); color:#fff;
        box-shadow: 0 18px 42px rgba(2,6,23,.16);
      }
      .gap-hero:before {content:""; position:absolute; width:220px; height:220px; border-radius:50%; top:-120px; left:-80px; background:radial-gradient(circle,rgba(202,167,80,.25),rgba(202,167,80,0) 72%);}
      .gap-kicker {font-size:.76rem; color:#d6bd78; font-weight:850; letter-spacing:.12em; direction:ltr; text-align:left; margin-bottom:.6rem;}
      .gap-title {font-size:2.2rem; line-height:1.1; font-weight:900; margin:.25rem 0 .7rem; direction:ltr; text-align:left;}
      .gap-ar {font-size:1.35rem; line-height:1.65; font-weight:800; margin:.2rem 0 .5rem;}
      .gap-copy {font-size:1rem; line-height:1.9; color:#d8e0ea; margin-top:.55rem;}
      .gap-tag {display:inline-block; margin-top:.75rem; padding:.35rem .65rem; border-radius:999px; background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.10); color:#d6bd78; font-weight:800; font-size:.75rem;}
      .section-card {direction:rtl;text-align:right;padding:1.2rem 1.25rem;border-radius:20px;background:#fff;border:1px solid #e7ebf0;margin:.65rem 0;box-shadow:0 8px 24px rgba(15,23,42,.05);}
      .result-card {direction:rtl;text-align:right;padding:1.2rem 1.25rem;border-radius:20px;background:linear-gradient(145deg,#fbfcfe,#f4f7fb);border:1px solid #dfe6ef;margin:.65rem 0;}
      .result-label {font-size:.78rem;font-weight:850;color:#8a6d22;margin-bottom:.25rem;}
      .result-value {font-size:1.35rem;font-weight:900;color:#111827;line-height:1.5;}
      .result-sub {font-size:.92rem;color:#657284;line-height:1.7;margin-top:.25rem;}
      .mini {font-size:.83rem;color:#7b8795;direction:rtl;text-align:right;}
      .rtl {direction:rtl;text-align:right;unicode-bidi:plaintext;}
      [data-testid="stRadio"] {direction:rtl;text-align:right;}
      [data-testid="stRadio"] label {direction:rtl;text-align:right;}
      [data-testid="stProgress"] {direction:ltr;}
      div.stButton > button {border-radius:14px;font-weight:850;min-height:3.2rem;}
      @media(max-width:640px){
        .block-container{padding-left:1rem;padding-right:1rem;padding-top:4.8rem;}
        .gap-hero{padding:1.4rem 1.1rem;border-radius:22px;}
        .gap-title{font-size:1.65rem;}
        .gap-ar{font-size:1.15rem;}
        .gap-copy{font-size:.94rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# STATE
# -----------------------------
if "gap_started" not in st.session_state:
    st.session_state.gap_started = False
if "gap_step" not in st.session_state:
    st.session_state.gap_step = 0
if "gap_answers" not in st.session_state:
    st.session_state.gap_answers = {}
if "gap_done" not in st.session_state:
    st.session_state.gap_done = False


def reset_test():
    for k in list(st.session_state.keys()):
        if str(k).startswith("q_"):
            del st.session_state[k]
    st.session_state.gap_started = False
    st.session_state.gap_step = 0
    st.session_state.gap_answers = {}
    st.session_state.gap_done = False


def get_dimension_questions(dim_key):
    return [q for q in QUESTIONS if q["dim"] == dim_key]


def option_score(question, selected_label):
    for label, score in question["options"]:
        if label == selected_label:
            if question.get("reverse"):
                # For this one question the statement asks which behavior is problematic.
                # The intentionally correct recognition is still encoded with score=4,
                # so no numerical inversion is required.
                return score
            return score
    return 0


def calculate_results():
    raw = {k: 0 for k in DIMENSIONS}
    counts = {k: 0 for k in DIMENSIONS}
    for q in QUESTIONS:
        selected = st.session_state.gap_answers.get(q["id"])
        if selected is not None:
            raw[q["dim"]] += option_score(q, selected)
            counts[q["dim"]] += 1

    pct = {}
    for key in DIMENSIONS:
        # 5 questions per dimension, min=5, max=20.
        score = raw[key]
        pct[key] = round(((score - 5) / 15) * 100) if counts[key] == 5 else 0
        pct[key] = max(0, min(100, pct[key]))

    overall = round(sum(pct.values()) / len(pct))
    ordered = sorted(pct.items(), key=lambda x: x[1])
    primary = ordered[0][0]
    secondary = ordered[1][0]
    strongest = max(pct.items(), key=lambda x: x[1])[0]
    return raw, pct, overall, strongest, primary, secondary


def level_from_score(score):
    if score >= 85:
        return "Evidence-Led QC Decision Maker", "تفكيرك التحليلي متماسك جدًا؛ الأولوية الآن هي تحويله إلى نظام ثابت يمكن تكراره وتعليمه للآخرين."
    if score >= 70:
        return "Strong QC Investigator", "عندك قاعدة قوية، لكن فجوة أو اثنتان قد تبطئان الوصول للسبب الجذري أو تقللان قوة القرار."
    if score >= 55:
        return "Developing QC Investigator", "عندك خبرة تشغيلية جيدة، لكن تحتاج نقل التفكير من حل المشكلة إلى بناء دليل يثبت السبب."
    return "Execution-First Analyst", "أكبر فرصة أمامك هي الانتقال من تنفيذ الخطوات إلى فهم لماذا تختار الخطوة التالية وما الدليل الذي ستنتجه."


def priority_for(dim):
    mapping = {
        "science": "ارجع للأساس العلمي للكروماتوجرافي: الاحتجاز، الانتقائية، الكفاءة، Peak Shape، وتأثير flow / pH / organic strength قبل حفظ حلول جاهزة.",
        "investigation": "درّب نفسك على سؤال واحد: ما الاختبار الذي يفرق بين الفرضيات؟ استخدم Investigation Assistant على حالات حقيقية بدل القفز للحلول.",
        "evidence": "افصل دائمًا بين ما تم رصده، وما استنتجته، وما لا يزال مجهولًا. لا ترفع احتمال فرضية لأنها شائعة فقط.",
        "gmp": "اربط troubleshooting دائمًا بحماية Raw Data، Audit Trail، SOP، QA، وعدم استخدام retesting للحصول على Passing result.",
        "instrument": "ابنِ خريطة ذهنية لمسار HPLC كاملًا: solvent → pump → injector → column → detector، وتعلم اختبارات العزل لكل جزء.",
        "decision": "حوّل كل تحقيق إلى قصة قابلة للمراجعة: Observation → Hypothesis → Test → Evidence → Conclusion → Documentation.",
    }
    return mapping[dim]


# -----------------------------
# HERO
# -----------------------------
st.markdown(
    f"""
    <div class="gap-hero">
      <div class="gap-kicker">PHARMACEUTICAL QC · ANALYTICAL DECISION MAKING</div>
      <div class="gap-title">{TITLE}</div>
      <div class="gap-ar">خبرتك ممكن تكون قوية… لكن هل طريقة اتخاذك للقرار بنفس القوة؟</div>
      <div class="gap-copy">اختبار عملي قصير يكشف أين تقف بين <b>تشغيل الـHPLC</b> و<b>التفكير كمحقق QC محترف</b>. النتيجة لا تقيس الحفظ؛ تقيس طريقة تفكيرك عندما تكون الأدلة ناقصة والمشكلة غير واضحة.</div>
      <span class="gap-tag">{TAGLINE}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# LANDING
# -----------------------------
if not st.session_state.gap_started:
    st.markdown(
        """
        <div class="section-card">
          <h2>المشكلة مش دايمًا إنك محتاج معلومات أكتر.</h2>
          <p>ممكن تعرف HPLC كويس، ومع ذلك أول ما تظهر مشكلة تبدأ تغيّر أجزاء أو تعيد الحقن قبل ما تحدد: <b>إيه الدليل الناقص؟ وإيه الاختبار اللي يفرق بين الاحتمالات؟</b></p>
          <p>الاختبار ده يقيس 6 أبعاد في طريقة اتخاذ القرار داخل معمل QC.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    cards = [
        ("الفهم الكروماتوجرافي", "هل بتفهم معنى التغير في RT وPeak Shape والضغط؟"),
        ("منطق التحقيق", "هل تبدأ من الفرضيات أم من الاختبار الذي يميز بينها؟"),
        ("الانضباط مع الأدلة", "هل تفرق بين Fact وInference وUnknown؟"),
        ("GMP وسلامة البيانات", "هل تحمي التحقيق من retesting وdata-integrity traps؟"),
        ("فهم الجهاز والنظام", "هل تعرف تعزل Pump / Injector / Column / Detector؟"),
        ("القرار والتوثيق", "هل قرارك قابل للدفاع عنه وإعادة تتبع منطقه؟"),
    ]
    for i, (h, p) in enumerate(cards):
        with cols[i % 2]:
            st.markdown(f'<div class="section-card"><h3>{h}</h3><p>{p}</p></div>', unsafe_allow_html=True)

    st.markdown('<p class="mini">30 سؤال · 6 أبعاد · حوالي 4–6 دقائق · بدون استخدام API أو تكلفة إضافية</p>', unsafe_allow_html=True)
    if st.button("ابدأ الاختبار ←", type="primary", use_container_width=True):
        st.session_state.gap_started = True
        st.session_state.gap_step = 0
        st.rerun()

    st.page_link("app.py", label="🧪 عندك مشكلة HPLC الآن؟ افتح مساعد يحيى للتحقيق", use_container_width=True)
    st.stop()

# -----------------------------
# RESULTS
# -----------------------------
if st.session_state.gap_done:
    raw, pct, overall, strongest, primary, secondary = calculate_results()
    level, level_desc = level_from_score(overall)

    st.markdown(f'<div class="section-card"><h2>نتيجتك: {overall}/100</h2><h3>{level}</h3><p>{level_desc}</p></div>', unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a:
        st.markdown(f'<div class="result-card"><div class="result-label">أقوى نقطة</div><div class="result-value">{DIMENSIONS[strongest]["name"]}</div><div class="result-sub">{pct[strongest]}%</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="result-card"><div class="result-label">Primary Gap</div><div class="result-value">{DIMENSIONS[primary]["name"]}</div><div class="result-sub">{pct[primary]}%</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="result-card"><div class="result-label">Secondary Gap</div><div class="result-value">{DIMENSIONS[secondary]["name"]}</div><div class="result-sub">{pct[secondary]}%</div></div>', unsafe_allow_html=True)

    st.markdown("### خريطة قرارك")
    for key, meta in DIMENSIONS.items():
        st.markdown(f'**{meta["name"]} — {pct[key]}%**')
        st.progress(pct[key] / 100)

    st.markdown(
        f"""
        <div class="section-card">
          <h2>الأولوية الاستراتيجية الجاية</h2>
          <p><b>{DIMENSIONS[primary]['name']}</b></p>
          <p>{priority_for(primary)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    share_text = (
        f"نتيجتي في The QC Analyst Decision Gap™: {overall}/100\n"
        f"المستوى: {level}\n"
        f"أقوى نقطة: {DIMENSIONS[strongest]['name']} ({pct[strongest]}%)\n"
        f"Primary Gap: {DIMENSIONS[primary]['name']} ({pct[primary]}%)\n"
        f"Secondary Gap: {DIMENSIONS[secondary]['name']} ({pct[secondary]}%)\n"
        "DON'T GUESS. FOLLOW THE EVIDENCE."
    )
    with st.expander("نص جاهز لمشاركة النتيجة"):
        st.code(share_text, language=None)

    st.markdown("### اختبر طريقة تفكيرك على Case حقيقية")
    st.write("الاختبار قال لك أين الفجوة. الآن خلّي المساعد يختبر معك قرارًا حقيقيًا خطوة بخطوة بدون قفز للسبب الجذري.")
    st.page_link("app.py", label="🧪 افتح Yahia HPLC Investigation Assistant", use_container_width=True)

    if st.button("إعادة الاختبار", use_container_width=True):
        reset_test()
        st.rerun()
    st.stop()

# -----------------------------
# QUIZ FLOW — 6 steps × 5 questions
# -----------------------------
dim_keys = list(DIMENSIONS.keys())
step = st.session_state.gap_step
current_dim = dim_keys[step]
questions = get_dimension_questions(current_dim)

st.progress(step / len(dim_keys))
st.markdown(
    f"""
    <div class="section-card">
      <div class="result-label">المرحلة {step + 1} من 6</div>
      <div class="result-value">{DIMENSIONS[current_dim]['name']}</div>
      <div class="result-sub">{DIMENSIONS[current_dim]['en']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

for q in questions:
    labels = [x[0] for x in q["options"]]
    existing = st.session_state.gap_answers.get(q["id"])
    idx = labels.index(existing) if existing in labels else None
    answer = st.radio(
        f"{q['id']}. {q['q']}",
        labels,
        index=idx,
        key=f"q_{q['id']}",
    )
    if answer is not None:
        st.session_state.gap_answers[q["id"]] = answer
    st.markdown("---")

answered_current = all(q["id"] in st.session_state.gap_answers for q in questions)

left, right = st.columns(2)
with left:
    if step > 0 and st.button("→ السابق", use_container_width=True):
        st.session_state.gap_step -= 1
        st.rerun()
with right:
    label = "اعرض النتيجة" if step == len(dim_keys) - 1 else "التالي ←"
    if st.button(label, type="primary", use_container_width=True, disabled=not answered_current):
        if step == len(dim_keys) - 1:
            st.session_state.gap_done = True
        else:
            st.session_state.gap_step += 1
        st.rerun()

if not answered_current:
    st.caption("أجب عن الأسئلة الخمسة للانتقال للمرحلة التالية.")
