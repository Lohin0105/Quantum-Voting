"""
Patch script: adds Polls tab + updates voter page for active polls.
Run: python patch_polls.py
"""
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# ── 1. Insert t7 Polls tab before admin logout ──────────────────────────────
POLLS_TAB = '''
    # ── TAB 7: POLLS ──────────────────────────────────────
    with t7:
        import datetime as dt_mod2
        st.markdown("### 🗳️ Create New Election Poll")
        with st.form("create_poll_form"):
            poll_name_f   = st.text_input("Election Name", placeholder="e.g. 2025 General Election")
            poll_desc_f   = st.text_area("Description", placeholder="Brief description for voters...")
            col_sd, col_sti = st.columns(2)
            with col_sd:
                p_start_date = st.date_input("Start Date", key="p_start_date")
            with col_sti:
                p_start_ti = st.time_input("Start Time (UTC)", key="p_start_time")
            col_ed, col_eti = st.columns(2)
            with col_ed:
                p_end_date = st.date_input("End Date", key="p_end_date")
            with col_eti:
                p_end_ti = st.time_input("End Time (UTC)", key="p_end_time")
            poll_submitted = st.form_submit_button("🚀 Create Poll & Notify All Voters")
        if poll_submitted:
            if not poll_name_f.strip():
                st.error("Poll name is required.")
            else:
                p_start = dt_mod2.datetime.combine(p_start_date, p_start_ti)
                p_end   = dt_mod2.datetime.combine(p_end_date, p_end_ti)
                if p_end <= p_start:
                    st.error("End time must be after start time.")
                else:
                    new_pid = create_poll(poll_name_f.strip(), poll_desc_f.strip(),
                                          p_start, p_end, st.session_state.get("admin",""))
                    with st.spinner("Sending email to all voters..."):
                        sc = send_poll_announcement_email(poll_name_f.strip(), poll_desc_f.strip(), p_start, p_end)
                        mark_poll_email_sent(new_pid)
                    st.success(f"Poll **{poll_name_f}** created! ID:`{new_pid}` — 📧 {sc} voters notified.")

        st.markdown("---")
        st.markdown("### 🏛️ Manage Candidates Per Poll")
        all_polls_list = get_all_polls()
        if not all_polls_list:
            st.info("No polls yet. Create one above!")
        else:
            poll_opts = {p["poll_id"]: f"{p[\'name\']} [{p[\'poll_id\']}]" for p in all_polls_list}
            sel_pid = st.selectbox("Select Poll", list(poll_opts.keys()),
                                   format_func=lambda x: poll_opts[x], key="admin_sel_poll")
            sel_p = get_poll(sel_pid)
            if sel_p:
                now_u = dt_mod2.datetime.utcnow()
                status_lbl = ("🟢 Active"    if sel_p["start_time"] <= now_u <= sel_p["end_time"]
                              else ("🔜 Upcoming" if now_u < sel_p["start_time"] else "🔴 Ended"))
                st.markdown(
                    f"<div style=\'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);"
                    f"border-radius:10px;padding:0.8rem;\'><b style=\'color:#a5b4fc;\'>{sel_p[\'name\']}</b>"
                    f" &nbsp;<span style=\'color:#64748b;font-size:0.8rem;\'>{status_lbl}</span><br>"
                    f"<span style=\'color:#64748b;font-size:0.78rem;\'>{sel_p[\'start_time\']} → {sel_p[\'end_time\']}</span></div>",
                    unsafe_allow_html=True)

                pcands = get_poll_candidates(sel_pid)
                if pcands:
                    st.markdown(f"**Candidates ({len(pcands)}):**")
                    for pc in pcands:
                        pca, pcb = st.columns([5, 1])
                        with pca:
                            ib = pc.get("symbol_image_b64","")
                            img_tag = (f"<img src=\'data:image/png;base64,{ib}\' width=\'44\' height=\'44\' "
                                       f"style=\'border-radius:6px;margin-right:10px;vertical-align:middle;\'>"
                                       if ib else "<span style=\'font-size:1.8rem;margin-right:10px;\'>🗳️</span>")
                            st.markdown(f"<div style=\'display:flex;align-items:center;background:rgba(255,255,255,0.03);"
                                        f"border-radius:8px;padding:0.5rem;margin:2px 0;\'>"
                                        f"{img_tag}<div><b style=\'color:#e2e8f0;\'>{pc[\'name\']}</b><br>"
                                        f"<span style=\'color:#94a3b8;font-size:0.78rem;\'>{pc.get(\'party\',\'Independent\')} • {pc.get(\'symbol\',\'\')}</span></div></div>",
                                        unsafe_allow_html=True)
                        with pcb:
                            if st.button("❌", key=f"rpc_{sel_pid}_{pc[\'name\']}"):
                                remove_poll_candidate(sel_pid, pc["name"])
                                st.rerun()
                else:
                    st.info("No candidates yet.")

                st.markdown("**➕ Add Candidate:**")
                ia, ib2, ic = st.columns(3)
                with ia:
                    nc_name  = st.text_input("Name", key="pc_nm")
                with ib2:
                    nc_party = st.text_input("Party", key="pc_pty")
                with ic:
                    nc_sym   = st.text_input("Symbol (describe)", key="pc_sym", placeholder="lotus, hand, sun...")

                g1, g2 = st.columns(2)
                with g1:
                    if st.button("🎨 Generate Image", key="gen_sym_img"):
                        if nc_sym.strip():
                            with st.spinner(f"AI generating image for \'{nc_sym}\' (~10s)..."):
                                gimg = generate_symbol_image(nc_sym.strip())
                            if gimg:
                                st.session_state["prev_img"] = gimg
                                st.session_state["prev_sym"] = nc_sym.strip()
                                st.success("✅ Image generated! Preview below.")
                            else:
                                st.error("Generation failed. Check internet.")
                        else:
                            st.warning("Enter symbol description first.")

                if st.session_state.get("prev_img"):
                    st.image(f"data:image/png;base64,{st.session_state[\'prev_img\']}",
                             caption=f"Symbol: {st.session_state.get(\'prev_sym\',\'\')}",
                             width=130)

                with g2:
                    if st.button("➕ Add Candidate", key="apc_btn"):
                        if not nc_name.strip():
                            st.error("Name required.")
                        else:
                            simg = st.session_state.get("prev_img","")
                            if add_poll_candidate(sel_pid, nc_name.strip(),
                                                   nc_party.strip() or "Independent",
                                                   nc_sym.strip(), simg):
                                st.session_state.pop("prev_img", None)
                                st.session_state.pop("prev_sym", None)
                                st.success(f"✅ {nc_name} added!")
                                st.rerun()
                            else:
                                st.error("Already exists in this poll.")

                st.markdown("---")
                p_votes = get_poll_vote_counts(sel_pid)
                p_total = total_poll_votes(sel_pid)
                st.markdown(f"**📊 Poll Results: {p_total} votes**")
                if p_votes:
                    for cn, cv in sorted(p_votes.items(), key=lambda x: x[1], reverse=True):
                        pv = round(cv/p_total*100,1) if p_total else 0
                        st.markdown(f"**{cn}**: {cv} votes ({pv}%)")
                        st.progress(pv/100)
                else:
                    st.info("No votes yet for this poll.")

                if st.button("🗑️ Delete Poll", key=f"dp_{sel_pid}"):
                    delete_poll(sel_pid)
                    st.warning("Poll deleted.")
                    st.rerun()

'''

