# Yahia QC Instrument Lifecycle & Investigation Intelligence™ — v0.2 User Guide

## Purpose
This product helps Pharmaceutical QC analysts turn scattered instrument lifecycle information into better evidence-based decisions.

**Brand principle:** DON'T GUESS. FOLLOW THE EVIDENCE.

## Why it matters
Instrument identity, maintenance, qualification, calibration, component changes, failures, and investigation notes are often separated. v0.2 connects them into one private user workspace so recurrence and lifecycle risks become visible before they are mistaken for root cause.

## Quick start
1. Create an Instrument Passport.
2. Add current Qualification, PM, and Calibration due dates.
3. Log maintenance and key component changes when they happen.
4. Record failures as observed facts, not diagnoses.
5. Use Command Center to prioritize attention.
6. Use Investigation Intelligence to connect the current problem with history and choose the next discriminating evidence action.

## Core modules
- Command Center
- Digital Instrument Passport
- Maintenance History
- Calibration & Qualification History
- Component Lifecycle
- Instrument Event / Failure Log
- QC Investigation Intelligence™
- QR Digital Passport
- User Guide

## Health Score v2
The Health Score combines:
- instrument operational status,
- qualification / PM / calibration due dates,
- severity of open events,
- repeated 90-day subsystem patterns,
- overdue component lifecycle items.

It is a **prioritization aid only**. It is not a GMP disposition and does not determine instrument fitness or compliance by itself.

## Evidence discipline
- OBSERVED / REPORTED: what is actually known.
- INFERRED: supported interpretation, not confirmed fact.
- UNKNOWN: information still required.
- Recurrence is a pattern, not automatic proof of root cause.
- Root cause should only be called confirmed after a targeted intervention behaves as predicted and credible alternatives are reasonably excluded.

## Data and security
- Supabase Auth handles user accounts.
- Row Level Security isolates each user's rows.
- The app uses a publishable key plus the authenticated user's JWT.
- No service-role key belongs in the Streamlit app.
- Persistent login uses an encrypted refresh-token cookie; the password is not stored in the cookie.

## GxP boundary
This application is decision-support software, not a validated GxP system of record. Keep official GMP records, approvals, deviations, controlled maintenance documents, certificates, and SOP-controlled forms in approved company systems.

## Arabic quick guide | دليل سريع
- أنشئ Passport لكل جهاز.
- أضف مواعيد PM / Calibration / Qualification.
- سجّل الصيانة وتغيير الأجزاء المهمة وقت حدوثها.
- عند حدوث مشكلة، اكتب ما حدث فعلاً قبل كتابة التشخيص.
- استخدم Investigation Intelligence لربط الحالة بتاريخ الجهاز.
- تكرار المشكلة يقوّي الفرضية لكنه لا يثبت Root Cause وحده.

## CTA
Keep the lifecycle history alive. When a problem appears, use the history to decide what evidence to collect next.

**DON'T GUESS. FOLLOW THE EVIDENCE.**
