import os

def fix_app():
    path = r'd:\QuVote\app.py'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    for i, line in enumerate(lines):
        if '    with t1:' in line and 1500 < i < 1650:
            start_idx = i
        if '    # ── TAB 2: CANDIDATE MANAGER ────────────────────────────' in line and 1650 < i < 1800:
            end_idx = i

    if start_idx == -1 or end_idx == -1:
        # Fallback to broader markers if line numbers shifted significantly
        for i, line in enumerate(lines):
            if '    with t1:' in line:
                start_idx = i
            if '# ── TAB 2: CANDIDATE MANAGER ────────────────────────────' in line:
                end_idx = i

    if start_idx != -1 and end_idx != -1:
        new_content = [
            "    with t1:\n",
            "        import datetime as _dt_r\n",
            "        all_polls_r = get_all_polls()\n",
            "        now_r = _dt_r.datetime.now()\n",
            "\n",
            "        if not all_polls_r:\n",
            "            st.info(\"No election polls found in the system.\")\n",
            "        else:\n",
            "            # Categorize Polls\n",
            "            live_polls = [p for p in all_polls_r if p[\"start_time\"] <= now_r <= p[\"end_time\"]]\n",
            "            previous_polls = [p for p in all_polls_r if now_r > p[\"end_time\"]]\n",
            "            upcoming_polls = [p for p in all_polls_r if now_r < p[\"start_time\"]]\n",
            "\n",
            "            # — SECTION 1: LIVE POLLING ———————————————————\n",
            "            st.markdown(\"### 🔴 Live Polling\")\n",
            "            if not live_polls:\n",
            "                st.caption(\"No polls are currently active.\")\n",
            "            else:\n",
            "                for lp in live_polls:\n",
            "                    lpid = lp[\"poll_id\"]\n",
            "                    lp_votes = get_poll_vote_counts(lpid)\n",
            "                    lp_total = sum(lp_votes.values()) if lp_votes else 0\n",
            "                    lp_cands = get_poll_candidates(lpid)\n",
            "                    lp_eligible = total_eligible_voters()\n",
            "\n",
            "                    with st.expander(f\"🗳️ {lp['name']}\", expanded=True):\n",
            "                        st.markdown(f\"**Description:** {lp.get('description', 'No description available.')}\")\n",
            "                        st.markdown(\"---\")\n",
            "                        \n",
            "                        # Candidates with symbols on the right\n",
            "                        st.markdown(\"#### Candidates\")\n",
            "                        if lp_cands:\n",
            "                            for c in lp_cands:\n",
            "                                c_name = c[\"name\"]\n",
            "                                c_votes = lp_votes.get(c_name, 0)\n",
            "                                c_img = c.get(\"symbol_image_b64\", \"\")\n",
            "                                c_sym = c.get(\"symbol\", \"🗳️\")\n",
            "                                \n",
            "                                symbol_html = (f\"<img src='data:image/png;base64,{c_img}' width='32' height='32' style='vertical-align:middle; margin-left:40px; border-radius:6px;'>\" \n",
            "                                              if c_img else f\"<span style='margin-left:40px; font-size:1.5rem; vertical-align:middle;'>{c_sym}</span>\")\n",
            "                                \n",
            "                                st.markdown(f\"\"\"\n",
            "                                <div style='display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:12px 20px; border-radius:12px; margin-bottom:8px; border:1px solid rgba(255,255,255,0.05);'>\n",
            "                                    <div style='display:flex; align-items:center;'>\n",
            "                                        <span style='font-weight:700; color:#e2e8f0; font-size:1.1rem;'>{c_name}</span>\n",
            "                                        {symbol_html}\n",
            "                                    </div>\n",
            "                                    <div style='font-weight:800; color:#a5b4fc; font-size:1.2rem;'>{c_votes} <span style='font-size:0.8rem; color:#64748b; font-weight:400;'>votes</span></div>\n",
            "                                </div>\n",
            "                                \"\"\", unsafe_allow_html=True)\n",
            "                        \n",
            "                        st.markdown(\"<br>\", unsafe_allow_html=True)\n",
            "                        # Stats: Total Voters vs Participated\n",
            "                        sc1, sc2 = st.columns(2)\n",
            "                        sc1.metric(\"👥 Total Voters\", lp_eligible)\n",
            "                        sc2.metric(\"📥 Participated\", lp_total)\n",
            "\n",
            "                        # Lead Comparison\n",
            "                        if lp_votes and len(lp_votes) > 1:\n",
            "                            sorted_v = sorted(lp_votes.items(), key=lambda x: x[1], reverse=True)\n",
            "                            leader_name, leader_v = sorted_v[0]\n",
            "                            runner_up_name, runner_up_v = sorted_v[1]\n",
            "                            diff = leader_v - runner_up_v\n",
            "                            if diff > 0:\n",
            "                                st.info(f\"🚀 **{leader_name}** is leading by **{diff}** votes over {runner_up_name}\")\n",
            "                            elif diff == 0 and leader_v > 0:\n",
            "                                st.warning(f\"⚖️ **{leader_name}** and **{runner_up_name}** are currently tied!\")\n",
            "                        elif lp_votes and len(lp_votes) == 1:\n",
            "                            st.info(f\"🏆 **{list(lp_votes.keys())[0]}** is leading\")\n",
            "\n",
            "            st.markdown(\"<br><br>\", unsafe_allow_html=True)\n",
            "            \n",
            "            # — SECTION 2: PREVIOUS POLLING ———————————————————\n",
            "            st.markdown(\"### 📂 Previous Polling\")\n",
            "            if not previous_polls:\n",
            "                st.caption(\"No previous polls found.\")\n",
            "            else:\n",
            "                for pp in previous_polls:\n",
            "                    ppid = pp[\"poll_id\"]\n",
            "                    pp_votes = get_poll_vote_counts(ppid)\n",
            "                    pp_total = sum(pp_votes.values()) if pp_votes else 0\n",
            "                    pp_cands = get_poll_candidates(ppid)\n",
            "                    pp_eligible = total_eligible_voters()\n",
            "\n",
            "                    with st.expander(f\"📜 {pp['name']}\"):\n",
            "                        st.markdown(f\"**Description:** {pp.get('description', 'No description available.')}\")\n",
            "                        st.markdown(\"---\")\n",
            "                        \n",
            "                        # Final Standings with Symbols\n",
            "                        st.markdown(\"#### Final Results\")\n",
            "                        if pp_cands:\n",
            "                            for c in sorted(pp_cands, key=lambda x: pp_votes.get(x[\"name\"],0), reverse=True):\n",
            "                                c_name = c[\"name\"]\n",
            "                                c_votes = pp_votes.get(c_name, 0)\n",
            "                                c_img = c.get(\"symbol_image_b64\", \"\")\n",
            "                                c_sym = c.get(\"symbol\", \"🗳️\")\n",
            "                                \n",
            "                                symbol_html = (f\"<img src='data:image/png;base64,{c_img}' width='32' height='32' style='vertical-align:middle; margin-left:40px; border-radius:6px;'>\" \n",
            "                                              if c_img else f\"<span style='margin-left:40px; font-size:1.5rem; vertical-align:middle;'>{c_sym}</span>\")\n",
            "                                \n",
            "                                st.markdown(f\"\"\"\n",
            "                                <div style='display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:10px 18px; border-radius:10px; margin-bottom:6px;'>\n",
            "                                    <div style='display:flex; align-items:center;'>\n",
            "                                        <span style='font-weight:600; color:#cbd5e1;'>{c_name}</span>\n",
            "                                        {symbol_html}\n",
            "                                    </div>\n",
            "                                    <div style='font-weight:700; color:#818cf8;'>{c_votes} votes</div>\n",
            "                                </div>\n",
            "                                \"\"\", unsafe_allow_html=True)\n",
            "\n",
            "                        st.markdown(\"<br>\", unsafe_allow_html=True)\n",
            "                        # Stats\n",
            "                        psc1, psc2 = st.columns(2)\n",
            "                        psc1.metric(\"👥 Total Voters\", pp_eligible)\n",
            "                        psc2.metric(\"📥 Participated\", pp_total)\n",
            "\n",
            "                        # Winner Declaration\n",
            "                        if pp_votes:\n",
            "                            winner = max(pp_votes, key=pp_votes.get)\n",
            "                            st.success(f\"🎊 **Final Verdict:** **{winner}** has won the election!\")\n",
            "            \n",
            "            # — SECTION 3: UPCOMING ———————————————————\n",
            "            if upcoming_polls:\n",
            "                with st.expander(\"🔜 Upcoming Polls\"):\n",
            "                    for up in upcoming_polls:\n",
            "                        st.write(f\"• **{up['name']}** (Scheduled: {up['start_time'].strftime('%Y-%m-%d %H:%M')})\")\n"
        ]
        
        lines[start_idx:end_idx] = new_content
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Successfully fixed Results tab. Replaced lines {start_idx} to {end_idx}.")
    else:
        print(f"Failed to find anchors: start_idx={start_idx}, end_idx={end_idx}")

if __name__ == '__main__':
    fix_app()