VOTER_ACTIVE_POLL = '''
# ═══════════════════════════════════════════════════════════
# PAGE: ACTIVE POLL VOTING
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "vote":
    # Check for an active poll and override the standard vote UI
    _active_poll = get_active_poll()
    if _active_poll:
        _poll_id = _active_poll["poll_id"]
        _poll_cands = get_poll_candidates(_poll_id)
        username = st.session_state.get("user")
        user_doc2 = get_user(username) if username else None
        vid2 = user_doc2.get("vote_id","") if user_doc2 else ""

        st.markdown(f\'\'\'
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.1));
             border:1px solid rgba(99,102,241,0.35);border-radius:16px;padding:1.2rem;margin:0.5rem 0;text-align:center;">
          <div style="font-size:0.8rem;color:#6366f1;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;">Active Election</div>
          <div style="font-size:1.2rem;font-weight:700;color:#a5b4fc;margin:6px 0;">{_active_poll["name"]}</div>
          <div style="color:#64748b;font-size:0.85rem;">{_active_poll.get("description","")}</div>
        </div>\'\'\', unsafe_allow_html=True)

        if has_voted_in_poll(_poll_id, vid2):
            st.markdown(\'\'\'
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
                 border-radius:14px;padding:1.5rem;text-align:center;margin:1rem 0;">
              <div style="font-size:2.5rem;">✅</div>
              <div style="font-weight:700;color:#6ee7b7;font-size:1.1rem;">You have already voted in this election!</div>
            </div>\'\'\', unsafe_allow_html=True)
        elif not _poll_cands:
            st.warning("⚠️ No candidates have been added to this election yet.")
        else:
            st.markdown("**Select your candidate:**")
            for _cand in _poll_cands:
                _img_b64 = _cand.get("symbol_image_b64","")
                if _img_b64:
                    _img_html = f"<img src=\'data:image/png;base64,{_img_b64}\' width=\'64\' height=\'64\' style=\'border-radius:10px;object-fit:cover;\'>"
                else:
                    _img_html = f"<div style=\'font-size:3rem;\'>{_cand.get(\'symbol\',\'🗳️\')}</div>"
                st.markdown(f\'\'\'
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                     border-radius:12px;padding:1rem;display:flex;align-items:center;gap:1rem;margin:6px 0;">
                  {_img_html}
                  <div>
                    <div style="font-weight:700;color:#e2e8f0;font-size:1rem;">{_cand["name"]}</div>
                    <div style="color:#94a3b8;font-size:0.82rem;">{_cand.get("party","Independent")}</div>
                    <div style="color:#64748b;font-size:0.75rem;">Symbol: {_cand.get("symbol","")}</div>
                  </div>
                </div>\'\'\', unsafe_allow_html=True)

            _choice = st.radio("Cast your vote for:", [c["name"] for c in _poll_cands], key="poll_vote_choice")
            if st.button("🗳️ Submit Vote", key="submit_poll_vote"):
                save_poll_vote(_poll_id, vid2, _choice)
                mark_voted(vid2)
                _receipt = generate_receipt(vid2, _choice)
                save_receipt(vid2, _receipt)
                voter_ip2 = get_voter_ip()
                log_activity(vid2, voter_ip2, "vote")
                st.session_state["last_receipt"] = _receipt
                st.session_state["last_choice"] = _choice
                st.success(f"✅ Vote submitted for **{_choice}**!")
                st.rerun()

'''

