# Yahia QC Instrument Lifecycle — UX ↔ User Need ↔ Business Goal Map

## Product principle
Every important screen should answer four questions in this order:
1. What does the user need to decide or do now?
2. What evidence supports that action?
3. What is the smallest next action?
4. What product/business outcome does that experience support?

The application is not designed as a collection of features. It is designed around recurring QC jobs-to-be-done.

## Primary user groups

| User | Core need | UX response | Product/business outcome |
|---|---|---|---|
| QC Analyst | Find the right instrument, log what happened quickly, avoid transcription errors | Task-first quick actions, camera-assisted identity capture, event-first observation flow | Faster activation, frequent daily use, cleaner data |
| Calibration / Maintenance Coordinator | Know what is due, overdue, OOC and what evidence is missing | Due-date prioritization, Cal & PM workspace, OOC visibility, next action | Recurring weekly/monthly use, operational dependency |
| QC Supervisor / Manager | Know what needs attention, why, and whether capacity is enough | Priority queue, Availability/Utilization, lifecycle portfolio, management signals | Management value, retention, broader instrument coverage |
| QA / Auditor / Reviewer | Trace history and distinguish facts from interpretation | Evidence-first reports, lifecycle history, Observed / Inferred / Unknown separation, RLS | Trust, credibility, adoption in controlled environments |
| New user / Team lead | Get value without rebuilding everything manually | Excel import, clear template, first-value onboarding, progressive disclosure | Lower onboarding friction, higher activation |

## Experience goals and product metrics

### 1. Activation
**User outcome:** first useful view quickly.

Design response:
- If there are no instruments: show one clear start path: Import Excel or Add first instrument.
- Do not expose advanced modules before the first record unless needed.
- Explain that only matching Excel headers are imported.

Suggested product metric: account reaches at least 1 instrument + 1 lifecycle record.

### 2. Time-to-value
**User outcome:** know what needs action without reading the whole database.

Design response:
- Dashboard opens with system state and priority attention.
- Role-based focus card explains the most relevant action for the current user.
- Each signal should end in a clear destination/action.

Suggested product metric: user reaches a decision/action screen in <= 2 interactions from Dashboard.

### 3. Retention
**User outcome:** application remains useful after initial setup.

Design response:
- Monthly Availability + Utilization.
- Calibration / PM / Qualification due dates.
- Open event/OOC tracking.
- Performance trend and recurring review.

Suggested product metric: user returns monthly and records performance/control activity.

### 4. Trust
**User outcome:** understand what the system knows, what it infers, and what remains missing.

Design response:
- Missing Evidence is visible rather than converted to zero or assumed values.
- Observed / Inferred / Unknown separation.
- RLS user isolation.
- GMP boundary remains explicit.

Suggested product metric: low correction/rework rate and high report usage.

### 5. Expansion / value growth
**User outcome:** application becomes more useful as more of the instrument portfolio is covered.

Design response:
- Portfolio coverage.
- Management reports.
- Capacity / reliability insights.
- Instrument lifecycle from Need to Retirement.

Suggested product metric: number of active instruments with complete lifecycle + monthly performance records.

### 6. Product learning
**User outcome:** easy way to report missing needs and friction.

Design response:
- Contextual Feedback entry.
- Ask after meaningful moments (report generated, lifecycle completed), not during data entry.

Suggested product metric: feedback rate and top recurring friction themes.

## Navigation rule
Navigation should be task-first, not software-first.

Top-level mental model:
- Dashboard = Decide what needs attention
- Lifecycle = Move the instrument forward
- Passport = Identify the instrument
- Cal & PM = Keep routine controls current
- Performance = Understand capacity and reliability
- Events = Record what happened
- Investigate = Decide what evidence to test next
- Reports = Share a decision-ready view
- Guide = Learn how to use the product correctly

## Visual hierarchy rule
1. Current risk / state
2. Next action
3. Supporting evidence
4. Detail / history

Red = action required, amber = review, blue = watch/information, green = controlled/healthy. Do not use these colors decoratively.

## Mobile rule
The mobile screen should never require the user to scan a dashboard before knowing the next action. Use short cards, collapsed detail, large tap targets, and one primary action per context.

## Arabic / English rule
Arabic screens use true RTL narrative flow; technical IDs, model numbers, URS/PR/PO/IQ/OQ/PQ and serial numbers remain stable LTR tokens where necessary. Language is a usability requirement, not decoration.

## Product promise
**Enter less. Decide better. Keep the instrument story connected.**

Every new feature should be rejected or redesigned if it does not improve one of these three outcomes.
