import streamlit as st

st.set_page_config(
    page_title="The QC Analyst Decision Gap™",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TITLE = "THE QC ANALYST DECISION GAP™"
VERSION = "v0.2 · Expert Calibration"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."

DIMENSIONS = {
    "science": {"name": "الفهم الكروماتوجرافي", "en": "Chromatography Understanding", "short": "الفهم العلمي"},
    "investigation": {"name": "منطق التحقيق", "en": "Investigation Logic", "short": "التحقيق"},
    "evidence": {"name": "الانضباط مع الأدلة", "en": "Evidence Discipline", "short": "الأدلة"},
    "gmp": {"name": "GMP وسلامة البيانات", "en": "GMP & Data Integrity", "short": "GMP"},
    "instrument": {"name": "فهم الجهاز والنظام", "en": "Instrument & System Thinking", "short": "الجهاز"},
    "decision": {"name": "القرار والتوثيق", "en": "Decision & Documentation", "short": "القرار"},
}


def opt(label, score, risk=0):
    return {"label": label, "score": score, "risk": risk}


QUESTIONS = [
    {"id": 1, "dim": "science", "weight": 1.3, "q": "على نفس الطريقة والعمود، أصبحت كل القمم تقريبًا عند نصف زمن الاحتجاز السابق، والضغط أعلى بكثير من المعتاد. ما القراءة العلمية الأقوى كبداية؟", "options": [
        opt("قد يكون هناك اختلاف في معدل التدفق الفعلي أو مسار السريان؛ أتحقق من التدفق والضغط الفعليين قبل تعديل الطريقة.", 4),
        opt("الـRT وحده يكفي لإثبات أن نسبة الـorganic أعلى من المطلوب.", 2),
        opt("أعوض الانخفاض بتقليل معدل التدفق حتى ترجع القمم لمكانها.", 0, 1),
        opt("أفترض أن العمود فقد كفاءته لأن الضغط ارتفع.", 1),
    ]},
    {"id": 2, "dim": "science", "weight": 1.1, "q": "مادة منخفضة التركيز أصبحت قمتها عريضة في الـStandard والـSample معًا، بينما المادة الثانية طبيعية وRT للمادة المتأثرة لم يتغير. أي استنتاج أولي أدق؟", "options": [
        opt("ثبات RT يجعل أي سبب كروماتوجرافي مستبعدًا.", 1),
        opt("المشكلة انتقائية لمادة واحدة؛ أفرّق بين تفاعلها مع المسار/العمود وبين الاستجابة والتركيز بدل اعتبار النظام كله تالفًا.", 4),
        opt("التركيز المنخفض هو السبب الجذري لأن القمة الأخرى طبيعية.", 1),
        opt("أغيّر الـintegration أولًا لأن RT ثابت.", 0, 1),
    ]},
    {"id": 3, "dim": "science", "weight": 1.2, "q": "انخفضت الـResolution بوضوح، بينما المسافة الزمنية بين مركزي القمتين لم تتغير كثيرًا لكن القمتين أصبحتا أعرض. أين يتركز تفكيرك أولًا؟", "options": [
        opt("في فقد الكفاءة/زيادة Peak Width أكثر من تغير الانتقائية وحدها.", 4),
        opt("في تغير الـselectivity فقط لأن الـResolution انخفضت.", 2),
        opt("في خطأ detector لأن زمن الاحتجاز ثابت.", 1),
        opt("أزيد زمن التشغيل لتعويض الـResolution.", 0, 1),
    ]},
    {"id": 4, "dim": "science", "weight": 1.0, "q": "ارتفع الضغط عن التاريخ المعتاد، لكن RT وشكل القمم ما زالا قريبين من الطبيعي. أي عبارة أكثر دقة؟", "options": [
        opt("وجود RT طبيعي يثبت أن مسار السريان سليم بالكامل.", 1),
        opt("قد توجد مقاومة إضافية لا تزال لا تؤثر بوضوح على الفصل؛ أحتاج تحديد مكانها قبل الحكم.", 4),
        opt("العمود هو السبب الأكثر احتمالًا لأنه المصدر الأكبر للمقاومة.", 2),
        opt("أخفض التدفق كحل تشغيلي وأكمل السلسلة.", 0, 1),
    ]},
    {"id": 5, "dim": "science", "weight": 1.2, "q": "بعد حقنة عالية التركيز ظهر Peak في الـblank التالي ثم انخفض تدريجيًا في blanks المتتالية. ما الذي يدعمه هذا النمط أكثر؟", "options": [
        opt("وجود carryover مرتبط بمسار الحقن/الغسل أكثر من Ghost Peak ثابت المصدر، مع بقاء الحاجة للعزل.", 4),
        opt("تلوث ثابت في الطور المتحرك لأن الـblank به Peak.", 2),
        opt("تدهور العمود لأن القمة ظهرت بعد العينة.", 1),
        opt("أحذف أول blank وأعتمد التالي إذا أصبح نظيفًا.", 0, 2),
    ]},

    {"id": 6, "dim": "investigation", "weight": 1.0, "q": "أمامك مشكلة جديدة وبها 4 أسباب تبدو معقولة. ما أفضل أول حركة؟", "options": [
        opt("أرتب الأسباب من الأكثر شيوعًا وأبدأ العلاج مباشرة.", 2),
        opt("أحدد المعلومة التي لو عرفتها ستقسم الاحتمالات، ثم أطلبها أو أصمم اختبارًا واحدًا ينتجها.", 4),
        opt("أجرب أسرع تغيير يمكن الرجوع عنه ثم أرى.", 1),
        opt("أكرر الحقن أولًا لأن أي مشكلة قد تكون عابرة.", 0, 1),
    ]},
    {"id": 7, "dim": "investigation", "weight": 1.5, "q": "الطريقة كانت ناجحة تاريخيًا، واليوم أعطت فشلًا جديدًا. لديك وقت لسؤال واحد قبل بدء الاختبارات. أي سؤال يعطي أعلى قيمة تشخيصية؟", "options": [
        opt("هل يوجد عمود احتياطي؟", 1),
        opt("ما الذي اختلف بين آخر تشغيل مقبول والتشغيل الحالي: شخص، تحضير، مواد، consumables، جهاز أو إعدادات؟", 4),
        opt("هل حدثت المشكلة سابقًا في شركة أخرى؟", 2),
        opt("هل يمكن تكرار الـStandard للتأكد؟", 1),
    ]},
    {"id": 8, "dim": "investigation", "weight": 1.5, "q": "غسل الـGuard Column أعاد Peak Shape الطبيعي واستمر التحسن خلال الـSequence. ما الاستنتاج الأكثر انضباطًا؟", "options": [
        opt("ثبت أن التلوث الكيميائي داخل الـGuard Column هو السبب الجذري.", 2),
        opt("أصبح الـGuard Column/حالته متورطًا بقوة، لكن نوع الآلية الدقيقة ما زال يحتاج دليلًا إذا كان مهمًا للتحقيق.", 4),
        opt("نجاح الغسل يثبت أن الـanalytical column سليم 100%.", 1),
        opt("بما أن النتيجة تحسنت، لا حاجة لتوثيق ما قبل/بعد الغسل.", 0, 2),
    ]},
    {"id": 9, "dim": "investigation", "weight": 1.3, "q": "نفس الـStandard والعمود والطريقة يفشلون على جهاز A وينجحون على جهاز B. أي خطوة تالية أكثر تمييزًا؟", "options": [
        opt("أستمر على جهاز B فقط لأن الطريقة نجحت عليه.", 0, 1),
        opt("أعتبر جهاز A هو Root Cause وأطلب صيانة عامة.", 2),
        opt("أقارن متغيرًا فعليًا عالي القيمة بين الجهازين مثل measured flow/pressure أو مسار الحقن، مع تثبيت باقي الظروف.", 4),
        opt("أعيد تحضير الـStandard مرة ثالثة على الجهاز A.", 1),
    ]},
    {"id": 10, "dim": "investigation", "weight": 1.5, "q": "ثلاث مواد حافظة في نفس الـStandard أعطت نتائج أقل من التاريخ، لكن الانخفاض ليس بنفس النسبة لكل مادة. قبل اتهام الـinjector أو detector، ما الخطوة الأعلى قيمة؟", "options": [
        opt("أعرف أولًا هل التغير في Peak Areas الخام أم في الحساب النهائي، وأراجع ما تغير في التحضير مقارنة بآخر Standard مقبول.", 4),
        opt("أعيد الحقن عدة مرات لأعرف المتوسط الجديد.", 0, 1),
        opt("أغير Response Factors لأن الثلاث مواد متأثرة.", 0, 1),
        opt("أفترض عدم تجانس الحقن لأن كل المواد انخفضت.", 2),
    ]},

    {"id": 11, "dim": "evidence", "weight": 1.2, "q": "ورد في السجل: الضغط المعتاد 180 bar، وبعد 25 حقنة كانت القراءة 310 bar. أي عبارة يمكن وضعها داخل «ما نعرفه»؟", "options": [
        opt("الضغط ارتفع تدريجيًا بسبب تراكم العينات.", 0),
        opt("بعد 25 حقنة سُجل ضغط 310 bar مقارنة بتاريخ معتاد 180 bar؛ شكل الاتجاه خلال الحقن غير معروف.", 4),
        opt("حدث انسداد بعد الحقنة رقم 24.", 0),
        opt("العمود بدأ يتدهور أثناء الـSequence.", 0),
    ]},
    {"id": 12, "dim": "evidence", "weight": 1.0, "q": "سبب ما شائع جدًا في خبرتك، لكن لا يوجد في الحالة الحالية دليل يميزه عن سببين آخرين. كيف تصفه؟", "options": [
        opt("High likelihood لأن الخبرة السابقة تعتبر Evidence.", 2),
        opt("فرضية ممكنة؛ شيوعها قد يوجّه الانتباه لكنه لا يرفعها وحده إلى استنتاج خاص بالحالة.", 4),
        opt("Probable Root Cause إذا لم توجد علامة تناقضها.", 1),
        opt("السبب العملي الأفضل لأن اختباره أسرع.", 1),
    ]},
    {"id": 13, "dim": "evidence", "weight": 1.4, "q": "اختبار مستهدف أعطى النتيجة التي توقعتها لفرضيتك. ما الذي يحدد إن كان هذا Confirmatory evidence كافيًا؟", "options": [
        opt("مجرد توافق النتيجة مع التوقع.", 2),
        opt("أن يكون الاختبار قادرًا على التمييز وأن تصبح البدائل المعقولة أقل احتمالًا، لا مجرد تحسن عرض واحد.", 4),
        opt("أن تتكرر النتيجة مرتين على الأقل مهما كان تصميم الاختبار.", 1),
        opt("أن يعود SST للنجاح مرة واحدة.", 2),
    ]},
    {"id": 14, "dim": "evidence", "weight": 1.3, "q": "قال المحلل: «ما اتغيرش أي حاجة». ما التصرف الأكثر انضباطًا؟", "options": [
        opt("أعتبر كل الظروف متطابقة وأنتقل مباشرة إلى عطل الجهاز.", 1),
        opt("أتعامل معها كتقرير أولي، ثم أتحقق من أعلى comparator قيمة مثل التحضير/الـlot/consumable/الجهاز حسب الحالة.", 4),
        opt("أعتبرها معلومة غير مفيدة تمامًا.", 2),
        opt("أعيد التحليل للتأكد من أن المشكلة ما زالت موجودة.", 1),
    ]},
    {"id": 15, "dim": "evidence", "weight": 1.2, "q": "تحضيران مستقلان للطور المتحرك أعطيا نفس الفشل. ما الذي يدعمه هذا تحديدًا؟", "options": [
        opt("يستبعد الطور المتحرك بالكامل من التحقيق.", 1),
        opt("يضعف فرضية خطأ تحضير عارض في زجاجة واحدة، لكنه لا يستبعد خطأ مشتركًا في الوصفة/المواد/القياس.", 4),
        opt("يثبت أن العمود هو السبب.", 0),
        opt("يثبت أن الطريقة نفسها غير Robust.", 1),
    ]},

    {"id": 16, "dim": "gmp", "weight": 1.5, "q": "ظهرت نتيجة OOS ويُشتبه في خطأ تحليلي. أي تصرف يحافظ على قوة التحقيق من البداية؟", "options": [
        opt("إعادة التحليل فورًا مع Analyst آخر لمعرفة النتيجة الصحيحة.", 0, 2),
        opt("حفظ الـRaw Data والكروماتوجرامات والسجل، وبدء التحقيق وفق SOP/QA قبل أي إعادة اختبار مبررة.", 4),
        opt("استبعاد الحقن غير الطبيعية ثم حساب الباقي.", 0, 2),
        opt("إعادة Integration بطريقة تعكس شكل القمة بشكل أفضل ثم تقييم النتيجة.", 1, 1),
    ]},
    {"id": 17, "dim": "gmp", "weight": 1.5, "q": "أي سيناريو يمثل Testing into compliance بصورة أوضح؟", "options": [
        opt("اختبار فرضية محددة ومسبقة التوثيق لمعرفة هل الـfilter يؤثر على recovery.", 1),
        opt("إجراء حقن إضافية متكررة، ثم اختيار المجموعة التي تقع داخل المواصفة واعتبارها النتيجة.", 4),
        opt("مقارنة actual flow بين جهازين كجزء من investigation.", 1),
        opt("إعادة تحضير مستقلة إذا كان الـSOP يسمح بها ولها rationale موثق.", 1),
    ]},
    {"id": 18, "dim": "gmp", "weight": 1.2, "q": "أثناء التحقيق احتجت Diagnostic Injection ليست جزءًا من الروتين. ما أفضل تعامل؟", "options": [
        opt("تُنفذ تحت الإجراء المناسب وتُوثق كاختبار تشخيصي مع غرض واضح، ولا تُستخدم لاستبدال النتيجة الأصلية.", 4),
        opt("تُنفذ خارج الـsequence حتى لا تؤثر على السجل الرسمي.", 0, 2),
        opt("تُستخدم كبديل للنتيجة الأصلية إذا نجحت.", 0, 2),
        opt("لا تحتاج توثيقًا لأنها ليست Reportable result.", 0, 2),
    ]},
    {"id": 19, "dim": "gmp", "weight": 1.5, "q": "استخدام Filter غير مذكور في الطريقة أعطى نتائج Passing، بينما التحضير بدون هذا الـFilter يعطي النتيجة التاريخية المقبولة. ما القرار الأكثر دفاعًا؟", "options": [
        opt("اعتماد الـFilter الجديد لأنه حسّن النتيجة.", 0, 2),
        opt("عدم تحويله إلى خطوة روتينية؛ أوثق الفرق وأحقق في recovery/compatibility وألتزم بالطريقة والإجراء المعتمدين.", 4),
        opt("إضافة الـFilter مؤقتًا لهذه الدفعة فقط.", 0, 2),
        opt("متوسط النتائج المفلترة وغير المفلترة يعطي تقديرًا أكثر عدلًا.", 0, 2),
    ]},
    {"id": 20, "dim": "gmp", "weight": 1.3, "q": "فشل الاختبار على جهاز A ونجح فورًا على جهاز B. أي موقف أقوى من ناحية GMP؟", "options": [
        opt("نتيجة B تلغي نتيجة A لأن نفس العينة نجحت.", 0, 2),
        opt("نتيجة B دليل تشخيصي مهم، لكن فشل A وبياناته يظلان جزءًا من التحقيق ولا يُتجاهلان.", 4),
        opt("نعتمد B ونفتح الصيانة لاحقًا بدون ربط الحالتين.", 1, 1),
        opt("نختار الجهاز الذي يعطي SST أفضل دائمًا.", 0, 1),
    ]},

    {"id": 21, "dim": "instrument", "weight": 1.2, "q": "ظهر High Pressure جديد. أي استراتيجية عزل تعطي معلومات أفضل بأقل تغييرات؟", "options": [
        opt("استبدال العمود أولًا لأنه غالبًا أعلى مقاومة.", 2),
        opt("عزل مسار السريان تدريجيًا وفق SOP/تعليمات الشركة، ومقارنة الضغط بعد إزالة أجزاء downstream بطريقة آمنة.", 4),
        opt("فتح purge valve؛ إذا انخفض الضغط يكون العمود السبب مؤكدًا.", 2),
        opt("خفض flow للنصف ومتابعة الـSequence.", 0, 1),
    ]},
    {"id": 22, "dim": "instrument", "weight": 1.5, "q": "الجهاز يعرض Set Flow = 1.0 mL/min، لكن RT أصبح نصف التاريخ تقريبًا. ما أقوى تحقق؟", "options": [
        opt("الاعتماد على الشاشة لأن setpoint هو القيمة التي يستخدمها النظام.", 0),
        opt("قياس/التحقق من معدل التدفق الفعلي وفق الإجراء المعتمد ومقارنته بالتاريخ والضغط.", 4),
        opt("زيادة زمن التشغيل حتى تعود القمة إلى 6 دقائق.", 0, 1),
        opt("قياس pH مرة أخرى فقط لأن RT تغيّر.", 2),
    ]},
    {"id": 23, "dim": "instrument", "weight": 1.2, "q": "Peak Area RSD أصبح سيئًا، لكن RT والضغط ثابتان وشكل القمم مقبول. أين تبدأ العزل بصورة أكثر منطقية؟", "options": [
        opt("من عناصر تؤثر على كمية/استجابة الحقن مثل autosampler/injection precision ثم detector response، مع مقارنة controlled.", 4),
        opt("من تغيير العمود لأن Area issue قد يأتي من stationary phase.", 1),
        opt("من تعديل mobile phase strength.", 1),
        opt("لا يوجد System issue لأن RT ثابت.", 1),
    ]},
    {"id": 24, "dim": "instrument", "weight": 1.1, "q": "Baseline spike يظهر بشكل متكرر قريبًا من توقيت حركة الـinjector، بينما يختفي في تشغيل بدون injection event. ماذا تفعل؟", "options": [
        opt("أستخدم التزامن كدليل يوجّه العزل نحو injector/event-related disturbance، ثم أختبره بدل اتهام detector مباشرة.", 4),
        opt("أغير detector lamp لأن الـspike ظاهرة على الإشارة.", 1),
        opt("أزيد smoothing في processing لإخفاء الـspike.", 0, 1),
        opt("أغير العمود لأن كل signal تمر عبره.", 1),
    ]},
    {"id": 25, "dim": "instrument", "weight": 1.2, "q": "Peak يظهر بعد high-standard ثم يقل في كل blank لاحق. ما الاختبار العازل الأكثر فائدة قبل تغيير العمود؟", "options": [
        opt("مراجعة/اختبار wash path وneedle/seat carryover بطريقة controlled مع blanks متسلسلة.", 4),
        opt("حقن mobile phase عشر مرات حتى تختفي القمة.", 0, 1),
        opt("تغيير analytical column ثم المقارنة.", 2),
        opt("زيادة run time فقط.", 1),
    ]},

    {"id": 26, "dim": "decision", "weight": 1.5, "q": "بعد تدخل واحد تحسنت المشكلة كما توقعت، لكن يوجد سبب بديل كان يمكن أن يعطي نفس التحسن. ما التصنيف الأدق؟", "options": [
        opt("ROOT CAUSE CONFIRMED لأن التدخل نجح.", 2),
        opt("ROOT CAUSE PROBABLE — نحتاج اختبارًا يميز عن البديل قبل التأكيد.", 4),
        opt("ROOT CAUSE NOT IDENTIFIED لأن أي تحسن غير كافٍ.", 2),
        opt("أغلق التحقيق طالما SST عاد للنجاح.", 0, 1),
    ]},
    {"id": 27, "dim": "decision", "weight": 1.1, "q": "مديرك يريد «الخطوة التالية» في جملة واحدة. أي إجابة هي الأقوى؟", "options": [
        opt("لدينا خمس احتمالات وسنراجعها بالترتيب.", 2),
        opt("سنقيس actual flow لأن النتيجة ستفصل بين خطأ توصيل/ضبط التدفق وبين فرضيات العمود أو التحضير، وسنفسر كلا الاتجاهين.", 4),
        opt("سنغير العمود لأنه أسرع طريقة لاستبعاد السبب.", 1),
        opt("سنكرر التحليل على جهاز آخر وإذا نجح نغلق الحالة.", 1),
    ]},
    {"id": 28, "dim": "decision", "weight": 1.2, "q": "أي Investigation Record يسمح لمراجع مستقل بإعادة بناء منطقك؟", "options": [
        opt("المشكلة → الحل → النتيجة.", 2),
        opt("Observation → Hypothesis → Test → Evidence → Interpretation → Conclusion، مع حفظ البيانات الأصلية.", 4),
        opt("قائمة بالأجزاء التي تم تغييرها حتى نجاح الجهاز.", 1),
        opt("السبب الجذري والتوصية النهائية فقط.", 1),
    ]},
    {"id": 29, "dim": "decision", "weight": 1.4, "q": "ثبت أن المشكلة تختفي عند إزالة Filter وتعود عند استخدامه بنفس شروط التحضير. ما الذي يمكنك تأكيده دون تجاوز الدليل؟", "options": [
        opt("الـFilter متورط سببيًا في فقد الاستجابة تحت هذه الشروط؛ لكن نوع الآلية الدقيقة يحتاج دليلًا منفصلًا إذا أردنا تحديده.", 4),
        opt("ثبت أن المادة الحافظة تمتز كيميائيًا على غشاء الفلتر.", 2),
        opt("ثبت أن حجم المسام غير مناسب.", 1),
        opt("ثبت أن الشركة المصنعة للـFilter غير مناسبة للطريقة.", 1),
    ]},
    {"id": 30, "dim": "decision", "weight": 1.5, "q": "وصلت إلى Component مسؤول بقوة، لكن لا تعرف هل المشكلة contamination أم partial blockage أم assembly issue. كيف تكتب الخلاصة؟", "options": [
        opt("أختار الآلية الأكثر شيوعًا حتى تكون الخلاصة مكتملة.", 1),
        opt("أفصل بين ما تم تأكيده: ارتباط المشكلة بالمكوّن، وما لم يُحدد بعد: الآلية الدقيقة، وأوثق الدليل وحدوده.", 4),
        opt("لا يمكن كتابة أي Root Cause حتى تعرف الآلية المجهرية بالكامل.", 2),
        opt("أكتب Component failure فقط بدون ذكر حدود الدليل.", 2),
    ]},
]

st.markdown(
    """
    <style>
      .block-container {max-width: 860px; padding-top: 3.3rem; padding-bottom: 5rem;}
      html, body, [class*="css"] {font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}
      .gap-hero {direction:rtl;text-align:right;position:relative;overflow:hidden;border-radius:28px;padding:2rem 1.6rem;margin-bottom:1.2rem;background:linear-gradient(145deg,#07101f 0%,#101b2d 58%,#151922 100%);border:1px solid rgba(202,167,80,.48);color:#fff;box-shadow:0 18px 42px rgba(2,6,23,.16);}
      .gap-hero:before {content:"";position:absolute;width:220px;height:220px;border-radius:50%;top:-120px;left:-80px;background:radial-gradient(circle,rgba(202,167,80,.25),rgba(202,167,80,0) 72%);}
      .gap-kicker {font-size:.76rem;color:#d6bd78;font-weight:850;letter-spacing:.12em;direction:ltr;text-align:left;margin-bottom:.6rem;}
      .gap-title {font-size:2.2rem;line-height:1.1;font-weight:900;margin:.25rem 0 .7rem;direction:ltr;text-align:left;}
      .gap-ar {font-size:1.35rem;line-height:1.65;font-weight:800;margin:.2rem 0 .5rem;}
      .gap-copy {font-size:1rem;line-height:1.9;color:#d8e0ea;margin-top:.55rem;}
      .gap-tag,.version-badge {display:inline-block;margin-top:.75rem;padding:.35rem .65rem;border-radius:999px;font-weight:800;font-size:.75rem;}
      .gap-tag {background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.10);color:#d6bd78;}
      .version-badge {margin-right:.4rem;background:rgba(45,156,219,.13);border:1px solid rgba(45,156,219,.28);color:#9bd8ff;}
      .section-card {direction:rtl;text-align:right;padding:1.2rem 1.25rem;border-radius:20px;background:#fff;border:1px solid #e7ebf0;margin:.65rem 0;box-shadow:0 8px 24px rgba(15,23,42,.05);}
      .result-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:.6rem 0 1rem;}
      .result-card {direction:rtl;text-align:right;padding:1.2rem 1.25rem;border-radius:20px;background:linear-gradient(145deg,#fbfcfe,#f4f7fb);border:1px solid #dfe6ef;min-height:150px;}
      .result-label {font-size:.78rem;font-weight:850;color:#8a6d22;margin-bottom:.25rem;}
      .result-value {font-size:1.25rem;font-weight:900;color:#111827;line-height:1.55;}
      .result-sub {font-size:.92rem;color:#657284;line-height:1.5;margin-top:.4rem;}
      .score-row {direction:rtl;display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:.8rem 0 .35rem;font-weight:850;font-size:1.05rem;}
      .score-pct {direction:ltr;unicode-bidi:isolate;white-space:nowrap;}
      .mini {font-size:.83rem;color:#7b8795;direction:rtl;text-align:right;}
      [data-testid="stRadio"] {direction:rtl;text-align:right;}
      [data-testid="stRadio"] label {direction:rtl;text-align:right;line-height:1.65;}
      [data-testid="stProgress"] {direction:ltr;}
      div.stButton > button {border-radius:14px;font-weight:850;min-height:3.2rem;}
      @media(max-width:640px){.block-container{padding-left:1rem;padding-right:1rem;padding-top:4.8rem}.gap-hero{padding:1.4rem 1.1rem;border-radius:22px}.gap-title{font-size:1.55rem}.gap-ar{font-size:1.12rem}.gap-copy{font-size:.93rem}.result-grid{grid-template-columns:1fr}.result-card{min-height:auto}}
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("gap_version") != VERSION:
    for key in list(st.session_state.keys()):
        if str(key).startswith("q_") or str(key).startswith("gap_"):
            del st.session_state[key]
    st.session_state.gap_version = VERSION

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


def selected_option(question, selected_label):
    for item in question["options"]:
        if item["label"] == selected_label:
            return item
    return {"score": 0, "risk": 0}


def calculate_results():
    earned = {k: 0.0 for k in DIMENSIONS}
    max_points = {k: 0.0 for k in DIMENSIONS}
    risk_points = {k: 0.0 for k in DIMENSIONS}
    for q in QUESTIONS:
        weight = float(q.get("weight", 1.0))
        dim = q["dim"]
        max_points[dim] += 4.0 * weight
        selected = st.session_state.gap_answers.get(q["id"])
        if selected is None:
            continue
        item = selected_option(q, selected)
        earned[dim] += float(item["score"]) * weight
        risk_points[dim] += float(item.get("risk", 0)) * weight
    pct = {}
    for key in DIMENSIONS:
        base = 100.0 * earned[key] / max_points[key] if max_points[key] else 0.0
        penalty = min(18.0, risk_points[key] * 4.0)
        pct[key] = round(max(0.0, min(100.0, base - penalty)))
    overall = round(sum(pct.values()) / len(pct))
    ordered = sorted(pct.items(), key=lambda x: (x[1], x[0]))
    primary = ordered[0][0]
    secondary = ordered[1][0]
    strongest = sorted(pct.items(), key=lambda x: (-x[1], x[0]))[0][0]
    total_risk = round(sum(risk_points.values()), 1)
    return pct, overall, strongest, primary, secondary, total_risk


def level_from_score(score):
    if score >= 92:
        return "Expert Evidence-Led Decision Maker", "مستواك قوي جدًا حتى مع السيناريوهات الملتبسة. ركّز الآن على ثبات المنهج، تعليم الآخرين، وبناء قرارات قابلة للمراجعة."
    if score >= 82:
        return "Advanced QC Investigator", "طريقة تفكيرك قوية، لكن ما زالت هناك نقاط معايرة يمكن أن تفرق بين قرار جيد وقرار Expert تحت الغموض."
    if score >= 68:
        return "Strong QC Investigator", "عندك أساس قوي، لكن بعض السيناريوهات المعقدة تكشف فجوات في ترتيب الأدلة أو اختيار الاختبار الفاصل."
    if score >= 52:
        return "Developing QC Investigator", "عندك خبرة تشغيلية مفيدة، وتحتاج نقل التفكير من حل العرض إلى تصميم دليل يثبت أو يستبعد الفرضيات."
    return "Execution-First Analyst", "أكبر فرصة أمامك هي الانتقال من تنفيذ خطوات مألوفة إلى فهم لماذا تختار الخطوة التالية وما الدليل الذي ستنتجه."


def priority_for(dim):
    return {
        "science": "ركز على ربط RT وPeak Shape والضغط والـResolution بالمبادئ الأساسية بدل حفظ symptom → solution.",
        "investigation": "درّب نفسك على Change-Delta Check ثم سؤال: ما الاختبار الواحد الذي يفرق بين الفرضيات بأقل تغييرات؟",
        "evidence": "افصل دائمًا بين الملاحظة والاستنتاج والمجهول، ولا ترفع فرضية لأنها شائعة أو لأنها منطقية فقط.",
        "gmp": "اربط كل Troubleshooting بحفظ Raw Data، Audit Trail، SOP، QA، ومنع Testing into compliance.",
        "instrument": "ابنِ خريطة لمسار السريان والإشارة، وتعلم اختبارات العزل التي تحدد أين يبدأ الاختلاف بدل استبدال أجزاء.",
        "decision": "اكتب كل قرار بحيث يستطيع مراجع مستقل تتبع: Observation → Hypothesis → Test → Evidence → Conclusion.",
    }[dim]


def gap_label(score, rank):
    if score >= 90:
        return "أولوية المعايرة" if rank == 1 else "أولوية المعايرة الثانية"
    return "Primary Gap" if rank == 1 else "Secondary Gap"


st.markdown(f"""
<div class="gap-hero">
  <div class="gap-kicker">PHARMACEUTICAL QC · ANALYTICAL DECISION MAKING</div>
  <div class="gap-title">{TITLE}</div>
  <div class="gap-ar">خبرتك ممكن تكون قوية… لكن هل قرارك يظل قويًا لما تكون كل الإجابات تبدو منطقية؟</div>
  <div class="gap-copy">نسخة <b>Expert Calibration</b> لا تختبر الحفظ. كل سؤال تقريبًا يحتوي أكثر من اختيار قابل للدفاع عنه، والمطلوب هو <b>أفضل قرار مبني على الدليل</b> بأقل افتراضات وأعلى قيمة تشخيصية.</div>
  <span class="gap-tag">{TAGLINE}</span><span class="version-badge">{VERSION}</span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.gap_started:
    st.markdown("""
    <div class="section-card">
      <h2>مش كل إجابة منطقية هي أفضل إجابة.</h2>
      <p>في المعمل الحقيقي ممكن يكون عندك 3 خطوات صحيحة نظريًا، لكن خطوة واحدة فقط هي الأعلى قيمة الآن لأنها تنتج دليلًا يفرّق بين الاحتمالات.</p>
      <p>النسخة دي موزونة: بعض القرارات الحرجة تأثيرها أكبر، والقرارات التي تهدد سلامة التحقيق أو تدفع نحو trial-and-error عليها Penalty إضافي.</p>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(2)
    cards = [
        ("الفهم الكروماتوجرافي", "هل تقرأ العلاقة بين RT وPeak Width والضغط والـResolution؟"),
        ("منطق التحقيق", "هل تختار السؤال أو الاختبار الأعلى قيمة قبل الحل؟"),
        ("الانضباط مع الأدلة", "هل تعرف حدود ما أثبته الدليل فعلًا؟"),
        ("GMP وسلامة البيانات", "هل يظل قرارك صحيحًا حتى تحت ضغط الحصول على Passing result؟"),
        ("فهم الجهاز والنظام", "هل تستطيع عزل Pump / Injector / Column / Detector بدل تبديل الأجزاء؟"),
        ("القرار والتوثيق", "هل تفرق بين Component involvement والآلية الدقيقة وRoot Cause confirmed؟"),
    ]
    for i, (h, p) in enumerate(cards):
        with cols[i % 2]:
            st.markdown(f'<div class="section-card"><h3>{h}</h3><p>{p}</p></div>', unsafe_allow_html=True)
    st.markdown('<p class="mini">30 سؤال · 6 أبعاد · 5–7 دقائق · Scoring موزون · لا يستخدم OpenAI API ولا يستهلك رصيدًا · أداة معايرة تعليمية وليست شهادة كفاءة</p>', unsafe_allow_html=True)
    if st.button("ابدأ Expert Calibration ←", type="primary", use_container_width=True):
        st.session_state.gap_started = True
        st.session_state.gap_step = 0
        st.rerun()
    st.page_link("app.py", label="🧪 عندك مشكلة HPLC الآن؟ افتح مساعد يحيى للتحقيق", use_container_width=True)
    st.stop()

if st.session_state.gap_done:
    pct, overall, strongest, primary, secondary, total_risk = calculate_results()
    level, level_desc = level_from_score(overall)
    st.markdown(f'<div class="section-card"><div class="result-label">{VERSION}</div><h2>نتيجتك: <span dir="ltr">{overall}/100</span></h2><h3>{level}</h3><p>{level_desc}</p></div>', unsafe_allow_html=True)
    primary_label = gap_label(pct[primary], 1)
    secondary_label = gap_label(pct[secondary], 2)
    st.markdown(f"""
    <div class="result-grid">
      <div class="result-card"><div class="result-label">أقوى نقطة</div><div class="result-value">{DIMENSIONS[strongest]['name']}</div><div class="result-sub" dir="ltr">{pct[strongest]}%</div></div>
      <div class="result-card"><div class="result-label">{primary_label}</div><div class="result-value">{DIMENSIONS[primary]['name']}</div><div class="result-sub" dir="ltr">{pct[primary]}%</div></div>
      <div class="result-card"><div class="result-label">{secondary_label}</div><div class="result-value">{DIMENSIONS[secondary]['name']}</div><div class="result-sub" dir="ltr">{pct[secondary]}%</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### خريطة قرارك")
    for key, meta in DIMENSIONS.items():
        st.markdown(f'<div class="score-row"><span>{meta["name"]}</span><span class="score-pct">{pct[key]}%</span></div>', unsafe_allow_html=True)
        st.progress(pct[key] / 100)
    st.markdown(f"""
    <div class="section-card"><h2>الأولوية الاستراتيجية الجاية</h2><p><b>{DIMENSIONS[primary]['name']}</b></p><p>{priority_for(primary)}</p></div>
    """, unsafe_allow_html=True)
    if total_risk > 0:
        st.markdown("""
        <div class="section-card"><h3>ملاحظة معايرة</h3><p>بعض اختياراتك تضمنت قرارًا قد يضعف سلامة التحقيق أو يقلل قابلية تفسير النتيجة. لذلك Expert Calibration لا تعتمد على متوسط الإجابات فقط، بل تطبق Penalty على القرارات الحرجة.</p></div>
        """, unsafe_allow_html=True)
    share_text = (
        f"نتيجتي في The QC Analyst Decision Gap™ — Expert Calibration: {overall}/100\n"
        f"المستوى: {level}\n"
        f"أقوى نقطة: {DIMENSIONS[strongest]['name']} ({pct[strongest]}%)\n"
        f"{primary_label}: {DIMENSIONS[primary]['name']} ({pct[primary]}%)\n"
        f"{secondary_label}: {DIMENSIONS[secondary]['name']} ({pct[secondary]}%)\n"
        "DON'T GUESS. FOLLOW THE EVIDENCE."
    )
    with st.expander("نص جاهز لمشاركة النتيجة"):
        st.code(share_text, language=None)
    st.markdown("### من الاختبار إلى Case حقيقية")
    st.write("الاختبار يقيس طريقة التفكير. المساعد يطبق نفس المنهج على مشكلة HPLC حقيقية خطوة بخطوة، بدون قفز للسبب الجذري.")
    st.page_link("app.py", label="🧪 افتح Yahia HPLC Investigation Assistant", use_container_width=True)
    if st.button("إعادة الاختبار", use_container_width=True):
        reset_test()
        st.rerun()
    st.stop()

# QUIZ FLOW — 6 steps × 5 questions
dim_keys = list(DIMENSIONS.keys())
step = st.session_state.gap_step
current_dim = dim_keys[step]
questions = get_dimension_questions(current_dim)
st.progress(step / len(dim_keys))
st.markdown(f"""
<div class="section-card">
  <div class="result-label">المرحلة {step + 1} من 6 · {VERSION}</div>
  <div class="result-value">{DIMENSIONS[current_dim]['name']}</div>
  <div class="result-sub">{DIMENSIONS[current_dim]['en']}</div>
  <p class="mini">اختر أفضل قرار في هذه اللحظة، وليس مجرد قرار يمكن أن يكون صحيحًا نظريًا.</p>
</div>
""", unsafe_allow_html=True)

for q in questions:
    labels = [x["label"] for x in q["options"]]
    existing = st.session_state.gap_answers.get(q["id"])
    idx = labels.index(existing) if existing in labels else None
    answer = st.radio(f"{q['id']}. {q['q']}", labels, index=idx, key=f"q_{q['id']}")
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