# ── Insert polls tab ────────────────────────────────────────────────────────
search_anchor = '    if st.button("\\U0001f6aa Logout", key="admin_logout"):'
if search_anchor not in code:
    # Try alternate
    for line in code.splitlines():
        if 'admin_logout' in line and 'st.button' in line:
            search_anchor = line.strip()
            print(f"Using anchor: {search_anchor[:60]}")
            break

# Find the divider before logout
import re
# Find line index
lines = code.splitlines(keepends=True)
logout_line_idx = None
for i, line in enumerate(lines):
    if 'admin_logout' in line and 'st.button' in line:
        logout_line_idx = i
        break

if logout_line_idx is not None:
    # Find the divider line before logout
    for i in range(logout_line_idx-1, max(logout_line_idx-5,0), -1):
        if 'divider' in lines[i]:
            # Insert polls tab before this divider
            insert_pos = i
            break
    else:
        insert_pos = logout_line_idx

    lines.insert(insert_pos, POLLS_TAB)
    code = "".join(lines)
    print(f"Inserted polls tab before line {insert_pos+1}")
else:
    print("WARNING: Could not find admin_logout anchor")

# ── Append active poll voter page at the END ────────────────────────────────
# Remove existing 'PAGE: VOTE' overrides if they conflict - just append
# Check if active poll section already exists
if 'Active Election' not in code:
    code = code + "\n\n" + VOTER_ACTIVE_POLL
    print("Appended active poll voter section")
else:
    print("Active poll section already exists")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("DONE - app.py patched successfully!")
