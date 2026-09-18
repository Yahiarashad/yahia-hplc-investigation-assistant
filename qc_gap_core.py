import streamlit as st

st.set_page_config(
    page_title="The QC Analyst Decision Gap™",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TITLE = "THE QC ANALYST DECISION GAP™"
VERSION = "v0.3 · Bilingual Analytical Calibration"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."

DIMENSIONS = {
    "science": {"ar": "الفهم الكروماتوجرافي", "en": "Chromatography Understanding"},
    "investigation": {"ar": "منطق التحقيق", "en": "Investigation Logic"},
    "evidence": {"ar": "الانضباط مع الأدلة", "en": "Evidence Discipline"},
    "gmp": {"ar": "GMP وسلامة البيانات", "en": "GMP & Data Integrity"},
    "instrument": {"ar": "فهم الجهاز والنظام", "en": "Instrument & System Thinking"},
    "decision": {"ar": "القرار والتوثيق", "en": "Decision & Documentation"},
}

TEXT = {
    "ar": {
        "lang": "اللغة",
        "hero": "خبرتك ممكن تكون قوية… لكن هل قرارك يظل قويًا لما تكون كل الإجابات منطقية؟",
        "hero_copy": "اختبار معايرة عملي لا يقيس الحفظ. كل سؤال تقريبًا يحتوي أكثر من اختيار قابل للدفاع عنه، والمطلوب هو أفضل قرار مبني على الدليل بأقل افتراضات وأعلى قيمة تشخيصية.",
        "landing_h": "مش كل إجابة منطقية هي أفضل إجابة.",
        "landing_p1": "في المعمل الحقيقي قد يكون أمامك 3 خطوات صحيحة نظريًا، لكن خطوة واحدة فقط هي الأعلى قيمة الآن لأنها تنتج دليلًا يفرق بين الاحتمالات.",
        "landing_p2": "النسخة دي موزونة: القرارات الحرجة تأثيرها أكبر، والقرارات التي تضعف سلامة التحقيق أو تدفع نحو trial-and-error عليها Penalty إضافي.",
        "start": "ابدأ Expert Calibration ←",
        "assistant_link": "🧪 عندك مشكلة HPLC الآن؟ افتح مساعد يحيى للتحقيق",
        "meta": "30 سؤال · 6 أبعاد · 5–7 دقائق · Scoring موزون · بدون API أو تكلفة إضافية · أداة معايرة تعليمية وليست شهادة كفاءة",
        "stage": "المرحلة",
        "choose": "اختر أفضل قرار في هذه اللحظة، وليس مجرد قرار يمكن أن يكون صحيحًا نظريًا.",
        "prev": "→ السابق",
        "next": "التالي ←",
        "show": "اعرض النتيجة",
        "answer_all": "أجب عن الأسئلة الخمسة للانتقال للمرحلة التالية.",
        "result": "نتيجتك",
        "strongest": "أقوى نقطة",
        "primary": "Primary Gap",
        "secondary": "Secondary Gap",
        "calibration": "أولوية المعايرة",
        "calibration2": "أولوية المعايرة الثانية",
        "map": "خريطة قرارك",
        "analysis": "التحليل المهني لنتيجتك",
        "profile": "ماذا تقول النتيجة عن طريقة تفكيرك؟",
        "why_gap": "لماذا ظهرت هذه الفجوة؟",
        "cost_points": "القرارات التي كلفتك نقاطًا",
        "strengths": "نقاط القوة المثبتة في الاختبار",
        "next_actions": "أفضل 3 خطوات تطوير الآن",
        "risk_note": "ملاحظة معايرة مهمة",
        "risk_text": "بعض الاختيارات لم تكن فقط أقل كفاءة تشخيصيًا، بل كانت قد تضعف سلامة التحقيق أو قابلية تفسير النتيجة. لذلك طُبقت Penalty إضافية على القرارات الحرجة.",
        "share": "نص جاهز لمشاركة النتيجة",
        "to_case": "من الاختبار إلى Case حقيقية",
        "to_case_copy": "الاختبار يقيس طريقة التفكير. المساعد يطبق نفس المنهج على مشكلة HPLC حقيقية خطوة بخطوة بدون قفز للسبب الجذري.",
        "open_assistant": "🧪 افتح Yahia HPLC Investigation Assistant",
        "reset": "إعادة الاختبار",
    },
    "en": {
        "lang": "Language",
        "hero": "Your experience may be strong… but does your decision stay strong when several answers look reasonable?",
        "hero_copy": "A practical calibration test that does not reward memorization. Most questions contain more than one defensible option; your task is to choose the decision with the strongest evidence value, the fewest assumptions, and the highest diagnostic power.",
        "landing_h": "Not every reasonable answer is the best answer.",
        "landing_p1": "In a real QC laboratory, three actions may all sound technically acceptable. Only one may be the highest-value next step because it generates evidence that separates competing hypotheses.",
        "landing_p2": "This version is weighted: critical decisions matter more, and choices that weaken investigation integrity or encourage trial-and-error receive an additional penalty.",
        "start": "Start Expert Calibration →",
        "assistant_link": "🧪 Have an HPLC problem now? Open Yahia Investigation Assistant",
        "meta": "30 questions · 6 dimensions · 5–7 minutes · weighted scoring · no API cost · educational calibration tool, not a competency certificate",
        "stage": "Stage",
        "choose": "Choose the best decision at this moment, not merely an action that could be technically valid.",
        "prev": "← Previous",
        "next": "Next →",
        "show": "Show result",
        "answer_all": "Answer all five questions to continue.",
        "result": "Your result",
        "strongest": "Strongest dimension",
        "primary": "Primary Gap",
        "secondary": "Secondary Gap",
        "calibration": "Calibration Priority",
        "calibration2": "Second Calibration Priority",
        "map": "Your Decision Map",
        "analysis": "Professional Result Analysis",
        "profile": "What does this result say about your thinking?",
        "why_gap": "Why did this gap appear?",
        "cost_points": "Decisions that cost you points",
        "strengths": "Strengths demonstrated in the test",
        "next_actions": "Your next 3 development actions",
        "risk_note": "Important calibration note",
        "risk_text": "Some choices were not simply less efficient diagnostically; they could also weaken investigation integrity or make the result harder to interpret. An additional penalty was therefore applied to critical decisions.",
        "share": "Ready-to-share result text",
        "to_case": "From assessment to a real case",
        "to_case_copy": "The assessment measures how you think. The assistant applies the same evidence-first method to a real HPLC problem step by step without jumping to a root cause.",
        "open_assistant": "🧪 Open Yahia HPLC Investigation Assistant",
        "reset": "Retake assessment",
    },
}


def o(ar, en, score, risk=0):
    return {"ar": ar, "en": en, "score": score, "risk": risk}


def q(i, dim, weight, ar, en, concept_ar, concept_en, options):
    return {"id": i, "dim": dim, "weight": weight, "ar": ar, "en": en, "concept_ar": concept_ar, "concept_en": concept_en, "options": options}


QUESTIONS = [
    q(1,"science",1.3,"على نفس الطريقة والعمود، أصبحت كل القمم تقريبًا عند نصف زمن الاحتجاز السابق، والضغط أعلى بكثير من المعتاد. ما القراءة العلمية الأقوى كبداية؟","Using the same method and column, nearly all peaks now elute at about half their historical retention time, while pressure is much higher than usual. What is the strongest initial scientific interpretation?","ربط RT بالتدفق الفعلي ومسار السريان","Linking RT to actual flow and the flow path",[
        o("قد يكون هناك اختلاف في معدل التدفق الفعلي أو مسار السريان؛ أتحقق من التدفق والضغط الفعليين قبل تعديل الطريقة.","There may be a difference in actual flow or the flow path; verify measured flow and pressure before changing the method.",4),
        o("الـRT وحده يكفي لإثبات أن نسبة الـorganic أعلى من المطلوب.","RT alone proves the organic percentage is too high.",2),
        o("أعوض الانخفاض بتقليل معدل التدفق حتى ترجع القمم لمكانها.","Reduce set flow until the peaks return to their old RT.",0,1),
        o("أفترض أن العمود فقد كفاءته لأن الضغط ارتفع.","Assume the column lost efficiency because pressure increased.",1)]),
    q(2,"science",1.1,"مادة منخفضة التركيز أصبحت قمتها عريضة في الـStandard والـSample معًا، بينما المادة الثانية طبيعية وRT للمادة المتأثرة لم يتغير. أي استنتاج أولي أدق؟","A low-concentration analyte becomes broad in both standard and sample, while the second analyte is normal and the affected analyte's RT is unchanged. Which initial conclusion is most accurate?","تمييز المشكلة الانتقائية لمادة واحدة","Recognizing analyte-selective behavior",[
        o("ثبات RT يجعل أي سبب كروماتوجرافي مستبعدًا.","Unchanged RT rules out chromatographic causes.",1),
        o("المشكلة انتقائية لمادة واحدة؛ أفرّق بين تفاعلها مع المسار/العمود وبين الاستجابة والتركيز بدل اعتبار النظام كله تالفًا.","The problem is selective to one analyte; distinguish analyte-specific interaction from response/concentration effects rather than calling the whole system faulty.",4),
        o("التركيز المنخفض هو السبب الجذري لأن القمة الأخرى طبيعية.","Low concentration is the root cause because the other peak is normal.",1),
        o("أغيّر الـintegration أولًا لأن RT ثابت.","Change integration first because RT is unchanged.",0,1)]),
    q(3,"science",1.2,"انخفضت الـResolution بوضوح، بينما المسافة الزمنية بين مركزي القمتين لم تتغير كثيرًا لكن القمتين أصبحتا أعرض. أين يتركز تفكيرك أولًا؟","Resolution decreases clearly; the time distance between peak centers changes little, but both peaks are broader. Where should your thinking focus first?","فصل تأثير الكفاءة عن الانتقائية","Separating efficiency loss from selectivity change",[
        o("في فقد الكفاءة/زيادة Peak Width أكثر من تغير الانتقائية وحدها.","On loss of efficiency/increased peak width more than on selectivity change alone.",4),
        o("في تغير الـselectivity فقط لأن الـResolution انخفضت.","On selectivity only because resolution decreased.",2),
        o("في خطأ detector لأن زمن الاحتجاز ثابت.","On a detector fault because RT is stable.",1),
        o("أزيد زمن التشغيل لتعويض الـResolution.","Increase run time to compensate for resolution.",0,1)]),
    q(4,"science",1.0,"ارتفع الضغط عن التاريخ المعتاد، لكن RT وشكل القمم ما زالا قريبين من الطبيعي. أي عبارة أكثر دقة؟","Pressure is higher than historical values, but RT and peak shape remain close to normal. Which statement is most accurate?","تحديد مقاومة إضافية قبل الحكم على العمود","Localizing added resistance before blaming the column",[
        o("وجود RT طبيعي يثبت أن مسار السريان سليم بالكامل.","Normal RT proves the entire flow path is healthy.",1),
        o("قد توجد مقاومة إضافية لا تزال لا تؤثر بوضوح على الفصل؛ أحتاج تحديد مكانها قبل الحكم.","Additional resistance may exist without yet affecting separation clearly; localize it before concluding.",4),
        o("العمود هو السبب الأكثر احتمالًا لأنه المصدر الأكبر للمقاومة.","The column is most likely because it is the largest resistance source.",2),
        o("أخفض التدفق كحل تشغيلي وأكمل السلسلة.","Lower flow as an operational workaround and continue the sequence.",0,1)]),
    q(5,"science",1.2,"بعد حقنة عالية التركيز ظهر Peak في الـblank التالي ثم انخفض تدريجيًا في blanks المتتالية. ما الذي يدعمه هذا النمط أكثر؟","After a high-concentration injection, a peak appears in the next blank and decreases across successive blanks. What does this pattern support most strongly?","تمييز carryover عن مصدر ثابت","Distinguishing carryover from a persistent source",[
        o("وجود carryover مرتبط بمسار الحقن/الغسل أكثر من Ghost Peak ثابت المصدر، مع بقاء الحاجة للعزل.","Carryover related to the injection/wash path is better supported than a fixed-source ghost peak, while isolation is still needed.",4),
        o("تلوث ثابت في الطور المتحرك لأن الـblank به Peak.","Persistent mobile-phase contamination because the blank has a peak.",2),
        o("تدهور العمود لأن القمة ظهرت بعد العينة.","Column deterioration because the peak appeared after the sample.",1),
        o("أحذف أول blank وأعتمد التالي إذا أصبح نظيفًا.","Discard the first blank and accept the next if it is clean.",0,2)]),

    q(6,"investigation",1.0,"أمامك مشكلة جديدة وبها 4 أسباب تبدو معقولة. ما أفضل أول حركة؟","You face a new problem with four plausible causes. What is the best first move?","اختيار المعلومة الأعلى قيمة قبل العلاج","Choosing the highest-value missing information before acting",[
        o("أرتب الأسباب من الأكثر شيوعًا وأبدأ العلاج مباشرة.","Rank causes by how common they are and start correcting the most common one.",2),
        o("أحدد المعلومة التي لو عرفتها ستقسم الاحتمالات، ثم أطلبها أو أصمم اختبارًا واحدًا ينتجها.","Identify the information that would split the hypotheses, then obtain it or design one test that produces it.",4),
        o("أجرب أسرع تغيير يمكن الرجوع عنه ثم أرى.","Try the fastest reversible change and see what happens.",1),
        o("أكرر الحقن أولًا لأن أي مشكلة قد تكون عابرة.","Repeat the injection first because any problem may be transient.",0,1)]),
    q(7,"investigation",1.5,"الطريقة كانت ناجحة تاريخيًا، واليوم أعطت فشلًا جديدًا. لديك وقت لسؤال واحد قبل بدء الاختبارات. أي سؤال يعطي أعلى قيمة تشخيصية؟","The method historically worked and fails today. You have time for one question before testing. Which question has the highest diagnostic value?","Change-Delta Check بين آخر نجاح والفشل الحالي","Change-Delta Check between last-known-good and current failure",[
        o("هل يوجد عمود احتياطي؟","Is a spare column available?",1),
        o("ما الذي اختلف بين آخر تشغيل مقبول والتشغيل الحالي: شخص، تحضير، مواد، consumables، جهاز أو إعدادات؟","What changed between the last acceptable run and the current one: analyst, preparation, materials, consumables, instrument, or settings?",4),
        o("هل حدثت المشكلة سابقًا في شركة أخرى؟","Has this happened in another company before?",2),
        o("هل يمكن تكرار الـStandard للتأكد؟","Can we repeat the standard to confirm?",1)]),
    q(8,"investigation",1.5,"غسل الـGuard Column أعاد Peak Shape الطبيعي واستمر التحسن خلال الـSequence. ما الاستنتاج الأكثر انضباطًا؟","Washing the guard column restored normal peak shape and the improvement continued through the sequence. What is the most disciplined conclusion?","فصل تورط المكوّن عن الآلية الدقيقة","Separating component involvement from the exact mechanism",[
        o("ثبت أن التلوث الكيميائي داخل الـGuard Column هو السبب الجذري.","Chemical contamination inside the guard column is proven as the root cause.",2),
        o("أصبح الـGuard Column/حالته متورطًا بقوة، لكن نوع الآلية الدقيقة ما زال يحتاج دليلًا إذا كان مهمًا للتحقيق.","The guard column/its condition is strongly implicated, but the exact mechanism still needs evidence if it matters to the investigation.",4),
        o("نجاح الغسل يثبت أن الـanalytical column سليم 100%.","Successful washing proves the analytical column is 100% healthy.",1),
        o("بما أن النتيجة تحسنت، لا حاجة لتوثيق ما قبل/بعد الغسل.","Because performance improved, before/after documentation is unnecessary.",0,2)]),
    q(9,"investigation",1.3,"نفس الـStandard والعمود والطريقة يفشلون على جهاز A وينجحون على جهاز B. أي خطوة تالية أكثر تمييزًا؟","The same standard, column, and method fail on instrument A and pass on instrument B. Which next step is most discriminating?","عزل اختلاف فعلي بين جهازين","Isolating a measurable difference between instruments",[
        o("أستمر على جهاز B فقط لأن الطريقة نجحت عليه.","Continue only on instrument B because the method works there.",0,1),
        o("أعتبر جهاز A هو Root Cause وأطلب صيانة عامة.","Declare instrument A the root cause and request general maintenance.",2),
        o("أقارن متغيرًا فعليًا عالي القيمة بين الجهازين مثل measured flow/pressure أو مسار الحقن، مع تثبيت باقي الظروف.","Compare one high-value measured variable between instruments, such as actual flow/pressure or injection path, while holding other conditions constant.",4),
        o("أعيد تحضير الـStandard مرة ثالثة على الجهاز A.","Prepare the standard a third time on instrument A.",1)]),
    q(10,"investigation",1.5,"ثلاث مواد حافظة في نفس الـStandard أعطت نتائج أقل من التاريخ، لكن الانخفاض ليس بنفس النسبة لكل مادة. قبل اتهام الـinjector أو detector، ما الخطوة الأعلى قيمة؟","Three preservatives in the same standard give lower-than-historical results, but not by the same percentage. Before blaming the injector or detector, what is the highest-value next step?","فصل Peak Area الخام عن الحساب ومراجعة التحضير","Separating raw peak area from calculation and reviewing preparation",[
        o("أعرف أولًا هل التغير في Peak Areas الخام أم في الحساب النهائي، وأراجع ما تغير في التحضير مقارنة بآخر Standard مقبول.","First determine whether the change is in raw peak areas or only the final calculation, and compare preparation with the last acceptable standard.",4),
        o("أعيد الحقن عدة مرات لأعرف المتوسط الجديد.","Repeat injections several times to establish a new average.",0,1),
        o("أغير Response Factors لأن الثلاث مواد متأثرة.","Change response factors because all three analytes are affected.",0,1),
        o("أفترض عدم تجانس الحقن لأن كل المواد انخفضت.","Assume injection non-uniformity because all analytes decreased.",2)]),

    q(11,"evidence",1.2,"ورد في السجل: الضغط المعتاد 180 bar، وبعد 25 حقنة كانت القراءة 310 bar. أي عبارة يمكن وضعها داخل «ما نعرفه»؟","The record says historical pressure was 180 bar, and after 25 injections the reading was 310 bar. Which statement belongs under 'What we know'?","الفصل بين الملاحظة والاتجاه غير المثبت","Separating observed facts from an unproven trend",[
        o("الضغط ارتفع تدريجيًا بسبب تراكم العينات.","Pressure progressively increased because of sample accumulation.",0),
        o("بعد 25 حقنة سُجل ضغط 310 bar مقارنة بتاريخ معتاد 180 bar؛ شكل الاتجاه خلال الحقن غير معروف.","After 25 injections, 310 bar was recorded versus a historical 180 bar; the pressure trend during the sequence is unknown.",4),
        o("حدث انسداد بعد الحقنة رقم 24.","A blockage occurred after injection 24.",0),
        o("العمود بدأ يتدهور أثناء الـSequence.","The column started deteriorating during the sequence.",0)]),
    q(12,"evidence",1.0,"سبب ما شائع جدًا في خبرتك، لكن لا يوجد في الحالة الحالية دليل يميزه عن سببين آخرين. كيف تصفه؟","A cause is very common in your experience, but this case contains no evidence that distinguishes it from two alternatives. How should you describe it?","عدم تحويل الشيوع إلى دليل خاص بالحالة","Not turning commonness into case-specific evidence",[
        o("High likelihood لأن الخبرة السابقة تعتبر Evidence.","High likelihood because prior experience is evidence.",2),
        o("فرضية ممكنة؛ شيوعها قد يوجّه الانتباه لكنه لا يرفعها وحده إلى استنتاج خاص بالحالة.","A possible hypothesis; commonness may guide attention but does not by itself elevate it to a case-specific conclusion.",4),
        o("Probable Root Cause إذا لم توجد علامة تناقضها.","Probable root cause if nothing contradicts it.",1),
        o("السبب العملي الأفضل لأن اختباره أسرع.","The best practical cause because it is fastest to test.",1)]),
    q(13,"evidence",1.4,"اختبار مستهدف أعطى النتيجة التي توقعتها لفرضيتك. ما الذي يحدد إن كان هذا Confirmatory evidence كافيًا؟","A targeted test gives the result predicted by your hypothesis. What determines whether this is sufficient confirmatory evidence?","قوة الاختبار في استبعاد البدائل","Whether the test meaningfully excludes alternatives",[
        o("مجرد توافق النتيجة مع التوقع.","Simply matching the predicted result.",2),
        o("أن يكون الاختبار قادرًا على التمييز وأن تصبح البدائل المعقولة أقل احتمالًا، لا مجرد تحسن عرض واحد.","The test must discriminate and make reasonable alternatives less likely, not merely improve one symptom.",4),
        o("أن تتكرر النتيجة مرتين على الأقل مهما كان تصميم الاختبار.","The result must repeat at least twice regardless of test design.",1),
        o("أن يعود SST للنجاح مرة واحدة.","SST needs to pass once.",2)]),
    q(14,"evidence",1.3,"قال المحلل: «ما اتغيرش أي حاجة». ما التصرف الأكثر انضباطًا؟","The analyst says, 'Nothing changed.' What is the most evidence-disciplined response?","اعتبار الرواية الأولية مدخلًا يحتاج تحققًا","Treating an initial report as a lead that still needs verification",[
        o("أعتبر كل الظروف متطابقة وأنتقل مباشرة إلى عطل الجهاز.","Treat all conditions as identical and move directly to an instrument fault.",1),
        o("أتعامل معها كتقرير أولي، ثم أتحقق من أعلى comparator قيمة مثل التحضير/الـlot/consumable/الجهاز حسب الحالة.","Treat it as an initial report, then verify the highest-value comparator such as preparation, lot, consumable, or instrument depending on the case.",4),
        o("أعتبرها معلومة غير مفيدة تمامًا.","Treat the statement as completely useless.",2),
        o("أعيد التحليل للتأكد من أن المشكلة ما زالت موجودة.","Repeat the analysis to confirm the problem still exists.",1)]),
    q(15,"evidence",1.2,"تحضيران مستقلان للطور المتحرك أعطيا نفس الفشل. ما الذي يدعمه هذا تحديدًا؟","Two independent mobile-phase preparations give the same failure. What does this specifically support?","تضييق الفرضية دون استبعاد زائد","Narrowing a hypothesis without over-excluding it",[
        o("يستبعد الطور المتحرك بالكامل من التحقيق.","It completely excludes mobile phase from the investigation.",1),
        o("يضعف فرضية خطأ تحضير عارض في زجاجة واحدة، لكنه لا يستبعد خطأ مشتركًا في الوصفة/المواد/القياس.","It weakens the hypothesis of a one-off preparation error in a single bottle, but does not exclude a shared error in recipe, materials, or measurement.",4),
        o("يثبت أن العمود هو السبب.","It proves the column is the cause.",0),
        o("يثبت أن الطريقة نفسها غير Robust.","It proves the method itself is not robust.",1)]),

    q(16,"gmp",1.5,"ظهرت نتيجة OOS ويُشتبه في خطأ تحليلي. أي تصرف يحافظ على قوة التحقيق من البداية؟","An OOS result appears and an analytical error is suspected. Which action best protects the investigation from the start?","حفظ البيانات الأصلية قبل أي إعادة اختبار","Preserving original data before any retesting",[
        o("إعادة التحليل فورًا مع Analyst آخر لمعرفة النتيجة الصحيحة.","Immediately repeat the analysis with another analyst to find the correct result.",0,2),
        o("حفظ الـRaw Data والكروماتوجرامات والسجل، وبدء التحقيق وفق SOP/QA قبل أي إعادة اختبار مبررة.","Preserve raw data, chromatograms, and records, and initiate the investigation per SOP/QA before any justified retest.",4),
        o("استبعاد الحقن غير الطبيعية ثم حساب الباقي.","Exclude abnormal injections and calculate the rest.",0,2),
        o("إعادة Integration بطريقة تعكس شكل القمة بشكل أفضل ثم تقييم النتيجة.","Reintegrate to better reflect the peak shape, then reassess the result.",1,1)]),
    q(17,"gmp",1.5,"أي سيناريو يمثل Testing into compliance بصورة أوضح؟","Which scenario most clearly represents testing into compliance?","التعرف على retesting بهدف الوصول للنجاح","Recognizing retesting intended to obtain a passing result",[
        o("اختبار فرضية محددة ومسبقة التوثيق لمعرفة هل الـfilter يؤثر على recovery.","Testing a predefined documented hypothesis to see whether the filter affects recovery.",1),
        o("إجراء حقن إضافية متكررة، ثم اختيار المجموعة التي تقع داخل المواصفة واعتبارها النتيجة.","Performing repeated extra injections, then selecting the passing subset as the result.",4),
        o("مقارنة actual flow بين جهازين كجزء من investigation.","Comparing actual flow between two instruments as part of an investigation.",1),
        o("إعادة تحضير مستقلة إذا كان الـSOP يسمح بها ولها rationale موثق.","An independent repreparation allowed by SOP with documented rationale.",1)]),
    q(18,"gmp",1.2,"أثناء التحقيق احتجت Diagnostic Injection ليست جزءًا من الروتين. ما أفضل تعامل؟","During an investigation you need a diagnostic injection that is not part of routine testing. What is the best approach?","توثيق الاختبار التشخيصي دون استبدال الأصل","Documenting diagnostic testing without replacing original data",[
        o("تُنفذ تحت الإجراء المناسب وتُوثق كاختبار تشخيصي مع غرض واضح، ولا تُستخدم لاستبدال النتيجة الأصلية.","Perform it under the appropriate procedure, document its diagnostic purpose, and do not use it to replace the original result.",4),
        o("تُنفذ خارج الـsequence حتى لا تؤثر على السجل الرسمي.","Run it outside the sequence so it does not affect the official record.",0,2),
        o("تُستخدم كبديل للنتيجة الأصلية إذا نجحت.","Use it as a replacement for the original result if it passes.",0,2),
        o("لا تحتاج توثيقًا لأنها ليست Reportable result.","It does not need documentation because it is not reportable.",0,2)]),
    q(19,"gmp",1.5,"استخدام Filter غير مذكور في الطريقة أعطى نتائج Passing، بينما التحضير بدون هذا الـFilter يعطي النتيجة التاريخية المقبولة. ما القرار الأكثر دفاعًا؟","Using a filter not specified in the method gives passing results, while preparation without that filter reproduces the historical acceptable result. Which decision is most defensible?","عدم تحويل workaround غير معتمد إلى خطوة روتينية","Not turning an unapproved workaround into a routine step",[
        o("اعتماد الـFilter الجديد لأنه حسّن النتيجة.","Adopt the new filter because it improved the result.",0,2),
        o("عدم تحويله إلى خطوة روتينية؛ أوثق الفرق وأحقق في recovery/compatibility وألتزم بالطريقة والإجراء المعتمدين.","Do not make it routine; document the difference, investigate recovery/compatibility, and follow the approved method and procedure.",4),
        o("إضافة الـFilter مؤقتًا لهذه الدفعة فقط.","Add the filter only for this batch.",0,2),
        o("متوسط النتائج المفلترة وغير المفلترة يعطي تقديرًا أكثر عدلًا.","Average filtered and unfiltered results for a fairer estimate.",0,2)]),
    q(20,"gmp",1.3,"فشل الاختبار على جهاز A ونجح فورًا على جهاز B. أي موقف أقوى من ناحية GMP؟","The test fails on instrument A and immediately passes on instrument B. Which position is stronger from a GMP perspective?","استخدام النجاح كدليل تشخيصي لا كإلغاء للفشل","Using a passing comparison as diagnostic evidence, not as cancellation of the failure",[
        o("نتيجة B تلغي نتيجة A لأن نفس العينة نجحت.","Result B invalidates result A because the same sample passed.",0,2),
        o("نتيجة B دليل تشخيصي مهم، لكن فشل A وبياناته يظلان جزءًا من التحقيق ولا يُتجاهلان.","Result B is important diagnostic evidence, but the failure on A and its data remain part of the investigation.",4),
        o("نعتمد B ونفتح الصيانة لاحقًا بدون ربط الحالتين.","Accept B and open maintenance later without linking the events.",1,1),
        o("نختار الجهاز الذي يعطي SST أفضل دائمًا.","Always choose the instrument that gives better SST.",0,1)]),

    q(21,"instrument",1.2,"ظهر High Pressure جديد. أي استراتيجية عزل تعطي معلومات أفضل بأقل تغييرات؟","A new high-pressure problem appears. Which isolation strategy gives the most information with the fewest changes?","عزل مسار السريان تدريجيًا","Stepwise isolation of the flow path",[
        o("استبدال العمود أولًا لأنه غالبًا أعلى مقاومة.","Replace the column first because it usually has the highest resistance.",2),
        o("عزل مسار السريان تدريجيًا وفق SOP/تعليمات الشركة، ومقارنة الضغط بعد إزالة أجزاء downstream بطريقة آمنة.","Isolate the flow path stepwise per SOP/manufacturer guidance and compare pressure after safely removing downstream components.",4),
        o("فتح purge valve؛ إذا انخفض الضغط يكون العمود السبب مؤكدًا.","Open the purge valve; if pressure drops, the column is confirmed as the cause.",2),
        o("خفض flow للنصف ومتابعة الـSequence.","Cut flow in half and continue the sequence.",0,1)]),
    q(22,"instrument",1.5,"الجهاز يعرض Set Flow = 1.0 mL/min، لكن RT أصبح نصف التاريخ تقريبًا. ما أقوى تحقق؟","The instrument displays Set Flow = 1.0 mL/min, but RT is about half the historical value. What is the strongest verification?","الفرق بين setpoint والتدفق الفعلي","Distinguishing setpoint from actual flow",[
        o("الاعتماد على الشاشة لأن setpoint هو القيمة التي يستخدمها النظام.","Trust the display because the setpoint is what the system uses.",0),
        o("قياس/التحقق من معدل التدفق الفعلي وفق الإجراء المعتمد ومقارنته بالتاريخ والضغط.","Measure/verify actual flow per the approved procedure and compare it with history and pressure.",4),
        o("زيادة زمن التشغيل حتى تعود القمة إلى 6 دقائق.","Increase run time until the peak returns to 6 minutes.",0,1),
        o("قياس pH مرة أخرى فقط لأن RT تغيّر.","Recheck pH only because RT changed.",2)]),
    q(23,"instrument",1.2,"Peak Area RSD أصبح سيئًا، لكن RT والضغط ثابتان وشكل القمم مقبول. أين تبدأ العزل بصورة أكثر منطقية؟","Peak-area RSD becomes poor, but RT and pressure are stable and peak shape is acceptable. Where should isolation begin more logically?","ربط area precision بمسار الحقن والاستجابة","Linking area precision to injection delivery and detector response",[
        o("من عناصر تؤثر على كمية/استجابة الحقن مثل autosampler/injection precision ثم detector response، مع مقارنة controlled.","Start with factors affecting delivered amount/response such as autosampler injection precision, then detector response, using controlled comparisons.",4),
        o("من تغيير العمود لأن Area issue قد يأتي من stationary phase.","Start by changing the column because area issues can come from stationary phase.",1),
        o("من تعديل mobile phase strength.","Start by adjusting mobile-phase strength.",1),
        o("لا يوجد System issue لأن RT ثابت.","There is no system issue because RT is stable.",1)]),
    q(24,"instrument",1.1,"Baseline spike يظهر بشكل متكرر قريبًا من توقيت حركة الـinjector، بينما يختفي في تشغيل بدون injection event. ماذا تفعل؟","A baseline spike repeatedly appears near injector movement and disappears in runs without an injection event. What should you do?","استخدام التزامن لتوجيه اختبار العزل","Using event timing to guide isolation",[
        o("أستخدم التزامن كدليل يوجّه العزل نحو injector/event-related disturbance، ثم أختبره بدل اتهام detector مباشرة.","Use the timing correlation to guide isolation toward an injector/event-related disturbance, then test it rather than blaming the detector immediately.",4),
        o("أغير detector lamp لأن الـspike ظاهرة على الإشارة.","Change the detector lamp because the spike appears in the signal.",1),
        o("أزيد smoothing في processing لإخفاء الـspike.","Increase smoothing in processing to hide the spike.",0,1),
        o("أغير العمود لأن كل signal تمر عبره.","Change the column because every signal passes through it.",1)]),
    q(25,"instrument",1.2,"Peak يظهر بعد high-standard ثم يقل في كل blank لاحق. ما الاختبار العازل الأكثر فائدة قبل تغيير العمود؟","A peak appears after a high standard and decreases in each subsequent blank. What is the most useful isolation test before changing the column?","اختبار wash path وcarryover بطريقة controlled","Controlled testing of wash path and carryover",[
        o("مراجعة/اختبار wash path وneedle/seat carryover بطريقة controlled مع blanks متسلسلة.","Review/test the wash path and needle/seat carryover in a controlled way with sequential blanks.",4),
        o("حقن mobile phase عشر مرات حتى تختفي القمة.","Inject mobile phase ten times until the peak disappears.",0,1),
        o("تغيير analytical column ثم المقارنة.","Change the analytical column and compare.",2),
        o("زيادة run time فقط.","Only increase run time.",1)]),

    q(26,"decision",1.5,"بعد تدخل واحد تحسنت المشكلة كما توقعت، لكن يوجد سبب بديل كان يمكن أن يعطي نفس التحسن. ما التصنيف الأدق؟","After one intervention, the problem improves as predicted, but an alternative cause could have produced the same improvement. What is the most accurate classification?","اختيار مستوى يقين يتناسب مع قوة الدليل","Matching certainty level to evidence strength",[
        o("ROOT CAUSE CONFIRMED لأن التدخل نجح.","ROOT CAUSE CONFIRMED because the intervention worked.",2),
        o("ROOT CAUSE PROBABLE — نحتاج اختبارًا يميز عن البديل قبل التأكيد.","ROOT CAUSE PROBABLE — a test that discriminates against the alternative is still needed before confirmation.",4),
        o("ROOT CAUSE NOT IDENTIFIED لأن أي تحسن غير كافٍ.","ROOT CAUSE NOT IDENTIFIED because any improvement is insufficient.",2),
        o("أغلق التحقيق طالما SST عاد للنجاح.","Close the investigation because SST passed again.",0,1)]),
    q(27,"decision",1.1,"مديرك يريد «الخطوة التالية» في جملة واحدة. أي إجابة هي الأقوى؟","Your manager asks for the 'next step' in one sentence. Which answer is strongest?","صياغة اختبار واحد مع سبب وتفسير مسبق","Stating one test with rationale and pre-defined interpretation",[
        o("لدينا خمس احتمالات وسنراجعها بالترتيب.","We have five possibilities and will review them in order.",2),
        o("سنقيس actual flow لأن النتيجة ستفصل بين خطأ توصيل/ضبط التدفق وبين فرضيات العمود أو التحضير، وسنفسر كلا الاتجاهين.","We will measure actual flow because the result will separate flow-delivery issues from column/preparation hypotheses, with both result directions pre-interpreted.",4),
        o("سنغير العمود لأنه أسرع طريقة لاستبعاد السبب.","We will change the column because it is the fastest way to rule it out.",1),
        o("سنكرر التحليل على جهاز آخر وإذا نجح نغلق الحالة.","We will repeat on another instrument and close the case if it passes.",1)]),
    q(28,"decision",1.2,"أي Investigation Record يسمح لمراجع مستقل بإعادة بناء منطقك؟","Which investigation record allows an independent reviewer to reconstruct your reasoning?","توثيق سلسلة المنطق كاملة","Documenting the full reasoning chain",[
        o("المشكلة → الحل → النتيجة.","Problem → solution → result.",2),
        o("Observation → Hypothesis → Test → Evidence → Interpretation → Conclusion، مع حفظ البيانات الأصلية.","Observation → Hypothesis → Test → Evidence → Interpretation → Conclusion, with original data preserved.",4),
        o("قائمة بالأجزاء التي تم تغييرها حتى نجاح الجهاز.","A list of parts changed until the system worked.",1),
        o("السبب الجذري والتوصية النهائية فقط.","Root cause and final recommendation only.",1)]),
    q(29,"decision",1.4,"ثبت أن المشكلة تختفي عند إزالة Filter وتعود عند استخدامه بنفس شروط التحضير. ما الذي يمكنك تأكيده دون تجاوز الدليل؟","The problem disappears when a filter is removed and returns when it is used under the same preparation conditions. What can you confirm without exceeding the evidence?","تأكيد السببية دون اختراع الآلية","Confirming causal involvement without inventing the mechanism",[
        o("الـFilter متورط سببيًا في فقد الاستجابة تحت هذه الشروط؛ لكن نوع الآلية الدقيقة يحتاج دليلًا منفصلًا إذا أردنا تحديده.","The filter is causally involved in response loss under these conditions; the exact mechanism needs separate evidence if we want to specify it.",4),
        o("ثبت أن المادة الحافظة تمتز كيميائيًا على غشاء الفلتر.","Chemical adsorption of the preservative on the membrane is proven.",2),
        o("ثبت أن حجم المسام غير مناسب.","The pore size is proven unsuitable.",1),
        o("ثبت أن الشركة المصنعة للـFilter غير مناسبة للطريقة.","The filter manufacturer is proven unsuitable for the method.",1)]),
    q(30,"decision",1.5,"وصلت إلى Component مسؤول بقوة، لكن لا تعرف هل المشكلة contamination أم partial blockage أم assembly issue. كيف تكتب الخلاصة؟","You strongly localize the problem to a component, but do not know whether the mechanism is contamination, partial blockage, or assembly error. How should the conclusion be written?","تحديد ما تم إثباته وحدود ما لم يثبت","Separating what is proven from what remains unknown",[
        o("أختار الآلية الأكثر شيوعًا حتى تكون الخلاصة مكتملة.","Choose the most common mechanism so the conclusion feels complete.",1),
        o("أفصل بين ما تم تأكيده: ارتباط المشكلة بالمكوّن، وما لم يُحدد بعد: الآلية الدقيقة، وأوثق الدليل وحدوده.","Separate what is confirmed—the component association—from what remains unidentified—the exact mechanism—and document both evidence and limits.",4),
        o("لا يمكن كتابة أي Root Cause حتى تعرف الآلية المجهرية بالكامل.","No root cause can be written until the microscopic mechanism is fully known.",2),
        o("أكتب Component failure فقط بدون ذكر حدود الدليل.","Write 'component failure' without stating evidence limits.",2)]),
]

PROFILE_COPY = {
    "ar": {
        "expert": ("Expert Evidence-Led Decision Maker", "نتيجتك لا تعكس معرفة تقنية فقط؛ تعكس قدرة مستقرة على حماية الدليل، اختيار اختبار فاصل، وضبط مستوى اليقين في القرار. لا توجد فجوة حرجة منخفضة بما يكفي لتقويض اللقب."),
        "advanced": ("Advanced Evidence-Led QC Professional", "ملفك العام قوي جدًا، لكن هناك بُعدًا واحدًا على الأقل أقل من مستوى الـExpert gate. هذا يعني أن المشكلة ليست في كمية المعرفة، بل في ثبات تطبيق المنهج تحت سيناريوهات محددة."),
        "strong": ("Strong QC Investigator", "عندك أساس مهني قوي، لكن بعض القرارات ما زالت تميل إلى إجراء يبدو منطقيًا بدل اختيار الاختبار الأعلى قيمة تشخيصية."),
        "developing": ("Developing QC Investigator", "لديك خبرة تشغيلية جيدة، لكنك تحتاج تحويلها إلى نظام قرار أكثر ثباتًا: ماذا نعرف؟ ماذا لا نعرف؟ وما الاختبار الذي يغيّر قرارنا فعلًا؟"),
        "execution": ("Execution-First Analyst", "الفرصة الأكبر أمامك هي الانتقال من تنفيذ خطوات مألوفة أو حلول سريعة إلى بناء دليل يحدد السبب ويجعل القرار قابلًا للدفاع عنه."),
    },
    "en": {
        "expert": ("Expert Evidence-Led Decision Maker", "Your result reflects more than technical knowledge. It shows consistent ability to protect evidence, choose discriminating tests, and match confidence to evidence strength. No critical dimension falls below the expert gate."),
        "advanced": ("Advanced Evidence-Led QC Professional", "Your overall profile is very strong, but at least one dimension falls below the expert gate. The issue is not lack of knowledge; it is consistency of applying the method in specific ambiguous scenarios."),
        "strong": ("Strong QC Investigator", "You have a strong professional base, but some decisions still favor a reasonable action over the highest-value diagnostic test."),
        "developing": ("Developing QC Investigator", "You have useful operational experience, but it needs to become a more stable decision system: what is known, what is unknown, and which test would actually change the decision?"),
        "execution": ("Execution-First Analyst", "Your biggest opportunity is to move from familiar actions and quick fixes toward building evidence that localizes the cause and makes the decision defensible."),
    },
}

ACTION_MAP = {
    "science": {
        "ar": ["اربط كل تغير في RT أو Resolution أو Peak Width بالمبدأ العلمي قبل التفكير في الجزء المتهم.", "عند أي تغير، افصل بين retention وefficiency وselectivity بدل استخدام كلمة «column problem» كتشخيص عام.", "استخدم كروماتوجرام تاريخي مقبول كمرجع كمي، لا كصورة شكلية."],
        "en": ["Link every RT, resolution, or peak-width change to the underlying chromatographic principle before blaming a component.", "Separate retention, efficiency, and selectivity instead of using 'column problem' as a catch-all diagnosis.", "Use a historical acceptable chromatogram as a quantitative comparator, not just a visual reference."],
    },
    "investigation": {
        "ar": ["ابدأ أي Failure له تاريخ نجاح بسؤال Change-Delta Check قبل اقتراح الحلول.", "قبل كل اختبار اسأل: أي فرضيتين سيفرق بينهما؟ وماذا سأفهم من كل اتجاه للنتيجة؟", "غيّر متغيرًا واحدًا في كل اختبار تمييزي كلما كان ذلك ممكنًا ومسموحًا."],
        "en": ["For any failure with a last-known-good history, start with a Change-Delta Check before proposing fixes.", "Before every test, ask: which hypotheses will this separate, and what will each possible result mean?", "Change one variable at a time in discriminating tests whenever practical and permitted."],
    },
    "evidence": {
        "ar": ["اكتب الحقائق بصيغة لا تحتوي أي تفسير زائد: Observed / Reported / Unknown.", "لا ترفع فرضية إلى Probable لمجرد أنها شائعة؛ اطلب دليلًا خاصًا بالحالة.", "قبل كلمة Confirmed، اسأل: هل الاختبار استبعد بديلًا معقولًا أم فقط حسّن العرض؟"],
        "en": ["Write facts without hidden interpretation: Observed / Reported / Unknown.", "Do not promote a hypothesis to Probable because it is common; require case-specific evidence.", "Before using Confirmed, ask whether the test excluded a reasonable alternative or merely improved the symptom."],
    },
    "gmp": {
        "ar": ["احفظ Raw Data وAudit Trail قبل أي retest أو إعادة معالجة.", "افصل الاختبار التشخيصي عن النتيجة الأصلية ولا تستخدمه كبديل لها.", "أي workaround غير مذكور في الطريقة يحتاج تقييمًا وتوثيقًا، لا يتحول تلقائيًا إلى خطوة روتينية."],
        "en": ["Preserve raw data and audit trail before any retest or reprocessing.", "Keep diagnostic testing separate from the original result and never use it as a replacement.", "Any workaround not specified in the method requires evaluation and documentation; it does not automatically become routine."],
    },
    "instrument": {
        "ar": ["فكر في الجهاز كمسار: solvent → pump → injector → column → detector، واعزل المنطقة قبل استبدال الجزء.", "فرّق دائمًا بين Set Value والقيمة الفعلية measured value.", "اربط نوع العرض بالجزء القادر فعليًا على إنتاجه ثم اختبر هذا الارتباط."],
        "en": ["Think of the instrument as a path: solvent → pump → injector → column → detector, and localize the region before replacing parts.", "Always distinguish a set value from the actual measured value.", "Link the symptom type to the component capable of producing it, then test that relationship."],
    },
    "decision": {
        "ar": ["اجعل كل خلاصة تحتوي على ما تم إثباته وما لم يُثبت بعد.", "استخدم Confirmed / Probable / Not Yet Identified حسب قوة الدليل، لا حسب رغبتك في إغلاق التحقيق.", "اكتب Next Best Step كاختبار واحد + سبب اختياره + تفسير النتيجتين المحتملتين."],
        "en": ["Every conclusion should state both what is proven and what remains unproven.", "Use Confirmed / Probable / Not Yet Identified according to evidence strength, not the desire to close the investigation.", "Write the Next Best Step as one test + why it was chosen + how each possible result will be interpreted."],
    },
}

STRENGTH_COPY = {
    "science": {"ar":"تقرأ التغيرات الكروماتوجرافية من خلال المبادئ لا من خلال أعراض محفوظة.","en":"You interpret chromatographic changes through principles rather than memorized symptoms."},
    "investigation": {"ar":"تميل لاختيار اختبارات تمييزية بدل القفز إلى تبديل الأجزاء.","en":"You tend to choose discriminating tests rather than jumping to part replacement."},
    "evidence": {"ar":"تفصل جيدًا بين الحقيقة والاستنتاج وحدود ما أثبته الاختبار.","en":"You separate facts, inferences, and the limits of what a test actually proves."},
    "gmp": {"ar":"قراراتك تحافظ على البيانات الأصلية وتقاوم ضغط الحصول على Passing result.","en":"Your decisions protect original data and resist pressure to test into a passing result."},
    "instrument": {"ar":"تفكر في الجهاز كنظام مترابط وتستخدم العزل بدل التخمين.","en":"You think of the instrument as an interconnected system and use isolation rather than guessing."},
    "decision": {"ar":"تضبط مستوى اليقين في الخلاصة وتكتب قرارًا يمكن مراجعته والدفاع عنه.","en":"You calibrate certainty in conclusions and write decisions that can be reviewed and defended."},
}

st.markdown("""
<style>
.block-container{max-width:860px;padding-top:3.2rem;padding-bottom:5rem}
html,body,[class*="css"]{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.gap-hero{position:relative;overflow:hidden;border-radius:28px;padding:2rem 1.6rem;margin-bottom:1.1rem;background:linear-gradient(145deg,#07101f 0%,#101b2d 58%,#151922 100%);border:1px solid rgba(202,167,80,.48);color:#fff;box-shadow:0 18px 42px rgba(2,6,23,.16)}
.gap-hero:before{content:"";position:absolute;width:220px;height:220px;border-radius:50%;top:-120px;left:-80px;background:radial-gradient(circle,rgba(202,167,80,.25),rgba(202,167,80,0) 72%)}
.gap-kicker{font-size:.76rem;color:#d6bd78;font-weight:850;letter-spacing:.12em;direction:ltr;text-align:left;margin-bottom:.6rem}.gap-title{font-size:2.05rem;line-height:1.1;font-weight:900;margin:.25rem 0 .7rem;direction:ltr;text-align:left}.gap-ar{font-size:1.3rem;line-height:1.65;font-weight:800;margin:.2rem 0 .5rem}.gap-copy{font-size:.98rem;line-height:1.85;color:#d8e0ea;margin-top:.55rem}.tag{display:inline-block;margin-top:.7rem;margin-right:.35rem;padding:.35rem .65rem;border-radius:999px;font-weight:800;font-size:.75rem;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.10);color:#d6bd78}.version{color:#9bd8ff;border-color:rgba(45,156,219,.28);background:rgba(45,156,219,.13)}
.section-card{padding:1.2rem 1.25rem;border-radius:20px;background:#fff;border:1px solid #e7ebf0;margin:.65rem 0;box-shadow:0 8px 24px rgba(15,23,42,.05)}
.result-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:.6rem 0 1rem}.result-card{padding:1.2rem 1.25rem;border-radius:20px;background:linear-gradient(145deg,#fbfcfe,#f4f7fb);border:1px solid #dfe6ef;min-height:145px}.result-label{font-size:.78rem;font-weight:850;color:#8a6d22;margin-bottom:.25rem}.result-value{font-size:1.22rem;font-weight:900;color:#111827;line-height:1.5}.result-sub{font-size:.92rem;color:#657284;line-height:1.5;margin-top:.4rem}.score-row{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:.8rem 0 .35rem;font-weight:850;font-size:1.04rem}.score-pct{direction:ltr;unicode-bidi:isolate;white-space:nowrap}.mini{font-size:.83rem;color:#7b8795}.analysis-chip{display:inline-block;padding:.28rem .55rem;border-radius:999px;background:#eef6ff;border:1px solid #d6e9ff;font-size:.78rem;font-weight:800;margin:.15rem}.danger-chip{background:#fff4ed;border-color:#ffd8c2;color:#9a3412}
[data-testid="stRadio"] label{line-height:1.62}[data-testid="stProgress"]{direction:ltr}div.stButton>button{border-radius:14px;font-weight:850;min-height:3.2rem}
@media(max-width:640px){.block-container{padding-left:1rem;padding-right:1rem;padding-top:4.7rem}.gap-hero{padding:1.35rem 1.05rem;border-radius:22px}.gap-title{font-size:1.48rem}.gap-ar{font-size:1.08rem}.gap-copy{font-size:.92rem}.result-grid{grid-template-columns:1fr}.result-card{min-height:auto}}
</style>
""", unsafe_allow_html=True)

if "gap_lang" not in st.session_state:
    st.session_state.gap_lang = "العربية"
lang_label = st.radio("Language / اللغة", ["العربية", "English"], horizontal=True, key="gap_lang", label_visibility="collapsed")
lang = "ar" if lang_label == "العربية" else "en"
T = TEXT[lang]
rtl = lang == "ar"
if rtl:
    st.markdown("<style>.section-card,.result-card,.mini,[data-testid='stRadio']{direction:rtl;text-align:right}.result-grid{direction:rtl}</style>", unsafe_allow_html=True)

if st.session_state.get("gap_version") != VERSION:
    for key in list(st.session_state.keys()):
        if str(key).startswith("q_") or (str(key).startswith("gap_") and key != "gap_lang"):
            del st.session_state[key]
    st.session_state.gap_version = VERSION

for key, default in [("gap_started",False),("gap_step",0),("gap_answers",{}),("gap_done",False)]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_test():
    for key in list(st.session_state.keys()):
        if str(key).startswith("q_"):
            del st.session_state[key]
    st.session_state.gap_started=False
    st.session_state.gap_step=0
    st.session_state.gap_answers={}
    st.session_state.gap_done=False


def dim_name(key):
    return DIMENSIONS[key][lang]


def q_text(item):
    return item[lang]


def option_text(item):
    return item[lang]


def selected_option(question, index):
    try:
        return question["options"][int(index)]
    except Exception:
        return {"score":0,"risk":0}


def calculate_results():
    earned={k:0.0 for k in DIMENSIONS}; max_points={k:0.0 for k in DIMENSIONS}; risk_points={k:0.0 for k in DIMENSIONS}; details=[]
    for item in QUESTIONS:
        w=float(item.get("weight",1)); d=item["dim"]; max_points[d]+=4*w
        idx=st.session_state.gap_answers.get(item["id"])
        if idx is None: continue
        choice=selected_option(item,idx); earned[d]+=float(choice["score"])*w; risk_points[d]+=float(choice.get("risk",0))*w
        if choice["score"]<4:
            details.append({"id":item["id"],"dim":d,"score":choice["score"],"risk":choice.get("risk",0),"weight":w,"concept":item["concept_ar"] if lang=="ar" else item["concept_en"]})
    pct={}
    for d in DIMENSIONS:
        base=100*earned[d]/max_points[d] if max_points[d] else 0; penalty=min(18,risk_points[d]*4); pct[d]=round(max(0,min(100,base-penalty)))
    overall=round(sum(pct.values())/len(pct)); ordered=sorted(pct.items(),key=lambda x:(x[1],x[0])); primary=ordered[0][0]; secondary=ordered[1][0]; strongest=sorted(pct.items(),key=lambda x:(-x[1],x[0]))[0][0]
    return pct,overall,strongest,primary,secondary,round(sum(risk_points.values()),1),details


def profile_level(overall,pct):
    lowest=min(pct.values())
    if overall>=90 and lowest>=80: key="expert"
    elif overall>=82 and lowest>=65: key="advanced"
    elif overall>=70 and lowest>=55: key="strong"
    elif overall>=52: key="developing"
    else: key="execution"
    return PROFILE_COPY[lang][key]


def gap_label(score,rank):
    if score>=90: return T["calibration"] if rank==1 else T["calibration2"]
    return T["primary"] if rank==1 else T["secondary"]


def analytical_profile(pct,overall,primary,details):
    high=[d for d,s in pct.items() if s>=85]
    low=sorted(pct.items(),key=lambda x:x[1])[:2]
    if lang=="ar":
        strength_txt=("أداؤك يظهر ثباتًا قويًا في " + "، ".join(DIMENSIONS[d]["ar"] for d in high) + ".") if high else "النتيجة لا تُظهر بعد بُعدًا ثابتًا فوق 85%."
        gap_txt=f"أضعف بُعد حاليًا هو {DIMENSIONS[primary]['ar']} عند {pct[primary]}%. الفجوة هنا لا تعني نقص خبرة عامة؛ تعني أن بعض السيناريوهات دفعتك لاختيار خطوة منطقية لكنها لم تكن الأعلى قيمة تشخيصية في تلك اللحظة."
    else:
        strength_txt=("Your performance shows strong consistency in " + ", ".join(DIMENSIONS[d]["en"] for d in high) + ".") if high else "No dimension is yet consistently above 85%."
        gap_txt=f"Your lowest current dimension is {DIMENSIONS[primary]['en']} at {pct[primary]}%. This does not imply weak overall experience; it means some scenarios led you toward a reasonable action that was not the highest-value diagnostic decision at that moment."
    return strength_txt,gap_txt,low

st.markdown(f"""
<div class="gap-hero" style="direction:{'rtl' if rtl else 'ltr'};text-align:{'right' if rtl else 'left'}">
<div class="gap-kicker">PHARMACEUTICAL QC · ANALYTICAL DECISION MAKING</div>
<div class="gap-title">{TITLE}</div>
<div class="gap-ar">{T['hero']}</div>
<div class="gap-copy">{T['hero_copy']}</div>
<span class="tag">{TAGLINE}</span><span class="tag version">{VERSION}</span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.gap_started:
    st.markdown(f"<div class='section-card'><h2>{T['landing_h']}</h2><p>{T['landing_p1']}</p><p>{T['landing_p2']}</p></div>", unsafe_allow_html=True)
    cols=st.columns(2)
    landing_desc={
        "science":{"ar":"هل تقرأ العلاقة بين RT وPeak Width والضغط والـResolution؟","en":"Can you connect RT, peak width, pressure, and resolution?"},
        "investigation":{"ar":"هل تختار السؤال أو الاختبار الأعلى قيمة قبل الحل؟","en":"Do you choose the highest-value question or test before the fix?"},
        "evidence":{"ar":"هل تعرف حدود ما أثبته الدليل فعلًا؟","en":"Do you recognize the limits of what evidence actually proves?"},
        "gmp":{"ar":"هل يظل قرارك صحيحًا تحت ضغط الحصول على Passing result؟","en":"Does your decision remain sound under pressure to obtain a passing result?"},
        "instrument":{"ar":"هل تستطيع عزل Pump / Injector / Column / Detector بدل تبديل الأجزاء؟","en":"Can you isolate Pump / Injector / Column / Detector rather than swapping parts?"},
        "decision":{"ar":"هل تفرق بين involvement والآلية الدقيقة وRoot Cause confirmed؟","en":"Can you separate component involvement, exact mechanism, and confirmed root cause?"},
    }
    for i,d in enumerate(DIMENSIONS):
        with cols[i%2]: st.markdown(f"<div class='section-card'><h3>{dim_name(d)}</h3><p>{landing_desc[d][lang]}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<p class='mini'>{T['meta']}</p>", unsafe_allow_html=True)
    if st.button(T["start"],type="primary",use_container_width=True): st.session_state.gap_started=True; st.session_state.gap_step=0; st.rerun()
    st.page_link("app.py",label=T["assistant_link"],use_container_width=True)
    st.stop()

if st.session_state.gap_done:
    pct,overall,strongest,primary,secondary,total_risk,details=calculate_results(); level,level_desc=profile_level(overall,pct); primary_label=gap_label(pct[primary],1); secondary_label=gap_label(pct[secondary],2)
    st.markdown(f"<div class='section-card'><div class='result-label'>{VERSION}</div><h2>{T['result']}: <span dir='ltr'>{overall}/100</span></h2><h3>{level}</h3><p>{level_desc}</p></div>",unsafe_allow_html=True)
    st.markdown(f"""<div class='result-grid'>
    <div class='result-card'><div class='result-label'>{T['strongest']}</div><div class='result-value'>{dim_name(strongest)}</div><div class='result-sub' dir='ltr'>{pct[strongest]}%</div></div>
    <div class='result-card'><div class='result-label'>{primary_label}</div><div class='result-value'>{dim_name(primary)}</div><div class='result-sub' dir='ltr'>{pct[primary]}%</div></div>
    <div class='result-card'><div class='result-label'>{secondary_label}</div><div class='result-value'>{dim_name(secondary)}</div><div class='result-sub' dir='ltr'>{pct[secondary]}%</div></div>
    </div>""",unsafe_allow_html=True)
    st.markdown(f"### {T['map']}")
    for d in DIMENSIONS:
        st.markdown(f"<div class='score-row'><span>{dim_name(d)}</span><span class='score-pct'>{pct[d]}%</span></div>",unsafe_allow_html=True); st.progress(pct[d]/100)

    strength_txt,gap_txt,_=analytical_profile(pct,overall,primary,details)
    st.markdown(f"### {T['analysis']}")
    st.markdown(f"<div class='section-card'><h3>{T['profile']}</h3><p>{strength_txt}</p><p>{gap_txt}</p></div>",unsafe_allow_html=True)

    primary_misses=sorted([x for x in details if x['dim']==primary],key=lambda x:(-(4-x['score'])*x['weight'],-x['risk']))
    if primary_misses:
        chips="".join(f"<span class='analysis-chip'>{x['concept']}</span>" for x in primary_misses[:3])
        expl=("أكثر ما خفّض هذا البُعد كان مرتبطًا بالموضوعات التالية. هذه ليست قائمة «إجابات صحيحة»، لكنها توضح أين كان منطق القرار أقل قوة من أفضل اختيار ممكن:" if lang=="ar" else "The largest losses in this dimension came from the following concepts. This is not an answer key; it shows where your decision logic was weaker than the best available option:")
        st.markdown(f"<div class='section-card'><h3>{T['why_gap']}</h3><p>{expl}</p>{chips}</div>",unsafe_allow_html=True)

    weak_all=sorted(details,key=lambda x:(-(4-x['score'])*x['weight'],-x['risk']))[:5]
    if weak_all:
        items="".join(f"<li>{x['concept']} — {('قرار خطر على سلامة التحقيق' if x['risk'] else 'اختيار أقل قيمة تشخيصية') if lang=='ar' else ('Investigation-integrity risk' if x['risk'] else 'Lower diagnostic value')}</li>" for x in weak_all)
        st.markdown(f"<div class='section-card'><h3>{T['cost_points']}</h3><ul>{items}</ul></div>",unsafe_allow_html=True)

    strong_dims=[d for d,s in sorted(pct.items(),key=lambda x:-x[1]) if s>=85][:3]
    if strong_dims:
        items="".join(f"<li><b>{dim_name(d)}</b>: {STRENGTH_COPY[d][lang]}</li>" for d in strong_dims)
        st.markdown(f"<div class='section-card'><h3>{T['strengths']}</h3><ul>{items}</ul></div>",unsafe_allow_html=True)

    actions=ACTION_MAP[primary][lang]
    st.markdown(f"<div class='section-card'><h3>{T['next_actions']}</h3><ol><li>{actions[0]}</li><li>{actions[1]}</li><li>{actions[2]}</li></ol></div>",unsafe_allow_html=True)
    if total_risk>0: st.markdown(f"<div class='section-card'><h3>{T['risk_note']}</h3><p>{T['risk_text']}</p></div>",unsafe_allow_html=True)

    share_text=(f"The QC Analyst Decision Gap™ — {VERSION}\n{T['result']}: {overall}/100\n{level}\n{T['strongest']}: {dim_name(strongest)} ({pct[strongest]}%)\n{primary_label}: {dim_name(primary)} ({pct[primary]}%)\n{secondary_label}: {dim_name(secondary)} ({pct[secondary]}%)\n{TAGLINE}")
    with st.expander(T["share"]): st.code(share_text,language=None)
    st.markdown(f"### {T['to_case']}"); st.write(T["to_case_copy"]); st.page_link("app.py",label=T["open_assistant"],use_container_width=True)
    if st.button(T["reset"],use_container_width=True): reset_test(); st.rerun()
    st.stop()

# QUIZ FLOW
dim_keys=list(DIMENSIONS.keys()); step=st.session_state.gap_step; current_dim=dim_keys[step]; questions=[x for x in QUESTIONS if x['dim']==current_dim]
st.progress(step/len(dim_keys))
st.markdown(f"<div class='section-card'><div class='result-label'>{T['stage']} {step+1} / 6 · {VERSION}</div><div class='result-value'>{dim_name(current_dim)}</div><p class='mini'>{T['choose']}</p></div>",unsafe_allow_html=True)
for item in questions:
    options=list(range(len(item['options']))); existing=st.session_state.gap_answers.get(item['id']); idx=existing if isinstance(existing,int) and 0<=existing<len(options) else None
    ans=st.radio(f"{item['id']}. {q_text(item)}",options,index=idx,key=f"q_{item['id']}",format_func=lambda i,item=item: option_text(item['options'][i]))
    if ans is not None: st.session_state.gap_answers[item['id']]=ans
    st.markdown("---")
answered_current=all(item['id'] in st.session_state.gap_answers for item in questions)
left,right=st.columns(2)
with left:
    if step>0 and st.button(T['prev'],use_container_width=True): st.session_state.gap_step-=1; st.rerun()
with right:
    label=T['show'] if step==len(dim_keys)-1 else T['next']
    if st.button(label,type='primary',use_container_width=True,disabled=not answered_current):
        if step==len(dim_keys)-1: st.session_state.gap_done=True
        else: st.session_state.gap_step+=1
        st.rerun()
if not answered_current: st.caption(T['answer_all'])
