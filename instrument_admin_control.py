from __future__ import annotations
import json
from urllib import parse as urlparse
import streamlit as st

MODULES = [
    ("instruments","Instrument Registry"),("lifecycle","Lifecycle"),
    ("controls","Calibration / PM"),("events","Events / OOC"),
    ("investigations","Investigations"),("performance","Performance"),
    ("reports","Reports"),("management","Management"),
]
ACTIONS=["view","add","edit","delete","approve"]
ROLE_PRESETS={
 "QC Analyst":{"instruments":["view","add","edit"],"lifecycle":["view"],"events":["view","add","edit"],"investigations":["view","add","edit"],"reports":["view"]},
 "QC Supervisor":{m:[a for a in ACTIONS if a!="delete"] for m,_ in MODULES},
 "QC Manager":{m:[a for a in ACTIONS if a!="delete"] for m,_ in MODULES},
 "QC Director / Head":{"instruments":["view"],"performance":["view"],"reports":["view"],"management":["view","approve"]},
 "Calibration / Maintenance":{"instruments":["view"],"lifecycle":["view","edit"],"controls":["view","add","edit"],"events":["view","add"],"reports":["view"]},
 "QA / Reviewer":{"instruments":["view"],"lifecycle":["view"],"controls":["view"],"events":["view"],"investigations":["view"],"reports":["view","approve"],"management":["view"]},
 "Read Only / Auditor":{m:["view"] for m,_ in MODULES},
}
def _preset(role):
    src=ROLE_PRESETS.get(role,{})
    return {m:{a:a in src.get(m,[]) for a in ACTIONS} for m,_ in MODULES}

def _uid():
    u=_auth_user() if "_auth_user" in globals() else {}
    return str(u.get("id") or "")

def _workspace_context():
    uid=_uid()
    if not uid:return [],None,None
    members,_,ok=_db_list("qc_workspace_members","workspace_id,user_id,job_role,access_role,account_status,is_admin,permissions,joined_at","joined_at.asc")
    mine=[m for m in members if str(m.get("user_id"))==uid and m.get("account_status")=="active"] if ok else []
    if not mine:return [],None,None
    ids=[str(m["workspace_id"]) for m in mine]
    workspaces,_,wok=_db_list("qc_workspaces","id,name,workspace_type,created_by,created_at","created_at.asc")
    visible=[w for w in workspaces if str(w.get("id")) in ids] if wok else []
    active=st.session_state.get("ilm_workspace_id")
    if active not in ids: active=ids[0]; st.session_state.ilm_workspace_id=active
    membership=next((m for m in mine if str(m["workspace_id"])==active),None)
    return visible,active,membership

def render_admin_control_center():
    st.markdown("## 🛡 Admin Control Center")
    st.caption("Workspace members · privileges · accountability")
    workspaces,wid,me=_workspace_context()
    if not wid or not me:
        st.error("No active workspace membership was found."); return
    if not me.get("is_admin"):
        st.error("Workspace administrator privilege is required."); return
    ws=next((w for w in workspaces if str(w["id"])==wid),{})
    st.markdown(f"### {ws.get('name','Workspace')}")
    members,_,ok=_db_list("qc_workspace_members","workspace_id,user_id,job_role,access_role,account_status,is_admin,permissions,joined_at","joined_at.asc")
    members=[m for m in members if str(m.get("workspace_id"))==wid] if ok else []
    if not members: st.info("No members found."); return
    labels={str(m["user_id"]):str(m["user_id"])[:8]+" · "+str(m.get("job_role") or "Member") for m in members}
    uid=st.selectbox("Member",list(labels),format_func=lambda x:labels[x])
    row=next(m for m in members if str(m["user_id"])==uid)
    c1,c2=st.columns(2)
    roles=list(ROLE_PRESETS)
    role=c1.selectbox("Job role",roles,index=roles.index(row.get("job_role")) if row.get("job_role") in roles else 0)
    status_opts=["pending","active","suspended"]
    status=c2.selectbox("Account status",status_opts,index=status_opts.index(row.get("account_status","active")))
    is_admin=st.checkbox("Workspace administrator",value=bool(row.get("is_admin")))
    current=row.get("permissions") or _preset(role)
    if st.button("Load role preset",use_container_width=True):
        st.session_state.admin_perm_draft=_preset(role); st.rerun()
    current=st.session_state.get("admin_perm_draft",current)
    st.markdown("### Privileges")
    new={}
    for mod,label in MODULES:
        cols=st.columns([2,1,1,1,1,1]); cols[0].markdown(f"**{label}**"); new[mod]={}
        for i,a in enumerate(ACTIONS,1):
            new[mod][a]=cols[i].checkbox(a.title(),value=bool((current.get(mod) or {}).get(a)),key=f"perm_{wid}_{uid}_{mod}_{a}")
    reason=st.text_input("Reason for access change",placeholder="Required for traceability")
    if st.button("Save privileges",type="primary",use_container_width=True,disabled=not reason.strip()):
        payload={"job_role":role,"account_status":status,"is_admin":is_admin,"permissions":new,"access_role":"Admin" if is_admin else "Member"}
        path=f"qc_workspace_members?workspace_id=eq.{urlparse.quote(wid)}&user_id=eq.{urlparse.quote(uid)}"
        ok,_,_,err=_db_request(path,method="PATCH",payload=payload,prefer="return=representation")
        if ok:
            _db_insert("qc_access_audit",{"workspace_id":wid,"actor_user_id":_uid(),"target_user_id":uid,"action":"ACCESS_UPDATED","module":"admin","old_value":{"job_role":row.get("job_role"),"account_status":row.get("account_status"),"is_admin":row.get("is_admin"),"permissions":row.get("permissions")},"new_value":payload,"reason":reason.strip()})
            st.session_state.pop("admin_perm_draft",None); st.success("Privileges updated."); st.rerun()
        else: st.error(err or "Could not update privileges.")
    st.divider()
    st.markdown("### Audit trail")
    audit,_,aok=_db_list("qc_access_audit","id,actor_user_id,target_user_id,action,module,reason,created_at","created_at.desc")
    audit=[x for x in audit if str(x.get("workspace_id",wid))==wid] if aok else []
    if audit: st.dataframe(audit[:50],use_container_width=True,hide_index=True)
    else: st.caption("No access changes recorded yet.")
    st.info("For GMP-relevant history, prefer Archive / Void / Retire with reason and audit trail over hard deletion.")
