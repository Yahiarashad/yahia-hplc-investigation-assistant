from __future__ import annotations
import json
import streamlit as st

MODULES = [
    ("instruments","Instrument Registry"),
    ("lifecycle","Lifecycle"),
    ("controls","Calibration / PM"),
    ("events","Events / OOC"),
    ("investigations","Investigations"),
    ("performance","Performance"),
    ("reports","Reports"),
    ("management","Management"),
]
ACTIONS = ["view","add","edit","delete","approve"]

ROLE_PRESETS = {
    "QC Analyst": {"instruments":["view","add","edit"],"lifecycle":["view"],"events":["view","add","edit"],"investigations":["view","add","edit"],"reports":["view"]},
    "QC Supervisor": {m:[a for a in ACTIONS if a!="delete"] for m,_ in MODULES},
    "QC Manager": {m:[a for a in ACTIONS if a!="delete"] for m,_ in MODULES},
    "QC Director / Head": {"instruments":["view"],"performance":["view"],"reports":["view"],"management":["view","approve"]},
    "Calibration / Maintenance": {"instruments":["view"],"lifecycle":["view","edit"],"controls":["view","add","edit"],"events":["view","add"],"reports":["view"]},
    "QA / Reviewer": {"instruments":["view"],"lifecycle":["view"],"controls":["view"],"events":["view"],"investigations":["view"],"reports":["view","approve"],"management":["view"]},
    "Read Only / Auditor": {m:["view"] for m,_ in MODULES},
}

def _preset(role):
    src=ROLE_PRESETS.get(role,{})
    return {m:{a:(a in src.get(m,[])) for a in ACTIONS} for m,_ in MODULES}

def _uid():
    u=_auth_user() if "_auth_user" in globals() else {}
    return str(u.get("id") or "")

def _access_rows():
    rows,_,ok=_db_list("app_user_access", order="created_at.asc")
    return rows if ok else []

def render_admin_control_center():
    st.markdown("## 🛡 Admin Control Center")
    st.caption("Controlled access · clear accountability · complete traceability")
    me=_uid()
    mine=[x for x in _access_rows() if str(x.get("user_id"))==me]
    if not mine or not mine[0].get("is_admin") or mine[0].get("account_status")!="active":
        st.error("Administrator privilege is required.")
        return
    rows=_access_rows()
    if not rows:
        st.info("No access profiles yet.")
        return
    labels={str(r["user_id"]): (r.get("display_name") or str(r["user_id"])[:8])+" · "+r.get("app_role","") for r in rows}
    uid=st.selectbox("User", list(labels), format_func=lambda x: labels[x])
    row=next(r for r in rows if str(r["user_id"])==uid)
    c1,c2=st.columns(2)
    role=c1.selectbox("Assigned role", list(ROLE_PRESETS), index=list(ROLE_PRESETS).index(row.get("app_role")) if row.get("app_role") in ROLE_PRESETS else 0)
    status=c2.selectbox("Account status", ["pending","active","suspended"], index=["pending","active","suspended"].index(row.get("account_status","pending")))
    is_admin=st.checkbox("Administrator", value=bool(row.get("is_admin")))
    current=row.get("permissions") or _preset(role)
    if st.button("Load role preset", use_container_width=True):
        current=_preset(role); st.session_state["admin_perm_draft"]=current
    current=st.session_state.get("admin_perm_draft",current)
    st.markdown("### Privileges")
    new={}
    for mod,label in MODULES:
        cols=st.columns([2,1,1,1,1,1])
        cols[0].markdown(f"**{label}**")
        new[mod]={}
        for i,a in enumerate(ACTIONS,1):
            new[mod][a]=cols[i].checkbox(a.title(), value=bool((current.get(mod) or {}).get(a)), key=f"perm_{uid}_{mod}_{a}")
    reason=st.text_input("Reason for access change", placeholder="Required for traceability")
    if st.button("Save privileges", type="primary", use_container_width=True, disabled=not reason.strip()):
        payload={"app_role":role,"account_status":status,"is_admin":is_admin,"permissions":new}
        ok,data,_,err=_db_patch("app_user_access",uid,payload)
        if ok:
            _db_insert("app_audit_log",{"actor_user_id":me,"target_user_id":uid,"action":"ACCESS_UPDATED","module":"admin","old_value":{"app_role":row.get("app_role"),"account_status":row.get("account_status"),"is_admin":row.get("is_admin"),"permissions":row.get("permissions")},"new_value":payload,"reason":reason.strip()})
            st.success("Privileges updated.")
            st.session_state.pop("admin_perm_draft",None)
            st.rerun()
        else:
            st.error(err or "Could not update privileges.")
    st.info("Delete permission is intentionally explicit. For GMP-relevant history, prefer Archive / Void / Retire with reason and audit trail over hard deletion.")
