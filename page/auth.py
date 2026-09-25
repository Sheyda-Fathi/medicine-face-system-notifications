"""Authentication screen for staff passwords and patient face login."""

import streamlit as st

from database.auth_queries import AuthQueries


def show_auth():
    st.markdown(
        """
        <div style="text-align:center; padding:30px 0 8px 0;">
            <h1 style="color:#1E1B3A; margin:6px 0 0 0;">
                Smart Medication System
            </h1>
            <p style="color:#67677A; margin:8px 0 0 0; font-size:18px;">
                Patient medication access through face recognition
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _left, center, _right = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="smms-card">', unsafe_allow_html=True)
        staff_tab, patient_tab = st.tabs(["Staff Login", "Patient Face Login"])

        with staff_tab:
            st.caption("Administrators and doctors sign in with staff credentials.")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button(
                "Log in",
                type="primary",
                use_container_width=True,
                key="btn_staff_login",
            ):
                if not username.strip() or not password:
                    st.error("Username and password are required.")
                else:
                    user, error = AuthQueries().login(username.strip(), password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error(error or "Login failed.")

        with patient_tab:
            from page.face_login import show_face_login

            show_face_login()
            st.caption(
                "A doctor or administrator must register the patient and reference photo first."
            )

        st.markdown("</div>", unsafe_allow_html=True)
